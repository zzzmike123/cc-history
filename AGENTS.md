# CC History Agent Guide

## 项目概述

CC History 是 Claude Code 历史对话查看器，本地桌面应用，用于浏览、搜索和管理 Claude Code 的历史会话。

- **仓库**: https://github.com/zzzmike123/cc-history
- **当前版本**: v1.2.0
- **技术栈**: Python + Flask + pywebview

## 知识库

用户的 Obsidian 知识库位于 `D:\Obsidian\zyz`，包含 ML/推荐系统学习笔记。

相关页面：
- `10 Sources/来源 - CC History v1.2.0 开发实录.md`
- `20 Wiki/Topic/主题 - Python桌面应用开发.md`
- `40 Journal/2026-06-19.md`

## 当前进度

### 已完成（v1.2.0）

**核心功能**
- 项目分组显示
- 对话浏览（user / assistant）
- 全文搜索
- 会话重命名（右键菜单）
- 继续对话（PowerShell）
- Markdown 渲染
- 原生窗口（pywebview）

**v1.2.0 新增**
- 收藏会话（星标 + 侧边栏置顶）
- 导出会话（原生保存对话框）
- 统计面板（30天趋势、小时/周分布、工具使用排行）

**修复与优化**
- 修复 PowerShell 参数传递 bug（`$args` 不生效，必须内联）
- 修复项目路径显示 bug（从 JSONL `cwd` 字段回退）
- 合并连续 assistant 消息
- 设置按钮样式统一
- 统计柱状图对齐
- 图标背景透明

**打包与发布**
- PyInstaller + Inno Setup 安装包
- GitHub Releases：`CC-History-Setup-1.2.0.exe`

### 待办

- 分页/虚拟滚动（消息多时性能优化）
- 搜索结果高亮
- 会话时间分组（今天/昨天/本周/更早）

## 关键技术要点

1. **PowerShell 参数传递**：`pwsh -Command "script" arg1 arg2` 不会传参给 `$args`，必须内联到脚本字符串
2. **JSONL 路径映射**：项目目录名是编码后的（`\`→`-`），需从 `history.jsonl` 或 `cwd` 字段提取真实路径
3. **pywebview JS API**：通过 `js_api` 参数暴露 Python 方法，前端调用 `window.pywebview.api.xxx()`
4. **Windows 图标缓存**：修改 `.ico` 后需清除 `%LOCALAPPDATA%\Microsoft\Windows\Explorer\iconcache_*` 并重启资源管理器

## 项目结构

```
cc-history/
├── pyproject.toml              # 包配置
├── requirements.txt            # 依赖
├── README.md                   # 文档
├── AGENTS.md                   # 本文件
├── cat.ico                     # 主图标
├── installer/
│   ├── cc-history.iss          # Inno Setup 脚本
│   └── output/                 # 安装包输出
├── packaging/
│   └── cc-history.spec         # PyInstaller 配置
├── scripts/
│   └── build_windows.ps1      # 构建脚本
└── src/cc_history/
    ├── __init__.py
    ├── __main__.py
    ├── app.py                  # Flask 路由 + pywebview
    ├── data.py                 # 数据解析
    └── templates/
        └── index.html          # 前端 UI
```

## 常用命令

```powershell
# 安装
pip install -e .

# 运行
cc-history
cc-historyw          # 无控制台窗口
python -m cc_history.app

# 构建安装包
.\scripts\build_windows.ps1

# Git
git push origin master
git push origin v1.2.0
```

