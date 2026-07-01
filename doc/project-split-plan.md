# Kwafoo 项目拆分方案（修订版 v2）

> 文档创建时间：2026-05-30
> 修订时间：2026-05-30
> 当前项目状态：单体项目，所有模块耦合在一个代码仓库中

---

## 一、项目现状分析

### 1.1 当前项目结构

```
kwafoo/
├── main.py                    # 统一入口：依次启动数据库、调度器、HTTP服务器、WebSocket
├── config.toml                # 全局配置文件（所有模块共用）
├── requirements.txt           # 全局依赖
│
├── ai/                        # AI处理模块（与模型交互的核心层）
│   ├── ai_client.py           # 统一AI调用接口（基于LiteLLM，含重试/验证）
│   ├── classifier.py          # AI分类器
│   ├── summarizer.py          # AI摘要生成器
│   ├── scorer.py              # AI评分器（多维度评分）
│   ├── processor.py           # AI新闻处理器（编排分类→摘要→评分流程）
│   ├── report_generator.py    # AI报告生成器（日报/周报/月报）
│   ├── response_validator.py  # 响应验证器
│   └── retry_strategy.py      # 重试策略
│
├── database/                  # 数据库模块
│   └── manager.py             # SQLite数据库管理器（单例，含表创建/迁移/CRUD）
│
├── fetcher/                   # 新闻抓取模块
│   ├── rss_fetcher.py         # RSS抓取器
│   ├── api_fetcher.py         # API抓取器
│   ├── web_fetcher.py         # 网页抓取器
│   └── content_fetcher.py     # 正文内容提取器
│
├── rag/                       # RAG对话模块
│   └── engine.py              # RAG引擎（搜索/上下文构建）
│
├── scheduler/                 # 调度模块
│   └── scheduler.py           # 任务调度器（定时抓取/AI处理队列）
│
├── utils/                     # 工具模块
│   ├── helpers.py             # 配置管理
│   ├── logger.py              # 日志管理
│   ├── image_processor.py     # 图片处理器
│   ├── default_compressor.py  # 默认文本压缩器
│   ├── textrank_compressor.py # TextRank压缩器
│   ├── hybrid_compressor.py   # 混合压缩器
│   ├── progress.py            # 进度监控
│   ├── config_validator.py    # 配置验证器
│   ├── validators.py          # 通用验证器
│   ├── error_handler.py       # 错误处理
│   ├── exceptions.py          # 自定义异常
│   └── constants.py           # 常量定义
│
├── web/                       # Web模块
│   ├── server.py              # HTTP服务器（基于Python http.server）
│   ├── websocket.py           # WebSocket服务器
│   ├── api/                   # REST API接口
│   │   ├── news_api.py
│   │   ├── ai_api.py
│   │   ├── chat_api.py
│   │   ├── config_api.py
│   │   ├── system_api.py
│   │   └── report_api.py
│   └── frontend/              # Vue 3前端
│       ├── src/
│       ├── package.json
│       ├── vite.config.ts
│       └── ...
│
├── tests/                     # 测试文件
├── design/                    # 设计文档
├── doc/                       # 详细文档
├── hooks/                     # PyInstaller打包钩子
└── data/                      # 运行时数据目录
```

### 1.2 当前核心问题

1. **AI模块承担了过多职责**：AI模块（`ai/`）不仅负责模型交互，还包含业务编排逻辑（`processor.py`），违反了单一职责原则
2. **调度器直接调用AI**：`scheduler/scheduler.py` 直接导入并调用 `ai/classifier.py`、`ai/summarizer.py`、`ai/scorer.py`，耦合过紧
3. **爬虫与业务逻辑耦合**：`fetcher/` 模块与调度器、数据库紧密耦合，无法独立运行
4. **AI功能扩展需要修改代码**：增加新的AI调用方式需要在 `ai_client.py`、`response_validator.py`、`retry_strategy.py` 等多个文件中添加处理逻辑
5. **API直接触发AI处理**：`web/api/ai_api.py` 直接调用AI处理器，跳过中间协调层
6. **前端直接依赖后端**：前端构建产物混在后端项目中，无法独立部署
7. **全局配置文件混杂**：`config.toml` 包含所有模块配置，没有分层

---

## 二、拆分目标

将当前单体项目拆分为 **五个** 独立子项目，各司其职：

```
┌──────────────────────────────────────────────────────────────────┐
│                     kwafoo-frontend                              │
│                   纯前端展示层                                     │
│             Vue 3 + TypeScript + Vite                            │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP REST API (只读已处理数据)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                      kwafoo-api                                  │
│                   前后端交互层                                     │
│     FastAPI + WebSocket + RAG引擎                                │
│     只负责数据查询与展示，不直接调用AI                             │
└──────────────────────────┬───────────────────────────────────────┘
                           │ 提交异步任务
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                 kwafoo-data-processor                            │
│                   数据处理核心层                                   │
│     异步任务队列 + 定时任务调度 + 数据加工编排                     │
│     协调爬虫数据 → AI处理 → 结果落库                               │
└────────────┬──────────────────────────────────┬──────────────────┘
             │ 获取原始数据                      │ 调用AI处理
             ▼                                  ▼
┌─────────────────────────┐    ┌────────────────────────────────────┐
│    kwafoo-crawler       │    │         kwafoo-ai                  │
│      爬虫层              │    │      AI模型交互层                   │
│  数据抓取 + 存储          │    │  统一接口 + 配置文件驱动            │
│  RSS/API/Web/Content     │    │  零代码扩展新AI功能                 │
└─────────────────────────┘    └────────────────────────────────────┘
```

| 子项目 | 定位 | 一句话描述 |
|--------|------|-----------|
| **kwafoo-ai** | AI模型交互层 | 单一接口暴露，通过配置文件即可增加AI调用功能，不参与任何业务逻辑 |
| **kwafoo-crawler** | 爬虫层 | 只负责数据获取与保存（数据库/文件），不关心数据如何被使用 |
| **kwafoo-data-processor** | 数据处理核心层 | 异步任务队列 + 定时调度，协调爬虫与AI，是系统的"大脑" |
| **kwafoo-api** | 前后端交互层 | 只提供已处理数据的查询与展示，提交异步任务而非直接操作 |
| **kwafoo-frontend** | 前端展示层 | 纯数据展现，通过HTTP与API通信 |

---

## 三、全局数据流设计

