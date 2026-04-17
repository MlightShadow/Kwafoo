# 系统架构设计

## 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Web前端模块                          │
│  - Vue 3 + TypeScript                                   │
│  - 新闻展示、管理界面、系统监控                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    Web API模块                          │
│  - RESTful API接口                                      │
│  - 新闻管理、AI处理、聊天、配置、系统状态               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    调度模块                             │
│  - 任务调度                                             │
│  - 进度监控                                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   新闻抓取模块                          │
│  - RSS订阅源                                            │
│  - API接口                                              │
│  - 网页爬虫（CSS选择器）                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   SQLite数据库                          │
│  - 新闻存储                                             │
│  - AI处理状态跟踪                                       │
│  - 全文搜索索引                                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   AI处理模块                            │
│  - 智能分类（支持深度思考）                             │
│  - 内容摘要（支持点评、翻译）                           │
│  - 批量处理                                             │
│  - 状态更新                                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   RAG对话模块                           │
│  - 全文搜索                                             │
│  - 上下文构建                                           │
│  - 智能问答                                             │
└─────────────────────────────────────────────────────────┘
```

## 数据流程

### 1. 抓取阶段
```
调度器触发抓取任务 → 抓取器从RSS/API/网页获取新闻 → 数据清洗 → 存入SQLite（ai_processed=0）
```

### 2. 展示阶段
```
前端调用API → API从数据库获取数据 → 返回给前端展示
```

### 3. AI处理阶段
```
调度器触发AI处理任务 → 处理器从数据库获取未处理新闻 → 串行AI处理 → 更新分类和摘要 → 标记已处理（ai_processed=1）
```

### 4. 对话阶段
```
用户提问 → RAG引擎进行全文搜索 → 构建上下文 → 调用AI生成回答 → 返回给前端
```

## 技术栈

### 后端技术
- **编程语言**：Python 3.10+
- **数据库**：SQLite（轻量级嵌入式数据库）
- **Web框架**：FastAPI
- **AI框架**：OpenAI SDK（支持本地模型）
- **任务调度**：schedule（简单定时任务）
- **爬虫库**：requests + BeautifulSoup4
- **文本压缩**：textrank4zh

### 前端技术
- **框架**：Vue 3 + TypeScript
- **构建工具**：Vite
- **UI组件库**：Element Plus
- **状态管理**：Pinia
- **路由管理**：Vue Router
- **HTTP客户端**：Axios

### AI模型
- **本地模型**：NVIDIA Nemotron-3-Nano-4B（通过OpenAI兼容API）
- **支持功能**：分类、摘要、深度思考、点评、翻译

## 模块设计

### 1. 新闻抓取模块 (fetcher/)
负责从多种来源抓取新闻内容。

**核心功能**：
- RSS订阅源抓取
- API接口抓取
- 网页抓取（使用BeautifulSoup和CSS选择器）
- 数据清洗和去重

**代码引用**：
- [fetcher/rss_fetcher.py](../../fetcher/rss_fetcher.py) - RSS抓取器
- [fetcher/api_fetcher.py](../../fetcher/api_fetcher.py) - API抓取器
- [fetcher/web_fetcher.py](../../fetcher/web_fetcher.py) - 网页抓取器

### 2. 数据库管理模块 (database/)
负责数据库的创建、查询、更新等操作。

**核心功能**：
- 数据表创建和管理
- 新闻数据的增删改查
- AI处理状态跟踪
- 图片数据存储
- 阅读状态管理
- 全文搜索索引

**代码引用**：
- [database/manager.py](../../database/manager.py) - 数据库管理器

### 3. AI处理模块 (ai/)
负责新闻的智能分类和摘要生成。

**核心功能**：
- 智能分类（支持深度思考功能）
- 内容摘要生成（支持点评功能、翻译功能）
- 批量处理和队列管理
- 处理状态跟踪

**代码引用**：
- [ai/classifier.py](../../ai/classifier.py) - AI分类器
- [ai/summarizer.py](../../ai/summarizer.py) - AI摘要生成器
- [ai/processor.py](../../ai/processor.py) - AI新闻处理器

### 4. RAG对话模块 (rag/)
负责基于新闻数据的智能问答。

**核心功能**：
- 全文搜索
- 上下文构建
- 智能问答
- 聊天历史管理

**代码引用**：
- [rag/engine.py](../../rag/engine.py) - RAG引擎

### 5. 调度模块 (scheduler/)
负责任务调度和进度监控。

**核心功能**：
- 定时任务调度
- 任务队列管理
- 进度监控和广播
- WebSocket实时通信

**代码引用**：
- [scheduler/scheduler.py](../../scheduler/scheduler.py) - 任务调度器

### 6. 工具模块 (utils/)
提供各种工具函数和辅助功能。

**核心功能**：
- 图片处理（下载、压缩、存储）
- 文本压缩（多种算法）
- 日志记录
- 错误处理
- 配置验证

**代码引用**：
- [utils/image_processor.py](../../utils/image_processor.py) - 图片处理
- [utils/default_compressor.py](../../utils/default_compressor.py) - 默认压缩器
- [utils/textrank_compressor.py](../../utils/textrank_compressor.py) - TextRank压缩器
- [utils/hybrid_compressor.py](../../utils/hybrid_compressor.py) - 混合压缩器
- [utils/logger.py](../../utils/logger.py) - 日志记录
- [utils/progress.py](../../utils/progress.py) - 进度监控

### 7. Web API模块 (web/api/)
提供RESTful API接口。

**核心功能**：
- 新闻管理API（列表、搜索、分类、阅读状态）
- AI处理API（队列管理、重新分析）
- 聊天和RAG API
- 配置管理API
- 系统状态API

**代码引用**：
- [web/api/news_api.py](../../web/api/news_api.py) - 新闻API
- [web/api/ai_api.py](../../web/api/ai_api.py) - AI API
- [web/api/chat_api.py](../../web/api/chat_api.py) - 聊天API
- [web/api/config_api.py](../../web/api/config_api.py) - 配置API
- [web/api/system_api.py](../../web/api/system_api.py) - 系统API

### 8. 前端模块 (web/frontend/)
提供现代化的Web用户界面。

**核心功能**：
- 新闻展示和浏览
- 管理界面
- 系统监控界面
- 实时状态更新（WebSocket）
- 响应式设计

**代码引用**：
- [web/frontend/src/App.vue](../../web/frontend/src/App.vue) - 主应用组件
- [web/frontend/src/views/NewsView.vue](../../web/frontend/src/views/NewsView.vue) - 新闻视图
- [web/frontend/src/views/AdminView.vue](../../web/frontend/src/views/AdminView.vue) - 管理视图
- [web/frontend/src/views/MonitorView.vue](../../web/frontend/src/views/MonitorView.vue) - 监控视图

## 项目结构

```
kwafoo/
├── design/                 # 概要设计文档
│   ├── overview.md        # 系统概览
│   └── modules/           # 模块设计文档
├── doc/                   # 详细设计文档
├── database/              # 数据库模块
├── fetcher/               # 新闻抓取模块
├── ai/                    # AI处理模块
├── rag/                   # RAG对话模块
├── scheduler/             # 调度模块
├── utils/                 # 工具模块
├── web/                   # Web模块
│   ├── api/              # API接口
│   └── frontend/         # 前端界面
├── data/                  # 数据目录
│   ├── kwafoo.db         # SQLite数据库
│   ├── images/           # 图片存储
│   └── logs/             # 日志文件
└── tests/                 # 测试文件
```

## 技术亮点

1. **轻量级数据库设计**：使用SQLite，无需额外数据库服务，部署简单
2. **直接数据库API**：数据实时更新，无需生成中间文件
3. **AI串行处理**：单条处理，避免并发冲突，适合本地AI性能有限的情况
4. **完整的AI处理状态跟踪**：每条新闻都有ai_processed字段，便于管理
5. **模块化设计**：各模块职责清晰，低耦合高内聚，易于扩展和维护
6. **灵活的爬虫配置**：支持CSS选择器定位，适应不同网页结构
7. **现代化前端**：Vue 3 + TypeScript，提供良好的用户体验
8. **实时进度展示**：WebSocket实时通信，任务状态一目了然
9. **Web管理界面**：配置修改更便捷，无需编辑配置文件
10. **多种文本压缩算法**：支持默认压缩、TextRank压缩、混合压缩等

## 设计原则

- **模块化**：各模块职责清晰，低耦合高内聚
- **可扩展**：易于添加新的新闻源、AI功能等
- **可维护**：代码结构清晰，文档完善
- **高性能**：支持批量处理、队列管理、缓存等
- **用户友好**：现代化的Web界面，实时反馈
- **轻量级**：使用SQLite和本地模型，部署简单