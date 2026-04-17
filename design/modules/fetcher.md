# 新闻抓取模块设计

## 模块概述

新闻抓取模块负责从多种来源抓取新闻内容，包括RSS订阅源、API接口和网页抓取。模块采用统一的接口设计，支持灵活的配置和扩展。

## 抓取方式

### 1. RSS抓取器

**技术选型：**
- 使用`feedparser`库解析RSS/Atom feeds
- 使用`requests`库进行HTTP请求
- 支持代理配置

**核心功能：**
- 解析RSS/Atom feeds
- 提取新闻标题、描述、链接、发布时间
- 支持时间范围过滤（fetch_days）
- 自动处理图片URL
- 支持多种RSS格式

**配置示例：**
```toml
[[sources.rss]]
name = "36氪"
url = "https://36kr.com/feed"
category = "科技"
fetch_days = 7
```

**实现思路：**
1. 使用feedparser解析RSS feed
2. 遍历feed中的每个entry
3. 提取标题、描述、链接、发布时间等字段
4. 根据fetch_days过滤新闻
5. 返回标准化的新闻数据结构

**代码引用：**
[fetcher/rss_fetcher.py](../../fetcher/rss_fetcher.py) - RSS抓取器实现

### 2. API抓取器

**技术选型：**
- 使用`requests`库进行HTTP请求
- 支持API密钥认证
- 支持代理配置

**核心功能：**
- 调用RESTful API获取新闻
- 支持Bearer Token认证
- 提取新闻数据
- 支持时间范围过滤（fetch_days）
- 自动处理图片URL

**配置示例：**
```toml
[[sources.api]]
name = "新闻API"
url = "https://api.example.com/news"
api_key = "your-api-key"
category = "综合"
fetch_days = 7
```

**实现思路：**
1. 构建HTTP请求头（包含API密钥）
2. 发送GET请求到API端点
3. 解析返回的JSON数据
4. 提取新闻字段
5. 根据fetch_days过滤新闻
6. 返回标准化的新闻数据结构

**代码引用：**
[fetcher/api_fetcher.py](../../fetcher/api_fetcher.py) - API抓取器实现

### 3. 网页抓取器

**技术选型：**
- 使用`BeautifulSoup4`解析HTML
- 使用`requests`库进行HTTP请求
- 使用CSS选择器定位元素
- 支持代理配置

**核心功能：**
- 抓取网页内容
- 使用CSS选择器提取新闻元素
- 支持列表页和详情页抓取
- 支持时间范围过滤（fetch_days）
- 自动处理图片URL
- 支持多种网页结构

**配置示例：**
```toml
[[sources.web]]
name = "示例网站"
url = "https://example.com/news"
category = "科技"
fetch_days = 7

# 列表页配置
[list_page]
item_selector = ".news-item"
title_selector = ".title"
description_selector = ".description"
link_selector = "a"
time_selector = ".time"

# 详情页配置（可选）
[detail_page]
content_selector = ".content"
image_selector = ".main-image img"
```

**实现思路：**
1. 发送HTTP请求获取网页内容
2. 使用BeautifulSoup解析HTML
3. 使用CSS选择器定位新闻列表项
4. 提取每条新闻的标题、描述、链接、时间
5. 如果配置了详情页，抓取详情页内容
6. 根据fetch_days过滤新闻
7. 返回标准化的新闻数据结构

**CSS选择器说明：**
- `.news-item`：选择class为news-item的元素
- `.title`：选择class为title的元素
- `a`：选择所有a标签
- `#main`：选择id为main的元素
- `.content p`：选择content下的p标签

**代码引用：**
[fetcher/web_fetcher.py](../../fetcher/web_fetcher.py) - 网页抓取器实现

## 数据清洗

### 统一数据格式

所有抓取器返回统一的数据格式：

```python
{
    'title': '新闻标题',
    'description': '新闻描述',
    'url': '新闻链接',
    'source': '新闻来源',
    'publish_time': '发布时间',
    'category': '分类',
    'image_url': '图片URL（可选）'
}
```

### 数据验证

- 标题不能为空
- URL必须有效
- 发布时间格式统一为ISO 8601
- 描述长度限制（避免过长）