```
┌─────────────────────────────────────────────────────────────────────────┐
│  数据流入                                                                │
│                                                                          │
│  kwafoo-crawler                                                          │
│  ├─ RSS抓取 ────┐                                                        │
│  ├─ API抓取 ────┼──→ 原始数据 ──→ Database (ai_processed=0)              │
│  ├─ Web抓取 ────┤                   或 File System                       │
│  └─ Content抓取 ┘                                                        │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │ 爬虫写入数据库
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  数据处理（kwafoo-data-processor）                                        │
│                                                                          │
│  ┌──────────────────────────────┐                                        │
│  │  定时扫描任务                │  ─── 每N分钟扫描 ai_processed=0 的数据  │
│  │  发现新数据 → 创建处理任务   │                                        │
│  └──────────────┬───────────────┘                                        │
│                 │ 提交AI任务                                             │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                        │
│  │  异步任务队列                │                                        │
│  │  Task: classify → summarize  │  ─── 顺序执行：分类 → 摘要 → 评分      │
│  │       → score                │                                        │
│  └──────────────┬───────────────┘                                        │
│                 │ 调用AI                                                 │
│                 ▼                                                        │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │               kwafoo-ai 统一接口                          │           │
│  │  ai.execute("classify", title=..., description=...)      │           │
│  │  ai.execute("summarize", content=..., title=...)         │           │
│  │  ai.execute("score", title=..., summary=..., category=...│           │
│  │  ai.execute("report", news_list=..., type="daily")       │           │
│  └──────────────────────────────────────────────────────────┘           │
│                 │ AI返回结果                                             │
│                 ▼                                                        │
│  ┌──────────────────────────────┐                                        │
│  │  结果落库                    │  ─── 更新 ai_processed=1, category,    │
│  │  更新状态 + 写入AI结果       │       ai_summary, score 等字段          │
│  └──────────────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────┘
         │
         │ 处理完成的数据
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  数据服务（kwafoo-api）                                                   │
│                                                                          │
│  GET  /api/news           ──→ 查询 ai_processed=1 的新闻                 │
│  GET  /api/news/search    ──→ 全文搜索已处理数据                          │
│  POST /api/chat           ──→ RAG引擎 + kwafoo-ai 生成回答               │
│  POST /api/tasks/process  ──→ 向 data-processor 提交异步任务              │
│  WS   /ws                 ──→ 推送进度（来自 data-processor）             │
└──────────────────────────┬──────────────────────────────────────────────┘
                           │ HTTP JSON
                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  数据展现（kwafoo-frontend）                                               │
│                                                                          │
│  Vue 3 SPA → 调用 API → 渲染新闻列表/管理界面/监控面板                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**关键设计原则：**

1. **API层不直接调AI**：`kwafoo-api` 需要触发AI处理时，通过向 `kwafoo-data-processor` 提交异步任务来实现，不在API请求链路中同步等待AI响应
2. **爬虫不关心数据用途**：`kwafoo-crawler` 只负责抓取→标准化→存储，不包含任何AI或业务逻辑
3. **AI层不参与业务**：`kwafoo-ai` 只提供单一的 `execute(task_name, **params)` 接口，完全由调用方决定何时调用、如何处理结果
4. **数据处理模块是编排核心**：`kwafoo-data-processor` 是唯一有权同时调用爬虫和AI的模块，负责所有异步任务编排和定时调度

---

## 四、子项目详细设计

### 4.1 kwafoo-ai（AI模型交互层）

#### 4.1.1 设计目标

> **核心原则：仅一个接口对外，通过传参执行不同的AI交互功能。增加新功能只需添加配置文件，零代码修改。**

#### 4.1.2 配置驱动的任务定义系统

kwafoo-ai 的所有AI调用功能通过 **任务配置文件** 定义。每个 `.yaml` 文件描述一个完整的AI交互任务。

**目录结构：**

```
kwafoo-ai/
├── pyproject.toml
├── README.md
├── src/
│   └── kwafoo_ai/
│       ├── __init__.py          # 暴露统一入口：AIEngine
│       ├── engine.py            # 核心引擎：加载配置 + 调用AI
│       ├── task_loader.py       # 任务配置文件加载器
│       ├── validator.py         # 通用响应验证器（基于JSON Schema）
│       ├── retry.py             # 重试策略管理器
│       └── types.py             # 核心数据类型定义
│
├── tasks/                       # 【任务配置目录】添加新功能只需在此加文件
│   ├── classify.yaml            # 新闻分类任务
│   ├── summarize.yaml           # 新闻摘要任务
│   ├── score.yaml               # 新闻评分任务
│   ├── report.yaml              # 报告生成任务
│   └── _template.yaml           # 任务配置模板（供参考）
│
├── config/
│   └── ai_config.toml.example   # AI连接配置示例
│
└── tests/
    ├── test_engine.py
    ├── test_task_loader.py
    └── test_custom_task.yaml    # 测试用的自定义任务
```

#### 4.1.3 任务配置文件格式

每个任务配置包含：任务元信息、输入参数定义、输出格式定义、提示词模板、AI调用参数。

**示例1：分类任务 `tasks/classify.yaml`**

```yaml
# ===== 任务元信息 =====
name: classify
version: "1.0"
description: "新闻智能分类 - 根据标题和内容判断所属分类，并提取关键字"

# ===== 输入参数定义 =====
input_schema:
  type: object
  required: [title, content]
  properties:
    title:
      type: string
      description: "新闻标题"
      max_length: 200
    content:
      type: string
      description: "新闻内容（正文/摘要/描述）"
      max_length: 2000
    categories:
      type: array
      items:
        type: string
      description: "可用分类列表"
      default_from_config: "categories"   # 从全局配置中读取
    context:
      type: object
      description: "额外上下文（如用户信息）"
      properties:
        nationality:
          type: string
        religion:
          type: string

# ===== 输出格式定义 =====
output_schema:
  type: object
  required: [categories, keywords]
  properties:
    categories:
      type: array
      items:
        type: string
      description: "分类名称列表，最多2个"
      max_items: 2
    keywords:
      type: array
      items:
        type: string
      description: "关键字列表，最多10个"
      max_items: 10

# ===== 系统提示词 =====
system_prompt: "你是一个专业的新闻分类助手，负责准确识别新闻的分类和提取关键字。"

# ===== 用户提示词模板 =====
prompt_template: |
  请根据以下新闻的标题和描述，判断它属于哪个分类，并提取10个关键字。

  可用分类：{categories}

  标题：{title}

  描述：{content}

  用户信息：
  - 国籍：{context.nationality}
  - 宗教：{context.religion}

  要求：
  1. 仔细阅读新闻内容，理解其主题领域
  2. 从可用分类中选择1-2个最匹配的分类
  3. 提取10个最能代表新闻内容的关键字
  4. 严格按照JSON格式返回

# ===== AI调用参数 =====
model_params:
  temperature: 0.7
  max_tokens: 2048
  timeout: 120

# ===== 重试策略 =====
retry:
  max_retries: 3
  backoff_base: 1.5
  max_delay: 30.0
  retry_on:
    - timeout
    - connection
    - json_parse

# ===== 后处理 =====
post_process:
  - type: validate_categories     # 验证分类是否在允许列表中
  - type: keyword_fallback        # 如果分类为空，尝试从关键字推断分类
```

**示例2：摘要任务 `tasks/summarize.yaml`**

```yaml
name: summarize
version: "1.0"
description: "新闻智能摘要 - 生成简洁准确的新闻摘要和一句话评价"

input_schema:
  type: object
  required: [content]
  properties:
    content:
      type: string
      description: "新闻正文内容"
      max_length: 5000
    title:
      type: string
      description: "新闻标题（可选）"
      max_length: 200
      required: false
    enable_comment:
      type: boolean
      description: "是否生成评价"
      default: true
    personality:
      type: string
      description: "评价人设描述"
      default: ""

output_schema:
  type: object
  required: [comment, summary]
  properties:
    comment:
      type: string
      description: "一句话评价，包含emoji，不超过30字"
      max_length: 100
    summary:
      type: string
      description: "新闻摘要，120-160字"
      min_length: 120
      max_length: 160

system_prompt: "你是一个专业的新闻摘要助手，负责生成简洁准确的新闻摘要。"

prompt_template: |
  {personality_block}

  请根据以下新闻内容生成摘要和一句话评价：

  {content}

  要求：
  1. 评价：一句话，包含emoji，不超过30字
  2. 摘要：准确概括核心内容，120-160字
  3. 严格使用中文书写
  4. 必须返回JSON格式

model_params:
  temperature: 0.7
  max_tokens: 2048
  timeout: 120

retry:
  max_retries: 3
  backoff_base: 1.5
  max_delay: 30.0

# 预处理：将enable_comment和personality转换为personality_block
pre_process:
  - type: conditional_block
    condition: "{enable_comment}"
    template: "请以以下人设进行点评：{personality}"
    target_var: "personality_block"
```

**示例3：评分任务 `tasks/score.yaml`**

```yaml
name: score
version: "1.0"
description: "新闻综合评分 - 从关联度、重要程度、来源分三个维度评分"

input_schema:
  type: object
  required: [title, summary]
  properties:
    title:
      type: string
      description: "新闻标题"
    summary:
      type: string
      description: "新闻摘要"
    content:
      type: string
      description: "新闻正文片段"
      max_length: 1000
    category:
      type: string
      description: "新闻分类"
    source_score:
      type: number
      description: "来源基准分（0-100）"
    interest_keywords:
      type: array
      items:
        type: string
      description: "用户兴趣关键字"

output_schema:
  type: object
  required: [relevance, importance, source_score]
  properties:
    relevance:
      type: number
      minimum: 0
      maximum: 100
      description: "关联度评分"
    importance:
      type: number
      minimum: 0
      maximum: 100
      description: "重要程度评分"
    source_score:
      type: number
      minimum: 0
      maximum: 100
      description: "来源评分"
    reason:
      type: string
      description: "评分综合理由"

system_prompt: "你是一个专业的新闻分析师，擅长对新闻进行多维度评分。"

prompt_template: |
  请对以下新闻进行多维度评分：

  标题：{title}
  摘要：{summary}
  分类：{category}

  用户兴趣关键字：{interest_keywords}

  评分标准：
  1. 关联度（0-100）：新闻与用户兴趣的匹配程度
  2. 重要程度（0-100）：新闻的社会影响力
  3. 来源分：使用给定的来源基准分 {source_score}

  要求返回JSON格式。

