# AI处理模块设计

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

**为什么不用LangChain？**

LangChain虽然功能强大，但对于Kwafoo的需求来说：
- 过于复杂，引入不必要的抽象层
- 学习曲线陡，增加开发成本
- 依赖较多，增加项目体积
- 对于简单的LLM调用场景，OpenAI SDK已经足够

**结论：** Kwafoo使用OpenAI SDK直接调用本地模型，保持代码简洁高效。

## AI处理系统概述

### 核心功能

1. **智能分类**：自动识别新闻分类（支持深度思考功能）
2. **摘要生成**：生成新闻摘要（支持点评功能、翻译功能）
3. **批量处理**：支持批量处理未处理的新闻
4. **状态跟踪**：使用`ai_processed`字段跟踪处理状态
5. **队列管理**：支持AI处理队列和重新分析
6. **错误处理**：完善的错误处理和降级策略

### 处理流程

```
┌─────────────────────────────────────────────────────────┐
│  1. 定时抓取新闻                                        │
│     - 从RSS/API/网页源抓取                              │
│     - 存入数据库（ai_processed=0）                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  2. 定时检查未处理新闻                                  │
│     - 查询ai_processed=0的新闻                          │
│     - 如果没有，跳过处理                                │
│     - 如果有，启动AI处理                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  3. AI串行处理                                          │
│     - 分批获取未处理新闻（batch_size）                  │
│     - 单条串行处理（max_workers=1）                     │
│     - 每条新闻：                                        │
│       * AI分类（如果启用）                              │
│       * AI摘要（如果启用）                              │
│       * 更新ai_processed=1                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  4. 结果验证                                            │
│     - 检查是否还有未处理的新闻                          │
│     - 统计处理结果                                      │
│     - 记录处理日志                                      │
└─────────────────────────────────────────────────────────┘
```

## AI分类器

### AIClassifier类

**主要功能：**
- 根据新闻标题和描述进行智能分类
- 支持多分类（最多2个分类）
- 支持深度思考功能（reasoning_effort）
- 自动降级处理

**配置参数：**
```json
{
  "ai": {
    "enable_classifier_reasoning": false,
    "max_input_length": 800,
    "timeout": 120
  }
}
```

**深度思考功能：**

当启用`enable_classifier_reasoning`时，分类器会使用深度思考模式：
- 设置`reasoning_effort: "medium"`
- AI会进行更深入的推理
- 从`reasoning_content`中提取分类结果
- 提高分类准确性

**分类提示词：**

```
请根据以下新闻的标题和描述，判断它属于哪个分类。

可用分类：科技、财经、国际、体育、娱乐

标题：海底捞：控股股东张勇拟增持不少于1亿港元

描述：海底捞在港交所公告，公司控股股东张勇拟增持公司股份，增持金额不少于1亿港元。

要求：
1. 只返回分类名称，不要添加任何解释
2. 如果新闻涉及多个分类，请用逗号分隔，例如："科技,财经"
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

## AI摘要生成器

### AISummarizer类

**主要功能：**
- 生成新闻摘要
- 支持点评功能（comment_stance）
- 支持翻译功能
- 自动降级处理

**配置参数：**
```json
{
  "ai": {
    "enable_comment": false,
    "enable_translate": false,
    "comment_stance": {
      "nationality": "中国",
      "gender": "",
      "age": "",
      "family_status": "",
      "income": "",
      "health_status": "",
      "religion": "无",
      "custom_description": ""
    }
  }
}
```

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

**点评功能：**

当启用`enable_comment`时，摘要生成器会根据`comment_stance`配置生成个性化点评：
- 支持自定义人设（国籍、性别、年龄、家庭状况、收入、健康状况、宗教信仰）
- 支持自定义描述
- 在摘要后添加个性化点评

**翻译功能：**

当启用`enable_translate`时，摘要生成器会：
- 自动检测非中文内容
- 翻译为中文
- 生成中文摘要

**摘要提示词：**

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

## AI新闻处理器

### AINewsProcessor类

**主要功能：**
- 处理单条新闻
- 批量处理新闻
- 处理所有未处理的新闻
- 获取处理状态

**配置参数：**
```json
{
  "ai": {
    "max_workers": 1,
    "batch_size": 1,
    "enable_summary": true,
    "enable_classifier": true
  },
  "scheduler": {
    "ai_process_interval": 600
  }
}
```

**处理流程：**

1. 从数据库获取未处理的新闻（`ai_processed=0`）
2. 对每条新闻执行：
   - AI分类（如果启用）
   - AI摘要（如果启用）
   - 更新数据库
   - 更新处理状态（`ai_processed=1`）
3. 记录处理日志
4. 返回处理结果

**队列管理：**

- 支持AI处理队列
- 支持重新分析新闻
- 支持取消处理任务
- 实时进度更新

## 错误处理与降级

### AI分类失败处理

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

### 数据库事务处理

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

## 性能指标

### 处理效率
- **单条新闻处理时间**：约0.70秒（不含AI调用时间）
- **批量处理效率**：单线程串行处理，适合本地AI性能有限的情况
- **吞吐量**：约1.4条/秒（不含AI调用时间）

### 资源占用
- **内存占用**：约50MB（处理100条新闻）
- **CPU占用**：单线程处理，约20%
- **数据库连接**：单例模式，避免连接泄漏

## 代码引用

### AI分类器
[ai/classifier.py](../../ai/classifier.py) - AI分类器实现，支持深度思考功能

### AI摘要生成器
[ai/summarizer.py](../../ai/summarizer.py) - AI摘要生成器实现，支持点评和翻译功能

### AI新闻处理器
[ai/processor.py](../../ai/processor.py) - AI新闻处理器实现，支持队列处理和批量处理

## 配置说明

### AI基础配置
```toml
[ai]
base_url = "http://localhost:1234"
model = "nvidia/nemotron-3-nano-4b"
max_tokens = 4096
temperature = 0.7
max_input_length = 800
timeout = 120

# 深度思考功能
enable_classifier_reasoning = false

# 摘要功能
enable_summary = true

# 分类功能
enable_classifier = true

# 点评功能
enable_comment = false

# 翻译功能
enable_translate = false

# 点评人设
[ai.comment_stance]
nationality = "中国"
gender = ""
age = ""
family_status = ""
income = ""
health_status = ""
religion = "无"
custom_description = ""
```

### 调度配置
```toml
[scheduler]
ai_process_interval = 600  # AI处理间隔（秒）
```