### 去重处理

- 基于URL去重
- 基于标题相似度去重（可选）

## 代理配置

所有抓取器支持统一的代理配置：

```toml
[network]
enable_proxy = false
proxy_url = "http://proxy.example.com:8080"
```

**代理模式：**
1. 不启用代理：跟随系统网络设置
2. 启用代理（自定义URL）：使用配置的代理
3. 启用代理（无URL）：使用系统环境变量中的代理

## 错误处理

### 网络错误
- 超时重试
- 代理失败降级
- 连接失败记录日志

### 解析错误
- RSS解析失败跳过该feed
- API返回错误记录日志
- HTML解析失败使用备用选择器

### 数据错误
- 缺失必填字段跳过该新闻
- 时间格式错误使用当前时间
- URL无效跳过该新闻

## 性能优化

### 并发控制
- 使用Session复用连接
- 合理设置超时时间
- 限制并发请求数

### 缓存策略
- RSS feed缓存（避免频繁请求）
- API响应缓存（根据Cache-Control）
- 网页内容缓存（可选）

### 增量抓取
- 基于publish_time过滤
- 基于fetch_days限制
- 避免重复抓取

## 正文抓取器

### 模块概述

正文抓取器负责从新闻链接对应的网页中提取完整正文内容，并进行压缩处理。模块支持三种提取算法，可根据网站特点选择最佳策略。

**技术选型：**
- 使用`requests`库进行HTTP请求
- 使用`BeautifulSoup4`解析HTML
- 使用`HybridCompressor`进行文本压缩
- 支持代理配置和缓存机制

**核心功能：**
- 从网页中提取正文内容
- 支持三种提取算法（文本密度法、DOM评分法、混合模式）
- 自动压缩正文到指定长度
- 支持缓存机制，避免重复抓取
- 完善的错误处理和降级策略

### 提取算法

#### 1. 文本密度法

**原理：**
- 基于文本统计特征计算每个节点的文本密度
- 过滤噪声节点（导航、侧边栏、页脚等）
- 选择文本密度最高的节点作为正文

**特征计算：**
- 文本长度：纯文本字符数
- 标签密度：子标签数量 / 文本长度
- 链接密度：链接数量 / 文本长度
- 标点密度：标点符号数 / 文本长度

**过滤规则：**
- 最小文本长度：200字符
- 最大标签密度：0.5
- 最大链接密度：0.4

**优势：**
- 无需先验知识
- 对未知网站鲁棒性强
- 计算相对简单

**劣势：**
- 可能误选非正文区域
- 对复杂结构效果一般

#### 2. DOM评分法

**原理：**
- 基于HTML标签语义和结构特征评分
- 使用预定义的标签权重表
- 综合多个维度计算得分

**评分维度：**
- 语义分：标签名、类名、ID匹配关键词库
- 文本量分：log(纯文本长度) × 标准化系数
- 结构分：兄弟节点中排名
- 密度分：1 - (链接数×10 / 文本长度)
- 连续分：子节点中`<p>`标签的连续出现次数
- 位置分：在页面垂直方向的居中程度

**标签权重示例：**
```python
tag_weights = {
    'article': 50,
    'main': 40,
    '[role="main"]': 35,
    'div.content': 30,
    'div.post': 25,
    'div.entry': 20,
    'div.sidebar': -40,
    'nav': -50,
    'footer': -60,
    'aside': -40
}
```

**优势：**
- 利用语义标签，准确性高
- 考虑页面结构
- 可针对特定站点优化

**劣势：**
- 需要维护规则库
- 对非语义化HTML效果差

#### 3. 混合模式

**原理：**
- 先用文本密度法快速筛选候选区域
- 验证结果质量（中文比例、文本长度等）
- 质量不达标时降级到DOM评分法

**验证规则：**
- 中文比例 > 30%
- 文本长度 >= 200字符
- 标点密度合理

**优势：**
- 兼顾速度和准确性
- 自适应选择最佳策略
- 降级机制保证可用性

