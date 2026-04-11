# 优化变更记录

本文档记录 Kwafoo 项目的重要重构、优化和功能变更。

---

## 2026-04-11

### API模块化改造

**问题**：`web/server.py` 文件过大，所有API处理逻辑集中在一个类中。

**方案**：拆分为独立模块

```
web/
├── api/
│   ├── __init__.py
│   ├── base.py           # 基础API处理器
│   ├── news_api.py      # 新闻API
│   ├── chat_api.py      # 聊天API
│   ├── config_api.py    # 配置API
│   ├── ai_api.py        # AI处理API
│   └── system_api.py    # 系统API
├── server.py            # HTTP服务器（简化）
└── websocket.py        # WebSocket服务器
```

---

### WebSocket实时通信

**问题**：前端使用轮询方式获取任务进度，效率低下。

**方案**：新增WebSocket支持

- 新增 `web/websocket.py` - WebSocket服务器
- 新增 `utils/progress.py` - 进度监控器（集成WebSocket广播）
- 前端使用 `useWebSocket.ts` - WebSocket客户端Composables

**效果**：
- 服务器主动推送，实时性大幅提升
- 减少服务器负载

---

### 前端Composables重构

**问题**：前端代码组织不够优雅，逻辑分散。

**方案**：新增Vue 3组合式函数

```
web/frontend/src/composables/
├── useWebSocket.ts      # WebSocket管理
├── useNews.ts           # 新闻管理
└── useChat.ts           # 聊天管理
```

---

### 前端界面优化

**功能**：
- 页面全屏显示，充分利用屏幕空间
- 新闻网格布局，每行显示2条
- 智能摘要管理，长度限制140字
- 优先展示AI摘要
- 顶部工具栏设计

---

### 异常处理改进

**问题**：多处代码使用空的 `except:` 块，隐藏错误。

**方案**：统一改进异常捕获，记录详细错误信息

```python
# 修改前
except:
    pass

# 修改后
except Exception as e:
    logger.error(f"操作失败: {e}", exc_info=True)
```

---

### 配置文件统一

**问题**：同时存在 `config.toml` 和 `config.json`。

**方案**：统一使用 `config.toml`，删除JSON配置文件

---

### CSS文件编码修复

**问题**：`web/css/style.css` 存在编码损坏的注释。

**方案**：删除损坏的注释内容

---

## AI处理系统

### 串行处理架构

Kwafoo采用单线程串行处理新闻，避免并发冲突：

```python
[ai]
max_workers = 1      # 串行处理
batch_size = 1       # 单条处理
```

### 核心功能

1. **状态跟踪**：使用 `ai_processed` 字段标记处理状态
2. **智能分类**：AI自动识别新闻分类
3. **摘要生成**：AI生成新闻摘要
4. **降级策略**：AI服务不可用时优雅降级

### 处理流程

```
定时抓取 → 存入数据库(ai_processed=0) → 定时检查未处理 → 
AI串行处理(分类+摘要) → 更新状态(ai_processed=1)
```

---

## 技术选型

### 为什么使用OpenAI SDK？

- 轻量级，专注于API调用
- 性能更好，开销更小
- 代码简洁，易于维护

### 为什么不用LangChain？

- 过于复杂，引入不必要的抽象层
- 对于简单的LLM调用场景，OpenAI SDK已足够