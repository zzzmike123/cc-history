"""Flask 应用 + pywebview 桌面窗口。"""

import socket
import subprocess
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from .data import (
    get_claude_dir,
    get_real_project_paths,
    get_session_messages,
    get_sessions,
    load_custom_names,
    load_settings,
    save_custom_names,
    save_settings,
)

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))


def _json_error(message, status=500):
    return jsonify({"error": message}), status


def _session_index():
    return {(s["projectDir"], s["sessionId"]): s for s in get_sessions()}


def _get_known_session(project_dir, session_id):
    return _session_index().get((project_dir, session_id))


def _get_session_by_id(session_id):
    for session in get_sessions():
        if session["sessionId"] == session_id:
            return session
    return None


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# ========== API Routes ==========

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def api_health():
    return jsonify({"ok": True})


@app.route("/api/projects")
def api_projects():
    """返回项目列表。"""
    try:
        sessions = get_sessions()
        path_map = get_real_project_paths()
    except Exception as exc:
        return _json_error(f"读取 Claude Code 历史失败：{exc}")

    projects = {}
    for s in sessions:
        proj = s["project"]
        if proj not in projects:
            real_path = path_map.get(proj, proj)
            projects[proj] = {
                "name": proj,
                "realPath": real_path,
                "projectDir": s["projectDir"],
                "sessions": [],
            }
        real_path = path_map.get(proj, proj)
        projects[proj]["sessions"].append({
            "sessionId": s["sessionId"],
            "messageCount": s["messageCount"],
            "firstMessage": s["firstMessage"],
            "firstTimestamp": s["firstTimestamp"],
            "lastTimestamp": s["lastTimestamp"],
            "realPath": real_path,
        })

    return jsonify(list(projects.values()))


@app.route("/api/messages")
def api_messages():
    """返回会话消息。"""
    project_dir = request.args.get("projectDir", "")
    session_id = request.args.get("sessionId", "")
    if not project_dir or not session_id:
        return _json_error("缺少参数", 400)

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
        sessions = get_sessions()
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
    return jsonify({"ok": True, "settings": current})


@app.route("/api/resume")
def api_resume():
    """启动 PowerShell 继续对话。"""
    import shutil

    session_id = request.args.get("sessionId", "")
    if not session_id:
        return _json_error("缺少 sessionId", 400)

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

    # 将参数直接内联到脚本中（pwsh -Command 不会将后续参数传给 $args）
    cwd_escaped = str(cwd).replace("'", "''")
    sid_escaped = session_id.replace("'", "''")
    script = f"Set-Location -LiteralPath '{cwd_escaped}'; claude --resume '{sid_escaped}'"

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
        webview.create_window(
            "Claude Code 历史查看器",
            url,
            width=1200,
            height=800,
            min_size=(800, 500),
        )
        webview.start()


def main_noconsole():
    """Windows GUI script entry point."""
    main()


if __name__ == "__main__":
    main()
