# 数据库修复快速参考卡

## 🚨 紧急问题诊断

### 问题1：新闻不显示
```bash
# 快速诊断
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE DATE(fetch_time) = DATE(\"now\") AND is_visible = 1 AND is_deleted = 0'); print('今日新闻:', cursor.fetchone()[0]); cursor.execute('SELECT is_deleted, is_read, COUNT(*) FROM news WHERE DATE(fetch_time) = DATE(\"now\") GROUP BY is_deleted, is_read'); print('状态:'); [print(f'  {row}') for row in cursor.fetchall()]; conn.close()"
```

### 问题2：reanalyze失败
```bash
# 检查ID字段
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE id IS NULL'); print('NULL ID:', cursor.fetchone()[0]); cursor.execute('SELECT id, title FROM news WHERE DATE(fetch_time) = DATE(\"now\") LIMIT 3'); print('今日新闻ID:'); [print(f'  ID={row[0]}') for row in cursor.fetchall()]; conn.close()"
```

### 问题3：表结构损坏
```bash
# 检查表结构
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT sql FROM sqlite_master WHERE type=\"table\" AND name=\"news\"'); print(cursor.fetchone()[0]); conn.close()"
```

## ⚡ 快速修复步骤

### 标准修复流程（推荐）
```bash
# 1. 停止服务器
# Ctrl+C 或发送停止信号

# 2. 备份数据库
cp data/kwafoo.db data/kwafoo_backup_$(date +%Y%m%d_%H%M%S).db

# 3. 运行修复脚本
python fix_database.py

# 4. 验证修复
python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE is_visible = 1 AND is_deleted = 0'); print('可用新闻:', cursor.fetchone()[0]); cursor.execute('SELECT COUNT(*) FROM news WHERE id IS NULL'); print('NULL ID:', cursor.fetchone()[0]); conn.close()"

# 5. 重启服务器
python main.py
```

### 紧急修复（仅NULL值问题）
```bash
# 连接数据库
sqlite3 data/kwafoo.db

# 修复NULL值
UPDATE news SET is_deleted = 0 WHERE is_deleted IS NULL;
UPDATE news SET is_read = 0 WHERE is_read IS NULL;

# 验证修复
SELECT is_deleted, is_read, COUNT(*) FROM news GROUP BY is_deleted, is_read;

# 退出
.quit
```

## 🔧 代码修复位置

### 1. INSERT语句修复
**文件：** `database/manager.py`  
**方法：** `insert_news`  
**行号：** ~402行  
**修复：** 添加 `is_deleted` 和 `is_read` 字段

### 2. UPDATE语句修复
**文件：** `database/manager.py`  
**方法：** `insert_news` (恢复已删除新闻部分)  
**行号：** ~454行  
**修复：** 添加 `is_read` 字段

### 3. 迁移代码修复
**文件：** `database/manager.py`  
**方法：** `_migrate_database`  
**行号：** ~285行  
**修复：** 使用正确的表重建逻辑

## 📊 验证检查清单

修复后请确认：
- [ ] 今日新闻数 > 0
- [ ] 可用新闻数 > 0
- [ ] NULL ID数量 = 0
- [ ] 表结构包含 `PRIMARY KEY AUTOINCREMENT`
- [ ] 服务器启动无错误
- [ ] 页面能正常显示新闻
- [ ] reanalyze功能正常工作

## 🆘 常见错误处理

### 错误：UNIQUE constraint failed: news.url
```bash
# 删除重复URL
sqlite3 data/kwafoo.db
DELETE FROM news WHERE ROWID NOT IN (SELECT MIN(ROWID) FROM news GROUP BY url);
.quit
```

### 错误：修复脚本执行失败
```bash
# 恢复备份
cp data/kwafoo_backup.db data/kwafoo.db

# 重新运行
python fix_database.py
```

### 错误：服务器启动失败
```bash
# 检查数据库完整性
sqlite3 data/kwafoo.db "PRAGMA integrity_check;"

# 如果损坏，从备份恢复
cp data/kwafoo_backup.db data/kwafoo.db
```

## 📞 获取帮助

1. 查看详细指南：`doc/database_fix_guide.md`
2. 检查日志文件：`logs/`
3. 备份数据库：`data/kwafoo_backup.db`
4. 联系技术支持

## 📝 重要提醒

- ⚠️ 修复前务必备份数据库
- ⚠️ 停止服务器后再进行修复
- ⚠️ 修复后验证所有功能
- ⚠️ 定期备份数据库文件
- ⚠️ 监控数据库健康状态

## 🔗 相关文件

- **详细指南：** `doc/database_fix_guide.md`
- **修复脚本：** `fix_database.py`
- **数据库文件：** `data/kwafoo.db`
- **日志文件：** `logs/kwafoo.log`