model_params:
  temperature: 0.3       # 评分类任务使用较低温度
  max_tokens: 1024
  timeout: 120

retry:
  max_retries: 2
  backoff_base: 2.0
```

**示例4：用户自定义任务 `tasks/custom_example.yaml`**

```yaml
# 这只是个示例，用户可复制修改后创建自己的AI调用任务
name: my_custom_task
version: "1.0"
description: "自定义AI任务示例 - 情感分析"

input_schema:
  type: object
  required: [text]
  properties:
    text:
      type: string
      description: "待分析文本"

output_schema:
  type: object
  required: [sentiment, confidence]
  properties:
    sentiment:
      type: string
      enum: [positive, negative, neutral]
    confidence:
      type: number
      minimum: 0
      maximum: 1

system_prompt: "你是一个专业的情感分析助手。"

prompt_template: |
  请分析以下文本的情感倾向：

  {text}

  返回JSON格式。

model_params:
  temperature: 0.3
  max_tokens: 512
  timeout: 60
```

#### 4.1.4 核心引擎设计

引擎是 kwafoo-ai 的唯一对外接口，负责加载任务配置、校验输入、构建提示词、调用AI、验证输出。

**引擎类设计：**

```
AIEngine
│
├── __init__(config_path: str)
│     - 加载全局AI配置（base_url, model, api_key等）
│     - 扫描 tasks/ 目录加载所有任务配置文件
│     - 初始化 LiteLLM 客户端
│     - 初始化响应验证器
│     - 初始化重试策略管理器
│
├── execute(task_name: str, **params) -> AIResult
│     - 根据 task_name 查找任务配置
│     - 校验输入参数是否符合 input_schema
│     - 执行 pre_process 预处理
│     - 渲染 prompt_template
│     - 调用 AI（含重试和退避）
│     - 解析和验证输出
│     - 执行 post_process 后处理
│     - 返回统一 AIResult 对象
│
├── list_tasks() -> List[TaskMeta]
│     - 列出所有可用的任务名称和描述
│
├── get_task_info(task_name: str) -> TaskConfig
│     - 获取指定任务的完整配置信息
│
└── reload_tasks()
      - 热重载任务配置文件（无需重启）
```

**统一调用方式：**

```python
from kwafoo_ai import AIEngine

# 初始化（只需一次）
ai = AIEngine(config_path="config/ai_config.toml")

# 查看可用任务
print(ai.list_tasks())
# [TaskMeta(name='classify', description='新闻智能分类...'),
#  TaskMeta(name='summarize', description='新闻智能摘要...'),
#  TaskMeta(name='score', description='新闻综合评分...'),
#  TaskMeta(name='report', description='报告生成...')]

# 执行分类
result = ai.execute("classify",
    title="海底捞控股股东张勇拟增持不少于1亿港元",
    content="海底捞在港交所公告...",
    categories=["科技", "财经", "国际", "体育"],
    context={"nationality": "中国", "religion": "无"}
)
print(result.data)   # {"categories": ["财经"], "keywords": ["海底捞", "增持", ...]}
print(result.success)  # True
print(result.retry_count)  # 0

# 执行摘要
result = ai.execute("summarize",
    content="特斯拉将欣旺达动力电池加入其全球供应链...",
    title="特斯拉新增电池供应商",
    enable_comment=True
)
print(result.data)  # {"comment": "🚗 特斯拉供应链再添新成员", "summary": "..."}

# 执行评分
result = ai.execute("score",
    title="新闻标题",
    summary="新闻摘要",
    category="科技",
    source_score=80,
    interest_keywords=["AI", "大模型"]
)
print(result.data)  # {"relevance": 85.0, "importance": 70.0, "source_score": 80.0}
```

#### 4.1.5 扩展新功能的步骤

**只需三步，零代码修改：**

1. **创建任务配置文件**：在 `tasks/` 目录下新建 `my_task.yaml`
2. **定义任务参数**：按模板填写 `name`、`input_schema`、`output_schema`、`prompt_template`
3. **直接使用**：`ai.execute("my_task", ...)`

**示例：增加一个"关键信息提取"任务**

```yaml
# 创建文件：tasks/extract.yaml
name: extract
version: "1.0"
description: "从文本中提取关键信息"

input_schema:
  type: object
  required: [text]
  properties:
    text:
      type: string
      description: "待提取的文本"
    fields:
      type: array
      items:
        type: string
      description: "需要提取的字段列表"

output_schema:
  type: object
  properties:
    result:
      type: object
      description: "提取结果，key为字段名"

system_prompt: "你是一个信息提取助手。"

prompt_template: |
  从以下文本中提取信息：
  
  需要提取的字段：{fields}
  
  文本：{text}
  
  返回JSON格式。

model_params:
  temperature: 0.3
  max_tokens: 1024
  timeout: 60
```

保存文件后即可直接使用，无需重启：
```python
result = ai.execute("extract",
    text="苹果公司于2024年6月发布了iOS 18操作系统...",
    fields=["公司", "产品", "时间"]
)
```

#### 4.1.6 技术选型说明

| 组件 | 选型 | 理由 |
|------|------|------|
| AI调用库 | LiteLLM | 统一的多模型接口，已在项目中验证可用 |
| 配置文件格式 | YAML | 可读性强，支持注释，适合任务定义 |
| Schema校验 | jsonschema (Python) | 标准的JSON Schema校验库，输入输出都可校验 |
| 提示词模板 | Python str.format() | 内置模板引擎，足够满足需求，无需额外依赖 |

#### 4.1.7 配置文件热加载与发现机制

```
引擎初始化时：
  1. 读取 config/ai_config.toml 获取AI连接参数
  2. 扫描 tasks/ 目录下所有 *.yaml 文件
  3. 逐个解析校验，合法则注册、非法则跳过并告警
  4. 建立 task_name -> TaskConfig 的映射表

运行时新增任务：
  - 调用 ai.reload_tasks() 重新扫描 tasks/ 目录
  - 或监听 tasks/ 目录的文件变更自动重载（可选）

任务配置校验规则：
  - name 必须唯一
  - required 字段不能缺失
  - prompt_template 中引用的变量必须在 input_schema 中定义
  - output_schema 必须符合 JSON Schema 规范
```

---

### 4.2 kwafoo-crawler（爬虫层）

#### 4.2.1 设计目标

> **核心原则：只关心数据获取与保存，不关心数据如何被使用。支持输出到数据库或文件系统。**

#### 4.2.2 目录结构

```
kwafoo-crawler/
├── pyproject.toml
├── README.md
├── src/
│   └── kwafoo_crawler/
│       ├── __init__.py
│       ├── engine.py              # 爬虫引擎（统一入口）
│       ├── fetchers/
│       │   ├── __init__.py
│       │   ├── base.py            # 爬虫基类
│       │   ├── rss.py             # ← 原 fetcher/rss_fetcher.py
│       │   ├── api.py             # ← 原 fetcher/api_fetcher.py
│       │   ├── web.py             # ← 原 fetcher/web_fetcher.py
│       │   └── content.py         # ← 原 fetcher/content_fetcher.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── base.py            # 存储基类
│       │   ├── sqlite.py          # SQLite存储后端
│       │   └── file.py            # 文件系统存储后端（JSON/CSV）
│       └── utils/
│           ├── __init__.py
│           ├── image_processor.py # ← 原 utils/image_processor.py
│           └── helpers.py         # 爬虫专用工具（URL处理等）
│
├── config/
│   ├── crawler_config.toml.example  # 爬虫配置（新闻源定义）
│   └── sources/                     # 可选：每个源独立的配置文件
│       ├── 36kr.yaml
│       └── ithome.yaml
│
└── tests/
    ├── test_rss.py
    ├── test_api.py
    ├── test_web.py
    └── test_storage.py
```

#### 4.2.3 爬虫引擎设计

```
CrawlerEngine
│
├── __init__(config_path: str)
│     - 加载爬虫配置（新闻源列表、并发数、代理等）
│     - 初始化各类型抓取器
│     - 初始化存储后端
│
├── crawl_all() -> CrawlResult
│     - 并发抓取所有启用的新闻源
│     - 汇总结果
│
├── crawl_source(source_name: str) -> CrawlResult
│     - 抓取指定新闻源
│
├── fetch_content(url: str) -> Optional[str]
│     - 抓取单篇文章正文
│
├── add_source(source_config: dict)
│     - 动态添加新闻源
│
└── get_sources() -> List[SourceConfig]
      - 列出所有新闻源配置
