# Kwafoo - 夸父新闻聚合 AI Agent

## 项目简介

**Kwafoo（夸父）** - 一个基于AI的新闻和热点聚合系统，以中国神话中"夸父逐日"的精神为灵感，象征着对信息的不懈追求和对真相的执着探索。

夸父逐日，永不言弃。Kwafoo 系统通过定时抓取新闻源，使用SQLite数据库存储，直接通过数据库API提供新闻展示。系统集成了AI串行处理能力，能够对新闻进行智能分类和摘要生成，同时提供RAG（检索增强生成）对话功能，让用户可以基于历史新闻数据进行智能问答。

### 项目寓意

> "夸父与日逐走，入日；渴，欲得饮，饮于河、渭；河、渭不足，北饮大泽。未至，道渴而死。弃其杖，化为邓林。"

夸父逐日的故事象征着：
- **坚持不懈**：对信息的持续追踪和更新
- **追求真理**：从海量信息中提取有价值的内容
- **无私奉献**：为用户提供准确、及时的新闻聚合服务
- **生生不息**：AI驱动的智能处理，让信息价值倍增

## 功能特性

### 核心功能
- **定时新闻抓取**：支持多个新闻源的数据抓取，可配置抓取频率
  - **RSS订阅源**：支持标准RSS/Atom订阅
  - **API接口**：支持RESTful API数据获取
  - **网页爬虫**：支持基于CSS选择器的网页内容提取
  - **抓取天数限制**：可配置只抓取指定天数内的新闻
- **SQLite数据存储**：使用SQLite数据库存储所有新闻数据，便于管理和查询
- **直接数据库展示**：前端通过API直接从数据库获取数据，无需JSON文件
- **AI串行处理**：使用单线程串行处理新闻，适合本地AI性能有限的情况
  - **智能分类**：AI自动识别新闻分类
  - **内容摘要**：AI生成新闻摘要
  - **处理状态跟踪**：记录每条新闻的AI处理状态
- **RAG对话功能**：基于历史新闻数据进行智能问答
- **HTTP服务**：内置HTTP服务器，提供Web访问和管理界面
- **运行进度展示**：实时展示抓取、处理等任务的执行进度
- **配置管理**：提供Web管理界面，支持在线修改配置

### 技术亮点
- 轻量级数据库设计，无需额外数据库服务
- 直接数据库API，数据实时更新，无需生成JSON
- AI串行处理，避免并发冲突，适合本地AI性能有限的情况
- 完整的AI处理状态跟踪机制
- 模块化设计，易于扩展
- 灵活的爬虫配置，支持CSS选择器定位
- 内置HTTP服务器，无需额外部署
- 实时进度展示，任务状态一目了然
- Web管理界面，配置修改更便捷

## 快速开始

### 环境要求

- Python 3.10+
- SQLite 3
- 本地AI服务（如Ollama、LM Studio等，支持OpenAI兼容API）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置系统

1. 复制配置文件模板：
```bash
cp config.json.example config.json
```

2. 编辑 `config.json`，配置新闻源和AI服务：
```json
{
  "news_sources": {
    "rss": [
      {
        "url": "https://36kr.com/feed",
        "name": "36氪",
        "enabled": true,
        "fetch_days": 2
      }
    ]
  },
  "scheduler": {
    "auto_fetch": false,
    "auto_ai_process": false
  },
  "ai": {
    "base_url": "http://localhost:1234",
    "model": "nvidia/nemotron-3-nano-4b",
    "max_workers": 1,
    "batch_size": 1
  }
}
```

**重要配置说明：**
- `auto_fetch`: 是否自动抓取新闻（默认false，关闭）
- `auto_ai_process`: 是否自动AI分析新闻（默认false，关闭）
- 测试阶段建议关闭自动功能，通过管理界面手动触发

### 启动系统

```bash
python main.py
```

系统启动后，访问 http://localhost:8000 查看Web界面。

## 使用指南

### Web界面

启动系统后，打开浏览器访问 http://localhost:8000，可以看到：

- **新闻列表**：按时间线展示所有新闻
- **分类浏览**：按分类筛选新闻
- **AI对话**：基于历史新闻进行智能问答
- **管理界面**：手动抓取新闻、AI分析新闻、查看任务进度和系统状态

### 手动操作

#### 1. 手动抓取新闻

