"""数据解析模块：读取 Claude Code 的会话历史文件。"""

import json
import os
from pathlib import Path

CONFIG_FILE = Path.home() / ".cc-history.json"


def _default_claude_dir():
    return Path.home() / ".claude"


def load_settings():
    """加载应用设置。"""
    defaults = {
        "claude_dir": str(_default_claude_dir()),
        "theme": "light",
    }
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            defaults.update(saved)
        except Exception:
            pass
    env_dir = os.environ.get("CLAUDE_DIR")
    if env_dir:
        defaults["claude_dir"] = env_dir
    return defaults


def save_settings(settings):
    """保存应用设置。"""
    CONFIG_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")


def get_claude_dir():
    """获取当前 .claude 目录路径。"""
    return Path(load_settings()["claude_dir"])


def _get_projects_dir():
    return get_claude_dir() / "projects"


def _get_history_file():
    return get_claude_dir() / "history.jsonl"


def _read_jsonl(path):
    """Yield decoded JSONL objects, skipping broken lines/files."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue
    except OSError:
        return


def get_custom_names_path():
    """返回自定义名称文件路径（存在用户目录下）"""
    return get_claude_dir() / "cc-history-names.json"


def parse_history():
    """解析 history.jsonl，返回所有用户消息。"""
    messages = []
    history_file = _get_history_file()
    if not history_file.exists():
        return messages
    for obj in _read_jsonl(history_file):
        messages.append(obj)
    return messages


def get_real_project_paths():
    """从 history.jsonl 中提取真实的项目路径映射。"""
    mapping = {}
    for msg in parse_history():
        project = msg.get("project", "")
        if project:
            encoded = project.replace("\\", "-").replace("/", "-").replace(":", "-")
            mapping[encoded] = project
    return mapping


def _extract_content(msg_data):
    """从消息体中提取文本内容。"""
    if not isinstance(msg_data, dict):
        return ""
    raw = msg_data.get("content", "")
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def get_sessions():
    """扫描 projects 目录，返回所有会话信息。"""
    sessions = []
    projects_dir = _get_projects_dir()
    if not projects_dir.exists():
        return sessions

    path_map = get_real_project_paths()

    try:
        project_dirs = list(projects_dir.iterdir())
    except OSError:
        return sessions

    for project_dir in project_dirs:
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name
        real_path = path_map.get(project_name, project_name)

        for jsonl_file in project_dir.glob("*.jsonl"):
            session_id = jsonl_file.stem
            messages = []
            first_user_msg = None
            first_ts = None
            last_ts = None

            for obj in _read_jsonl(jsonl_file):
                msg_type = obj.get("type")
                if msg_type == "user":
                    content = _extract_content(obj.get("message", {}))
                    ts = obj.get("timestamp", "")
                    if content:
                        messages.append({"role": "user", "content": content, "timestamp": ts})
                        if first_user_msg is None:
                            first_user_msg = content[:100]
                        if ts:
                            last_ts = ts
                            if first_ts is None:
                                first_ts = ts

                elif msg_type == "assistant":
                    content = _extract_content(obj.get("message", {}))
                    ts = obj.get("timestamp", "")
                    if content:
                        messages.append({"role": "assistant", "content": content, "timestamp": ts})
                        if ts:
                            last_ts = ts

            if messages:
                sessions.append({
                    "sessionId": session_id,
                    "project": project_name,
                    "realProjectPath": real_path,
                    "projectDir": str(project_dir),
                    "messageCount": len(messages),
                    "firstMessage": first_user_msg or "(无文本消息)",
                    "firstTimestamp": first_ts,
                    "lastTimestamp": last_ts,
                })

    sessions.sort(key=lambda s: s.get("lastTimestamp") or "", reverse=True)
    return sessions


def get_session_messages(project_dir, session_id):
    """获取指定会话的所有消息。"""
    jsonl_path = Path(project_dir) / f"{session_id}.jsonl"
    if not jsonl_path.exists():
        return []

    messages = []
    for obj in _read_jsonl(jsonl_path):
        msg_type = obj.get("type")
        if msg_type in ("user", "assistant"):
            content = ""
            msg_data = obj.get("message", {})
            if isinstance(msg_data, dict):
                raw = msg_data.get("content", "")
                if isinstance(raw, str):
                    content = raw
                elif isinstance(raw, list):
                    parts = []
                    for block in raw:
                        if isinstance(block, dict):
                            if block.get("type") == "text":
                                parts.append(block.get("text", ""))
                            elif block.get("type") == "tool_use":
                                tool_name = block.get("name", "unknown")
                                tool_input = block.get("input", {})
                                if tool_name == "Bash":
                                    cmd = tool_input.get("command", "")
                                    parts.append(f"```bash\n{cmd}\n```")
                                elif tool_name in ("Read", "Write", "Edit"):
                                    fp = tool_input.get("file_path", "")
                                    parts.append(f"**{tool_name}**: `{fp}`")
                                elif tool_name == "Grep":
                                    pattern = tool_input.get("pattern", "")
                                    parts.append(f"**Grep**: `{pattern}`")
                                elif tool_name == "Glob":
                                    pattern = tool_input.get("pattern", "")
                                    parts.append(f"**Glob**: `{pattern}`")
                                else:
                                    parts.append(f"**{tool_name}**")
                        elif isinstance(block, str):
                            parts.append(block)
                    content = "\n".join(parts)

            ts = obj.get("timestamp", "")
            if content:
                messages.append({"role": msg_type, "content": content, "timestamp": ts})

    return messages


def load_custom_names():
    """加载自定义会话名称。"""
    path = get_custom_names_path()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            pass
    return {}


def save_custom_names(names):
    """保存自定义会话名称。"""
    path = get_custom_names_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(names, ensure_ascii=False, indent=2), encoding="utf-8")