```

**核心调用方式：**

```python
from kwafoo_crawler import CrawlerEngine

crawler = CrawlerEngine(config_path="config/crawler_config.toml")

# 抓取所有源
result = crawler.crawl_all()
print(f"抓取完成: {result.total_fetched} 条新闻, "
      f"成功: {result.success_count}, 失败: {result.fail_count}")

# 抓取指定源
result = crawler.crawl_source("36氪")
for news in result.data:
    print(f"  [{news['source']}] {news['title']}")

# 提取正文
content = crawler.fetch_content("https://example.com/article/123")
```

#### 4.2.4 存储后端设计

支持两种存储模式，通过配置切换：

```toml
# crawler_config.toml
[storage]
backend = "sqlite"        # "sqlite" 或 "file"
sqlite_path = "data/crawler.db"
file_path = "data/raw_news/"
file_format = "json"      # "json" 或 "csv"
```

```
StorageBackend (抽象基类)
│
├── SQLiteStorage
│     - insert_news(news_data) -> int    # 返回news_id
│     - batch_insert(news_list) -> [int]
│     - exists(url) -> bool
│
└── FileStorage
      - save(news_data) -> str           # 返回文件路径
      - batch_save(news_list) -> [str]
      - exists(url) -> bool
```

**数据标准化输出格式：**

无论哪种抓取方式，输出的新闻数据都是统一格式：

```python
{
    "title": "新闻标题",
    "description": "新闻原始描述/摘要",
    "content": "新闻正文（可能为空）",
    "url": "https://example.com/news/123",
    "source": "新闻来源名称",
    "source_url": "来源首页URL",
    "publish_time": "2026-05-30 12:00:00",
    "fetch_time": "2026-05-30 12:30:00",
    "image_url": "https://example.com/image.jpg",
    "category_from_source": "科技",   # 来源标注的分类（可选）
    "raw_data": {}                    # 原始数据保留（调试用）
}
```

#### 4.2.5 新闻源配置格式

```toml
# crawler_config.toml
[crawler]
max_workers = 20
user_agent = "Kwafoo-Crawler/1.0"
request_timeout = 30

[network]
enable_proxy = false
proxy_url = ""

[[sources.rss]]
name = "36氪"
url = "https://36kr.com/feed"
enabled = true
fetch_days = 1
score = 100

[[sources.rss]]
name = "少数派"
url = "https://sspai.com/feed"
enabled = true
fetch_days = 1
score = 100

[[sources.web]]
name = "示例网站"
url = "https://example.com/news"
enabled = false
fetch_days = 1
selectors = { container = "div.news-list", title = "h2.title", link = "a" }

[storage]
backend = "sqlite"
sqlite_path = "data/crawler.db"
```

#### 4.2.6 依赖关系

| 依赖类型 | 内容 | 说明 |
|---------|------|------|
| 外部依赖 | requests, feedparser, beautifulsoup4, Pillow | 爬虫核心依赖 |
| 外部依赖 | aiosqlite (可选) | 异步SQLite支持 |
| 被依赖关系 | kwafoo-data-processor | 数据处理模块读取其输出数据 |
| 被依赖关系 | 命令行直接使用 | 可作为CLI工具独立运行 |

**kwafoo-crawler 不依赖 kwafoo-ai**，两者完全解耦。

---

### 4.3 kwafoo-data-processor（数据处理核心层）

#### 4.3.1 设计目标

> **核心原则：系统的"大脑"，负责编排数据加工流程。API不直接调AI，而是向此模块提交异步任务。支持定时任务对爬虫数据进行后道加工。**

#### 4.3.2 核心职责

1. **异步任务队列**：接收来自 kwafoo-api 的处理请求，放入队列异步执行
2. **定时调度**：定时扫描数据库中新抓取的数据（`ai_processed=0`），自动触发AI处理
3. **处理编排**：按顺序编排处理流程（摘要 → 分类 → 评分），衔接 kwafoo-crawler 的原始数据和 kwafoo-ai 的AI能力
4. **进度管理**：跟踪每批处理任务的进度，通过事件机制向外广播
5. **结果落库**：将AI处理结果写回数据库

#### 4.3.3 目录结构

```
kwafoo-data-processor/
├── pyproject.toml
├── README.md
├── src/
│   └── kwafoo_data_processor/
│       ├── __init__.py
│       ├── engine.py                # 处理引擎主入口
│       ├── task_queue.py            # 异步任务队列（基于 asyncio + Queue）
│       ├── scheduler.py             # 定时任务调度器
│       ├── pipeline.py              # 处理管道（定义处理步骤和顺序）
│       ├── worker.py                # 任务工作器
│       ├── event_bus.py             # 事件总线（进度/完成通知）
│       │
│       ├── steps/                   # 处理步骤定义
│       │   ├── __init__.py
│       │   ├── base.py              # 步骤基类
│       │   ├── fetch_content.py     # 正文抓取步骤
│       │   ├── compress.py          # 文本压缩步骤
│       │   ├── summarize.py         # AI摘要步骤（调用 kwafoo-ai）
│       │   ├── classify.py          # AI分类步骤（调用 kwafoo-ai）
│       │   ├── score.py             # AI评分步骤（调用 kwafoo-ai）
│       │   └── download_image.py    # 图片下载步骤
│       │
│       └── storage/
│           ├── __init__.py
│           └── db.py                # 数据库操作（读爬虫数据 + 写AI结果）
│
├── config/
│   └── processor_config.toml.example
│
└── tests/
    ├── test_engine.py
    ├── test_pipeline.py
    └── test_steps.py
```

#### 4.3.4 处理引擎设计

```
DataProcessorEngine
│
├── __init__(ai_engine, db_manager, config)
│     - 注入 kwafoo_ai.AIEngine 实例
│     - 注入数据库管理器（访问爬虫写入的DB）
│     - 初始化任务队列、工作器、调度器、事件总线
│     - 注册处理步骤和管道
│
├── start()
│     - 启动工作器（消费任务队列）
│     - 启动定时调度器（扫描新数据）
│     - 启动事件总线
│
├── stop()
│     - 优雅关闭所有组件
│
│  ----- 任务提交（供外部调用）-----
│
├── submit_process_task(news_ids: List[int], task_type: str) -> task_id
│     - API层调用此方法提交处理任务
│     - 返回 task_id 供后续查询进度
│     - task_type: "all" | "summary" | "classify" | "score"
│
├── submit_batch_process(news_ids: List[int]) -> task_id
│     - 批量处理（完整管道）
│
│  ----- 任务状态查询 -----
│
├── get_task_status(task_id: str) -> TaskStatus
│     - 查询任务进度和结果
│
├── get_active_tasks() -> List[TaskStatus]
│     - 获取所有进行中的任务
│
│  ----- 事件订阅 -----
│
├── on(event: str, callback: Callable)
│     - 订阅事件（progress_update, task_completed, task_failed)
│
└── get_event_bus() -> EventBus
      - 获取事件总线实例（供WebSocket广播使用）
```

#### 4.3.5 处理管道设计

管道定义了数据处理的标准流程，由多个步骤按顺序组成：

```
Pipeline: 标准新闻处理管道
│
├── Step 1: FetchContent         # 正文抓取
│     - 输入: news.url
│     - 调用: kwafoo-crawler 的内容抓取器
│     - 输出: news.content
│
├── Step 2: Compress             # 文本压缩（可选）
│     - 输入: news.content
│     - 调用: HybridCompressor
│     - 输出: news.compressed_content
│
├── Step 3: DownloadImage        # 图片下载（可选）
│     - 输入: news.image_url
│     - 输出: 本地图片路径
│
├── Step 4: Summarize            # AI摘要 ← 调用 kwafoo-ai
│     - 输入: news.content / news.compressed_content
│     - 调用: ai.execute("summarize", content=..., title=...)
│     - 输出: news.ai_summary, news.ai_comment
│
├── Step 5: Classify             # AI分类 ← 调用 kwafoo-ai
│     - 输入: news.ai_summary / news.description
│     - 调用: ai.execute("classify", title=..., content=...)
│     - 输出: news.category, news.keywords
│
├── Step 6: Score                # AI评分 ← 调用 kwafoo-ai
│     - 输入: news.ai_summary
│     - 调用: ai.execute("score", title=..., summary=...)
│     - 输出: news.relevance_score, news.importance_score
│
└── Step 7: SaveResult           # 结果落库
      - 将所有处理结果写回数据库
      - 设置 news.ai_processed = 1
