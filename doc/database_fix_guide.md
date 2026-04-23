# 数据库修复指南

## 概述

本指南提供了Kwafoo新闻聚合系统数据库问题的诊断和修复方法，主要解决以下常见问题：

1. RSS抓取的新闻无法在页面显示
2. reanalyze功能参数验证失败
3. 数据库表结构损坏
4. ID字段失去自增属性

## 问题诊断

### 1. 检查新闻显示问题

```bash
# 检查今日新闻数量
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE DATE(fetch_time) = DATE(\"now\") AND is_visible = 1 AND is_deleted = 0'); print('今日新闻数:', cursor.fetchone()[0]); conn.close()"

# 检查NULL值问题
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT is_deleted, is_read, COUNT(*) FROM news WHERE DATE(fetch_time) = DATE(\"now\") GROUP BY is_deleted, is_read'); print('今日新闻状态:'); [print(f'  is_deleted={row[0]}, is_read={row[1]}: {row[2]}条') for row in cursor.fetchall()]; conn.close()"
```

**症状：**
- 今日新闻数为0，但日志显示抓取成功
- 新闻状态显示 `is_deleted=NULL` 或 `is_read=NULL`

### 2. 检查表结构问题

```bash
# 检查表结构
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT sql FROM sqlite_master WHERE type=\"table\" AND name=\"news\"'); print('news表结构:'); print(cursor.fetchone()[0]); conn.close()"
```

**症状：**
- 表结构中缺少 `PRIMARY KEY AUTOINCREMENT`
- 字段之间缺少逗号分隔
- ID字段类型为 `INT` 而不是 `INTEGER`

### 3. 检查ID字段问题

```bash
# 检查NULL ID
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE id IS NULL'); print('NULL ID数量:', cursor.fetchone()[0]); conn.close()"

# 检查最新新闻的ID
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT id, title FROM news WHERE DATE(fetch_time) = DATE(\"now\") LIMIT 5'); print('今日新闻ID:'); [print(f'  ID={row[0]}, title={row[1][:40]}...') for row in cursor.fetchall()]; conn.close()"
```

**症状：**
- 新闻ID为None
- 前端reanalyze功能报错：参数验证失败

## 修复方法

### 方法1：使用自动修复脚本（推荐）

#### 步骤1：停止服务器

```bash
# 如果服务器正在运行，先停止
# 在服务器终端按 Ctrl+C 或发送停止信号
```

#### 步骤2：备份数据库

```bash
# 创建数据库备份
cp data/kwafoo.db data/kwafoo_backup_$(date +%Y%m%d_%H%M%S).db
```

#### 步骤3：运行修复脚本

```bash
# 执行修复脚本
python fix_database.py
```

#### 步骤4：验证修复结果

```bash
# 检查修复后的数据
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE is_visible = 1 AND is_deleted = 0'); print('可用新闻数:', cursor.fetchone()[0]); cursor.execute('SELECT COUNT(*) FROM news WHERE id IS NULL'); print('NULL ID数量:', cursor.fetchone()[0]); conn.close()"
```

#### 步骤5：重启服务器

```bash
# 启动服务器
python main.py
```

### 方法2：手动修复（高级用户）

#### 修复NULL值问题

```sql
-- 连接到数据库
sqlite3 data/kwafoo.db

-- 修复is_deleted字段
UPDATE news SET is_deleted = 0 WHERE is_deleted IS NULL;

-- 修复is_read字段
UPDATE news SET is_read = 0 WHERE is_read IS NULL;

-- 验证修复结果
SELECT is_deleted, is_read, COUNT(*) FROM news GROUP BY is_deleted, is_read;
```

#### 重建表结构（如果表结构损坏）

