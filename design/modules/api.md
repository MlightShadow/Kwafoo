# API接口设计

## 概述

Kwafoo提供RESTful API接口，用于获取新闻数据、管理AI处理、触发任务、配置管理等。API采用统一的响应格式，支持JSON数据交换。

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
      "ai_processed": 1,
      "image_url": "https://example.com/image.jpg",
      "is_read": 0
    }
  ],
  "count": 20,
  "limit": 20,
  "offset": 10
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
  "category": "科技",
  "limit": 10,
  "offset": 0
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

### 4. 获取新闻统计

获取新闻统计数据。

**请求：**
```
GET /api/news/stats
```

**响应：**
```json
{
  "success": true,
  "data": {
    "total": 100,
    "active": 95,
    "deleted": 5,
    "processed": 80
  }
}
```

### 5. 标记阅读状态

标记新闻为已读或未读。

**请求：**
```
POST /api/news/mark-read
```

**请求体：**
```json
{
  "news_id": 1,
  "is_read": true
}
```

**响应：**
```json
{
  "success": true,
  "message": "阅读状态已更新"
}
```

### 6. 获取已读新闻

获取已读的新闻列表。

**请求：**
```
GET /api/news/read?limit=10
```

**查询参数：**
- `limit` (可选): 返回数量，默认10

**响应：**
```json
{
  "success": true,
  "data": [...],
  "count": 10
}
```

### 7. 获取未读新闻

获取未读的新闻列表。

**请求：**
```
GET /api/news/unread?limit=10
```

**查询参数：**
- `limit` (可选): 返回数量，默认10

**响应：**
```json
{
  "success": true,
  "data": [...],
  "count": 10
}
```

### 8. 清空新闻

清空所有新闻数据。

**请求：**
```
POST /api/news/clear
```

**响应：**
```json
{
  "success": true,
  "message": "已清空100条新闻",
  "count": 100
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

### 2. 触发AI处理

手动触发AI处理任务，将所有未处理的新闻添加到AI队列。

**请求：**
```
POST /api/ai/process
```

**响应：**
```json
{
  "success": true,
  "message": "已将未处理新闻添加到AI队列"
}
```

### 3. 处理所有新闻

将所有新闻添加到AI队列（高优先级）。

**请求：**
```
POST /api/ai/process-all
```

**响应：**
```json
{
  "success": true,
  "message": "已将所有新闻添加到AI队列"
}
```

### 4. 重新分析新闻

重新分析指定的新闻。

**请求：**
```
POST /api/ai/reanalyze
```

**请求体：**
```json
{
  "news_id": 1,
  "task_type": "all"
}
```

**响应：**
```json
{
  "success": true,
  "message": "已将新闻添加到AI队列"
}
```

### 5. 处理新闻分类

处理新闻分类任务。

**请求：**
```
POST /api/ai/process-category
```

**请求体：**
```json
{
  "news_id": 1
}
```

**响应：**
```json
{
  "success": true,
  "message": "已将新闻添加到分类队列"
}
```

### 6. 处理新闻摘要

处理新闻摘要任务。

**请求：**
```
POST /api/ai/process-summary
```

**请求体：**
```json
{
  "news_id": 1
}
```

**响应：**
```json
{
  "success": true,
  "message": "已将新闻添加到摘要队列"
}
```

## 聊天和RAG接口

### 1. 聊天

基于新闻数据进行智能问答。

**请求：**
```
POST /api/chat
```

**请求体：**
```json
{
  "message": "用户问题",
  "session_id": "session_20260417_120000",
  "category": "科技"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "response": "AI回答",
    "context": "相关新闻上下文",
    "session_id": "session_20260417_120000"
  }
}
```

### 2. 获取聊天历史

获取指定会话的聊天历史。

**请求：**
```
GET /api/chat/history?session_id=session_20260417_120000
```

**查询参数：**
- `session_id` (必需): 会话ID

**响应：**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "role": "user",
        "content": "用户问题"
      },
      {
        "role": "assistant",
        "content": "AI回答"
      }
    ]
  }
}
```

## 配置接口

### 1. 获取配置

获取系统配置。

**请求：**
```
GET /api/config
```

