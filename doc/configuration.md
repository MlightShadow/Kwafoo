# 配置说明

## 概述

Kwafoo的配置文件为`config.json`，包含所有系统配置项。配置文件位于项目根目录。

## 完整配置示例

```json
{
  "database": {
    "path": "data/kwafoo.db"
  },
  "news_sources": {
    "rss": [
      {
        "url": "https://36kr.com/feed",
        "name": "36氪",
        "enabled": true,
        "fetch_days": 2
      }
    ],
    "api": [
      {
        "url": "https://api.example.com/news",
        "api_key": "your_api_key",
        "name": "Example API",
        "enabled": true,
        "fetch_days": 1
      }
    ],
    "web": [
      {
        "url": "https://example.com/news",
        "name": "Example Website",
        "enabled": true,
        "fetch_days": 1,
        "selectors": {
          "container": "div.news-list",
          "item": "div.news-item",
          "title": "h2.news-title",
          "content": "div.news-content",
          "link": "a.news-link",
          "time": "span.news-time"
        }
      }
    ]
  },
  "categories": {
    "科技": ["人工智能", "科技", "互联网", "编程"],
    "财经": ["股票", "金融", "经济", "投资"],
    "国际": ["国际", "世界", "外交"],
    "体育": ["体育", "足球", "篮球"],
    "娱乐": ["娱乐", "电影", "音乐"]
  },
  "default_category": "未分类",
  "enable_ai_category": true,
  "scheduler": {
    "fetch_interval": 1800,
    "ai_process_interval": 600
  },
  "ai": {
    "base_url": "http://localhost:1234",
    "model": "nvidia/nemotron-3-nano-4b",
    "api_key": "",
    "max_tokens": 4096,
    "temperature": 0.7,
    "max_workers": 1,
    "batch_size": 1,
    "enable_summary": true
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "enable_websocket": true
  },
  "json": {
    "output_path": "data/json/current.json",
    "snapshot_path": "data/json/snapshots/"
  },
  "rag": {
    "top_k": 5,
    "use_fts": true
  },
  "logging": {
    "level": "INFO",
    "file": "data/logs/kwafoo.log",
    "max_size": 10485760,
    "backup_count": 5
  }
}
```

## 配置项说明

### 数据库配置 (database)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| path | string | 数据库文件路径 | data/kwafoo.db |

