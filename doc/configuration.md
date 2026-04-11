# 配置说明

## 概述

Kwafoo的配置文件为`config.toml`，包含所有系统配置项。配置文件位于项目根目录。

## 配置文件格式

本系统使用TOML格式配置文件，支持以下注释方式：
- 单行注释: `# 注释内容`

**注意**: TOML格式比JSON更简洁，支持注释，并且更易于阅读和编辑。

## 完整配置示例

```toml
[database]
path = "data/kwafoo.db"

[news_sources]

[[news_sources.rss]]
url = "https://36kr.com/feed"
name = "36氪"
enabled = true
fetch_days = 2

[[news_sources.api]]
url = "https://api.example.com/news"
api_key = "your_api_key"
name = "Example API"
category = "未分类"
enabled = true
fetch_days = 1

[[news_sources.web]]
url = "https://example.com/news"
name = "Example Website"
category = "未分类"
enabled = true
fetch_days = 1

[news_sources.web.selectors]
container = "div.news-list"
item = "div.news-item"
title = "h2.news-title"
content = "div.news-content"
link = "a.news-link"
time = "span.news-time"

[categories.tech]
name = "科技"
keywords = ["人工智能", "科技", "互联网", "编程"]
description = "涉及人工智能、科技产品、互联网、编程、软件、硬件等技术相关内容"
icon = "💻"
color = "#3498db"

[categories.finance]
name = "财经"
keywords = ["股票", "金融", "经济", "投资"]
description = "涉及股票、金融、经济、投资、企业财报等财经相关内容"
icon = "💰"
color = "#27ae60"

[categories.world]
name = "国际"
keywords = ["国际", "世界", "外交"]
description = "涉及国际新闻、世界大事、外交关系等国际相关内容"
icon = "🌍"
color = "#e74c3c"

[categories.sports]
name = "体育"
keywords = ["体育", "足球", "篮球"]
description = "涉及体育赛事、运动员、体育组织等体育相关内容"
icon = "⚽"
color = "#f39c12"

[categories.entertainment]
name = "娱乐"
keywords = ["娱乐", "电影", "音乐"]
description = "涉及电影、音乐、明星、娱乐活动等娱乐相关内容"
icon = "🎬"
color = "#9b59b6"

default_category = "未分类"
ai_summary_threshold = 140
enable_ai_category = true
enable_ai_summary = true

[scheduler]
fetch_interval = 1800
ai_process_interval = 600
auto_fetch = false
auto_ai_process = false
auto_ai_after_fetch = false

[network]
enable_proxy = false
proxy_url = ""

[image]
enable_fetch = true

[image.thumbnail_size]
width = 256
height = 256

default_image = ""
supported_formats = ["jpg", "jpeg", "png", "webp", "gif"]
max_image_size = 5242880

[ai]
base_url = "http://localhost:1234"
model = "nvidia/nemotron-3-nano-4b"
api_key = ""
max_tokens = 4096
temperature = 0.7
max_workers = 1
batch_size = 1
enable_summary = true

[server]
host = "0.0.0.0"
port = 8000
enable_websocket = true

[json]
output_path = "data/json/current.json"
snapshot_path = "data/json/snapshots/"

[rag]
top_k = 5
use_fts = true

[logging]
level = "INFO"
file = "data/logs/kwafoo.log"
max_size = 10485760
backup_count = 5
```

## 配置项说明

### 数据库配置 (database)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| path | string | 数据库文件路径 | data/kwafoo.db |

**示例：**
```toml
[database]
path = "data/kwafoo.db"
```

### 新闻源配置 (news_sources)

#### RSS订阅源 (rss)

| 配置项 | 类型 | 说明 | 必填 |
|--------|------|------|------|
| url | string | RSS订阅地址 | 是 |
| name | string | 源名称 | 是 |
| enabled | boolean | 是否启用 | 否 |
| fetch_days | integer | 抓取天数 | 否 |

**示例：**
```toml
[[news_sources.rss]]
url = "https://36kr.com/feed"
name = "36氪"
enabled = true
fetch_days = 2
```

#### API接口 (api)

| 配置项 | 类型 | 说明 | 必填 |
|--------|------|------|------|
| url | string | API地址 | 是 |
| api_key | string | API密钥 | 否 |
| name | string | 源名称 | 是 |
| category | string | 分类 | 否 |
| enabled | boolean | 是否启用 | 否 |
| fetch_days | integer | 抓取天数 | 否 |

**示例：**
```toml
[[news_sources.api]]
url = "https://api.example.com/news"
api_key = "your_api_key"
name = "Example API"
category = "未分类"
enabled = true
fetch_days = 1
```

