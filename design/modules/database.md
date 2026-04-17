# 数据库设计

## 数据库概述

Kwafoo使用SQLite作为数据库，存储新闻数据、对话消息和统计信息。SQLite是轻量级的嵌入式数据库，无需额外数据库服务，非常适合中小型应用。

## 数据表设计

### news表（新闻表）

新闻表是系统的核心表，存储所有抓取的新闻数据。

```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    ai_summary TEXT,
    content TEXT,
    url TEXT UNIQUE,
    source TEXT NOT NULL,
    category TEXT,
    publish_time DATETIME,
    fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_visible BOOLEAN DEFAULT 1,
    ai_processed BOOLEAN DEFAULT 0,
    image_url TEXT,
    image_data BLOB,
    is_deleted BOOLEAN DEFAULT 0,
    is_read BOOLEAN DEFAULT 0
);
```

#### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | INTEGER | 是 | 主键，自增 |
| title | TEXT | 是 | 新闻标题（必须抓取） |
| description | TEXT | 否 | 抓取的原始描述（RSS必须抓取，网页可选） |
| ai_summary | TEXT | 否 | AI生成的摘要 |
| content | TEXT | 否 | 新闻正文（不一定抓取，取决于描述情况） |
| url | TEXT | 是 | 新闻链接（唯一，用于点击跳转） |
| source | TEXT | 是 | 新闻来源名称（RSS源名称或网站名称） |
| category | TEXT | 否 | 新闻分类（多个分类用逗号分隔，如"科技,互联网"） |
| publish_time | DATETIME | 是 | 新闻发布时间 |
| fetch_time | DATETIME | 是 | 抓取时间（默认当前时间） |
| is_visible | BOOLEAN | 是 | 是否可见（默认1） |
| ai_processed | BOOLEAN | 是 | 是否已通过AI处理（默认0） |
| image_url | TEXT | 否 | 新闻图片URL |
| image_data | BLOB | 否 | 压缩后的图片数据（Base64编码） |
| is_deleted | BOOLEAN | 是 | 是否已删除（默认0） |
| is_read | BOOLEAN | 是 | 是否已读（默认0） |

#### AI处理状态说明

- `ai_processed = 0`：未处理，等待AI处理
- `ai_processed = 1`：已处理，已完成AI分类和摘要生成

#### 分类字段说明

- **单分类**：`category = "科技"`
- **多分类**：`category = "科技,财经"`（用逗号分隔，最多2个分类）
- **无分类**：`category = ""`（留空，展示在默认分类中）
- **页面展示**：新闻会在所有匹配的分类中展示

#### 阅读状态说明

- `is_read = 0`：未读
- `is_read = 1`：已读

#### 删除状态说明

- `is_deleted = 0`：未删除
- `is_deleted = 1`：已删除（软删除）

#### 图片处理说明

- `image_url`：存储原始图片URL
- `image_data`：存储压缩后的图片数据（Base64编码）
- 图片自动下载、压缩和存储
- 支持多种图片格式

#### 索引设计

```sql
-- 按发布时间索引（用于时间线展示）
CREATE INDEX idx_publish_time ON news(publish_time DESC);

-- 按分类索引（用于分类筛选）
CREATE INDEX idx_category ON news(category);

-- 按可见性索引（用于过滤不展示的新闻）
CREATE INDEX idx_is_visible ON news(is_visible);

-- 按抓取时间索引（用于增量抓取）
CREATE INDEX idx_fetch_time ON news(fetch_time DESC);

-- 复合索引：按分类和状态查询
CREATE INDEX idx_category_visible ON news(category, is_visible);

-- 覆盖索引：包含常用查询字段
CREATE INDEX idx_covering ON news(publish_time DESC, category, is_visible) 
    WHERE is_visible = 1;

-- 全文搜索索引（用于RAG对话）
CREATE VIRTUAL TABLE news_fts USING fts5(title, description, ai_summary, content);
```

### chat_sessions表（对话会话表）

存储对话会话信息。