```sql
-- 1. 备份数据
CREATE TABLE news_backup AS SELECT * FROM news;

-- 2. 删除损坏的表
DROP TABLE news;

-- 3. 创建正确的新表
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    ai_summary TEXT,
    content TEXT,
    url TEXT UNIQUE,
    source TEXT NOT NULL,
    source_url TEXT,
    category TEXT,
    publish_time DATETIME,
    fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_visible BOOLEAN DEFAULT 1,
    ai_processed BOOLEAN DEFAULT 0,
    image_url TEXT,
    image_data BLOB,
    is_deleted BOOLEAN DEFAULT 0,
    is_read BOOLEAN DEFAULT 0,
    compressed_content TEXT,
    keywords TEXT,
    ai_comment TEXT,
    ai_score REAL,
    ai_score_topic_relevance REAL,
    ai_score_importance REAL,
    ai_score_source REAL
);

-- 4. 处理重复URL
DELETE FROM news_backup 
WHERE ROWID NOT IN (
    SELECT MIN(ROWID) FROM news_backup GROUP BY url
);

-- 5. 恢复数据
INSERT INTO news (
    id, title, description, ai_summary, content, url, source, source_url,
    category, publish_time, fetch_time, is_visible, ai_processed,
    image_url, image_data, is_deleted, is_read,
    compressed_content, keywords, ai_comment, ai_score,
    ai_score_topic_relevance, ai_score_importance, ai_score_source
)
SELECT id, title, description, ai_summary, content, url, source, source_url,
       category, publish_time, fetch_time, is_visible, ai_processed,
       image_url, image_data, is_deleted, is_read,
       compressed_content, keywords, ai_comment, ai_score,
       ai_score_topic_relevance, ai_score_importance, ai_score_source
FROM news_backup;

-- 6. 删除备份表
DROP TABLE news_backup;

-- 7. 重建索引
CREATE INDEX IF NOT EXISTS idx_news_fetch_time ON news(fetch_time DESC);
CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news(publish_time DESC);
CREATE INDEX IF NOT EXISTS idx_news_category ON news(category);
CREATE INDEX IF NOT EXISTS idx_news_source ON news(source);
CREATE INDEX IF NOT EXISTS idx_news_visible ON news(is_visible, is_deleted);

-- 8. 重建全文搜索表
DROP TABLE IF EXISTS news_fts;
CREATE VIRTUAL TABLE news_fts USING fts5(
    title, description, ai_summary, content, keywords,
    content='news', content_rowid='id'
);
INSERT INTO news_fts(rowid, title, description, ai_summary, content, keywords)
SELECT id, title, description, ai_summary, content, keywords FROM news;
```

## 代码修复

### 修复INSERT语句

**文件：** `database/manager.py`

**位置：** `insert_news` 方法中的INSERT语句

**修复前：**
```python
cursor.execute('''
    INSERT INTO news (
        title, description, ai_summary, content, compressed_content, url, 
        source, source_url, category, publish_time, is_visible, image_url, image_data, fetch_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    news_data.get('title'),
    news_data.get('description'),
    news_data.get('ai_summary'),
    news_data.get('content'),
    news_data.get('compressed_content'),
    news_data.get('url'),
    news_data.get('source'),
    news_data.get('source_url'),
    news_data.get('category'),
    news_data.get('publish_time'),
    news_data.get('is_visible', 1),
    image_url,
    image_data,
    fetch_time
))
```

**修复后：**
```python
cursor.execute('''
    INSERT INTO news (
        title, description, ai_summary, content, compressed_content, url, 
        source, source_url, category, publish_time, is_visible, is_deleted, is_read, image_url, image_data, fetch_time
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    news_data.get('title'),
    news_data.get('description'),
    news_data.get('ai_summary'),
    news_data.get('content'),
    news_data.get('compressed_content'),
    news_data.get('url'),
    news_data.get('source'),
    news_data.get('source_url'),
    news_data.get('category'),
    news_data.get('publish_time'),
    news_data.get('is_visible', 1),
    news_data.get('is_deleted', 0),
    news_data.get('is_read', 0),
    image_url,
    image_data,
    fetch_time
))
```

### 修复UPDATE语句

**文件：** `database/manager.py`

**位置：** 恢复已删除新闻的UPDATE语句

**修复前：**
```python
cursor.execute('''
    UPDATE news SET
        title = ?,
        description = ?,
        ai_summary = ?,
        content = ?,
        compressed_content = ?,
        source = ?,
        source_url = ?,
        category = ?,
        publish_time = ?,
        is_visible = ?,
        image_url = ?,
        image_data = ?,
        is_deleted = 0,
        fetch_time = ?
    WHERE id = ?
''', (
    news_data.get('title'),
    news_data.get('description'),
    news_data.get('ai_summary'),
    news_data.get('content'),
    news_data.get('compressed_content'),
    news_data.get('source'),
    news_data.get('source_url'),
    news_data.get('category'),
    news_data.get('publish_time'),
    news_data.get('is_visible', 1),
    image_url,
    image_data,
    fetch_time,
    news_id
))
```