```

**管道是可配置的**，通过配置文件可以：
- 启用/禁用某个步骤
- 调整步骤顺序
- 设置步骤的超时和重试

```toml
# processor_config.toml
[pipeline.standard]
steps = ["fetch_content", "compress", "download_image", "summarize", "classify", "score", "save_result"]

[pipeline.lightweight]
steps = ["summarize", "classify", "save_result"]
description = "轻量处理（跳过正文抓取）"

[pipeline.reprocess]
steps = ["summarize", "classify", "score", "save_result"]
description = "重新处理（已有正文，只做AI处理）"

[steps.summarize]
enabled = true
timeout = 120
retry = 3

[steps.classify]
enabled = true
timeout = 120
retry = 3

[steps.score]
enabled = true          # 可通过配置关闭评分
timeout = 120
retry = 2

[steps.fetch_content]
enabled = false         # 默认关闭正文抓取
timeout = 30
retry = 2

[steps.compress]
enabled = true
algorithm = "auto"      # auto / default / textrank
target_tokens = 2000
```

#### 4.3.6 异步任务队列设计

```
                    ┌─────────────────────┐
                    │   任务提交方         │
                    │   (kwafoo-api)      │
                    └──────────┬──────────┘
                               │ submit_process_task(news_ids, type)
                               ▼
                    ┌─────────────────────┐
                    │   TaskQueue         │
                    │   (asyncio.Queue)   │
                    │                     │
                    │  pending_tasks      │
                    │  ┌───────┐          │
                    │  │Task 1 │──→ worker_1 ──→ pipeline.run()
                    │  │Task 2 │──→ worker_2 ──→ pipeline.run()
                    │  │Task 3 │──→ worker_3 ──→ pipeline.run()
                    │  └───────┘          │
                    │                     │
                    │  task_registry      │
                    │  task_id -> Task    │
                    └──────────┬──────────┘
                               │ 事件推送
                               ▼
                    ┌─────────────────────┐
                    │   EventBus          │
                    │                     │
                    │  progress_update    │──→ WebSocket Broadcast
                    │  task_completed     │──→ WebSocket Broadcast
                    │  task_failed        │──→ WebSocket Broadcast
                    │  db_updated         │──→ 内部通知
                    └─────────────────────┘
```

#### 4.3.7 定时任务调度

定时任务负责自动扫描新数据并触发处理：

```toml
# processor_config.toml - 定时任务配置
[scheduler.tasks.auto_process_new_news]
enabled = true
interval = 600              # 每10分钟扫描一次
action = "scan_and_process"
params:
  batch_size = 10           # 每次处理10条
  pipeline = "standard"
  conditions:
    ai_processed = 0        # 只处理未处理的新闻
    is_deleted = 0          # 排除已删除

[scheduler.tasks.auto_generate_report]
enabled = false
schedule = "0 8 * * *"      # 每天早上8点（cron表达式）
action = "generate_report"
params:
  report_type = "daily"
  pipeline = "report"

[scheduler.tasks.cleanup_old_data]
enabled = true
schedule = "0 3 * * 0"      # 每周日凌晨3点
action = "cleanup"
params:
  max_age_days = 30
  cleanup_images = true
  cleanup_logs = true

[scheduler.tasks.retry_failed_tasks]
enabled = true
interval = 1800              # 每30分钟
action = "retry_failed"
params:
  max_retry_age_hours = 24   # 只重试24小时内的失败任务
```

**调度器的定时扫描逻辑：**

```
每 interval 秒执行一次：
  1. 查询数据库：SELECT * FROM news WHERE ai_processed = 0 AND is_deleted = 0
  2. 如果有新数据：
     - 按 batch_size 分批
     - 每批提交一个处理任务到 TaskQueue
     - 通过 EventBus 广播进度
  3. 如果无新数据：
     - 跳过本轮
```

#### 4.3.8 事件总线与进度广播

事件总线负责将处理进度实时推送给订阅者（主要是 kwafoo-api 的 WebSocket）：

```python
# 事件类型
event_bus.on("task_created",     callback)   # 任务创建
event_bus.on("task_started",     callback)   # 任务开始执行
event_bus.on("step_started",     callback)   # 步骤开始
event_bus.on("step_completed",   callback)   # 步骤完成
event_bus.on("step_failed",      callback)   # 步骤失败
event_bus.on("task_completed",   callback)   # 任务完成
event_bus.on("task_failed",      callback)   # 任务失败
event_bus.on("db_updated",       callback)   # 数据库更新（通知API刷新缓存）
event_bus.on("scan_completed",   callback)   # 定时扫描完成

# 事件数据格式
{
    "event": "step_completed",
    "task_id": "task_20260530_120000",
    "data": {
        "step_name": "classify",
        "news_id": 123,
        "duration_ms": 3500,
        "result": {"categories": ["科技"], "keywords": [...]}
    },
    "timestamp": "2026-05-30 12:00:05"
}
```

#### 4.3.9 依赖关系

| 依赖类型 | 内容 | 说明 |
|---------|------|------|
| 内部依赖 | kwafoo-ai | 调用AI引擎进行数据处理 |
| 内部依赖 | kwafoo-crawler | 读取爬虫输出数据（DB/文件），调用正文抓取 |
| 外部依赖 | schedule (可选) | 定时任务 |
| 外部依赖 | asyncio | 异步任务队列 |
| 被依赖关系 | kwafoo-api | API通过此模块提交异步处理任务 |
| 被依赖关系 | 命令行直接使用 | 可作为CLI独立运行数据处理 |

---

### 4.4 kwafoo-api（前后端交互层）

#### 4.4.1 设计目标

> **核心原则：只负责已处理数据的查询与展示，不直接调用AI。需要触发AI处理时，向 data-processor 提交异步任务。**

#### 4.4.2 目录结构

```
kwafoo-api/
├── pyproject.toml
├── README.md
├── src/
│   └── kwafoo_api/
│       ├── __init__.py
│       ├── main.py                 # FastAPI 应用入口
│       ├── config.py               # API配置管理
│       │
│       ├── api/                    # API路由层（只做数据查询）
│       │   ├── __init__.py
│       │   ├── router.py           # 统一路由注册
│       │   ├── news.py             # 新闻查询API
│       │   ├── chat.py             # 聊天API（RAG）
│       │   ├── task.py             # 任务提交API（向processor提交）
│       │   ├── config.py           # 配置管理API
│       │   ├── report.py           # 报告查询API
│       │   └── system.py           # 系统状态API
│       │
│       ├── services/               # 服务层（业务逻辑）
│       │   ├── __init__.py
│       │   ├── news_service.py     # 新闻查询服务
│       │   ├── chat_service.py     # 聊天服务（含RAG）
│       │   ├── task_service.py     # 任务服务（对接data-processor）
│       │   └── report_service.py   # 报告服务
│       │
│       ├── rag/                    # RAG引擎（保留在API层）
│       │   ├── __init__.py
│       │   └── engine.py           # ← 原 rag/engine.py
│       │
│       ├── websocket/              # WebSocket
│       │   ├── __init__.py
│       │   └── server.py           # 实时推送（订阅processor事件）
│       │
│       └── models/                 # Pydantic数据模型
│           ├── __init__.py
│           ├── news.py
│           ├── chat.py
│           ├── task.py
│           └── config.py
│
├── config/
│   └── api_config.toml.example
│
└── tests/
    ├── test_news_api.py
    ├── test_chat_api.py
    └── test_websocket.py
```

#### 4.4.3 核心设计：API与数据处理的分工

```
kwafoo-api 的边界：
  ✅ 查询已处理数据（GET /api/news）
  ✅ 搜索已处理数据（GET /api/news/search）
  ✅ RAG对话（POST /api/chat）
  ✅ 提交异步任务（POST /api/tasks/process）──→ 委托给 data-processor
  ✅ 查询任务进度（GET /api/tasks/{task_id}/status）
  ✅ WebSocket推送（订阅 data-processor 事件总线）
  ✅ 配置管理（GET/POST /api/config）

  ❌ 不直接调用 kwafoo-ai
  ❌ 不直接操作原始数据
  ❌ 不管理系统调度