**响应：**
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "name": "科技",
        "icon": "🔬",
        "color": "#3b82f6"
      }
    ],
    "default_category": "全部",
    "enable_ai_category": true,
    "image_display": {
      "enabled": true,
      "position": "left",
      "size": "medium"
    }
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
  "categories": [...],
  "default_category": "全部",
  "enable_ai_category": true
}
```

**响应：**
```json
{
  "success": true,
  "message": "配置已更新"
}
```

## 系统接口

### 1. 获取任务进度

获取所有任务的进度信息。

**请求：**
```
GET /api/system/progress
```

**响应：**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "fetch_20260417_120000",
        "task_name": "抓取新闻",
        "status": "running",
        "progress": 50,
        "current_step": "正在抓取RSS源..."
      }
    ]
  }
}
```

### 2. 健康检查

检查系统健康状态。

**请求：**
```
GET /api/system/health
```

**响应：**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2026-04-17T12:00:00"
}
```

### 3. 手动抓取新闻

手动触发新闻抓取任务。

**请求：**
```
POST /api/system/fetch
```

**响应：**
```json
{
  "success": true,
  "message": "抓取任务已启动（异步执行）"
}
```

### 4. 手动AI处理

手动触发AI处理任务。

**请求：**
```
POST /api/system/process-ai
```

**响应：**
```json
{
  "success": true,
  "message": "AI处理任务已启动（异步执行）"
}
```

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": "错误信息"
}
```

### 常见错误码

- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误

### 错误示例

```json
{
  "success": false,
  "error": "缺少必需参数: category"
}
```

## 参数验证

所有API接口都使用参数验证器确保请求参数的正确性。

**验证器类型：**
- `GetNewsParams`: 获取新闻参数
- `SearchNewsParams`: 搜索新闻参数
- `GetNewsByCategoryParams`: 获取分类新闻参数
- `MarkAsReadParams`: 标记阅读状态参数
- `ProcessNewsParams`: 处理新闻参数

## WebSocket接口

### 连接

```
ws://localhost:8000/ws
```

### 消息格式

**任务开始：**
```json
{
  "type": "task_started",
  "task_id": "fetch_20260417_120000",
  "task_name": "抓取新闻",
  "total_steps": 10,
  "timestamp": "2026-04-17T12:00:00"
}
```

**进度更新：**
```json
{
  "type": "progress_update",
  "task_id": "fetch_20260417_120000",
  "task_name": "抓取新闻",
  "progress": 50,
  "message": "正在抓取RSS源...",
  "timestamp": "2026-04-17T12:00:00"
}
```

**任务完成：**
```json
{
  "type": "task_completed",
  "task_id": "fetch_20260417_120000",
  "task_name": "抓取新闻",
  "success": true,
  "timestamp": "2026-04-17T12:00:00"
}
```

**任务失败：**
```json
{
  "type": "task_failed",
  "task_id": "fetch_20260417_120000",
  "task_name": "抓取新闻",
  "error": "错误信息",
  "timestamp": "2026-04-17T12:00:00"
}
```

## 代码引用

### 新闻API
[web/api/news_api.py](../../web/api/news_api.py) - 新闻API实现

### AI API
[web/api/ai_api.py](../../web/api/ai_api.py) - AI API实现

### 聊天API
[web/api/chat_api.py](../../web/api/chat_api.py) - 聊天API实现

### 配置API
[web/api/config_api.py](../../web/api/config_api.py) - 配置API实现

### 系统API
[web/api/system_api.py](../../web/api/system_api.py) - 系统API实现

## 注意事项

1. **参数验证**：所有请求参数都会被验证，确保数据正确性
2. **错误处理**：完善的错误处理机制，返回详细的错误信息
3. **异步执行**：长时间运行的任务（如抓取、AI处理）采用异步执行
4. **进度监控**：支持实时进度监控，通过WebSocket推送进度更新
5. **线程安全**：所有API接口都是线程安全的
6. **日志记录**：所有API调用都会记录日志，便于调试和监控
7. **性能优化**：支持分页查询，避免一次性返回大量数据
8. **安全性**：注意API安全性，避免敏感信息泄露