**修复后：**
```python
cursor.execute('''
    UPDATE news SET
        title = ?,
        description = ?,
        ai_summary = ?,
        content = ?,
        compressed_content = ?,
        source = ?,
        source_url = ?,
        category = ?,
        publish_time = ?,
        is_visible = ?,
        is_deleted = 0,
        is_read = 0,
        image_url = ?,
        image_data = ?,
        fetch_time = ?
    WHERE id = ?
''', (
    news_data.get('title'),
    news_data.get('description'),
    news_data.get('ai_summary'),
    news_data.get('content'),
    news_data.get('compressed_content'),
    news_data.get('source'),
    news_data.get('source_url'),
    news_data.get('category'),
    news_data.get('publish_time'),
    news_data.get('is_visible', 1),
    image_url,
    image_data,
    fetch_time,
    news_id
))
```

### 修复数据库迁移代码

**文件：** `database/manager.py`

**位置：** `_migrate_database` 方法中的表重建逻辑

**修复要点：**
1. 使用明确的表创建语句，而不是 `CREATE TABLE ... AS SELECT`
2. 保留所有约束和属性（PRIMARY KEY, UNIQUE, DEFAULT等）
3. 正确处理数据恢复过程
4. 删除备份表

**修复示例：**
```python
# 移除 ai_score_freshness 字段（SQLite不支持直接删除列，需要重建表）
if 'ai_score_freshness' in columns:
    logger.info("数据库迁移：移除 ai_score_freshness 字段")
    
    # 备份数据
    cursor.execute('''
        CREATE TABLE news_backup AS
        SELECT id, title, description, ai_summary, content, url, source, source_url,
               category, publish_time, fetch_time, is_visible, ai_processed,
               image_url, image_data, is_deleted, is_read,
               compressed_content, keywords, ai_comment, ai_score,
               ai_score_topic_relevance, ai_score_importance, ai_score_source
        FROM news
    ''')
    
    # 删除旧表
    cursor.execute('DROP TABLE news')
    
    # 创建新表（包含正确的约束）
    cursor.execute('''
        CREATE TABLE news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            ai_summary TEXT,
            content TEXT,
            url TEXT UNIQUE,
            source TEXT NOT NULL,
            source_url TEXT,
            category TEXT,
            publish_time DATETIME,
            fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_visible BOOLEAN DEFAULT 1,
            ai_processed BOOLEAN DEFAULT 0,
            image_url TEXT,
            image_data BLOB,
            is_deleted BOOLEAN DEFAULT 0,
            is_read BOOLEAN DEFAULT 0,
            compressed_content TEXT,
            keywords TEXT,
            ai_comment TEXT,
            ai_score REAL,
            ai_score_topic_relevance REAL,
            ai_score_importance REAL,
            ai_score_source REAL
        )
    ''')
    
    # 恢复数据
    cursor.execute('''
        INSERT INTO news (
            id, title, description, ai_summary, content, url, source, source_url,
            category, publish_time, fetch_time, is_visible, ai_processed,
            image_url, image_data, is_deleted, is_read,
            compressed_content, keywords, ai_comment, ai_score,
            ai_score_topic_relevance, ai_score_importance, ai_score_source
        )
        SELECT id, title, description, ai_summary, content, url, source, source_url,
               category, publish_time, fetch_time, is_visible, ai_processed,
               image_url, image_data, is_deleted, is_read,
               compressed_content, keywords, ai_comment, ai_score,
               ai_score_topic_relevance, ai_score_importance, ai_score_source
        FROM news_backup
    ''')
    
    # 删除备份表
    cursor.execute('DROP TABLE news_backup')
    
    logger.info("数据库迁移完成：已重建news表")
    # 重建表后，重新创建索引
    self._create_indexes()
    self._create_fts_table()
    # 重新获取列信息
    cursor.execute("PRAGMA table_info(news)")
    columns = [row[1] for row in cursor.fetchall()]
```

## 预防措施

### 1. 定期备份数据库

```bash
# 创建每日备份脚本
#!/bin/bash
BACKUP_DIR="data/backups"
mkdir -p $BACKUP_DIR
cp data/kwafoo.db $BACKUP_DIR/kwafoo_$(date +%Y%m%d_%H%M%S).db

# 保留最近7天的备份
find $BACKUP_DIR -name "kwafoo_*.db" -mtime +7 -delete
```

### 2. 监控数据库健康状态

