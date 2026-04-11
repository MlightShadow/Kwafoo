# 系统架构设计

## 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    HTTP服务器                           │
│  - Web页面访问                                          │
│  - 管理界面                                             │
│  - API接口                                              │
│  - 进度展示                                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    定时任务调度器                       │
│  - 进度监控                                             │
│  - 任务调度                                             │
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
│                   AI处理模块                           │
│  - 智能分类（串行处理）                                   │
│  - 内容摘要（串行处理）                                   │
│  - 批量处理                                             │
│  - 状态更新                                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   RAG对话模块                          │
│  - 全文搜索                                             │
│  - 上下文构建                                           │
│  - AI问答                                               │
└─────────────────────────────────────────────────────────┘
```

## 数据流程

### 1. 抓取阶段
```
定时任务触发 → 抓取新闻源（RSS/API/网页）→ 数据清洗 → 存入SQLite（ai_processed=0）
```

### 2. 展示阶段
```
HTTP服务提供API → 前端从数据库获取数据 → 动态渲染展示
```

### 3. AI处理阶段
```
定时任务触发 → 获取未处理新闻 → 串行AI处理 → 更新分类和摘要 → 标记已处理（ai_processed=1）
```

### 4. 对话阶段
```
用户提问 → SQLite全文搜索 → 构建上下文 → AI生成回答
```

## 技术栈

- **编程语言**：Python 3.10+
- **数据库**：SQLite
- **HTTP服务器**：内置轻量级HTTP服务器
- **AI框架**：requests（直接调用本地模型）
- **AI模型**：本地模型 - NVIDIA Nemotron-3-Nano-4B (通过OpenAI兼容API)
- **任务调度**：schedule（简单定时任务）
- **前端**：HTML + JavaScript + CSS
- **爬虫库**：requests + BeautifulSoup4

## 模块设计

### 1. 新闻抓取模块 (fetcher/)

```python
class NewsFetcher:
    - fetch_from_rss(rss_url, source_name, fetch_days)
    - fetch_from_api(api_config, fetch_days)
    - fetch_from_webpage(url, selectors, fetch_days)
    - clean_content(raw_data)
    - clean_html(text)
    - save_to_database(news_data)
```

### 2. 数据库管理模块 (database/)

```python
class DatabaseManager:
    - create_tables()
    - insert_news(news_data)
    - get_news_by_date(date)
    - get_news_by_category(category)
    - search_news(query)
    - get_unprocessed_news(limit)
    - update_news_ai_status(news_id, ai_processed)
    - update_news_category(news_id, category)
    - update_news_summary(news_id, ai_summary)
    - create_chat_session(session_id)
    - add_chat_message(session_id, role, content)
```

### 3. AI处理模块 (ai/)

```python
class AINewsProcessor:
    - process_news(news_id, news_data)
    - process_batch(news_list)
    - process_all_unprocessed()
    - get_status()
```

### 4. AI分类器 (ai/classifier.py)

```python
class AIClassifier:
    - classify(title, description)
    - _build_classify_prompt(title, description)
    - _parse_result(result)
```

### 5. AI摘要生成器 (ai/summarizer.py)

```python
class AISummarizer:
    - generate_summary(content, description)
    - _build_summary_prompt(content)
    - _build_rewrite_prompt(description)
```

### 6. RAG对话模块 (rag/)

```python
class RAGEngine:
    - search_relevant_news(query)
    - build_context(search_results)
    - chat_with_ai(query, context)
    - get_chat_history()
```

### 7. HTTP服务模块 (web/)

```python
class HTTPServer:
    - start_server(host, port)
    - handle_news_request()
    - handle_api_request()
    - handle_config_request()
    - handle_ai_status_request()
    - handle_ai_process_request()
```

### 8. 进度监控模块 (utils/progress.py)

```python
class ProgressMonitor:
    - start_task(task_id, task_name)
    - update_progress(task_id, progress, message)
    - complete_task(task_id)
    - broadcast_progress()
```

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

## 技术亮点

1. **轻量级数据库设计**：使用SQLite，无需额外数据库服务
2. **直接数据库API**：数据实时更新，无需生成JSON文件
3. **AI串行处理**：单条处理，避免并发冲突，适合本地AI性能有限的情况
4. **完整的AI处理状态跟踪**：每条新闻都有ai_processed字段
5. **模块化设计**：易于扩展和维护
6. **灵活的爬虫配置**：支持CSS选择器定位
7. **内置HTTP服务器**：无需额外部署
8. **实时进度展示**：任务状态一目了然
9. **Web管理界面**：配置修改更便捷