**配置示例：**
```toml
[content_fetch]
# 是否启用正文抓取
enable_content_fetch = true
# 提取算法：density, dom, hybrid
algorithm = "hybrid"
# 最小正文长度（字符）
min_content_length = 200
# 最大正文长度（字符，超过则压缩）
max_content_length = 10000
# 超时时间（秒）
timeout = 30
# 是否使用代理
use_proxy = true
# 是否缓存已抓取的正文
enable_cache = true
```

### 数据流程

```
RSS URL → feedparser解析 → 提取条目信息
    ↓
检查是否启用正文抓取
    ↓
是 → content_fetcher.fetch_content(link)
    ↓
获取网页 → BeautifulSoup解析 → 正文提取 → 文本压缩
    ↓
更新news数据（content、compressed_content）
    ↓
插入数据库
    ↓
description就是摘要（AI将来处理）
```

### 摘要策略

**重要说明：**
- RSS的`description`字段本身就是摘要
- 不生成额外的summary字段
- AI将来处理：`ai_summary`字段

**摘要优先级：**
1. `description`（RSS描述）= 摘要
2. 如果`description`和`content`都不存在，寄希望于AI

### 错误处理

**网络错误：**
- 超时重试：最多3次
- 代理失败降级：禁用代理重试
- 连接失败：记录日志，返回空结果

**解析错误：**
- HTML解析失败：返回None
- 正文提取失败：降级到其他算法
- 图片提取失败：跳过该图片

**数据错误：**
- 正文长度不足：使用RSS description
- 编码错误：自动检测编码，尝试修复

**降级策略：**
- 正文抓取失败不影响RSS抓取流程
- 失败时`content`和`compressed_content`为None
- `description`始终存在（RSS提供），就是摘要

### 性能优化

**并发控制：**
- 使用Session复用连接
- 合理设置超时时间
- 限制并发请求数

**缓存机制：**
- 相同URL不重复抓取
- 内存缓存（可配置）
- 缓存有效期：整个会话期间

**超时控制：**
- 单个页面抓取超时：30秒
- 避免阻塞RSS抓取流程
- 失败后快速降级

### 代码引用

[fetcher/content_fetcher.py](../../fetcher/content_fetcher.py) - 正文抓取器实现

## 未来功能

### 文本压缩
虽然当前版本未在抓取模块中使用，但系统支持多种文本压缩算法：
- 默认压缩器（融合基础和高级算法）
- TextRank压缩器（基于textrank4zh）
- 混合压缩器（智能选择最佳算法）
- 支持多种压缩级别和模式

## 配置说明

### RSS源配置
```toml
[[sources.rss]]
name = "36氪"
url = "https://36kr.com/feed"
category = "科技"
fetch_days = 7
```

### API源配置
```toml
[[sources.api]]
name = "新闻API"
url = "https://api.example.com/news"
api_key = "your-api-key"
category = "综合"
fetch_days = 7
```

### 网页源配置
```toml
[[sources.web]]
name = "示例网站"
url = "https://example.com/news"
category = "科技"
fetch_days = 7

[list_page]
item_selector = ".news-item"
title_selector = ".title"
description_selector = ".description"
link_selector = "a"
time_selector = ".time"
```

### 网络配置
```toml
[network]
enable_proxy = false
proxy_url = "http://proxy.example.com:8080"
timeout = 30
```

## 代码引用

### RSS抓取器
[fetcher/rss_fetcher.py](../../fetcher/rss_fetcher.py) - RSS抓取器实现

### API抓取器
[fetcher/api_fetcher.py](../../fetcher/api_fetcher.py) - API抓取器实现

### 网页抓取器
[fetcher/web_fetcher.py](../../fetcher/web_fetcher.py) - 网页抓取器实现

## 依赖库

- `feedparser` - RSS/Atom feed解析
- `requests` - HTTP请求
- `beautifulsoup4` - HTML解析
- `lxml` - XML/HTML解析（BeautifulSoup的解析器）

## 注意事项

1. **遵守robots.txt**：抓取网页前检查robots.txt
2. **设置合理的User-Agent**：避免被网站屏蔽
3. **控制请求频率**：避免对目标网站造成压力
4. **处理编码问题**：正确处理各种字符编码
5. **错误日志记录**：记录所有错误便于调试
6. **数据验证**：验证抓取的数据质量
7. **异常处理**：完善的异常处理机制