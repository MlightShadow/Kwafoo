# 调度模块设计

## 模块概述

调度模块负责任务调度、进度监控和队列管理。模块支持定时任务、手动触发、并发处理、实时进度更新等功能，确保系统的稳定运行和高效处理。

## 核心功能

### 1. 任务调度

**技术选型：**
- 使用`schedule`库实现定时任务
- 使用`threading`实现异步执行
- 使用`ThreadPoolExecutor`实现并发处理

**调度类型：**

**定时任务：**
- 自动抓取新闻（可配置间隔）
- 自动AI处理（可配置间隔）
- 抓取完成后自动AI处理（可选）

**手动触发：**
- 手动抓取新闻
- 手动AI处理
- 手动重新分析新闻

**配置参数：**
```toml
[scheduler]
fetch_interval = 1800              # 抓取间隔（秒），默认30分钟
ai_process_interval = 600         # AI处理间隔（秒），默认10分钟
auto_fetch = false                # 是否自动抓取
auto_ai_process = false           # 是否自动AI处理
auto_ai_after_fetch = false       # 抓取完成后是否自动AI处理
max_fetch_workers = 20            # 最大抓取并发数
```

**任务状态管理：**
- `fetching`：抓取任务运行状态
- `ai_processing`：AI处理任务运行状态
- 使用线程锁保护状态

### 2. 新闻抓取调度

**抓取流程：**
1. 生成任务ID
2. 启动进度监控
3. 并发抓取所有源（RSS、API、网页）
4. 保存新闻到数据库
5. 更新进度
6. 完成任务

**并发控制：**
- 使用`ThreadPoolExecutor`实现并发抓取
- 限制最大并发数（`max_fetch_workers`）
- 每个源独立抓取，互不影响

**进度监控：**
- 实时更新抓取进度
- 记录每个源的抓取结果
- 计算总体进度百分比

**错误处理：**
- 单个源失败不影响其他源
- 记录详细的错误日志
- 返回抓取结果统计

### 3. AI处理调度

**处理流程：**

**自动处理：**
1. 获取所有未处理的新闻
2. 添加到AI队列
3. 启动队列处理器
4. 处理队列中的新闻

**手动处理：**
1. 获取所有新闻或指定新闻
2. 添加到AI队列（高优先级）
3. 启动队列处理器
4. 处理队列中的新闻

**队列管理：**
- 支持优先级队列
- 支持任务类型（分类、摘要、全部）
- 支持取消任务
- 支持重新分析

**队列处理器：**
- 后台线程持续运行
- 从队列中获取任务
- 调用AI处理器处理
- 更新处理状态
- 实时广播进度

### 4. 进度监控

**技术选型：**
- 单例模式
- 线程安全
- WebSocket实时广播

**监控功能：**
- 任务开始/完成
- 进度更新
- 错误报告
- 预计完成时间

**任务信息：**
```python
{
    'task_id': '任务ID',
    'task_name': '任务名称',
    'status': 'running/completed/failed',
    'progress': 0-100,
    'current_step': '当前步骤',
    'total_steps': '总步骤数',
    'current_step_index': '当前步骤索引',
    'start_time': '开始时间',
    'estimated_end_time': '预计完成时间'
}
```

**WebSocket广播：**
- 任务开始：`task_started`
- 进度更新：`progress_update`
- 任务完成：`task_completed`
- 任务失败：`task_failed`

**启用WebSocket：**
```python
from utils.progress import progress_monitor

def ws_broadcast(message):
    # WebSocket广播实现
    pass

progress_monitor.enable_websocket(ws_broadcast)
```

### 5. 配置热更新

**配置观察者模式：**
- 调度器实现`ConfigObserver`接口
- 配置更新时自动重新设置定时任务
- 支持动态调整参数

**配置更新流程：**
1. 配置文件修改
2. 配置管理器检测到变化
3. 通知所有观察者
4. 调度器更新配置
5. 重新设置定时任务

## 数据库设计

### ai_queue表（AI处理队列表）

```sql
CREATE TABLE ai_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news_id INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    error_message TEXT,
    FOREIGN KEY (news_id) REFERENCES news(id)
);
```

**字段说明：**
- `news_id`：新闻ID
- `task_type`：任务类型（'classify', 'summarize', 'all'）
- `priority`：优先级（0=普通，1=高）
- `status`：状态（'pending', 'processing', 'completed', 'failed'）
- `created_at`：创建时间
- `processed_at`：处理时间
- `error_message`：错误消息

## API接口

### 获取任务状态
```
GET /api/scheduler/status
```

**响应：**
```json
{
  "success": true,
  "data": {
    "fetching": false,
    "ai_processing": false,
    "tasks": [...]
  }
}
```

### 手动抓取新闻
```
POST /api/scheduler/fetch
```

**响应：**
```json
{
  "success": true,
  "message": "抓取任务已启动",
  "task_id": "fetch_20260417_120000"
}
```

### 手动AI处理
```
POST /api/scheduler/process-ai
```

**请求参数：**
```json
{
  "news_id": 123,
  "task_type": "all"
}
```

**响应：**
```json
{
  "success": true,
  "message": "AI处理任务已启动"
}
```

### 获取任务列表
```
GET /api/scheduler/tasks
```

**响应：**
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "fetch_20260417_120000",
        "task_name": "抓取新闻",
        "status": "running",
        "progress": 50,
        "current_step": "正在抓取RSS源..."
      }
    ]
  }
}
```

## 性能优化

### 并发控制
- 限制最大并发数
- 使用线程池管理
- 避免资源竞争

### 任务队列
- 使用优先级队列
- 支持任务取消
- 避免重复任务

### 进度监控
- 异步广播进度
- 避免阻塞主线程
- 限制广播频率

### 错误处理
- 单个任务失败不影响其他任务
- 记录详细错误日志
- 支持任务重试

## 错误处理

### 抓取错误
- 单个源失败不影响其他源
- 记录详细的错误信息
- 返回抓取结果统计

### AI处理错误
- 单条新闻失败不影响其他新闻
- 记录错误消息到队列
- 支持重新处理

### 队列处理错误
- 捕获所有异常
- 记录错误日志
- 继续处理下一个任务

## 代码引用

### 调度器
[scheduler/scheduler.py](../../scheduler/scheduler.py) - 调度器实现

### 进度监控
[utils/progress.py](../../utils/progress.py) - 进度监控实现

### AI处理器
[ai/processor.py](../../ai/processor.py) - AI处理器实现

## 依赖库

- `schedule` - 定时任务
- `threading` - 线程
- `concurrent.futures` - 线程池
- `time` - 时间处理
- `datetime` - 日期时间

## 注意事项

1. **线程安全**：使用锁保护共享状态
2. **资源管理**：合理设置并发数，避免资源耗尽
3. **错误处理**：完善的错误处理，避免任务失败影响系统
4. **进度监控**：实时更新进度，提供良好的用户体验
5. **配置热更新**：支持配置热更新，无需重启系统
6. **任务队列**：使用队列管理任务，避免任务丢失
7. **WebSocket广播**：注意WebSocket连接状态，避免广播失败
8. **性能监控**：监控任务执行时间，及时优化性能