```

#### 4.4.4 API路由设计

```
GET    /api/news                  # 获取新闻列表（仅返回 ai_processed=1 的数据）
GET    /api/news/{id}             # 获取新闻详情
GET    /api/news/category/{name}  # 按分类获取新闻
GET    /api/news/search           # 全文搜索
GET    /api/news/stats            # 新闻统计信息
POST   /api/news/{id}/read        # 标记已读

POST   /api/chat                  # RAG对话
GET    /api/chat/history          # 对话历史

POST   /api/tasks/process         # 提交异步处理任务 → data-processor
GET    /api/tasks/status          # 获取活跃任务列表
GET    /api/tasks/{task_id}       # 获取任务详情
POST   /api/tasks/{task_id}/cancel # 取消任务

GET    /api/reports               # 获取报告列表
GET    /api/reports/{id}          # 获取报告详情

GET    /api/config                # 获取当前配置
POST   /api/config                # 更新配置
POST   /api/config/reload         # 重载配置

GET    /api/system/status         # 系统状态
GET    /api/system/logs           # 系统日志

WS     /ws                        # WebSocket实时推送
```

#### 4.4.5 任务提交API设计

当用户在前端点击"重新分析"按钮时，API不直接调AI，而是提交异步任务：

```python
# kwafoo-api/services/task_service.py

class TaskService:
    def __init__(self, processor_client):
        self.processor = processor_client  # 指向 data-processor
    
    async def submit_reprocess(self, news_ids: List[int]) -> str:
        """提交重新处理任务"""
        task_id = await self.processor.submit_process_task(
            news_ids=news_ids,
            task_type="all"
        )
        return task_id
    
    async def get_status(self, task_id: str) -> dict:
        """查询任务状态"""
        return await self.processor.get_task_status(task_id)
```

#### 4.4.6 推荐技术升级：http.server → FastAPI

| 特性 | http.server (当前) | FastAPI (推荐) |
|------|-------------------|----------------|
| 路由管理 | 手动注册字典 | 装饰器自动注册 |
| 请求/响应模型 | 手动JSON解析 | Pydantic自动校验 |
| API文档 | 无 | 自动生成 Swagger UI / ReDoc |
| CORS中间件 | 自行实现 | 一行配置 |
| 异步IO | 需自行实现 | 原生 asyncio |
| WebSocket | 独立实现 | 原生集成 |
| 依赖注入 | 无 | 内置 Depends() |
| 后台任务 | 无 | 内置 BackgroundTasks |
| 类型安全 | 无 | 完整类型提示 |
| 测试工具 | 无 | 内置 TestClient |

#### 4.4.7 与数据处理模块的通信方式

由于 `kwafoo-api` 和 `kwafoo-data-processor` 可能在同一个进程或不同进程中运行，设计两种通信方式：

**方式一：内存调用（同进程，开发/小规模部署推荐）**

```python
# API 启动时
processor = DataProcessorEngine(ai_engine=ai, db_manager=db)
processor.start()

# API 中提交任务
task_id = processor.submit_process_task(news_ids=[1,2,3], task_type="all")

# 订阅事件用于WebSocket
processor.on("progress_update", ws_handler.broadcast)
```

**方式二：消息队列（跨进程，生产环境推荐）**

```
kwafoo-api ──(submit task)──→ Redis/Kafka ──(consume task)──→ kwafoo-data-processor
kwafoo-api ←──(subscribe)─── Redis Pub/Sub ←──(publish event)── kwafoo-data-processor
```

推荐初期使用**方式一**（内存调用），架构上预留方式二的接口切换能力。

#### 4.4.8 依赖关系

| 依赖类型 | 内容 | 说明 |
|---------|------|------|
| 内部依赖 | kwafoo-data-processor | 提交异步任务、订阅事件 |
| 内部依赖 | kwafoo-ai | 仅用于RAG对话（chat_api） |
| 外部依赖 | fastapi, uvicorn | Web框架 |
| 外部依赖 | websockets | WebSocket |
| 被依赖关系 | kwafoo-frontend | 前端通过HTTP调用 |

---

### 4.5 kwafoo-frontend（前端展示层）

#### 4.5.1 设计目标

> **核心原则：纯数据展现，不包含任何业务逻辑。通过HTTP与API通信。**

#### 4.5.2 目录结构

```
kwafoo-frontend/
├── package.json
├── package-lock.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── index.html
├── .env.development              # 开发环境：API地址
├── .env.production               # 生产环境：API地址
├── public/
│   └── favicon.svg
├── src/
│   ├── api/
│   │   └── index.ts              # API客户端（从环境变量读地址）
│   ├── components/               # ← 原 web/frontend/src/components/
│   │   ├── CategoryList.vue
│   │   ├── ChatModal.vue
│   │   ├── NewsCard.vue
│   │   ├── NewsDetailModal.vue
│   │   └── ReportDetailModal.vue
│   ├── composables/              # ← 原 web/frontend/src/composables/
│   │   ├── useChat.ts
│   │   ├── useNews.ts
│   │   └── useWebSocket.ts
│   ├── router/
│   │   └── index.ts              # ← 原 web/frontend/src/router/
│   ├── stores/                   # ← 原 web/frontend/src/stores/
│   │   ├── chat.ts
│   │   ├── config.ts
│   │   └── news.ts
│   ├── types/                    # ← 原 web/frontend/src/types/
│   │   ├── chat.ts
│   │   ├── config.ts
│   │   ├── news.ts
│   │   └── report.ts
│   ├── utils/
│   │   └── errorHandler.ts       # ← 原 web/frontend/src/utils/
│   ├── views/                    # ← 原 web/frontend/src/views/
│   │   ├── AdminView.vue
│   │   ├── MonitorView.vue
│   │   ├── NewsView.vue
│   │   └── ReportView.vue
│   ├── App.vue
│   └── main.ts
├── dist/                         # 构建产物
└── tests/
```

#### 4.5.3 环境变量配置

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# .env.production
VITE_API_BASE_URL=https://api.kwafoo.example.com
VITE_WS_URL=wss://api.kwafoo.example.com/ws
```

#### 4.5.4 API客户端改造

```typescript
// src/api/index.ts
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL + '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

export const wsUrl = import.meta.env.VITE_WS_URL

export default api
```

#### 4.5.5 技术栈（不变）

- Vue 3 + TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router
- Axios

---

## 五、拆分后跨模块通信设计

### 5.1 通信拓扑

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                   │
│  kwafoo-frontend ──── HTTP REST ────→ kwafoo-api                  │
│       │                                   │                       │
│       │                                   │ ① 内存调用/消息队列    │
│       │                                   ▼                       │
│       │                           kwafoo-data-processor           │
│       │                              │            │               │
│       │                     ②读爬虫数据   ③调AI处理               │
│       │                              ▼            ▼               │
│       │                      kwafoo-crawler   kwafoo-ai           │
│       │                           │                               │
│       │                           │ ④写入原始数据                  │
│       │                           ▼                               │
│       └────────── 共享 ────────── Database                        │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 通信方式总结

| 通信方向 | 方式 | 说明 |
|---------|------|------|
| Frontend → API | HTTP REST | 标准前后端通信 |
| Frontend ← API | WebSocket | 实时进度推送 |
| API → Data-Processor | 内存调用 / 消息队列 | 提交异步任务 |
| API ← Data-Processor | 事件总线回调 / 消息订阅 | 接收进度事件 |
| Data-Processor → AI | Python import | 直接调用 kwafoo-ai 统一接口 |
| Data-Processor → Crawler | 数据库读取 / Python import | 读取爬虫输出 |
| Crawler → Database | SQLite写入 | 原始数据落库 |
| Data-Processor → Database | SQLite读写 | 读取原始数据 + 写入处理结果 |
| API → Database | SQLite只读 | 查询已处理数据 |

### 5.3 配置分层

