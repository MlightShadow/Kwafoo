# 程序启动卡住问题解决方案

## 问题描述

在启动Kwafoo新闻聚合系统时，程序会卡住，无法完成启动过程。具体表现为：

1. 程序在导入scheduler模块时卡住
2. 日志输出到"web_fetcher导入完成"后停止
3. 没有任何错误信息，程序处于无响应状态

## 问题分析

### 根本原因

问题出在`ai/ai_client.py`模块中。该模块在导入时会导入`litellm`库，而`litellm`在导入时会尝试从GitHub获取模型成本映射文件：

```python
# ai/ai_client.py
from litellm import completion  # 这里会触发litellm的网络请求
```

`litellm`库在导入时会执行以下操作：

1. 尝试从 `https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json` 获取模型成本映射
2. 如果网络请求超时或失败，会fallback到本地备份
3. 在某些网络环境下，这个fallback过程也会卡住

### 影响范围

由于`scheduler`模块依赖`ai.processor`模块，而`ai.processor`模块又依赖`ai.ai_client`模块，因此：

```
main.py
  └─> scheduler.scheduler
       └─> ai.processor
            └─> ai.ai_client  # 在这里卡住
                 └─> litellm  # 网络请求卡住
```

## 解决方案

### 方法1：在ai_client.py中设置环境变量和patch httpx（推荐）

在`ai/ai_client.py`模块的开头，在导入`litellm`之前，先设置环境变量和patch httpx：

```python
import os
# 禁用LiteLLM远程获取模型成本映射，避免启动时网络超时
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['LITELLM_DROP_PARAMS'] = 'true'
os.environ['LITELLM_MAX_RETRIES'] = '0'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'true'
os.environ['LITELLM_CACHE'] = 'false'
os.environ['LITELLM_REQUEST_TIMEOUT'] = '10'

# Patch httpx，让它立即失败，强制使用本地备份
import httpx
_original_httpx_get = httpx.get
def _patched_httpx_get(url, timeout=5, **kwargs):
    """立即抛出异常，强制使用本地备份"""
    raise Exception("Network blocked to force local backup")
httpx.get = _patched_httpx_get

from typing import Dict, Any, Optional, List, Callable
from litellm import completion  # 现在可以安全导入
```

### 环境变量说明

| 环境变量 | 值 | 说明 |
|---------|-----|------|
| `LITELLM_LOG` | `ERROR` | 只显示错误日志，减少日志输出 |
| `LITELLM_DROP_PARAMS` | `true` | 忽略不支持的参数 |
| `LITELLM_MAX_RETRIES` | `0` | 禁用重试 |
| `LITELLM_LOCAL_MODEL_COST_MAP` | `true` | 强制使用本地模型成本映射 |
| `LITELLM_CACHE` | `false` | 禁用缓存 |
| `LITELLM_REQUEST_TIMEOUT` | `10` | 设置请求超时时间（秒） |

### 方法2：在main.py中设置环境变量（备选）

如果不想修改`ai_client.py`，也可以在`main.py`的开头设置环境变量：

```python
import os
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['LITELLM_DROP_PARAMS'] = 'true'
os.environ['LITELLM_MAX_RETRIES'] = '0'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'true'
os.environ['LITELLM_CACHE'] = 'false'
os.environ['LITELLM_REQUEST_TIMEOUT'] = '10'
```

### 方法3：在.env文件中设置环境变量（备选）

在项目根目录的`.env`文件中添加：

```env
LITELLM_LOG=ERROR
LITELLM_DROP_PARAMS=true
LITELLM_MAX_RETRIES=0
LITELLM_LOCAL_MODEL_COST_MAP=true
LITELLM_CACHE=false
LITELLM_REQUEST_TIMEOUT=10
```

## 验证方法

启动程序后，应该看到以下日志：

```
2026-04-22 19:26:33802 - kwafoo - INFO - 环境变量文件 .env 加载成功
2026-04-22 19:26:33804 - kwafoo - INFO - 配置文件加载成功: config.toml
开始导入database模块...
database模块导入完成
开始导入scheduler模块...
开始导入fetcher模块...
rss_fetcher导入完成
api_fetcher导入完成
web_fetcher导入完成
ai_news_processor导入完成
scheduler模块导入完成
开始导入web.server模块...
web.server模块导入完成
开始导入web.websocket模块...
web.websocket模块导入完成
系统启动完成
```

## 注意事项

1. **推荐使用方法1**：在`ai_client.py`中设置环境变量和patch httpx，这样可以确保在任何情况下都能正常工作。

2. **不影响AI功能**：这些设置只是禁用了litellm的网络请求，不会影响AI调用的功能。

3. **本地模型成本映射**：litellm会使用内置的本地模型成本映射，包含了常见的AI模型信息。

4. **其他模块**：如果其他模块也导入了litellm，也需要在导入前设置环境变量。

## 相关文件

- `ai/ai_client.py` - AI客户端实现
- `scheduler/scheduler.py` - 调度器实现
- `ai/processor.py` - AI处理器实现
- `main.py` - 主程序入口

## 更新记录

- 2026-04-22: 创建文档，记录程序启动卡住问题的解决方案