# RAG对话模块设计

## 模块概述

RAG（Retrieval-Augmented Generation，检索增强生成）对话模块基于历史新闻数据进行智能问答。模块使用SQLite的FTS5全文搜索功能检索相关新闻，然后基于检索结果构建上下文，最后调用AI生成回答。

## 工作流程

```
用户提问 → 全文搜索 → 构建上下文 → AI生成回答 → 返回结果
```

### 详细流程

1. **用户提问**：用户通过前端界面输入问题
2. **全文搜索**：RAG引擎在新闻数据库中搜索相关新闻
3. **构建上下文**：从搜索结果中提取关键信息，构建对话上下文
4. **AI生成回答**：基于上下文调用AI生成回答
5. **返回结果**：将AI回答返回给前端展示

## 核心功能

### 1. 全文搜索

**技术选型：**
- 使用SQLite的FTS5全文搜索功能
- 支持中文分词（通过配置）
- 支持相关性排序

**搜索策略：**

**方式1：FTS全文搜索（推荐）**
```sql
CREATE VIRTUAL TABLE news_fts USING fts5(title, description, ai_summary, content);
```

**方式2：关键词匹配（备用）**
- 将查询拆分为关键词
- 在标题、描述、摘要中匹配
- 计算相关性得分
- 按得分排序

**搜索参数：**
- `top_k`：返回的新闻数量（默认5）
- `use_fts`：是否使用FTS全文搜索（默认true）
- `category`：按分类过滤（可选）

**代码实现：**
```python
def search(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    if self.use_fts:
        news_list = db.search_news(query, limit=self.top_k * 2)
    else:
        news_list = self._search_by_keywords(query)
    
    if category:
        news_list = self._filter_by_category(news_list, category)
    
    news_list = news_list[:self.top_k]
    
    return news_list
```

### 2. 上下文构建

**构建策略：**
- 从搜索结果中提取新闻标题、摘要、来源、链接
- 按相关性排序
- 格式化为结构化文本

**上下文格式：**
```
1. 标题：新闻标题1
   摘要：新闻摘要1
   来源：新闻来源1
   链接：新闻链接1

2. 标题：新闻标题2
   摘要：新闻摘要2
   来源：新闻来源2
   链接：新闻链接2
...
```

**代码实现：**
```python
def build_context(self, query: str, category: Optional[str] = None) -> str:
    news_list = self.search(query, category)
    
    if not news_list:
        return "没有找到相关新闻。"
    
    context_parts = []
    for i, news in enumerate(news_list, 1):
        title = news.get('title', '')
        summary = news.get('ai_summary') or news.get('description', '')
        source = news.get('source', '')
        url = news.get('url', '')
        
        context_part = f"""
{i}. 标题：{title}
   摘要：{summary}
   来源：{source}
   链接：{url}
"""
        context_parts.append(context_part)
    
    return ''.join(context_parts)
```

### 3. 智能问答

**AI调用：**
- 基于构建的上下文调用AI
- 使用OpenAI SDK
- 支持对话历史

**提示词设计：**
```
你是一个新闻助手，基于提供的新闻信息回答用户问题。

上下文：
{context}

问题：{query}

请基于上下文信息回答问题，如果上下文中没有相关信息，请说明。
```

**对话历史管理：**
- 存储在chat_sessions和chat_messages表中
- 支持多轮对话
- 支持上下文新闻ID记录

## 配置参数

### RAG配置
```toml
[rag]
top_k = 5              # 返回的新闻数量
use_fts = true         # 是否使用FTS全文搜索
```

### AI配置
```toml
[ai]
base_url = "http://localhost:1234"
model = "nvidia/nemotron-3-nano-4b"
max_tokens = 4096
temperature = 0.7
```

## 数据库设计

### chat_sessions表
```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    user_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### chat_messages表
```sql
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    context_news_ids TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);
```

### news_fts表（全文搜索）
```sql
CREATE VIRTUAL TABLE news_fts USING fts5(title, description, ai_summary, content);
```

## API接口

### 聊天接口
```
POST /api/chat
```

**请求参数：**
```json
{
  "message": "用户问题",
  "session_id": "会话ID（可选）",
  "category": "分类过滤（可选）"
}
```

**响应：**
```json
{
  "success": true,
  "data": {
    "response": "AI回答",
    "context_news": [...],
    "session_id": "会话ID"
  }
}
```

### 获取对话历史
```
GET /api/chat/history?session_id=xxx
```

**响应：**
```json
{
  "success": true,
  "data": {
    "messages": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ]
  }
}
```

## 性能优化

### 搜索优化
- 使用FTS5全文搜索（比关键词匹配快）
- 限制返回数量（top_k）
- 按分类过滤减少搜索范围

### 上下文优化
- 限制上下文长度（避免超出AI输入限制）
- 优先使用AI摘要（比原始描述更简洁）
- 按相关性排序，只使用最相关的新闻

### 缓存策略
- 缓存常见问题的搜索结果
- 缓存对话历史
- 定期清理过期会话

## 错误处理

### 搜索失败
- 降级到关键词匹配
- 返回空结果
- 记录错误日志

### 上下文构建失败
- 返回默认提示
- 记录错误日志
- 不影响对话继续

### AI调用失败
- 返回错误信息
- 记录错误日志
- 不影响对话历史

## 代码引用

### RAG引擎
[rag/engine.py](../../rag/engine.py) - RAG引擎实现

### 聊天API
[web/api/chat_api.py](../../web/api/chat_api.py) - 聊天API实现

### 数据库管理器
[database/manager.py](../../database/manager.py) - 数据库管理器（包含全文搜索）

## 注意事项

1. **FTS5配置**：确保SQLite编译时包含FTS5支持
2. **中文分词**：配置合适的中文分词器
3. **上下文长度**：控制上下文长度，避免超出AI输入限制
4. **隐私保护**：对话历史可能包含敏感信息，需要妥善处理
5. **性能监控**：监控搜索和AI调用的性能
6. **错误恢复**：完善的错误处理和降级策略
7. **会话管理**：定期清理过期会话，避免数据库膨胀