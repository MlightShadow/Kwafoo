# Kwafoo - 夸父新闻聚合 AI Agent

## 项目简介

**Kwafoo（夸父）** - 一个基于AI的新闻和热点聚合系统，以中国神话中"夸父逐日"的精神为灵感，象征着对信息的不懈追求和对真相的执着探索。

> "夸父与日逐走，入日；渴，欲得饮，饮于河、渭；河、渭不足，北饮大泽。未至，道渴而死。弃其杖，化为邓林。"

夸父逐日的故事象征着：坚持不懈、追求真理、无私奉献、生生不息。

### 核心功能

- **多源新闻抓取**：RSS订阅、API接口、网页爬虫
- **SQLite数据存储**：轻量级嵌入式数据库，无需额外服务
- **AI智能处理**：自动分类 + 摘要生成
- **RAG对话**：基于历史新闻的智能问答
- **Web管理界面**：实时进度展示、在线配置修改

### 技术栈

- Python 3.10+ | SQLite | OpenAI SDK (本地模型)
- Vue 3 + TypeScript | WebSocket | 内置HTTP服务器

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

```bash
cp config.toml.example config.toml
```

编辑 `config.toml`，配置新闻源和AI服务：

```toml
# 新闻源配置
[news_sources]

[[news_sources.rss]]
url = "https://36kr.com/feed"
name = "36氪"
enabled = true
fetch_days = 2

# 调度配置
[scheduler]
auto_fetch = false        # 测试阶段建议关闭
auto_ai_process = false  # 测试阶段建议关闭

# AI配置 - 必须配置！
[ai]
base_url = "http://localhost:1234"  # AI服务地址
model = "nvidia/nemotron-3-nano-4b"  # 模型名称
max_workers = 1
batch_size = 1

# 服务器配置
[server]
host = "0.0.0.0"
port = 8000
```

> **重要配置说明：**
> - `auto_fetch`: 是否自动抓取新闻（默认false，关闭）
> - `auto_ai_process`: 是否自动AI分析新闻（默认false，关闭）
> - 测试阶段建议关闭自动功能，通过管理界面手动触发

### 3. 启动系统

```bash
python main.py
```

系统启动后，访问 http://localhost:8000 查看Web界面。

---

## 使用指南

### Web界面功能

启动系统后，打开浏览器访问 http://localhost:8000，可以看到：

- **新闻列表**：按时间线展示所有新闻
- **分类浏览**：按分类筛选新闻
- **AI对话**：基于历史新闻进行智能问答
- **管理界面**：手动抓取新闻、AI分析新闻、查看任务进度和系统状态

### 手动操作

1. **手动抓取新闻**：管理界面 → 点击"🔄 手动抓取新闻"
2. **手动AI分析**：管理界面 → 点击"🤖 AI分析新闻"

### 常用API

```bash
# 获取新闻列表
curl http://localhost:8000/api/news

# 搜索新闻
curl "http://localhost:8000/api/news/search?q=AI"

# 触发AI处理
curl -X POST http://localhost:8000/api/ai/process

# 健康检查
curl http://localhost:8000/api/health
```

---

## 项目结构

```
kwafoo/
├── main.py                 # 主程序入口
├── config.toml            # 配置文件
├── requirements.txt       # Python依赖
├── database/              # 数据库模块
│   └── manager.py
├── fetcher/              # 新闻抓取模块
│   ├── rss_fetcher.py
│   ├── api_fetcher.py
│   └── web_fetcher.py
├── ai/                   # AI处理模块
│   ├── classifier.py
│   ├── summarizer.py
│   └── processor.py
├── rag/                  # RAG对话模块
│   └── engine.py
├── scheduler/            # 定时任务模块
│   └── scheduler.py
├── utils/                # 工具模块
│   ├── logger.py
│   ├── progress.py
│   └── helpers.py
├── web/                  # Web服务模块
│   ├── server.py
│   ├── websocket.py
│   ├── api/             # API处理器
│   ├── frontend/        # Vue前端
│   └── dist/           # 构建产物
├── data/                # 数据目录（运行时生成）
│   ├── kwafoo.db
│   └── logs/
└── tests/               # 测试脚本
```

---

## 文档导航

| 分类 | 文档 | 说明 |
|------|------|------|
| 项目设计 | [architecture.md](doc/architecture.md) | 系统架构、技术栈、模块设计 |
| 项目设计 | [database.md](doc/database.md) | 数据库表结构、索引 |
| 项目设计 | [ai-design.md](doc/ai-design.md) | AI处理逻辑、分类器、摘要生成器 |
| 项目设计 | [api.md](doc/api.md) | RESTful API接口 |
| 配置讲解 | [configuration.md](doc/configuration.md) | 配置文件详解 |
| 配置讲解 | [configuration-guide.md](doc/configuration-guide.md) | 配置文件使用指南 |
| 优化记录 | [changelog.md](doc/changelog.md) | 优化变更记录 |
| 优化记录 | [REFACTORING_CHANGES.md](doc/REFACTORING_CHANGES.md) | 重构修改详情 |
| 优化记录 | [AI_PROCESSING_SUMMARY.md](doc/AI_PROCESSING_SUMMARY.md) | AI处理系统开发总结 |
| 优化记录 | [frontend-optimization.md](doc/frontend-optimization.md) | 前端优化功能说明 |
| 部署说明 | [deployment.md](doc/deployment.md) | 打包部署指南 |
| 问题解决 | [troubleshooting.md](doc/troubleshooting.md) | 问题解决指南 |
| 问题解决 | [npm-fix.md](doc/npm-fix.md) | npm包问题修复 |