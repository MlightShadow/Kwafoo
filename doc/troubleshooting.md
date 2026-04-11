# 问题解决指南

本文档记录 Kwafoo 项目开发过程中遇到的常见问题及解决方案。

---

## 构建问题

### npm包安装失败

**错误**：
```
Class extends value undefined is not a constructor or null
```

**原因**：`minipass-collect` 包存在语法错误或损坏

**解决**：

1. 定位问题包：
   ```
   web/frontend/node_modules/minipass-collect/index.js
   ```

2. 手动修复语法错误，确保有效JavaScript代码：
   ```javascript
   'use strict';
   var Minipass = require('minipass');
   
   function Collector() { }
   
   Collector.prototype = Object.create(Minipass.prototype);
   Collector.prototype.constructor = Collector;
   
   module.exports = Collector;
   ```

3. 或完全重装依赖：
   ```bash
   cd web/frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

**预防**：
- 定期更新npm和node版本
- 使用 `.gitignore` 排除 `node_modules`

---

### 前端构建失败

**检查项**：

1. Node.js版本是否兼容（建议 18+）
2. 是否已安装依赖：`npm install`
3. 检查 `package.json` 配置是否正确

**常用命令**：
```bash
# 开发模式
npm run dev

# 生产构建
npm run build
```

---

## 运行问题

### 端口被占用

**错误**：`Port 8000 is already in use`

**解决**：

1. 查找占用进程：
   ```bash
   # Windows
   netstat -ano | findstr 8000
   
   # 结束进程
   taskkill /PID <进程ID> /F
   ```

2. 或修改配置中的端口：
   ```toml
   [server]
   port = 8001
   ```

---

### 数据库错误

**常见问题**：

1. **数据库文件不存在**
   - 确保 `data/` 目录存在
   - 程序首次运行会自动创建

2. **数据库锁定**
   - 检查是否有其他进程访问数据库
   - 重启程序

3. **数据库损坏**
   - 删除 `data/kwafoo.db`
   - 重新启动程序会自动重建

---

### AI服务连接失败

**错误**：`Connection refused` 或 `AI service unavailable`

**检查项**：

1. AI服务是否启动（如Ollama、LM Studio）
2. 配置中的 `base_url` 是否正确：
   ```toml
   [ai]
   base_url = "http://localhost:1234"
   ```
3. 模型名称是否正确：
   ```toml
   [ai]
   model = "nvidia/nemotron-3-nano-4b"
   ```

**降级处理**：系统会在AI不可用时继续运行，只跳过AI处理步骤

---

## 配置问题

### 配置文件格式错误

**解决**：

1. 使用 `config.toml.example` 作为模板
2. 检查TOML语法（引号、括号匹配）
3. 验证工具：`python -c "import tomllib; tomllib.load(open('config.toml', 'rb'))"`

---

### 新闻源配置无效

**检查项**：

1. RSS源是否可用（浏览器测试）
2. API接口是否需要认证
3. 网页爬虫CSS选择器是否正确

---

## 性能问题

### 抓取速度慢

**优化建议**：

1. 减少 `fetch_days` 参数
2. 禁用不使用的新闻源
3. 增加抓取间隔

### AI处理慢

**优化建议**：

1. 使用更快的本地模型
2. 调整 `max_tokens` 减少输出
3. 降低 `temperature` 加快生成

---

## 其他问题

### 日志文件过大

**解决**：

```toml
[logging]
max_size = 10485760    # 10MB
backup_count = 5       # 保留5个备份
```

### WebSocket连接失败

**检查项**：

1. 端口8001是否开放
2. 防火墙是否阻止
3. 浏览器是否支持WebSocket

---

## 调试技巧

### 开启调试日志

```toml
[logging]
level = "DEBUG"
```

### 查看数据库

```bash
# 使用sqlite3
sqlite3 data/kwafoo.db

# 查看新闻表
SELECT * FROM news LIMIT 10;

# 查看未处理新闻
SELECT COUNT(*) FROM news WHERE ai_processed = 0;
```

### 测试API

```bash
# 健康检查
curl http://localhost:8000/api/health

# 新闻统计
curl http://localhost:8000/api/news/stats
```