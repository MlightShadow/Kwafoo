# Kwafoo - 夸父新闻聚合 AI Agent 🚀

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Vue](https://img.shields.io/badge/Vue-3.0-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-success)

<div align="center">

**🌟 一款基于AI的智能新闻聚合系统，让信息获取更高效！**

[功能特性](#-核心功能) • [快速开始](#-快速开始) • [部署指南](#-部署说明) • [API文档](#-主要api接口)

</div>

---

## 🎯 项目简介

**Kwafoo（夸父）** - 一个基于AI的新闻和热点聚合系统，以中国神话中"夸父逐日"的精神为灵感，象征着对信息的不懈追求和对真相的执着探索。

> "夸父与日逐走，入日；渴，欲得饮，饮于河、渭；河、渭不足，北饮大泽。未至，道渴而死。弃其杖，化为邓林。"

### 💡 项目特色

- 🤖 **AI智能处理** - 自动分类 + 智能摘要 + 深度推理
- 📰 **多源新闻抓取** - RSS订阅、API接口、网页爬虫三管齐下
- 💬 **RAG智能对话** - 基于历史新闻的智能问答系统
- 🎨 **现代化界面** - Vue 3 + TypeScript，响应式设计
- ⚡ **实时通信** - WebSocket实时推送任务进度
- 📦 **一键部署** - 可打包为独立可执行文件，无需安装Python
- 🗄️ **轻量存储** - SQLite嵌入式数据库，零配置启动
- 🖼️ **智能图片** - 自动下载、压缩、存储新闻图片
- 📊 **进度监控** - 实时任务进度展示，系统状态一目了然

---

## 🚀 快速开始

### 方式一：一键启动（推荐）⚡

双击运行 `start.bat`，脚本会自动：
- ✅ 检查Python环境
- ✅ 检查并安装依赖
- ✅ 启动HTTP服务器（端口8000）
- ✅ 启动WebSocket服务器（端口8001）

### 方式二：手动启动

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置系统

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

> 💡 **提示**：测试阶段建议关闭自动功能，通过管理界面手动触发

#### 3. 启动系统

```bash
python main.py
```

启动成功后，访问 http://localhost:8000 查看Web界面 🎉

---

## ✨ 核心功能

### 🤖 AI智能处理
- **自动分类**：智能识别新闻类别，支持自定义分类
- **智能摘要**：生成简洁准确的新闻摘要
- **深度推理**：支持深度思考模式，提供更深入的分析
- **点评翻译**：可选的新闻点评和翻译功能

### 📰 多源新闻抓取
- **RSS订阅**：支持标准RSS/Atom订阅源
- **API接口**：支持新闻API接口
- **网页爬虫**：基于BeautifulSoup的智能网页抓取
- **定时任务**：可配置的自动抓取间隔

### 💬 RAG智能对话
- **历史检索**：基于新闻数据的智能检索
- **上下文理解**：理解对话上下文，提供连贯回答
- **分类筛选**：支持按分类进行对话
- **会话管理**：完整的会话历史记录

### 🎨 现代化Web界面
- **响应式设计**：完美适配桌面、平板、手机
- **实时更新**：WebSocket实时推送任务进度
- **分类浏览**：按分类筛选新闻，支持图标和颜色
- **搜索功能**：全文搜索，快速定位新闻
- **阅读状态**：标记已读/未读，管理阅读进度

### ⚙️ 系统管理
- **在线配置**：Web界面直接修改配置
- **进度监控**：实时查看任务执行进度
- **系统状态**：服务器状态、AI状态一目了然
- **日志查看**：完整的系统日志记录

---

## 📦 部署说明

### 打包为独立可执行文件

#### 前置要求
- Python 3.8+
- 网络连接（用于下载依赖）

#### 打包步骤

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **运行打包脚本**
   ```bash
   # Windows
   build.bat
   
   # Linux/Mac
   chmod +x build.sh
   ./build.sh
   ```

3. **打包结果**
   - 可执行文件位于 `dist/kwafoo/kwafoo.exe` (Windows)
   - 包含所有必要的依赖和资源文件

### 部署到服务器

1. **复制整个文件夹**
   - 将 `dist/kwafoo` 整个文件夹复制到目标位置
   - 确保文件夹结构完整

2. **启动程序**
   ```bash
   # Windows
   kwafoo.exe
   
   # Linux/Mac
   ./kwafoo
   ```

3. **访问Web界面**
   - 打开浏览器访问: `http://localhost:8000`
   - 如果修改了端口，使用相应的地址

### 部署文件结构

```
kwafoo/
├── kwafoo.exe              # 主程序
├── config.toml             # 配置文件（可修改）
├── config.toml.example     # 配置示例
└── data/                   # 数据目录（运行时生成）
    ├── kwafoo.db            # 数据库文件
    └── logs/               # 日志文件
        └── kwafoo.log
```

---

## 🔧 配置说明

### 通过文件修改配置

直接编辑 `config.toml` 文件：

```toml
[server]
host = "0.0.0.0"
port = 8000

[scheduler]
fetch_interval = 1800  # 新闻抓取间隔（秒）
auto_fetch = false     # 自动抓取

[ai]
base_url = "http://localhost:1234"
model = "nvidia/nemotron-3-nano-4b"
enable_summary = true
```

### 通过Web界面修改配置

1. 访问系统设置页面
2. 修改配置项
3. 保存更改（会自动更新到config.toml）

---

## 🌐 主要API接口

### 基础接口
- `GET /api/health` - 健康检查
- `GET /api/progress` - 获取任务进度

### 新闻接口
- `GET /api/news` - 获取新闻列表
- `GET /api/news/stats` - 获取新闻统计
- `GET /api/news/search?q=关键词&limit=10` - 搜索新闻
- `GET /api/news/category?category=tech` - 按分类获取新闻
- `POST /api/news/clear` - 清空新闻
- `POST /api/news/mark-read` - 标记阅读状态

### AI接口
- `GET /api/ai/status` - 获取AI处理状态
- `POST /api/ai/process` - 触发AI处理
- `POST /api/ai/process-all` - 处理所有新闻
- `POST /api/ai/reanalyze` - 重新分析新闻

### 聊天接口
- `POST /api/chat` - 发送聊天消息
- `GET /api/chat/history?session_id=xxx` - 获取聊天历史

### 配置接口
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置

### 任务接口
- `POST /api/fetch` - 手动触发新闻抓取
- `GET /api/system/progress` - 获取系统进度

### WebSocket接口
- `ws://localhost:8001` - WebSocket实时通信

---

## 📁 项目结构

```
kwafoo/
├── main.py                 # 主程序入口
├── config.toml            # 配置文件
├── requirements.txt       # Python依赖
├── start.bat             # 一键启动脚本
├── test.bat              # 快速测试脚本
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
│   ├── images/          # 图片缓存
│   └── logs/            # 日志文件
├── design/              # 概要设计文档
├── doc/                 # 详细设计文档
└── tests/               # 测试脚本
```

---

## 📚 文档导航

### 📖 概要设计文档
| 文档 | 说明 |
|------|------|
| [overview.md](design/overview.md) | 系统概览和各模块介绍（主文档）|
| [architecture.md](design/modules/architecture.md) | 系统架构、技术栈、模块设计 |
| [database.md](design/modules/database.md) | 数据库表结构、索引 |
| [ai.md](design/modules/ai.md) | AI处理模块：分类器、摘要生成器、处理器 |
| [fetcher.md](design/modules/fetcher.md) | 新闻抓取模块：RSS、API、网页 |
| [rag.md](design/modules/rag.md) | RAG对话系统设计 |
| [image.md](design/modules/image.md) | 图片处理模块设计 |
| [compression.md](design/modules/compression.md) | 文本压缩模块设计 |
| [scheduler.md](design/modules/scheduler.md) | 调度模块设计 |
| [api.md](design/modules/api.md) | RESTful API接口 |
| [frontend.md](design/modules/frontend.md) | 前端模块：Vue 3 + TypeScript |

### 📝 详细设计文档
| 文档 | 说明 |
|------|------|
| [architecture.md](doc/architecture.md) | 系统架构、技术栈、模块设计 |
| [database.md](doc/database.md) | 数据库表结构、索引 |
| [ai-design.md](doc/ai-design.md) | AI处理逻辑、分类器、摘要生成器 |
| [fetch-design.md](doc/fetch-design.md) | 新闻抓取详细设计（包含代码示例）|
| [fetch-design2.md](doc/fetch-design2.md) | 文本压缩方案详细设计 |
| [api.md](doc/api.md) | RESTful API接口 |

### ⚙️ 配置文档
| 文档 | 说明 |
|------|------|
| [configuration.md](doc/configuration.md) | 配置文件详解 |
| [configuration-guide.md](doc/configuration-guide.md) | 配置文件使用指南 |

### 📊 优化记录
| 文档 | 说明 |
|------|------|
| [changelog.md](doc/changelog.md) | 优化变更记录 |
| [REFACTORING_CHANGES.md](doc/REFACTORING_CHANGES.md) | 重构修改详情 |
| [AI_PROCESSING_SUMMARY.md](doc/AI_PROCESSING_SUMMARY.md) | AI处理系统开发总结 |
| [frontend-optimization.md](doc/frontend-optimization.md) | 前端优化功能说明 |

### 🚀 部署和问题解决
| 文档 | 说明 |
|------|------|
| [deployment.md](doc/deployment.md) | 打包部署指南 |
| [troubleshooting.md](doc/troubleshooting.md) | 问题解决指南 |
| [npm-fix.md](doc/npm-fix.md) | npm包问题修复 |

---

## 🛠️ 技术栈

### 后端
- **Python 3.10+** - 主要开发语言
- **SQLite** - 轻量级嵌入式数据库
- **websockets** - WebSocket服务器
- **requests** - HTTP客户端
- **beautifulsoup4** - 网页解析
- **feedparser** - RSS解析
- **OpenAI SDK** - AI服务集成

### 前端
- **Vue 3** - 渐进式JavaScript框架
- **TypeScript** - 类型安全的JavaScript超集
- **Vite** - 下一代前端构建工具
- **Element Plus** - Vue 3组件库
- **Pinia** - 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP客户端

---

## 🔍 故障排除

### 服务器无法启动
1. 检查端口8000和8001是否被占用
2. 检查Python版本（需要3.10+）
3. 检查依赖是否完整安装
4. 查看日志文件：`data/logs/kwafoo.log`

### 新闻抓取失败
1. 检查网络连接
2. 检查新闻源URL是否有效
3. 查看日志文件：`data/logs/kwafoo.log`

### AI处理失败
1. 检查AI服务地址是否正确
2. 检查模型名称是否正确
3. 确保AI服务正在运行
4. 查看日志文件：`data/logs/kwafoo.log`

### 测试失败
1. 确保服务器正在运行
2. 检查防火墙设置
3. 查看测试脚本的错误信息

### 端口被占用
- 修改 `config.toml` 中的 `server.port` 值
- 重启程序

### 数据库错误
- 删除 `data/kwafoo.db` 文件
- 重启程序（会自动创建新数据库）

### 日志文件过大
- 修改 `config.toml` 中的 `logging.max_size` 值
- 或手动删除 `data/logs/` 下的旧日志文件

---

## 💻 开发说明

### 添加新的API接口
1. 在 `web/api/` 下创建新的API文件
2. 在 `web/server.py` 中注册路由
3. 更新测试脚本

### 添加新的新闻源
1. 在 `config.toml` 的 `[news_sources]` 部分添加配置
2. 支持RSS、API和网页爬虫三种类型

### 修改前端
1. 前端代码在 `web/frontend/src/`
2. 使用Vue 3 + TypeScript
3. 组件化开发，使用Composables

### 运行测试
```bash
# 快速测试
python test_quick.py

# 完整测试（包含等待新闻抓取）
python test_auto.py

# 或双击运行 test.bat
```

---

## 📊 系统要求

### 最低配置
- **CPU**: 双核处理器
- **内存**: 2GB RAM
- **磁盘**: 500MB 可用空间
- **网络**: 宽带连接

### 推荐配置
- **CPU**: 四核处理器
- **内存**: 4GB RAM
- **磁盘**: 2GB 可用空间
- **网络**: 稳定的宽带连接

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

## 📮 联系方式

如有问题，请查看：
1. 日志文件: `data/logs/kwafoo.log`
2. 配置文件: `config.toml`
3. 系统文档: `design/` 和 `doc/` 目录

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star！**

Made with ❤️ by Kwafoo Team

</div>