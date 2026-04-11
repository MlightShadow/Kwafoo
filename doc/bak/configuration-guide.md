# 配置文件说明

## 配置文件位置

- **配置文件**: `config.toml`
- **配置模板**: `config.toml.example`

## 配置文件格式

本系统使用带注释的JSON格式配置文件，支持以下注释方式：
- 单行注释: `// 注释内容`
- 多行注释: `/* 注释内容 */`

**注意**: 配置文件使用`jsoncomment`库进行解析，支持标准的JSON注释语法。

## 配置项详解

### 1. 数据库配置 (database)

```json
"database": {
  "path": "data/kwafoo.db"
}
```

- **path**: SQLite数据库文件路径
  - 默认值: `data/kwafoo.db`
  - 说明: 系统会自动创建数据库文件和目录

### 2. 新闻源配置 (news_sources)

系统支持三种新闻源类型：RSS、API、网页爬虫

#### 2.1 RSS订阅源 (rss)

```json
"rss": [
  {
    "url": "https://36kr.com/feed",
    "name": "36氪",
    "enabled": true,
    "fetch_days": 2
  }
]
```

- **url**: RSS订阅地址（必需）
- **name**: 新闻源名称（必需）
- **enabled**: 是否启用该新闻源（可选，默认true）
- **fetch_days**: 抓取最近几天的新闻（可选，默认2）

#### 2.2 API接口源 (api)

```json
"api": [
  {
    "url": "https://api.example.com/news",
    "api_key": "your_api_key",
    "name": "Example API",
    "category": "未分类",
    "enabled": true
  }
]
```

- **url**: API接口地址（必需）
- **api_key**: API密钥（可选）
- **name**: 新闻源名称（必需）
- **category**: 新闻分类（可选，默认"未分类"）
- **enabled**: 是否启用该新闻源（可选，默认true）

#### 2.3 网页爬虫源 (web)

```json
"web": [
  {
    "url": "https://example.com/news",
    "name": "Example Website",
    "category": "未分类",
    "enabled": true,
    "selectors": {
      "container": "div.news-list",
      "title": "h2.news-title",
      "content": "div.news-content",
      "link": "a.news-link",
      "time": "span.news-time"
    }
  }
]
```

- **url**: 网页地址（必需）
- **name**: 新闻源名称（必需）
- **category**: 新闻分类（可选，默认"未分类"）
- **enabled**: 是否启用该新闻源（可选，默认true）
- **selectors**: CSS选择器配置（必需）
  - **container**: 新闻列表容器选择器
  - **title**: 标题选择器
  - **content**: 内容选择器
  - **link**: 链接选择器
  - **time**: 时间选择器

### 3. 分类配置 (categories)

```json
"categories": {
  "科技": ["人工智能", "科技", "互联网", "编程"],
  "财经": ["股票", "金融", "经济", "投资"],
  "国际": ["国际", "世界", "外交"],
  "体育": ["体育", "足球", "篮球"],
  "娱乐": ["娱乐", "电影", "音乐"]
}
```

- **说明**: 定义分类和关键词的映射关系
- **用途**: AI根据新闻标题和内容中的关键词自动分类
- **格式**: 键为分类名称，值为关键词数组

### 4. 默认分类 (default_category)

```json
"default_category": "未分类"
```

- **说明**: 当AI无法识别分类时使用的默认分类
- **默认值**: "未分类"

### 5. AI分类开关 (enable_ai_category)

```json
"enable_ai_category": true
```

- **说明**: 是否启用AI自动分类功能
- **默认值**: true
- **注意**: 需要AI服务正常运行

### 6. 调度器配置 (scheduler) ⭐ 重要

```json
"scheduler": {
  "fetch_interval": 1800,
  "ai_process_interval": 600,
  "auto_fetch": false,
  "auto_ai_process": false
}
```

#### 6.1 抓取间隔 (fetch_interval)

- **说明**: 自动抓取新闻的时间间隔（秒）
- **默认值**: 1800（30分钟）
- **注意**: 只有在`auto_fetch`为true时生效

#### 6.2 AI分析间隔 (ai_process_interval)

- **说明**: 自动AI分析新闻的时间间隔（秒）
- **默认值**: 600（10分钟）
- **注意**: 只有在`auto_ai_process`为true时生效

#### 6.3 自动抓取开关 (auto_fetch) ⭐

- **说明**: 是否启用自动抓取新闻功能
- **默认值**: false（关闭）
- **推荐**: 测试阶段建议关闭，通过管理界面手动触发
- **使用**:
  - `true`: 系统按`fetch_interval`间隔自动抓取新闻
  - `false`: 不自动抓取，需要手动在管理界面点击"手动抓取新闻"按钮

#### 6.4 自动AI分析开关 (auto_ai_process) ⭐

