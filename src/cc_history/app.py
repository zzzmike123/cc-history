"""Flask 应用 + pywebview 桌面窗口。"""

import re
import socket
import subprocess
import sys
import threading
import time
from functools import lru_cache
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .data import (
    get_claude_dir,
    get_detailed_stats,
    get_plugins,
    get_real_project_paths,
    get_session_messages,
    get_sessions,
    get_skills,
    load_custom_names,
    load_favorites,
    load_settings,
    save_custom_names,
    save_favorites,
    save_settings,
)

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))

# UUID 格式验证（Claude Code 会话 ID 使用 UUID v4）
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)

# 会话列表缓存
_sessions_cache = {"data": None, "ts": 0}
_CACHE_TTL = 5  # 秒


def _json_error(message, status=500):
    return jsonify({"error": message}), status


def _is_valid_uuid(session_id):
    """验证是否为合法 UUID 格式。"""
    return bool(session_id and _UUID_RE.match(session_id))


def _is_under_projects_dir(path):
    """验证路径是否在 .claude/projects 目录下（防止路径穿越）。"""
    try:
        projects_dir = get_claude_dir() / "projects"
        resolved = Path(path).resolve()
        resolved.relative_to(projects_dir.resolve())
        return True
    except (ValueError, OSError):
        return False


def _get_sessions_cached():
    """带缓存的会话列表获取。"""
    now = time.monotonic()
    if _sessions_cache["data"] is not None and now - _sessions_cache["ts"] < _CACHE_TTL:
        return _sessions_cache["data"]
    data = get_sessions()
    _sessions_cache["data"] = data
    _sessions_cache["ts"] = now
    return data


def _session_index():
    return {(s["projectDir"], s["sessionId"]): s for s in _get_sessions_cached()}


def _get_known_session(project_dir, session_id):
    return _session_index().get((project_dir, session_id))


def _get_session_by_id(session_id):
    for session in _get_sessions_cached():
        if session["sessionId"] == session_id:
            return session
    return None


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _clear_sessions_cache():
    """清空会话缓存。"""
    _sessions_cache["data"] = None
    _sessions_cache["ts"] = 0


def _resource_path(*parts):
    """获取源码或 PyInstaller 运行时资源路径。"""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[2]
    return base.joinpath(*parts)


# ========== API Routes ==========

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    from flask import send_file
    icon_path = _resource_path("cat.ico")
    if icon_path.exists():
        return send_file(icon_path, mimetype="image/x-icon")
    return "", 404


@app.route("/api/health")
def api_health():
    return jsonify({"ok": True})


@app.route("/api/projects")
def api_projects():
    """返回项目列表。"""
    try:
        sessions = _get_sessions_cached()
    except Exception as exc:
        return _json_error(f"读取 Claude Code 历史失败：{exc}")

    projects = {}
    for s in sessions:
        proj = s["project"]
        if proj not in projects:
            projects[proj] = {
                "name": proj,
                "realPath": s["realProjectPath"],
                "projectDir": s["projectDir"],
                "sessions": [],
            }
        projects[proj]["sessions"].append({
            "sessionId": s["sessionId"],
            "messageCount": s["messageCount"],
            "firstMessage": s["firstMessage"],
            "firstTimestamp": s["firstTimestamp"],
            "lastTimestamp": s["lastTimestamp"],
            "realPath": s["realProjectPath"],
        })

    return jsonify(list(projects.values()))


@app.route("/api/messages")
def api_messages():
    """返回会话消息。"""
    project_dir = request.args.get("projectDir", "")
    session_id = request.args.get("sessionId", "")
    if not project_dir or not session_id:
        return _json_error("缺少参数", 400)

    if not _is_valid_uuid(session_id):
        return _json_error("无效的会话 ID", 400)

    if not _is_under_projects_dir(project_dir):
        return _json_error("无效的项目路径", 400)

    session = _get_known_session(project_dir, session_id)
    if not session:
        return _json_error("未找到该会话", 404)

    try:
        return jsonify(get_session_messages(session["projectDir"], session["sessionId"]))
    except Exception as exc:
        return _json_error(f"读取会话失败：{exc}")


