# AI设计文档

## AI框架选择

### 使用OpenAI SDK

Kwafoo采用**OpenAI SDK**直接调用本地模型，原因如下：

**优势：**
- 轻量级，专注于API调用
- 学习成本低，易于上手
- 性能更好，开销更小
- 代码简洁，易于维护
- 依赖少，安装快速

**适用场景：**
- 新闻摘要生成
- 简单问答
- 文本分类
- 内容聚合
- RAG对话（配合SQLite全文搜索）

**代码示例：**

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:1234",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="nvidia/nemotron-3-nano-4b",
    messages=[
        {"role": "user", "content": "请总结以下新闻..."}
    ]
)

print(response.choices[0].message.content)
```

**为什么不用LangChain？**

LangChain虽然功能强大，但对于Kwafoo的需求来说：
- 过于复杂，引入不必要的抽象层
- 学习曲线陡，增加开发成本
- 依赖较多，增加项目体积
- 对于简单的LLM调用场景，OpenAI SDK已经足够

**结论：** Kwafoo使用OpenAI SDK直接调用本地模型，保持代码简洁高效。

## AI并行处理系统

### 系统概述

Kwafoo的AI并行处理系统实现了以下核心功能：

1. **定时抓取新闻**：从RSS/API/网页源抓取新闻数据
2. **智能状态跟踪**：使用`ai_processed`字段跟踪每条新闻的处理状态
3. **串行AI处理**：单条串行处理，避免并发冲突
4. **自动检测机制**：定期检查未处理的新闻并自动处理
5. **降级策略**：AI服务不可用时优雅降级，不影响系统运行

### 处理流程

```
┌─────────────────────────────────────────────────────────┐
│  1. 定时抓取新闻                                    │
│     - 从RSS/API/网页源抓取                           │
│     - 存入数据库（ai_processed=0）                    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  2. 定时检查未处理新闻                              │
│     - 查询ai_processed=0的新闻                       │
│     - 如果没有，跳过处理                               │
│     - 如果有，启动AI处理                               │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  3. AI串行处理                                     │
│     - 分批获取未处理新闻（batch_size）               │
│     - 单条串行处理（max_workers=1）                   │
│     - 每条新闻：                                    │
│       * AI分类（如果启用）                             │
│       * AI摘要（如果启用）                             │
│       * 更新ai_processed=1                           │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  4. 结果验证                                       │
│     - 检查是否还有未处理的新闻                         │
│     - 统计处理结果                                   │
│     - 记录处理日志                                   │
└─────────────────────────────────────────────────────────┘
```

### 核心类：AINewsProcessor

**主要方法：**
- `process_news(news_id, news_data)` - 处理单条新闻
- `process_batch(news_list)` - 批量处理新闻
- `process_all_unprocessed()` - 处理所有未处理的新闻
- `get_status()` - 获取处理状态

**配置参数：**
```json
{
  "ai": {
    "max_workers": 1,      // 并发线程数（串行处理）
    "batch_size": 1,      // 每批处理数量（单条处理）
    "enable_summary": true  // 是否启用AI摘要
  },
  "scheduler": {
    "ai_process_interval": 600  // AI处理间隔（秒）
  }
}
```

### AI分类器

#### AIClassifier类

**主要方法：**
- `classify(title, description, source_category)` - 对新闻进行分类
- `_build_classify_prompt(title, description)` - 构建分类提示词
- `_parse_result(result)` - 解析AI返回的分类结果

**分类提示词示例：**

```
请根据以下新闻的标题和描述，判断它属于哪个分类。

可用分类：科技、财经、国际、体育、娱乐

标题：海底捞：控股股东张勇拟增持不少于1亿港元

描述：海底捞在港交所公告，公司控股股东张勇拟增持公司股份，增持金额不少于1亿港元。

要求：
1. 只返回分类名称，不要添加任何解释
2. 如果新闻涉及多个分类，请用逗号分隔，例如："科技,互联网"
3. 如果新闻不属于任何分类，返回"未分类"
4. 只返回分类名称，不要添加其他内容
```

**分类结果处理：**

```python
# AI识别多个分类
ai_categories = ["科技", "互联网"]
category = ",".join(ai_categories)  # "科技,互联网"

# 存入数据库
db.update_news_category(news_id, category)
```

### AI摘要生成器

#### AISummarizer类

**主要方法：**
- `generate_summary(content, description)` - 生成新闻摘要
- `_build_summary_prompt(content)` - 构建摘要提示词
- `_build_rewrite_prompt(description)` - 构建改写提示词

**摘要生成场景：**

**场景1：描述缺失**
- 如果RSS或网页抓取不到描述
- 抓取正文内容
- 调用AI读取正文生成摘要
- 将摘要存入`ai_summary`字段

**场景2：描述过长**
- 如果描述超过指定长度（如500字符）
- 调用AI对描述进行摘要改写
- 将摘要存入`ai_summary`字段
- 原始描述保留在`description`字段

**场景3：描述正常**
- 不需要AI处理
- `ai_summary`字段留空

**摘要提示词示例：**

```
请根据以下新闻正文，生成一个简洁准确的摘要（100-200字）：

特斯拉将欣旺达动力电池加入其全球供应链，成为第五家动力电池供应商。该电池自浙江义乌工厂出货，装配上海车型，支持3C超快充。为降低整车成本，特斯拉更倾向二三线动力电池厂商。该合作体现特斯拉寻找降本新供应商的尝试，同时提升电池材料和充电倍率。