1. 打开管理界面
2. 点击"🔄 手动抓取新闻"按钮
3. 等待抓取完成
4. 查看新闻列表更新

#### 2. 手动AI分析

1. 打开管理界面
2. 点击"🤖 AI分析新闻"按钮
3. 等待AI分析完成
4. 查看新闻摘要和分类更新

### API接口

系统提供RESTful API接口，可以用于集成到其他应用。

**获取新闻列表：**
```bash
curl http://localhost:8000/api/news
```

**搜索新闻：**
```bash
curl "http://localhost:8000/api/news/search?q=AI"
```

**触发AI处理：**
```bash
curl -X POST http://localhost:8000/api/ai/process
```

更多API接口请参考 [API文档](doc/api.md)。

### 配置说明

详细的配置说明请参考 [配置文档](doc/configuration.md)。

主要配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|---------|
| fetch_interval | 新闻抓取间隔（秒） | 1800 |
| ai_process_interval | AI处理间隔（秒） | 600 |
| max_workers | 并发线程数 | 1 |
| batch_size | 批处理大小 | 1 |
| enable_ai_category | 是否启用AI分类 | true |
| enable_summary | 是否启用AI摘要 | true |

## 项目结构

```
kwafoo/
├── README.md
├── requirements.txt
├── config.json
├── main.py
├── doc/                    # 文档目录
│   ├── architecture.md       # 系统架构设计
│   ├── database.md          # 数据库设计
│   ├── ai-design.md         # AI设计文档
│   ├── api.md              # API接口文档
│   └── configuration.md     # 配置说明
├── database/
│   ├── __init__.py
│   └── manager.py
├── fetcher/
│   ├── __init__.py
│   ├── rss_fetcher.py
│   ├── api_fetcher.py
│   └── web_fetcher.py
├── ai/
│   ├── __init__.py
│   ├── classifier.py
│   ├── summarizer.py
│   └── processor.py
├── rag/
│   ├── __init__.py
│   └── engine.py
├── scheduler/
│   ├── __init__.py
│   └── scheduler.py
├── utils/
│   ├── __init__.py
│   ├── logger.py
│   ├── progress.py
│   └── helpers.py
├── web/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── server.py
├── data/
│   ├── kwafoo.db
│   └── logs/
└── tests/
    ├── test_serial_processing.py
    ├── test_ai_call.py
    ├── test_direct_api.py
    ├── test_rss.py
    ├── demo_ai_processing.py
    ├── reset_ai_status.py
    └── check_ai_results.py
```

## 文档

- [系统架构设计](doc/architecture.md) - 系统架构、数据流程、模块设计
- [数据库设计](doc/database.md) - 数据库表结构、索引设计、操作示例
- [AI设计文档](doc/ai-design.md) - AI框架选择、处理逻辑、配置说明
- [API接口文档](doc/api.md) - RESTful API接口说明
- [配置说明](doc/configuration.md) - 配置文件详解

## 测试

运行测试脚本：

```bash
# 测试RSS抓取
python tests/test_rss.py

# 测试AI调用
python tests/test_ai_call.py

# 测试串行处理
python tests/test_serial_processing.py

# 查看AI处理结果
python tests/check_ai_results.py
```

## 常见问题

### 1. AI服务连接失败

确保本地AI服务正在运行，并且配置文件中的`base_url`和`model`正确。

### 2. 新闻抓取失败

检查网络连接和新闻源URL是否正确。查看日志文件`data/logs/kwafoo.log`获取详细错误信息。

### 3. 数据库错误

确保`data`目录存在且有写权限。如果数据库损坏，可以删除`data/kwafoo.db`重新创建。

### 4. 端口被占用

如果8000端口被占用，可以修改`config.json`中的`server.port`配置。

## 技术栈

- **编程语言**：Python 3.10+
- **数据库**：SQLite
- **HTTP服务器**：内置轻量级HTTP服务器
- **AI框架**：requests（直接调用本地模型）
- **AI模型**：本地模型 - NVIDIA Nemotron-3-Nano-4B (通过OpenAI兼容API)
- **任务调度**：schedule（简单定时任务）
- **前端**：HTML + JavaScript + CSS
- **爬虫库**：requests + BeautifulSoup4

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue
- 发送邮件

---

**Kwafoo - 夸父逐日，永不言弃**