```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    user_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | INTEGER | 是 | 主键，自增 |
| session_id | TEXT | 是 | 会话ID（唯一） |
| user_id | TEXT | 否 | 用户ID（可选） |
| created_at | DATETIME | 是 | 创建时间 |
| updated_at | DATETIME | 是 | 更新时间 |

### chat_messages表（对话消息表）

存储对话消息详情。

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

#### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | INTEGER | 是 | 主键，自增 |
| session_id | INTEGER | 是 | 会话ID（外键） |
| role | TEXT | 是 | 角色（user/assistant） |
| content | TEXT | 是 | 消息内容 |
| context_news_ids | TEXT | 否 | 上下文新闻ID（逗号分隔） |
| created_at | DATETIME | 是 | 创建时间 |

### daily_stats表（每日统计表）

存储每日统计数据，用于仪表盘展示。

```sql
CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE,
    total_news INTEGER,
    by_category TEXT,
    by_source TEXT,
    ai_summary_count INTEGER,
    ai_category_count INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 字段说明

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | INTEGER | 是 | 主键，自增 |
| date | DATE | 是 | 日期（唯一） |
| total_news | INTEGER | 否 | 总新闻数 |
| by_category | TEXT | 否 | 按分类统计（JSON格式） |
| by_source | TEXT | 否 | 按来源统计（JSON格式） |
| ai_summary_count | INTEGER | 否 | AI摘要数量 |
| ai_category_count | INTEGER | 否 | AI分类数量 |
| created_at | DATETIME | 是 | 创建时间 |

## 数据库管理器功能

### 核心功能

- **连接管理**：单例模式，支持多线程
- **表创建**：自动创建和迁移数据表
- **数据操作**：增删改查、批量操作
- **图片处理**：自动下载、压缩、存储图片
- **阅读状态管理**：标记新闻已读/未读
- **软删除**：支持软删除和恢复
- **全文搜索**：基于FTS5的全文搜索
- **统计功能**：新闻统计、分类统计
- **WebSocket广播**：实时更新前端

### 数据库操作示例

#### 插入新闻

```python
news_data = {
    'title': '新闻标题',
    'description': '新闻描述',
    'url': 'https://example.com/news/1',
    'source': '36氪',
    'publish_time': '2026-04-10 12:00:00',
    'category': None,
    'ai_processed': 0,
    'image_url': 'https://example.com/image.jpg'
}

db.insert_news(news_data)
```

#### 获取未处理的新闻

```python
unprocessed_news = db.get_unprocessed_news(limit=100)
```

#### 更新AI处理状态

```python
# 更新分类
db.update_news_category(news_id, '科技,互联网')

# 更新摘要
db.update_news_summary(news_id, 'AI生成的摘要')

# 更新处理状态
db.update_news_ai_status(news_id, True)
```

#### 按分类查询新闻

```python
tech_news = db.get_news_by_category('科技')
```

#### 全文搜索

```python
results = db.search_news('人工智能')
```

#### 标记阅读状态

```python
db.mark_news_as_read(news_id, is_read=True)
```

#### 获取统计数据

```python
stats = db.get_stats()
# 返回：{'total': 100, 'active': 95, 'deleted': 5, 'processed': 80}
```

## 数据库维护

### 数据备份

```bash
# 备份数据库
cp data/kwafoo.db data/kwafoo_backup_$(date +%Y%m%d).db
```

### 数据清理

```python
# 清理30天前的新闻
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('data/kwafoo.db')
cursor = conn.cursor()

cutoff_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
cursor.execute('DELETE FROM news WHERE fetch_time < ?', (cutoff_date,))

conn.commit()
conn.close()
```

### 性能优化

```sql
-- 分析查询计划
EXPLAIN QUERY PLAN SELECT * FROM news WHERE category = '科技' ORDER BY publish_time DESC LIMIT 20;

-- 重建索引
REINDEX idx_publish_time;

-- 清理数据库
VACUUM;
```

## 数据库安全

### 访问控制

- 数据库文件位于`data/kwafoo.db`
- 建议设置文件权限：`chmod 600 data/kwafoo.db`
- 生产环境建议使用加密数据库

### 数据完整性

- 使用外键约束
- 使用唯一约束（如URL）
- 使用事务保证数据一致性

## 数据库迁移

当需要修改数据库结构时，数据库管理器会自动检测并添加新字段：

- `image_url`：新闻图片URL
- `image_data`：压缩后的图片数据
- `is_deleted`：软删除标记
- `is_read`：阅读状态标记

迁移过程：
1. 检查字段是否存在
2. 如果不存在，自动添加字段
3. 记录迁移日志

## 代码引用

数据库管理器的完整实现：[database/manager.py](../../database/manager.py)

图片处理模块：[utils/image_processor.py](../../utils/image_processor.py)