#### 网页爬虫 (web)

| 配置项 | 类型 | 说明 | 必填 |
|--------|------|------|------|
| url | string | 网页地址 | 是 |
| name | string | 源名称 | 是 |
| category | string | 分类 | 否 |
| enabled | boolean | 是否启用 | 否 |
| fetch_days | integer | 抓取天数 | 否 |
| selectors | table | CSS选择器 | 是 |

**CSS选择器配置：**

| 选择器 | 说明 |
|--------|------|
| container | 新闻容器 |
| item | 新闻项 |
| title | 标题 |
| content | 内容 |
| link | 链接 |
| time | 时间 |

**示例：**
```toml
[[news_sources.web]]
url = "https://example.com/news"
name = "Example Website"
category = "未分类"
enabled = true
fetch_days = 1

[news_sources.web.selectors]
container = "div.news-list"
item = "div.news-item"
title = "h2.news-title"
content = "div.news-content"
link = "a.news-link"
time = "span.news-time"
```

### 分类配置 (categories)

**分类配置说明：**

系统使用英文键名作为分类标识，通过`name`字段显示中文名称。这种方式既保证了配置文件的规范性，又提供了良好的中文用户体验。

**配置格式：**

```toml
[categories.英文键名]
# 可选字段：
name = "显示名称"           # 分类显示名称（中文，用于界面显示）
keywords = ["关键词1", "关键词2"]  # 关键词列表（用于AI分类）
icon = "📰"                # 分类图标（默认📰）
color = "#95a5a6"           # 分类颜色（默认#95a5a6）
```

**预设分类示例：**

```toml
[categories.tech]
name = "科技"
keywords = ["人工智能", "科技", "互联网", "编程"]
icon = "💻"
color = "#3498db"

[categories.finance]
name = "财经"
keywords = ["股票", "金融", "经济", "投资"]
icon = "💰"
color = "#27ae60"

[categories.world]
name = "国际"
keywords = ["国际", "世界", "外交"]
icon = "🌍"
color = "#e74c3c"

[categories.sports]
name = "体育"
keywords = ["体育", "足球", "篮球"]
icon = "⚽"
color = "#f39c12"

[categories.entertainment]
name = "娱乐"
keywords = ["娱乐", "电影", "音乐"]
icon = "🎬"
color = "#9b59b6"
```

**自定义分类示例：**

```toml
[categories.automotive]
name = "汽车"
keywords = ["汽车", "新能源车", "电动车", "驾驶"]
icon = "🚗"
color = "#e67e22"

[categories.health]
name = "健康"
keywords = ["健康", "医疗", "养生", "疾病"]
icon = "🏥"
color = "#2ecc71"

[categories.education]
name = "教育"
keywords = ["教育", "学校", "考试", "学习"]
icon = "📚"
color = "#9b59b6"
```

**字段说明：**

| 配置项 | 类型 | 说明 | 必填 | 默认值 |
|--------|------|------|------|--------|
| name | string | 分类显示名称（中文） | 否 | 使用英文键名 |
| keywords | array | 分类关键词列表 | 否 | [] |
| description | string | 分类描述 | 否 | "" |
| icon | string | 分类图标 | 否 | 📰 |
| color | string | 分类颜色 | 否 | #95a5a6 |

**使用建议：**

1. **键名规范**：使用英文作为键名，避免编码和兼容性问题
2. **显示名称**：通过`name`字段设置中文显示名称
3. **关键词设置**：为每个分类设置3-5个相关关键词，提高AI分类准确度
4. **图标选择**：使用emoji作为图标，选择与分类相关的符号
5. **颜色搭配**：使用十六进制颜色代码，建议使用明亮的颜色
6. **灵活调整**：可以根据实际需求随时增减分类

**分类映射表：**

| 英文键名 | 中文名称 | 图标 | 颜色 |
|---------|---------|------|------|
| tech | 科技 | 💻 | #3498db |
| finance | 财经 | 💰 | #27ae60 |
| world | 国际 | 🌍 | #e74c3c |
| sports | 体育 | ⚽ | #f39c12 |
| entertainment | 娱乐 | 🎬 | #9b59b6 |

### 调度器配置 (scheduler)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| fetch_interval | integer | 抓取间隔(秒) | 1800 |
| ai_process_interval | integer | AI分析间隔(秒) | 600 |
| auto_fetch | boolean | 是否自动抓取 | false |
| auto_ai_process | boolean | 是否自动AI分析 | false |
| auto_ai_after_fetch | boolean | 抓取后是否自动AI分析 | false |