- **说明**: 是否启用自动AI分析新闻功能
- **默认值**: false（关闭）
- **推荐**: 测试阶段建议关闭，通过管理界面手动触发
- **使用**:
  - `true`: 系统按`ai_process_interval`间隔自动分析新闻
  - `false`: 不自动分析，需要手动在管理界面点击"AI分析新闻"按钮

### 7. AI配置 (ai)

```json
"ai": {
  "base_url": "http://localhost:1234",
  "model": "nvidia/nemotron-3-nano-4b",
  "api_key": "",
  "max_tokens": 4096,
  "temperature": 0.7,
  "max_workers": 1,
  "batch_size": 1,
  "enable_summary": true
}
```

- **base_url**: AI服务地址（必需）
- **model**: 使用的模型名称（必需）
- **api_key**: API密钥（可选）
- **max_tokens**: 最大生成token数（默认4096）
- **temperature**: 温度参数，控制随机性（0-1，默认0.7）
- **max_workers**: 最大并发工作线程数（默认1）
- **batch_size**: 批处理大小（默认1）
- **enable_summary**: 是否启用摘要生成（默认true）

### 8. 服务器配置 (server)

```json
"server": {
  "host": "0.0.0.0",
  "port": 8000,
  "enable_websocket": true
}
```

- **host**: 服务器监听地址（默认0.0.0.0，表示所有接口）
- **port**: 服务器端口（默认8000）
- **enable_websocket**: 是否启用WebSocket（默认true）

### 9. JSON配置 (json)

```json
"json": {
  "output_path": "data/json/current.json",
  "snapshot_path": "data/json/snapshots/"
}
```

- **output_path**: 当前JSON输出路径
- **snapshot_path**: 快照JSON存储路径

### 10. RAG配置 (rag)

```json
"rag": {
  "top_k": 5,
  "use_fts": true
}
```

- **top_k**: 检索返回的相关新闻数量（默认5）
- **use_fts**: 是否使用全文搜索（默认true）

### 11. 日志配置 (logging)

```json
"logging": {
  "level": "INFO",
  "file": "data/logs/kwafoo.log",
  "max_size": 10485760,
  "backup_count": 5
}
```

- **level**: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- **file**: 日志文件路径
- **max_size**: 单个日志文件最大大小（字节，默认100MB）
- **backup_count**: 保留的日志文件数量（默认5）

## 测试建议配置

### 测试阶段推荐配置

```json
{
  "scheduler": {
    "fetch_interval": 1800,
    "ai_process_interval": 600,
    "auto_fetch": false,        // 关闭自动抓取
    "auto_ai_process": false     // 关闭自动AI分析
  }
}
```

### 生产环境推荐配置

```json
{
  "scheduler": {
    "fetch_interval": 1800,      // 每30分钟抓取一次
    "ai_process_interval": 600,   // 每10分钟分析一次
    "auto_fetch": true,          // 启用自动抓取
    "auto_ai_process": true       // 启用自动AI分析
  }
}
```

## 使用说明

### 1. 手动抓取新闻

1. 打开管理界面
2. 点击"🔄 手动抓取新闻"按钮
3. 等待抓取完成
4. 查看新闻列表更新

### 2. 手动AI分析

1. 打开管理界面
2. 点击"🤖 AI分析新闻"按钮
3. 等待AI分析完成
4. 查看新闻摘要和分类更新

### 3. 查看系统状态

- 顶部导航栏右侧显示系统运行状态
- 系统监控页面查看详细任务进度
- 日志文件查看详细运行信息

## 常见问题

### 1. 如何启用自动功能？

修改`config.toml`中的以下配置：
```toml
[scheduler]
auto_fetch = true        # 启用自动抓取
auto_ai_process = true     # 启用自动AI分析
```

### 2. 如何调整抓取频率？

修改`fetch_interval`和`ai_process_interval`的值（单位：秒）：
```toml
[scheduler]
fetch_interval = 3600      # 每1小时抓取一次
ai_process_interval = 1800   # 每30分钟分析一次
```

### 3. 为什么新闻没有AI摘要？

检查以下几点：
1. `auto_ai_process`是否为true
2. AI服务是否正常运行
3. `enable_summary`是否为true
4. 是否手动触发了AI分析

### 4. 如何查看配置是否生效？

查看日志文件`data/logs/kwafoo.log`，搜索以下关键词：
- "自动抓取已启用" / "自动抓取已禁用"
- "自动AI分析已启用" / "自动AI分析已禁用"

## 注意事项

1. **配置修改后需要重启系统才能生效**
2. **测试阶段建议关闭自动功能，手动触发更方便调试**
3. **AI分析需要AI服务正常运行**
4. **新闻源URL需要可访问**
5. **数据库文件需要有写权限**