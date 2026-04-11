# API接口文档

## 概述

Kwafoo提供RESTful API接口，用于获取新闻数据、管理AI处理、触发任务等。

## 基础信息

- **Base URL**: `http://localhost:8000`
- **Content-Type**: `application/json`
- **字符编码**: `UTF-8`

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": {...}
}
```

### 错误响应

```json
{
  "success": false,
  "error": "错误信息"
}
```

## 新闻接口

### 1. 获取新闻列表

获取所有可见的新闻，按发布时间倒序排列。

**请求：**
```
GET /api/news
```

**查询参数：**
- `limit` (可选): 返回数量，默认30
- `offset` (可选): 偏移量，默认0

**示例：**
```
GET /api/news?limit=20&offset=10
```

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "新闻标题",
      "description": "新闻描述",
      "ai_summary": "AI摘要",
      "url": "https://example.com/news/1",
      "source": "36氪",
      "category": "科技,互联网",
      "publish_time": "2026-04-10 12:00:00",
      "fetch_time": "2026-04-10 12:30:00",
      "is_visible": 1,
      "ai_processed": 1
    }
  ],
  "count": 20
}
```

### 2. 获取分类新闻

获取指定分类的新闻。

**请求：**
```
GET /api/news/category?category=科技
```

**查询参数：**
- `category` (必需): 分类名称
- `limit` (可选): 返回数量，默认30
- `offset` (可选): 偏移量，默认0

**示例：**
```
GET /api/news/category?category=科技&limit=10
```

**响应：**
```json
{
  "success": true,
  "data": [...],
  "count": 10,
  "category": "科技"
}
```

### 3. 搜索新闻

根据关键词搜索新闻。

**请求：**
```
GET /api/news/search?q=AI&limit=10
```

**查询参数：**
- `q` (必需): 搜索关键词
- `limit` (可选): 返回数量，默认10

**示例：**
```
GET /api/news/search?q=人工智能&limit=5
```

**响应：**
```json
{
  "success": true,
  "data": [...],
  "count": 5,
  "query": "人工智能"
}
```

## AI接口

### 1. 获取AI处理状态

获取AI处理器的当前状态。

**请求：**
```
GET /api/ai/status
```

**响应：**
```json
{
  "success": true,
  "data": {
    "processing": false,
    "unprocessed_count": 30,
    "max_workers": 1,
    "batch_size": 1,
    "enable_ai_category": true,
    "enable_ai_summary": true
  }
}
```

**字段说明：**
- `processing`: 是否正在处理
- `unprocessed_count`: 未处理的新闻数量
- `max_workers`: 并发线程数
- `batch_size`: 批处理大小
- `enable_ai_category`: 是否启用AI分类
- `enable_ai_summary`: 是否启用AI摘要

### 2. 触发AI处理

手动触发AI处理任务。

**请求：**
```
POST /api/ai/process
```

**响应：**
```json
{
  "success": true,
  "message": "AI处理任务已启动",
  "task_id": "ai_process_20260410_115000"
}
```

## 任务接口

### 1. 手动抓取新闻

手动触发新闻抓取任务。

**请求：**
```
POST /api/fetch
```

**响应：**
```json
{
  "success": true,
  "message": "抓取任务已启动",
  "task_id": "manual_fetch_20260410_115000"
}
```

### 2. 获取任务进度

获取当前所有任务的执行进度。