**示例：**
```toml
[scheduler]
fetch_interval = 1800
ai_process_interval = 600
auto_fetch = false
auto_ai_process = false
auto_ai_after_fetch = false
```

### 网络配置 (network)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| enable_proxy | boolean | 是否启用代理 | false |
| proxy_url | string | 代理地址 | "" |

**示例：**
```toml
[network]
enable_proxy = false
proxy_url = ""
```

### 图片配置 (image)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| enable_fetch | boolean | 是否启用图片抓取 | true |
| thumbnail_size | table | 缩略图尺寸 | {width=256, height=256} |
| default_image | string | 默认图片URL | "" |
| supported_formats | array | 支持的格式 | ["jpg", "jpeg", "png", "webp", "gif"] |
| max_image_size | integer | 最大图片大小(字节) | 5242880 |

**示例：**
```toml
[image]
enable_fetch = true

[image.thumbnail_size]
width = 256
height = 256

default_image = ""
supported_formats = ["jpg", "jpeg", "png", "webp", "gif"]
max_image_size = 5242880
```

### AI配置 (ai)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| base_url | string | AI服务地址 | http://localhost:1234 |
| model | string | 模型名称 | nvidia/nemotron-3-nano-4b |
| api_key | string | API密钥 | "" |
| max_tokens | integer | 最大token数 | 4096 |
| temperature | number | 温度参数 | 0.7 |
| max_workers | integer | 最大并发数 | 1 |
| batch_size | integer | 批处理大小 | 1 |
| enable_summary | boolean | 是否启用摘要 | true |

**示例：**
```toml
[ai]
base_url = "http://localhost:1234"
model = "nvidia/nemotron-3-nano-4b"
api_key = ""
max_tokens = 4096
temperature = 0.7
max_workers = 1
batch_size = 1
enable_summary = true
```

### 服务器配置 (server)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| host | string | 监听地址 | 0.0.0.0 |
| port | integer | 端口 | 8000 |
| enable_websocket | boolean | 是否启用WebSocket | true |

**示例：**
```toml
[server]
host = "0.0.0.0"
port = 8000
enable_websocket = true
```

### JSON配置 (json)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| output_path | string | 输出路径 | data/json/current.json |
| snapshot_path | string | 快照路径 | data/json/snapshots/ |

**示例：**
```toml
[json]
output_path = "data/json/current.json"
snapshot_path = "data/json/snapshots/"
```

### RAG配置 (rag)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| top_k | integer | 检索数量 | 5 |
| use_fts | boolean | 是否使用全文搜索 | true |

**示例：**
```toml
[rag]
top_k = 5
use_fts = true
```

### 日志配置 (logging)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| level | string | 日志级别 | INFO |
| file | string | 日志文件路径 | data/logs/kwafoo.log |
| max_size | integer | 最大文件大小(字节) | 10485760 |
| backup_count | integer | 备份数量 | 5 |

**示例：**
```toml
[logging]
level = "INFO"
file = "data/logs/kwafoo.log"
max_size = 10485760
backup_count = 5
```

## 配置建议

### 开发环境

```toml
[scheduler]
fetch_interval = 300
ai_process_interval = 60
auto_fetch = false
auto_ai_process = false

[ai]
max_workers = 1
batch_size = 1

[logging]
level = "DEBUG"
```

### 生产环境

```toml
[scheduler]
fetch_interval = 1800
ai_process_interval = 600
auto_fetch = true
auto_ai_process = true

[ai]
max_workers = 1
batch_size = 1

[logging]
level = "INFO"
```

### 低性能环境

```toml
[scheduler]
fetch_interval = 3600
ai_process_interval = 1200
auto_fetch = false
auto_ai_process = false

[ai]
max_workers = 1
batch_size = 1
enable_summary = false
```

## 配置验证

启动系统时会自动验证配置文件的完整性，如果配置有误，系统会输出错误信息并使用默认配置。

## 配置热更新

支持通过Web管理界面在线修改配置，修改后自动生效，无需重启系统。

## 注意事项

1. **TOML格式**：确保配置文件是有效的TOML格式
2. **路径配置**：所有路径建议使用相对路径
3. **时间配置**：间隔时间单位为秒
4. **布尔值**：使用小写的true/false
5. **数值类型**：不要使用引号包裹数值
6. **字符串类型**：必须使用引号包裹字符串
7. **数组配置**：使用`[[array_name]]`语法定义数组元素
8. **表格配置**：使用`[table_name]`或`[table_name.sub_table]`语法定义表格