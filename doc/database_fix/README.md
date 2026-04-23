# 数据库修复文档

本目录包含Kwafoo新闻聚合系统数据库问题的诊断和修复指南。

## 📚 文档列表

### 1. database_fix_guide.md
**详细的数据库修复指南**

包含内容：
- 问题诊断方法和步骤
- 详细的修复说明
- 代码修复示例
- 预防措施建议
- 故障排除指南
- 常用SQL命令参考

**适用人群：** 需要深入了解问题原因和详细修复步骤的用户

### 2. database_fix_quickref.md
**快速参考卡**

包含内容：
- 紧急问题诊断命令
- 快速修复步骤
- 代码修复位置索引
- 验证检查清单
- 常见错误处理

**适用人群：** 需要快速解决问题的用户

## 🚀 快速开始

### 遇到问题？

1. **新闻不显示？**
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE DATE(fetch_time) = DATE(\"now\") AND is_visible = 1 AND is_deleted = 0'); print('今日新闻:', cursor.fetchone()[0]); conn.close()"
   ```

2. **reanalyze功能失败？**
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/kwafoo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM news WHERE id IS NULL'); print('NULL ID:', cursor.fetchone()[0]); conn.close()"
   ```

3. **需要修复？**
   ```bash
   # 标准修复流程
   cp data/kwafoo.db data/kwafoo_backup.db
   python fix_database.py
   python main.py
   ```

## 📖 使用建议

### 新手用户
1. 先阅读 `database_fix_quickref.md`
2. 按照快速参考卡中的步骤操作
3. 遇到问题时查看详细指南

### 高级用户
1. 直接查看 `database_fix_guide.md`
2. 根据问题类型选择相应章节
3. 参考代码修复示例

### 系统管理员
1. 建立定期备份机制
2. 实施健康检查脚本
3. 制定应急响应流程

## 🔧 相关工具

### 修复脚本
- **fix_database.py** - 自动修复脚本（项目根目录）

### 数据库工具
- **SQLite命令行工具** - 直接操作数据库
- **Python sqlite3模块** - 编程方式访问数据库

### 监控工具
- **健康检查脚本** - 监控数据库状态（需创建）
- **备份脚本** - 自动备份数据库（需创建）

## 📞 获取帮助

### 自助解决
1. 查看快速参考卡
2. 阅读详细指南
3. 检查相关代码文件

### 联系支持
如果自助解决无法解决问题：
1. 收集错误日志
2. 备份数据库文件
3. 记录复现步骤
4. 联系技术支持团队

## ⚠️ 重要提醒

### 修复前
- ✅ 务必备份数据库
- ✅ 停止运行中的服务器
- ✅ 记录当前问题状态

### 修复中
- ✅ 按步骤执行修复
- ✅ 验证每一步结果
- ✅ 记录修复过程

### 修复后
- ✅ 验证所有功能正常
- ✅ 检查数据完整性
- ✅ 更新相关文档

## 🔄 更新历史

### 2026-04-23
- 创建数据库修复指南文档
- 添加快速参考卡
- 记录常见问题和解决方案

## 📝 贡献指南

如果您发现文档中的问题或有改进建议：

1. 记录问题和建议
2. 提供改进方案
3. 更新相关文档
4. 分享给团队成员

## 🔗 相关资源

### 项目文档
- [项目README](../../README.md)
- [API文档](../api.md)
- [数据库设计](../database.md)

### 外部资源
- [SQLite官方文档](https://www.sqlite.org/docs.html)
- [Python sqlite3模块](https://docs.python.org/3/library/sqlite3.html)

---

**最后更新：** 2026-04-23  
**维护者：** Kwafoo开发团队  
**版本：** 1.0.0