```python
# 创建数据库健康检查脚本
#!/usr/bin/env python3
import sqlite3
import sys

def check_database_health():
    conn = sqlite3.connect('data/kwafoo.db')
    cursor = conn.cursor()
    
    issues = []
    
    # 检查NULL ID
    cursor.execute('SELECT COUNT(*) FROM news WHERE id IS NULL')
    null_id_count = cursor.fetchone()[0]
    if null_id_count > 0:
        issues.append(f"发现 {null_id_count} 条记录的ID为NULL")
    
    # 检查NULL is_deleted
    cursor.execute('SELECT COUNT(*) FROM news WHERE is_deleted IS NULL')
    null_deleted_count = cursor.fetchone()[0]
    if null_deleted_count > 0:
        issues.append(f"发现 {null_deleted_count} 条记录的is_deleted为NULL")
    
    # 检查NULL is_read
    cursor.execute('SELECT COUNT(*) FROM news WHERE is_read IS NULL')
    null_read_count = cursor.fetchone()[0]
    if null_read_count > 0:
        issues.append(f"发现 {null_read_count} 条记录的is_read为NULL")
    
    # 检查表结构
    cursor.execute('SELECT sql FROM sqlite_master WHERE type="table" AND name="news"')
    table_sql = cursor.fetchone()[0]
    if 'PRIMARY KEY AUTOINCREMENT' not in table_sql:
        issues.append("news表的ID字段缺少PRIMARY KEY AUTOINCREMENT属性")
    
    conn.close()
    
    if issues:
        print("❌ 数据库健康检查发现问题：")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 数据库健康检查通过")
        return True

if __name__ == '__main__':
    success = check_database_health()
    sys.exit(0 if success else 1)
```

### 3. 代码审查清单

在修改数据库相关代码时，请检查：

- [ ] INSERT语句包含所有必需字段
- [ ] UPDATE语句包含所有状态字段
- [ ] 表迁移代码使用正确的约束
- [ ] 避免使用 `CREATE TABLE ... AS SELECT` 重建表
- [ ] 添加适当的默认值
- [ ] 处理NULL值的情况
- [ ] 测试边界情况

## 故障排除

### 问题1：修复脚本执行失败

**错误信息：** `UNIQUE constraint failed: news.url`

**解决方案：**
```bash
# 检查重复URL
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT url, COUNT(*) FROM news GROUP BY url HAVING COUNT(*) > 1'); [print(f'重复URL: {row[0]}') for row in cursor.fetchall()]; conn.close()"

# 手动删除重复记录（保留ID最小的）
sqlite3 data/kwafoo.db
DELETE FROM news WHERE ROWID NOT IN (SELECT MIN(ROWID) FROM news GROUP BY url);
```

### 问题2：修复后数据丢失

**解决方案：**
```bash
# 恢复备份
cp data/kwafoo_backup.db data/kwafoo.db

# 重新运行修复脚本
python fix_database.py
```

### 问题3：服务器启动失败

**错误信息：** 数据库连接错误

**解决方案：**
```bash
# 检查数据库文件权限
ls -la data/kwafoo.db

# 检查数据库文件完整性
sqlite3 data/kwafoo.db "PRAGMA integrity_check;"

# 如果损坏，从备份恢复
cp data/kwafoo_backup.db data/kwafoo.db
```

## 联系支持

如果以上方法无法解决问题，请：

1. 收集错误日志
2. 备份数据库文件
3. 记录复现步骤
4. 联系技术支持团队

## 附录

### 常用SQL命令

```sql
-- 查看表结构
PRAGMA table_info(news);

-- 查看表创建语句
SELECT sql FROM sqlite_master WHERE type='table' AND name='news';

-- 统计记录数
SELECT COUNT(*) FROM news;

-- 查看字段分布
SELECT is_deleted, is_read, COUNT(*) FROM news GROUP BY is_deleted, is_read;

-- 检查重复记录
SELECT url, COUNT(*) FROM news GROUP BY url HAVING COUNT(*) > 1;

-- 查看最新记录
SELECT * FROM news ORDER BY fetch_time DESC LIMIT 10;
```

### 数据库文件位置

- **主数据库：** `data/kwafoo.db`
- **备份目录：** `data/backups/`
- **图片存储：** `data/images/`

### 相关文件

- **数据库管理器：** `database/manager.py`
- **修复脚本：** `fix_database.py`
- **健康检查：** `check_database_health.py`（需创建）
- **备份脚本：** `backup_database.sh`（需创建）