**示例：**
```json
{
  "database": {
    "path": "data/kwafoo.db"
  }
}
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
```json
{
  "rss": [
    {
      "url": "https://36kr.com/feed",
      "name": "36氪",
      "enabled": true,
      "fetch_days": 2
    }
  ]
}
```

#### API接口 (api)

| 配置项 | 类型 | 说明 | 必填 |
|--------|------|------|------|
| url | string | API地址 | 是 |
| api_key | string | API密钥 | 否 |
| name | string | 源名称 | 是 |
| enabled | boolean | 是否启用 | 否 |
| fetch_days | integer | 抓取天数 | 否 |

**示例：**
```json
{
  "api": [
    {
      "url": "https://api.example.com/news",
      "api_key": "your_api_key",
      "name": "Example API",
      "enabled": true,
      "fetch_days": 1
    }
  ]
}
```

#### 网页爬虫 (web)

| 配置项 | 类型 | 说明 | 必填 |
|--------|------|------|------|
| url | string | 网页地址 | 是 |
| name | string | 源名称 | 是 |
| enabled | boolean | 是否启用 | 否 |
| fetch_days | integer | 抓取天数 | 否 |
| selectors | object | CSS选择器 | 是 |

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
```json
{
  "web": [
    {
      "url": "https://example.com/news",
      "name": "Example Website",
      "enabled": true,
      "fetch_days": 1,
      "selectors": {
        "container": "div.news-list",
        "item": "div.news-item",
        "title": "h2.news-title",
        "content": "div.news-content",
        "link": "a.news-link",
        "time": "span.news-time"
      }
    }
  ]
}
```

### 分类配置 (categories)

| 配置项 | 类型 | 说明 |
|--------|------|------|
| 分类名 | array | 分类关键词列表 |

**示例：**
```json
{
  "categories": {
    "科技": ["人工智能", "科技", "互联网", "编程"],
    "财经": ["股票", "金融", "经济", "投资"],
    "国际": ["国际", "世界", "外交"],
    "体育": ["体育", "足球", "篮球"],
    "娱乐": ["娱乐", "电影", "音乐"]
  }
}
```

### 默认分类 (default_category)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| default_category | string | 默认分类名称 | 未分类 |

**示例：**
```json
{
  "default_category": "未分类"
}
```

### AI分类开关 (enable_ai_category)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| enable_ai_category | boolean | 是否启用AI分类 | true |

**示例：**
```json
{
  "enable_ai_category": true
}
```

### 调度器配置 (scheduler)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| fetch_interval | integer | 新闻抓取间隔（秒） | 1800 |
| ai_process_interval | integer | AI处理间隔（秒） | 600 |

**示例：**
```json
{
  "scheduler": {
    "fetch_interval": 1800,
    "ai_process_interval": 600
  }
}
```

### AI配置 (ai)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| base_url | string | AI服务地址 | http://localhost:1234 |
| model | string | AI模型名称 | nvidia/nemotron-3-nano-4b |
| api_key | string | API密钥 | "" |
| max_tokens | integer | 最大生成token数 | 4096 |
| temperature | float | 生成温度 | 0.7 |
| max_workers | integer | 并发线程数 | 1 |
| batch_size | integer | 批处理大小 | 1 |
| enable_summary | boolean | 是否启用AI摘要 | true |

**示例：**
```json
{
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
}
```

### 服务器配置 (server)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| host | string | 服务器地址 | 0.0.0.0 |
| port | integer | 服务器端口 | 8000 |
| enable_websocket | boolean | 是否启用WebSocket | true |

**示例：**
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "enable_websocket": true
  }
}
```

### RAG配置 (rag)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| top_k | integer | 返回相关新闻数量 | 5 |
| use_fts | boolean | 是否使用全文搜索 | true |

**示例：**
```json
{
  "rag": {
    "top_k": 5,
    "use_fts": true
  }
}
```

### 日志配置 (logging)

| 配置项 | 类型 | 说明 | 默认值 |
|--------|------|------|---------|
| level | string | 日志级别 | INFO |
| file | string | 日志文件路径 | data/logs/kwafoo.log |
| max_size | integer | 日志文件最大大小（字节） | 10485760 |
| backup_count | integer | 日志备份数量 | 5 |

**示例：**
```json
{
  "logging": {
    "level": "INFO",
    "file": "data/logs/kwafoo.log",
    "max_size": 10485760,
    "backup_count": 5
  }
}
```

## 配置建议

### 开发环境

```json
{
  "scheduler": {
    "fetch_interval": 300,
    "ai_process_interval": 60
  },
  "ai": {
    "max_workers": 1,
    "batch_size": 1
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

### 生产环境

```json
{
  "scheduler": {
    "fetch_interval": 1800,
    "ai_process_interval": 600
  },
  "ai": {
    "max_workers": 1,
    "batch_size": 1
  },
  "logging": {
    "level": "INFO"
  }
}
```

### 低性能环境

```json
{
  "scheduler": {
    "fetch_interval": 3600,
    "ai_process_interval": 1200
  },
  "ai": {
    "max_workers": 1,
    "batch_size": 1,
    "enable_summary": false
  }
}
```

## 配置验证

启动系统时会自动验证配置文件的完整性，如果配置有误，系统会输出错误信息并退出。

## 配置热更新

支持通过Web管理界面在线修改配置，修改后自动生效，无需重启系统。

## 注意事项

1. **JSON格式**：确保配置文件是有效的JSON格式
2. **路径配置**：所有路径建议使用相对路径
3. **时间配置**：间隔时间单位为秒
4. **布尔值**：使用小写的true/false
5. **数值类型**：不要使用引号包裹数值
6. **字符串类型**：必须使用引号包裹字符串