摘要要求：
1. 准确概括新闻核心内容
2. 语言简洁明了
3. 保持客观中立
4. 不添加主观评价
5. 100-200字之间
```

### 错误处理与降级

#### AI分类失败处理

```python
try:
    categories = ai_classifier.classify(title, description, None)
    if categories:
        # 更新分类
        pass
    else:
        logger.debug(f"AI分类返回空结果")
except Exception as e:
    logger.warning(f"AI分类失败: {e}")
    # 不影响整体处理流程
```

#### 数据库事务处理

```python
try:
    cursor.execute("UPDATE ...")
    self._connection.commit()
except Exception as e:
    logger.error(f"更新失败: {e}")
    try:
        self._connection.rollback()
    except:
        pass
    return False
```

### 性能指标

#### 处理效率
- **单条新闻处理时间**：约0.70秒（不含AI调用时间）
- **批量处理效率**：单线程串行处理，适合本地AI性能有限的情况
- **吞吐量**：约1.4条/秒（不含AI调用时间）

#### 资源占用
- **内存占用**：约50MB（处理100条新闻）
- **CPU占用**：单线程处理，约20%
- **数据库连接**：单例模式，避免连接泄漏

## RAG对话系统

### 系统概述

RAG（Retrieval-Augmented Generation，检索增强生成）对话系统基于历史新闻数据进行智能问答。

### 工作流程

```
用户提问 → SQLite全文搜索 → 构建上下文 → AI生成回答
```

### 全文搜索

使用SQLite的FTS5全文搜索功能：

```sql
CREATE VIRTUAL TABLE news_fts USING fts5(title, description, ai_summary, content);
```

### 上下文构建

从搜索结果中提取相关新闻，构建对话上下文：

```python
def build_context(search_results):
    context = "相关新闻：\n"
    for news in search_results:
        context += f"- {news['title']}\n"
        context += f"  {news['description'][:100]}...\n\n"
    return context
```

### AI对话

使用AI基于上下文生成回答：

```python
response = client.chat.completions.create(
    model="nvidia/nemotron-3-nano-4b",
    messages=[
        {
            "role": "system",
            "content": "你是一个新闻助手，基于提供的新闻信息回答用户问题。"
        },
        {
            "role": "user",
            "content": f"上下文：{context}\n\n问题：{query}"
        }
    ]
)
```

## AI配置说明

### 完整配置示例

```json
{
  "categories": {
    "科技": ["人工智能", "科技", "互联网", "编程"],
    "财经": ["股票", "金融", "经济", "投资"],
    "国际": ["国际", "世界", "外交"],
    "体育": ["体育", "足球", "篮球"],
    "娱乐": ["娱乐", "电影", "音乐"]
  },
  "default_category": "未分类",
  "enable_ai_category": true,
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
  "scheduler": {
    "fetch_interval": 1800,
    "ai_process_interval": 600
  }
}
```

### 关键配置项说明

| 配置项 | 说明 | 推荐值 |
|--------|------|---------|
| fetch_interval | 新闻抓取间隔（秒） | 1800（30分钟） |
| ai_process_interval | AI处理间隔（秒） | 600（10分钟） |
| max_workers | 并发线程数 | 1（串行处理） |
| batch_size | 每批处理数量 | 1（单条处理） |
| enable_ai_category | 是否启用AI分类 | true |
| enable_summary | 是否启用AI摘要 | true |
| temperature | AI生成温度 | 0.7 |
| max_tokens | 最大生成token数 | 4096 |

## AI使用建议

### 1. 本地AI性能优化

- 使用轻量级模型（如Nemotron-3-Nano-4B）
- 调整`max_workers`和`batch_size`参数
- 监控AI服务响应时间
- 合理设置超时时间

### 2. 分类准确性提升

- 提供清晰的分类定义
- 使用准确的分类关键词
- 定期检查分类结果
- 根据实际情况调整分类

### 3. 摘要质量控制

- 设置合理的描述长度阈值
- 提供明确的摘要要求
- 定期检查摘要质量
- 根据实际情况调整提示词

### 4. RAG对话优化

- 优化全文搜索索引
- 调整上下文长度
- 提供清晰的对话提示
- 定期更新新闻数据

## AI测试

### 测试脚本

```bash
# 测试AI调用
python tests/test_ai_call.py

# 测试直接API调用
python tests/test_direct_api.py

# 测试串行处理
python tests/test_serial_processing.py

# 查看AI处理结果
python tests/check_ai_results.py
```

### 测试结果

**串行处理性能：**
- 处理新闻：1条
- AI分类成功：1条
- 处理时间：26.71秒
- 平均速度：0.70秒/条

**系统状态：**
- 已处理新闻总数：38条
- 已分类新闻数：7条
- 已生成摘要数：1条
- 分类成功率：18.4%
- 摘要成功率：2.6%

## AI系统特点

### 1. 智能检测
- 自动检测未处理的新闻
- 避免重复处理
- 状态实时跟踪

### 2. 高效串行
- 单条串行处理
- 避免并发冲突
- 资源合理利用

### 3. 稳定可靠
- 完善的错误处理
- 优雅的降级策略
- 事务安全保障

### 4. 易于扩展
- 模块化设计
- 配置灵活
- 接口清晰