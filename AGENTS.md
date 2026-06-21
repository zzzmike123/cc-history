# CC History Agent Guide

## 项目概述

CC History 是 Claude Code 历史对话查看器，本地桌面应用，用于浏览、搜索和管理 Claude Code 的历史会话。

- **仓库**: https://github.com/zzzmike123/cc-history
- **当前版本**: v1.2.0
- **技术栈**: Python + Flask + pywebview + HTML/CSS/JS

## 知识库

用户的 Obsidian 知识库位于 `D:\Obsidian\zyz`，包含 ML/推荐系统学习笔记。

相关页面：
- `10 Sources/来源 - CC History v1.2.0 开发实录.md`
- `20 Wiki/Topic/主题 - Python桌面应用开发.md`
- `40 Journal/2026-06-19.md`
- `40 Journal/2026-06-20.md`

---

## 完整开发历史

### v0.1 — 从零搭建（2026-06-19 下午）

**项目初始化**
- 创建 Flask 应用 + pywebview 桌面窗口
- 解析 `~/.claude/projects/` 目录下的 JSONL 会话文件
- 实现项目分组、会话列表、消息浏览
- 前端单文件 HTML（内嵌 CSS + JS）

**核心功能**
- 项目分组显示（按编码后的目录名）
- 对话浏览（user / assistant 消息）
- 全文搜索（跨所有会话）
- Markdown 渲染（代码块、表格、加粗、链接）
- 原生窗口（pywebview）

### v1.0 — 功能完善（2026-06-19 晚上）

**新增功能**
- 收藏会话（星标 + 侧边栏置顶）
- 导出会话（原生保存对话框，可选位置）
- 统计面板（30天趋势、小时/周分布、工具使用排行）
- 会话重命名（右键菜单）
- 继续对话（打开 PowerShell 恢复会话）

**Bug 修复**
- 修复 PowerShell 参数传递：`pwsh -Command "script" arg1 arg2` 不会传参给 `$args`，必须内联
- 修复项目路径显示：从 JSONL 文件的 `cwd` 字段提取真实路径
- 合并连续 assistant 消息
- Windows 图标缓存问题

**打包发布**
- PyInstaller 打包成单文件 EXE
- Inno Setup 制作安装包
- GitHub Releases 发布

### v1.1.0 — 稳定版本（2026-06-19 深夜）

- 修复图标背景透明问题
- 优化统计面板布局
- 统一设置按钮样式

### v1.2.0 — 重大更新（2026-06-20）

**新功能**
- Skills & 插件查看（用户级/项目级，详情悬浮窗）
- 对话内搜索（实时高亮、上/下导航、TreeWalker 遍历）
- 全局搜索清除按钮
- 代码块复制按钮（悬停显示、点击复制）
- 快捷键扩展（Ctrl+F 对话搜索、Ctrl+E 导出、Escape 关闭弹窗）
- 消息分页加载（初始 50 条，点击加载更多）

**安全修复**
- UUID 格式验证（防止命令注入）
- 路径穿越防护（`Path.resolve()` + `relative_to()`）
- 会话列表缓存（5 秒 TTL）

**Bug 修复**
- pywebview 文字选中（`text_select=True`）
- switchTab 事件监听器泄漏
- 搜索 debounce（200ms）

**前端模块化**
- CSS 提取到 `static/styles.css`
- 图标提取到 `static/icons.js`
- 工具函数提取到 `static/utils.js`
- index.html 从 2382 行减少到 1170 行

**单元测试**
- 42 个测试覆盖 data.py 和 app.py 核心函数
- 测试 UUID 验证、路径防护、内容提取、SKILL.md 解析
- 测试所有 Flask API 端点

### v1.2.0+ — 持续优化（2026-06-20 下午）

**UI 美化**
- 整体 UI 优化（渐变色、圆角、阴影、动画）
- 统计面板美化（卡片图标、渐变柱状图、排名标记）
- 暗色主题完善（搜索高亮、滚动条颜色）

**项目管理增强**
- 项目自定义名称（悬浮显示原始路径）
- 项目下拉菜单（打开文件夹、重命名、新开对话）
- 会话三点菜单（归档、重命名、恢复默认、收藏）

**对话归档功能**
- 垃圾箱按钮查看归档对话
- 归档/取消归档
- 项目菜单批量归档
- 归档列表按项目分组显示
- 自定义确认对话框（替代原生 confirm）

**其他优化**
- 删除旧的右键菜单
- 菜单定位修复（position: relative）
- 取消归档后立即刷新左侧列表

---

## 当前功能清单

### 核心功能
- 项目分组显示
- 对话浏览（user / assistant）
- 全文搜索（跨会话）
- Markdown 渲染（代码块、表格、链接）
- 消息分页加载（50 条/批）

### 会话管理
- 收藏会话（星标置顶）
- 归档对话（软删除）
- 重命名会话
- 导出会话（Markdown）
- 继续对话（PowerShell）