```
全局配置
│
├── kwafoo-ai 配置
│   └── config/ai_config.toml         # AI模型连接参数
│       [model]: base_url, model, api_key
│       [params]: temperature, max_tokens, timeout
│       [retry]: max_retries, backoff
│
├── kwafoo-crawler 配置
│   └── config/crawler_config.toml    # 爬虫参数
│       [crawler]: max_workers, user_agent
│       [network]: proxy
│       [[sources]]: 新闻源定义
│       [storage]: 存储后端配置
│
├── kwafoo-data-processor 配置
│   └── config/processor_config.toml  # 处理参数
│       [pipeline]: 管道步骤定义
│       [scheduler]: 定时任务配置
│       [queue]: 队列参数
│       [steps]: 各步骤参数
│       [ai_config]: 指向 kwafoo-ai 配置路径
│       [crawler_config]: 指向 kwafoo-crawler 配置路径
│
├── kwafoo-api 配置
│   └── config/api_config.toml        # API服务参数
│       [server]: host, port, cors
│       [websocket]: 开关
│       [processor_config]: 指向 data-processor 配置路径
│       [database]: 数据库路径
│
└── kwafoo-frontend 配置
    └── .env / .env.production        # 前端环境变量
        VITE_API_BASE_URL, VITE_WS_URL
```

---

## 六、各模块归属对照表

| 原模块/文件 | 归属子项目 | 说明 |
|-------------|-----------|------|
| `ai/ai_client.py` | kwafoo-ai | 重写为配置驱动引擎 |
| `ai/classifier.py` | kwafoo-ai | 重写为 `tasks/classify.yaml` |
| `ai/summarizer.py` | kwafoo-ai | 重写为 `tasks/summarize.yaml` |
| `ai/scorer.py` | kwafoo-ai | 重写为 `tasks/score.yaml` |
| `ai/report_generator.py` | kwafoo-ai | 重写为 `tasks/report.yaml` |
| `ai/response_validator.py` | kwafoo-ai | 通用化：基于JSON Schema |
| `ai/retry_strategy.py` | kwafoo-ai | 独立为重试管理器 |
| `ai/processor.py` | kwafoo-data-processor | 重写为 pipeline + steps |
| `fetcher/rss_fetcher.py` | kwafoo-crawler | RSS抓取器 |
| `fetcher/api_fetcher.py` | kwafoo-crawler | API抓取器 |
| `fetcher/web_fetcher.py` | kwafoo-crawler | 网页抓取器 |
| `fetcher/content_fetcher.py` | kwafoo-crawler | 正文提取器 |
| `database/manager.py` | kwafoo-data-processor | 数据处理模块的持久层 |
| | kwafoo-api（只读） | API层需要只读访问 |
| `rag/engine.py` | kwafoo-api | RAG引擎保留在API层 |
| `scheduler/scheduler.py` | kwafoo-data-processor | 重写为定时调度器 |
| `web/server.py` | kwafoo-api（重写） | 替换为FastAPI |
| `web/api/news_api.py` | kwafoo-api（重写） | 纯查询接口 |
| `web/api/ai_api.py` | kwafoo-api（重写） | 改为提交异步任务 |
| `web/api/chat_api.py` | kwafoo-api（重写） | RAG对话 |
| `web/api/config_api.py` | kwafoo-api（重写） | 配置管理 |
| `web/api/system_api.py` | kwafoo-api（重写） | 系统状态 |
| `web/api/report_api.py` | kwafoo-api（重写） | 报告查询 |
| `web/websocket.py` | kwafoo-api | WebSocket推送 |
| `web/frontend/*` | kwafoo-frontend | 整体迁移 |
| `utils/helpers.py` | 各项目分别采用 | 配置管理各自独立 |
| `utils/logger.py` | 各项目分别复制 | 日志管理 |
| `utils/image_processor.py` | kwafoo-crawler | 图片下载处理 |
| `utils/*_compressor.py` | kwafoo-data-processor | 文本压缩步骤 |
| `utils/progress.py` | kwafoo-data-processor | 进度管理 |
| `utils/validators.py` | kwafoo-ai | 响应验证 |
| `utils/error_handler.py` | 各项目分别采用 | 错误处理各自独立 |
| `utils/exceptions.py` | 各项目分别采用 | 各自定义异常 |
| `utils/constants.py` | 各项目分别采用 | 各自定义常量 |
| `utils/config_validator.py` | kwafoo-api | 配置验证 |
| `config.toml` | 拆分到各项目 | 按模块分层 |
| `data/kwafoo.db` | 共享数据库 | 各模块按职责读写 |
| `main.py` | kwafoo-api | API服务入口 |
| `hooks/*` | kwafoo-api | 打包钩子 |

---

## 七、实施方案

### 阶段一：kwafoo-ai（配置驱动改造）

**工作内容：**
1. 分析现有 `ai/` 模块中4个主要任务的共同模式
2. 设计任务配置文件格式（YAML），提取 `classify`、`summarize`、`score`、`report` 四个任务
3. 开发 `AIEngine` 统一入口（加载配置 → 校验输入 → 渲染模板 → 调AI → 验证输出）
4. 开发 `TaskLoader` 任务加载器（扫描tasks目录、热重载）
5. 开发通用 `ResponseValidator`（基于 JSON Schema）
6. 开发通用 `RetryManager`
7. 编写每个任务的单元测试，mock AI响应

**产出物：** `kwafoo-ai` pip包（本地安装，不公开发布）

### 阶段二：kwafoo-crawler（爬虫独立）

**工作内容：**
1. 将 `fetcher/` 模块独立为 `kwafoo-crawler` 项目
2. 设计 `CrawlerEngine` 统一入口
3. 实现存储后端抽象（SQLite + File），支持配置切换
4. 分离爬虫配置到独立文件（`crawler_config.toml`）
5. 解耦数据库依赖（爬虫只写数据，不关心数据如何被读）
6. 从原 `utils/` 中提取图片处理到爬虫项目

**产出物：** `kwafoo-crawler` 独立项目

### 阶段三：kwafoo-data-processor（数据处理核心）

**工作内容：**
1. 新建 `kwafoo-data-processor` 项目
2. 设计处理管道（Pipeline）和步骤（Step）抽象
3. 实现异步任务队列（asyncio.Queue）
4. 实现定时调度器（扫描新数据 + cron任务）
5. 实现事件总线（进度广播）
6. 将原 `ai/processor.py` 的业务逻辑迁移为 pipeline steps
7. 集成 `kwafoo-ai`（通过 `ai.execute()` 调用）
8. 集成 `kwafoo-crawler` 数据库读取能力
9. 将原 `scheduler/scheduler.py` 的定时逻辑迁移至此
10. 将原 `utils/progress.py` 迁移至此

**产出物：** `kwafoo-data-processor` 独立项目

### 阶段四：kwafoo-api（API服务重构）

**工作内容：**
1. 新建 `kwafoo-api` 项目，引入 FastAPI
2. 重写所有API路由（纯数据查询 + 异步任务提交）
3. 保留并优化 RAG 引擎
4. 实现 WebSocket（订阅 data-processor 事件）
5. 将原 `web/server.py` 逻辑迁移到 FastAPI
6. 移除所有直接调用 AI 的代码
7. 接入 `kwafoo-data-processor`（提交任务 + 订阅事件）

**产出物：** `kwafoo-api` 独立服务

### 阶段五：kwafoo-frontend（前端独立）

**工作内容：**
1. 将 `web/frontend/` 整体迁移为独立项目
2. 配置环境变量（API地址、WebSocket地址）
3. 改造API客户端（从环境变量读取base URL）
4. 独立开发和构建流程

**产出物：** `kwafoo-frontend` 独立前端项目

### 阶段六：集成验证

**工作内容：**
1. 启动 kwafoo-crawler，验证数据抓取和存储
2. 启动 kwafoo-ai CLI，验证各任务配置正确
3. 启动 kwafoo-data-processor，验证定时扫描和任务队列
4. 启动 kwafoo-api，验证数据查询和任务提交
5. 启动 kwafoo-frontend，验证端到端数据流（抓取 → 处理 → 查询 → 展示）
6. WebSocket进度推送验证

**产出物：** 完整运行的系统

---

## 八、kwafoo-ai 配置扩展方案研究

### 8.1 为什么选择 YAML + JSON Schema 方案

在研究了多种配置驱动方案后，选择 **YAML任务定义 + JSON Schema校验** 方案，理由如下：

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| **YAML配置文件** | 可读性强、支持注释、层次清晰、社区广泛使用 | 格式严格（缩进敏感） | **采用** |
| **Python 代码插件** | 灵活性极高 | 需要写代码、安全风险、学习成本高 | 不采用 |
| **类 LangChain Chain** | 声明式、链式组合 | 引入重量级依赖、抽象过多 | 不采用 |
| **LangGraph workflow** | 支持DAG工作流 | 过度设计、当前场景无需DAG | 不采用 |
| **插件系统 (entry_points)** | 标准pip插件机制、可扩展 | 需要安装才能用、不能简单加文件 | 不采用 |
| **PluginBase子类** | 面向对象扩展 | 仍需写代码、重载复杂 | 不采用 |

