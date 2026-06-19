# CC History — Claude Code 历史对话查看器

本地桌面应用，用于浏览、搜索和管理 Claude Code 的历史对话记录。

## 功能

- **项目分组**：按项目目录自动分组显示所有会话
- **对话浏览**：查看完整的 user / assistant 对话内容
- **全文搜索**：跨所有会话搜索消息关键词
- **会话重命名**：右键会话可自定义名称，悬浮显示原标题
- **继续对话**：一键打开 PowerShell 恢复指定会话
- **Markdown 渲染**：代码块、表格、加粗、链接等
- **原生窗口**：基于 pywebview 的独立桌面窗口，不依赖浏览器

## 安装

### 方式一：pip 安装（推荐）

```bash
pip install git+https://github.com/yourname/cc-history.git
```

### 方式二：克隆安装

```bash
git clone https://github.com/yourname/cc-history.git
cd cc-history
pip install -e .
```

## 使用

安装后直接运行：

```bash
cc-history
```

或者：

```bash
python -m cc_history.app
```

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+K` | 聚焦搜索框 |
| `Esc` | 清空搜索 |
| 右键会话 | 重命名 / 恢复默认 |

## 数据来源

应用读取以下 Claude Code 本地数据（只读，不修改）：

- `~/.claude/history.jsonl` — 用户消息索引
- `~/.claude/projects/<project>/*.jsonl` — 完整对话记录

自定义名称存储在 `~/.claude/cc-history-names.json`。

## 技术栈

- **后端**：Python + Flask
- **前端**：HTML + CSS + JavaScript（内嵌）
- **桌面窗口**：pywebview
- **设计**：Inter 字体 + 浅色主题 + SVG 图标

## 系统要求

- Python 3.9+
- Windows / macOS / Linux
- Claude Code 已有历史对话数据

## 许可证

MIT