### 项目管理
- 项目自定义名称
- 打开文件夹
- 新开对话
- 批量归档项目

### 查看功能
- 统计面板（趋势、分布、排行）
- Skills & 插件查看
- 对话内搜索（高亮、导航）

### 界面
- 暗色主题
- 快捷键（Ctrl+K/F/E、Escape）
- 自定义确认对话框

---

## 关键技术要点

1. **PowerShell 参数传递**：`pwsh -Command "script" arg1 arg2` 不会传参给 `$args`，必须内联到脚本字符串
2. **JSONL 路径映射**：项目目录名是编码后的（`\`→`-`），需从 `history.jsonl` 或 `cwd` 字段提取真实路径
3. **pywebview JS API**：通过 `js_api` 参数暴露 Python 方法，前端调用 `window.pywebview.api.xxx()`
4. **pywebview 文字选中**：默认禁用，需要 `text_select=True`
5. **TreeWalker 高亮**：对 markdown 渲染后的 HTML 做搜索高亮，用 TreeWalker 遍历文本节点比 regex replace 更安全
6. **事件监听器泄漏**：SPA 中动态创建组件时，addEventListener 前需 removeEventListener 旧的
7. **消息分页**：记录 oldScrollHeight 保持滚动位置不变
8. **菜单定位**：absolute 定位的菜单需要父元素 position: relative

---

## 项目结构

```
cc-history/
├── pyproject.toml              # 包配置（版本号、依赖、入口）
├── requirements.txt            # 依赖
├── README.md                   # 文档
├── AGENTS.md                   # 本文件
├── cat.ico                     # 主图标
├── tests/                      # 单元测试
│   ├── test_app.py             # Flask API 测试
│   └── test_data.py            # 数据函数测试
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
    ├── static/
    │   ├── styles.css          # CSS 样式
    │   ├── icons.js            # SVG 图标
    │   └── utils.js            # 工具函数
    └── templates/
        └── index.html          # 前端 UI + 内联 JS
```

---

## API 端点

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/projects` | 项目列表 |
| GET | `/api/messages` | 会话消息 |
| GET | `/api/search` | 全文搜索 |
| GET | `/api/settings` | 获取设置 |
| POST | `/api/settings` | 保存设置 |
| GET | `/api/custom-names` | 获取自定义名称 |
| POST | `/api/custom-names` | 设置自定义名称 |
| GET | `/api/project-names` | 获取项目名称 |
| POST | `/api/project-names` | 设置项目名称 |
| GET | `/api/favorites` | 获取收藏 |
| POST | `/api/favorites` | 切换收藏 |
| GET | `/api/archives` | 获取归档 |
| POST | `/api/archives` | 切换归档 |
| GET | `/api/skills` | Skills 列表 |
| GET | `/api/plugins` | 插件列表 |
| GET | `/api/stats` | 统计数据 |
| GET | `/api/export` | 导出会话 |
| GET | `/api/resume` | 继续对话 |
| GET | `/api/resume-new` | 新开对话 |
| POST | `/api/open-folder` | 打开文件夹 |

---

## 数据文件

| 文件 | 位置 | 说明 |
|------|------|------|
| 会话数据 | `~/.claude/projects/` | Claude Code 原始 JSONL |
| 历史索引 | `~/.claude/history.jsonl` | 用户消息索引 |
| 自定义名称 | `~/.claude/cc-history-names.json` | 会话重命名 |
| 项目名称 | `~/.claude/cc-history-project-names.json` | 项目重命名 |
| 收藏 | `~/.claude/cc-history-favorites.json` | 收藏的会话 |
| 归档 | `~/.claude/cc-history-archives.json` | 归档的会话 |
| 设置 | `~/.cc-history.json` | 应用设置 |

---

## 常用命令

```powershell
# 安装
pip install -e .

# 运行
cc-history
cc-historyw          # 无控制台窗口
python -m cc_history.app

# 测试
python -m pytest tests/ -v

# 构建安装包
.\scripts\build_windows.ps1

# Git
git add -A && git commit -m "message"
git push origin master
```

---

## 踩坑记录

1. **PowerShell 参数传递**：`pwsh -Command "script" arg1 arg2` 不会传参给 `$args`，必须内联
2. **Windows 图标缓存**：修改 .ico 后需要清除缓存并重启资源管理器
3. **pywebview 下载**：`a.click()` 触发下载行为不一致，优先用原生保存对话框
4. **pywebview 文字选中**：默认禁用，需要 `text_select=True`
5. **TreeWalker 高亮**：regex replace 会破坏 HTML 结构，用 TreeWalker 遍历文本节点更安全
6. **事件监听器泄漏**：addEventListener 前需 removeEventListener 旧监听器
7. **前端模块化**：外部 JS 和内联脚本不能有同名变量定义
8. **菜单定位**：absolute 定位需要父元素 position: relative
9. **消息分页**：记录 oldScrollHeight 保持滚动位置
10. **JSONL 路径**：目录名是编码后的，需从 cwd 字段提取真实路径