**请求：**
```
GET /api/progress
```

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "task_id": "ai_process_20260410_115000",
      "task_name": "AI处理新闻",
      "progress": 50,
      "message": "正在处理第15条新闻",
      "status": "running",
      "created_at": "2026-04-10 11:50:00"
    },
    {
      "task_id": "manual_fetch_20260410_110000",
      "task_name": "抓取新闻",
      "progress": 100,
      "message": "任务完成",
      "status": "completed",
      "created_at": "2026-04-10 11:00:00"
    }
  ]
}
```

## 对话接口

### 1. 发送对话消息

发送对话消息并获取AI回复。

**请求：**
```
POST /api/chat
```

**请求体：**
```json
{
  "session_id": "session_123",
  "message": "最近有什么科技新闻？",
  "use_rag": true
}
```

**字段说明：**
- `session_id`: 会话ID（可选，不提供则创建新会话）
- `message`: 用户消息
- `use_rag`: 是否使用RAG（默认true）

**响应：**
```json
{
  "success": true,
  "data": {
    "session_id": "session_123",
    "message": "根据最新的新闻，科技领域有以下重要动态...",
    "context_news": [
      {
        "id": 1,
        "title": "新闻标题",
        "relevance": 0.95
      }
    ]
  }
}
```

### 2. 获取对话历史

获取指定会话的对话历史。

**请求：**
```
GET /api/chat/history?session_id=session_123
```

**查询参数：**
- `session_id` (必需): 会话ID
- `limit` (可选): 返回数量，默认50

**响应：**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "role": "user",
      "content": "最近有什么科技新闻？",
      "created_at": "2026-04-10 12:00:00"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "根据最新的新闻，科技领域有以下重要动态...",
      "created_at": "2026-04-10 12:00:05"
    }
  ]
}
```

## 配置接口

### 1. 获取配置

获取当前系统配置。

**请求：**
```
GET /api/config
```

**响应：**
```json
{
  "success": true,
  "data": {
    "news_sources": {...},
    "categories": {...},
    "ai": {...},
    "scheduler": {...}
  }
}
```

### 2. 更新配置

更新系统配置。

**请求：**
```
POST /api/config
```

**请求体：**
```json
{
  "news_sources": {
    "rss": [...]
  },
  "ai": {
    "max_workers": 1,
    "batch_size": 1
  }
}
```

**响应：**
```json
{
  "success": true,
  "message": "配置已更新"
}
```

## 健康检查

### 1. 健康检查

检查系统健康状态。

**请求：**
```
GET /api/health
```

**响应：**
```json
{
  "success": true,
  "status": "healthy",
  "database": "connected",
  "ai_service": "available",
  "timestamp": "2026-04-10 12:00:00"
}
```

## 错误码

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 使用示例

### Python示例

```python
import requests

# 获取新闻列表
response = requests.get('http://localhost:8000/api/news')
data = response.json()
print(data)

# 搜索新闻
response = requests.get('http://localhost:8000/api/news/search?q=AI')
data = response.json()
print(data)

# 触发AI处理
response = requests.post('http://localhost:8000/api/ai/process')
data = response.json()
print(data)

# 发送对话消息
response = requests.post(
    'http://localhost:8000/api/chat',
    json={
        'message': '最近有什么科技新闻？',
        'use_rag': True
    }
)
data = response.json()
print(data)
```

### JavaScript示例

```javascript
// 获取新闻列表
fetch('http://localhost:8000/api/news')
  .then(response => response.json())
  .then(data => console.log(data));

// 搜索新闻
fetch('http://localhost:8000/api/news/search?q=AI')
  .then(response => response.json())
  .then(data => console.log(data));

// 触发AI处理
fetch('http://localhost:8000/api/ai/process', {
  method: 'POST'
})
  .then(response => response.json())
  .then(data => console.log(data));

// 发送对话消息
fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    message: '最近有什么科技新闻？',
    use_rag: true
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL示例

```bash
# 获取新闻列表
curl http://localhost:8000/api/news

# 搜索新闻
curl "http://localhost:8000/api/news/search?q=AI"

# 触发AI处理
curl -X POST http://localhost:8000/api/ai/process

# 发送对话消息
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"最近有什么科技新闻？","use_rag":true}'
```

## 注意事项

1. **超时设置**：AI处理任务可能需要较长时间，建议设置合理的超时时间
2. **并发限制**：避免频繁触发AI处理任务，建议等待当前任务完成
3. **数据格式**：所有请求和响应都使用UTF-8编码
4. **错误处理**：建议检查`success`字段判断请求是否成功
5. **日志记录**：建议记录API调用的响应时间和错误信息