@app.route("/api/search")
def api_search():
    """搜索消息。"""
    keyword = request.args.get("q", "").strip().lower()
    if not keyword:
        return jsonify([])

    results = []
    try:
        sessions = _get_sessions_cached()
        for s in sessions:
            for msg in get_session_messages(s["projectDir"], s["sessionId"]):
                if keyword in msg["content"].lower():
                    results.append({
                        "sessionId": s["sessionId"],
                        "project": s["project"],
                        "projectDir": s["projectDir"],
                        "realProjectPath": s.get("realProjectPath", ""),
                        "role": msg["role"],
                        "content": msg["content"][:200],
                        "timestamp": msg["timestamp"],
                    })
                    if len(results) >= 50:
                        return jsonify(results)
    except Exception as exc:
        return _json_error(f"搜索失败：{exc}")
    return jsonify(results)


@app.route("/api/custom-names")
def api_get_custom_names():
    """获取所有自定义名称。"""
    return jsonify(load_custom_names())


@app.route("/api/custom-names", methods=["POST"])
def api_set_custom_name():
    """设置自定义名称。"""
    data = request.get_json(silent=True) or {}
    session_id = data.get("sessionId", "")
    name = data.get("name", "")
    if not session_id:
        return _json_error("缺少 sessionId", 400)
    if not _is_valid_uuid(session_id):
        return _json_error("无效的会话 ID", 400)
    if name is None:
        name = ""
    name = str(name).strip()[:120]

    names = load_custom_names()
    if name:
        names[session_id] = name
    else:
        names.pop(session_id, None)
    save_custom_names(names)
    return jsonify({"ok": True})


@app.route("/api/settings")
def api_get_settings():
    """获取设置。"""
    return jsonify(load_settings())


@app.route("/api/settings", methods=["POST"])
def api_save_settings():
    """保存设置。"""
    data = request.get_json(silent=True) or {}
    current = load_settings()

    if "claude_dir" in data:
        claude_dir = str(data["claude_dir"]).strip()
        if claude_dir:
            p = Path(claude_dir).expanduser()
            if not p.exists():
                return _json_error(f"目录不存在：{claude_dir}", 400)
            current["claude_dir"] = str(p)

    if "theme" in data:
        if data["theme"] in ("light", "dark"):
            current["theme"] = data["theme"]

    save_settings(current)
    _clear_sessions_cache()
    return jsonify({"ok": True, "settings": current})


@app.route("/api/favorites")
def api_get_favorites():
    """获取收藏列表。"""
    return jsonify(load_favorites())


@app.route("/api/favorites", methods=["POST"])
def api_toggle_favorite():
    """切换收藏状态。"""
    data = request.get_json(silent=True) or {}
    session_id = data.get("sessionId", "")
    if not session_id:
        return _json_error("缺少 sessionId", 400)
    if not _is_valid_uuid(session_id):
        return _json_error("无效的会话 ID", 400)

    favs = load_favorites()
    if favs.get(session_id):
        favs.pop(session_id, None)
    else:
        favs[session_id] = True
    save_favorites(favs)
    return jsonify({"ok": True, "favorited": session_id in favs})


@app.route("/api/export")
def api_export():
    """导出会话为 Markdown。"""
    session_id = request.args.get("sessionId", "")
    if not session_id:
        return _json_error("缺少 sessionId", 400)

    if not _is_valid_uuid(session_id):
        return _json_error("无效的会话 ID", 400)

    session = _get_session_by_id(session_id)
    if not session:
        return _json_error("未找到该会话", 404)

    try:
        messages = get_session_messages(session["projectDir"], session["sessionId"])
    except Exception as exc:
        return _json_error(f"读取会话失败：{exc}")

    lines = [f"# 会话 {session_id[:8]}\n"]
    lines.append(f"**项目**: {session.get('realProjectPath', session['project'])}\n")
    lines.append(f"**消息数**: {len(messages)}\n\n---\n")

    for msg in messages:
        role = "**你**" if msg["role"] == "user" else "**AI**"
        lines.append(f"\n{role}\n\n{msg['content']}\n")

    md = "\n".join(lines)
    return md, 200, {
        "Content-Type": "text/markdown; charset=utf-8",
        "Content-Disposition": f'attachment; filename="session-{session_id[:8]}.md"',
    }