### 8.2 与现有代码的兼容策略

当前的 `ai_client.py` 已经具备良好的抽象基础（`AIRequest`/`AIResponse`/重试/验证），配置驱动版本将在其上构建：

```
当前代码                          配置驱动版本
─────────────────────────────────────────────────────
AIRequest (task_type)      →     task_name (从配置文件查)
AIRequest (prompt)         →     prompt_template 渲染
AIRequest (system_prompt)  →     task.system_prompt
AIRequest (response_schema)→     task.output_schema
AIRequest (context)        →     回调函数注入
ResponseValidator          →     通用 JSON Schema Validator
RetryStrategy              →     task.retry 配置 + RetryManager
classifier.py/summarizer...→     全部迁移到 tasks/*.yaml
```

### 8.3 参考实现的现有框架

| 框架/工具 | 借鉴点 | 不直接采用的原因 |
|-----------|--------|------------------|
| **LiteLLM router** | 多模型路由配置 | 关注模型选择，非任务抽象 |
| **Dify DSL** | YAML定义AI pipeline | 过于重量级 |
| **OpenAI Structured Outputs** | JSON Schema约束输出 | 仅限OpenAI模型 |
| **Instructor** | Pydantic模型→AI输出 | 需要写代码定义模型 |
| **Guardrails AI** | XML配置+验证 | XML可读性不如YAML |
| **CrewAI task config** | YAML定义agent task | 面向多agent场景 |

### 8.4 kwafoo-ai 独特优势

1. **最简单的扩展方式**：创建一个YAML文件 = 一个新AI功能
2. **完全解耦**：不依赖任何AI业务逻辑，只做"参数→提示词→响应"的转换
3. **自带文档**：每个任务配置即文档（description字段解释功能）
4. **可测试性**：每个任务可独立mock测试
5. **可组合性**：上层模块（data-processor）可以自由组合多个任务

---

## 九、数据库设计

### 9.1 共享数据库表结构

各模块共享同一个 SQLite 数据库，但读写职责清晰分离：

```
kwafoo.db
│
├── news 表（核心表）
│   ├── id, title, url, source, publish_time, fetch_time
│   │   [爬虫写入]
│   ├── description, content, image_url
│   │   [爬虫写入正文字段]
│   ├── category, keywords, ai_summary, ai_comment, ai_summary_en
│   │   [data-processor 写入AI分类/摘要结果]
│   ├── relevance_score, importance_score, source_score
│   │   [data-processor 写入AI评分结果]
│   ├── ai_processed (0|1), ai_process_time
│   │   [data-processor 写入处理状态]
│   ├── is_read (0|1), is_deleted (0|1)
│   │   [api 写入读取/删除状态]
│   └── read_count, source_name
│       [api 更新计数]
│
├── reports 表
│   └── [data-processor 写入: 调用 kwafoo-ai report任务]
│
├── chat_history 表
│   └── [api 写入: RAG对话记录]
│
├── config 表
│   └── [api 读写: 配置管理]
│
└── task_log 表
    └── [data-processor 写入: 任务执行记录]
```

### 9.2 各模块对数据库的访问权限

| 模块 | 权限 | 操作的表 | 操作说明 |
|------|------|---------|---------|
| kwafoo-crawler | **只写** | news | INSERT 原始新闻数据 |
| kwafoo-data-processor | **读写** | news, reports, task_log | READ 未处理数据 + WRITE AI结果 |
| kwafoo-api | **只读+少量写** | news, reports, chat_history, config | 查询已处理数据、写入用户操作 |

---

## 十、设计总结

### 10.1 拆分后对比

| 维度 | 拆分前（当前） | 拆分后（目标） |
|------|--------------|---------------|
| 子项目数量 | 1个单体项目 | 5个独立子项目 |
| AI功能扩展 | 需改Python代码（4个文件） | 仅添加YAML配置文件 |
| 爬虫独立性 | 与调度器、AI紧耦合 | 完全独立，可单独运行 |
| API调用链 | API → AIClient 同步调用 | API → Processor → AI 异步任务 |
| 数据处理 | 调度器内嵌AI处理 | 独立处理模块+管道编排 |
| 配置管理 | 单一config.toml | 各模块独立配置+分层 |
| 前端部署 | 构建产物嵌入后端 | 独立项目，环境变量配置API地址 |
| 定时任务 | 混在调度器中 | 独立的定时调度器+事件通知 |
| API框架 | http.server | FastAPI (自动文档/类型校验/异步) |
| 跨模块通信 | 直接import | 接口约定+事件总线 |
| 测试独立性 | 需启动完整服务 | 各模块可独立单元测试 |

### 10.2 核心设计亮点

1. **kwafoo-ai 配置驱动**：一个YAML文件 = 一个新AI功能，零代码扩展。这是整个架构中最关键的创新点，彻底解决了AI功能扩展需要在多个文件中修改代码的问题

2. **API不调AI**：API层只做已有数据的查询和展示，需要AI处理时通过异步任务提交给data-processor，实现了"读写分离"

3. **数据处理独立**：data-processor 是整个系统的编排核心，异步任务队列 + 管道步骤 + 定时调度的组合，既有实时性又有批量处理能力

4. **爬虫完全解耦**：crawler 只关心数据获取和存储，不依赖任何其他模块，可以独立运行、独立测试、独立部署

5. **事件驱动进度**：通过事件总线（EventBus）实现松耦合的进度通知，data-processor负责生产事件，API通过WebSocket广播给前端

6. **两种通信模式**：内存调用模式适合小规模部署（所有模块在同一进程），消息队列模式适合生产环境（跨进程独立部署），两者接口一致，切换无需改业务代码

---

## 十一、完整数据流时序图

```
时间线 ────────────────────────────────────────────────────────────────────→

1. 数据抓取阶段
   Crawler         Database
     │                │
     │── RSS抓取 ──→   │
     │── API抓取 ──→   │
     │── Web抓取 ──→   │
     │                │  INSERT (ai_processed=0)
     │                │

2. 自动处理阶段（定时触发）
   Data-Processor   Database        kwafoo-ai
     │                │                 │
     │── 扫描新数据 →   │                 │
     │   SELECT WHERE ai_processed=0    │
     │ ←─ 返回10条 ─   │                 │
     │                │                 │
     │── 提交到TaskQueue                │
     │                │                 │
     │── Worker消费任务                │
     │                │                 │
     │── Pipeline.Summarize ─────────→  │
     │                  ai.execute("summarize", ...)
     │ ←────────────────────────────────  │
     │   {comment, summary}              │
     │                │                 │
     │── Pipeline.Classify ──────────→  │
     │                  ai.execute("classify", ...)
     │ ←────────────────────────────────  │
     │   {categories, keywords}          │
     │                │                 │
     │── Pipeline.Score ─────────────→  │
     │                  ai.execute("score", ...)
     │ ←────────────────────────────────  │
     │   {relevance, importance}         │
     │                │                 │
     │── 结果落库 →      │                 │
     │   UPDATE ai_processed=1          │
     │                │                 │
     │── EventBus: task_completed       │

3. 手动触发阶段（用户在前端点"重新分析"）
   Frontend    API         Data-Processor    kwafoo-ai
     │          │              │                 │
     │── POST ─→│              │                 │
     │ /api/tasks/process      │                 │
     │          │── submit ──→  │                 │
     │ ←─ {task_id: "abc"}    │                 │
     │          │              │                 │
     │── WS: progress_update ←── EventBus        │
     │   {step: "classify"}    │                 │
     │   ...                   │                 │
     │── WS: task_completed ←── EventBus        │
     │          │              │                 │

4. 数据查询阶段
   Frontend    API         Database
     │          │              │
     │── GET ──→│              │
     │ /api/news               │
     │          │── SELECT ──→  │
     │          │ ←── 数据 ──   │
     │ ←── JSON │              │
     │ 渲染列表  │              │
```

---

> **文档版本**：v2.0
> **修订日期**：2026-05-30
> **修订内容**：从3个子项目方案扩展为5个子项目方案，新增kwafoo-crawler（爬虫独立）和kwafoo-data-processor（数据处理核心），增加kwafoo-ai配置驱动扩展详细设计