@app.route("/api/stats")
def api_stats():
    """统计数据。"""
    try:
        return jsonify(get_detailed_stats())
    except Exception as exc:
        return _json_error(f"统计失败：{exc}")


@app.route("/api/skills")
def api_skills():
    """获取所有 skill。"""
    try:
        return jsonify(get_skills())
    except Exception as exc:
        return _json_error(f"读取 skill 失败：{exc}")


@app.route("/api/plugins")
def api_plugins():
    """获取所有已安装的插件。"""
    try:
        return jsonify(get_plugins())
    except Exception as exc:
        return _json_error(f"读取插件失败：{exc}")


@app.route("/api/resume")
def api_resume():
    """启动 PowerShell 继续对话。"""
    import shutil

    session_id = request.args.get("sessionId", "")
    if not session_id:
        return _json_error("缺少 sessionId", 400)

    if not _is_valid_uuid(session_id):
        return _json_error("无效的会话 ID", 400)

    session = _get_session_by_id(session_id)
    if not session:
        return _json_error("未找到该会话", 404)

    real_path = session.get("realProjectPath") or str(get_claude_dir() / "projects")
    cwd = Path(real_path).expanduser()
    if not cwd.exists():
        return _json_error(f"项目路径不存在：{real_path}", 404)

    # 选择可用的 shell：优先 pwsh，其次 powershell
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        return _json_error("未找到 PowerShell，请确认 pwsh 或 powershell 在 PATH 中", 500)

    # UUID 已验证格式，直接使用；路径用 -LiteralPath 防止注入
    script = f"Set-Location -LiteralPath '{str(cwd).replace(chr(39), chr(39)*2)}'; claude --resume '{session_id}'"

    try:
        creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        subprocess.Popen(
            [shell, "-NoExit", "-Command", script],
            creationflags=creationflags,
        )
        return jsonify({"ok": True, "message": "已启动"})
    except Exception as exc:
        return _json_error(f"启动失败：{exc}", 500)


# ========== Entry Point ==========

class Api:
    """pywebview JS API，供前端调用。"""

    def save_file(self, filename, content):
        """弹出原生保存对话框，保存文件。"""
        import webview
        import os

        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=filename,
            file_types=('Markdown 文件 (*.md)', '所有文件 (*.*)'),
        )
        if result:
            path = result if isinstance(result, str) else result[0]
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return {"ok": True, "path": path}
        return {"ok": False}


def main():
    """启动应用。"""
    import argparse
    import os
    import time
    import urllib.request
    import webview

    parser = argparse.ArgumentParser(description="Claude Code 历史对话查看器")
    parser.add_argument("--data-dir", help="指定 .claude 数据目录（默认: ~/.claude）")
    parser.add_argument("--port", type=int, default=0, help="指定端口（默认: 自动选择）")
    parser.add_argument("--no-window", action="store_true", help="仅启动服务，不打开窗口")
    args = parser.parse_args()

    if args.data_dir:
        os.environ["CLAUDE_DIR"] = args.data_dir

    port = args.port or _find_free_port()
    url = f"http://127.0.0.1:{port}"

    server_thread = threading.Thread(
        target=lambda: app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True),
        daemon=True,
    )
    server_thread.start()

    for _ in range(50):
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1):
                break
        except Exception:
            time.sleep(0.1)
    else:
        raise RuntimeError("Flask 服务启动超时")

    if args.no_window:
        print(f"服务已启动: {url}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        api = Api()
        window = webview.create_window(
            "Claude Code 历史查看器",
            url,
            width=1200,
            height=800,
            min_size=(800, 500),
            js_api=api,
            text_select=True,
        )
        webview.start()


def main_noconsole():
    """Windows GUI script entry point."""
    main()


if __name__ == "__main__":
    main()
