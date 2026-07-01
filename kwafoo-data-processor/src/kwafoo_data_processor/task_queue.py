import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskRecord:
    task_id: str
    task_type: str
    state: TaskState
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    progress_msg: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "state": self.state.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "progress_msg": self.progress_msg,
        }


class TaskQueue:
    def __init__(self, max_workers: int = 3):
        self._queue: queue.Queue = queue.Queue()
        self._registry: Dict[str, TaskRecord] = {}
        self._lock = threading.Lock()
        self._max_workers = max_workers
        self._workers: List[threading.Thread] = []
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        for i in range(self._max_workers):
            t = threading.Thread(target=self._worker_loop, name=f"task-worker-{i}", daemon=True)
            t.start()
            self._workers.append(t)
        logger.info("TaskQueue已启动，workers=%d", self._max_workers)

    def shutdown(self) -> None:
        self._running = False
        for _ in self._workers:
            self._queue.put(None)
        for t in self._workers:
            t.join(timeout=5.0)
        self._workers.clear()
        logger.info("TaskQueue已关闭")

    def submit(self, task_type: str, func: Callable, args: tuple = (),
               kwargs: Dict[str, Any] = None,
               on_complete: Callable = None,
               task_id: Optional[str] = None) -> str:
        if task_id is None:
            task_id = f"task_{uuid4().hex[:12]}"
        record = TaskRecord(
            task_id=task_id,
            task_type=task_type,
            state=TaskState.PENDING,
            created_at=time.time(),
        )
        with self._lock:
            self._registry[task_id] = record

        self._queue.put((task_id, task_type, func, args, kwargs or {}, on_complete))
        logger.info("任务已提交: %s (%s)", task_id, task_type)
        return task_id

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            record = self._registry.get(task_id)
        if record is None:
            return None
        return record.to_dict()

    def get_active(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                r.to_dict() for r in self._registry.values()
                if r.state in (TaskState.PENDING, TaskState.RUNNING)
            ]

    def get_all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [r.to_dict() for r in self._registry.values()]

    def update_progress(self, task_id: str, progress: float, msg: str = "") -> None:
        with self._lock:
            record = self._registry.get(task_id)
            if record:
                record.progress = progress
                record.progress_msg = msg

    def _worker_loop(self) -> None:
        while self._running:
            try:
                item = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if item is None:
                break

            task_id, task_type, func, args, kwargs, on_complete = item

            with self._lock:
                record = self._registry.get(task_id)
                if record:
                    record.state = TaskState.RUNNING
                    record.started_at = time.time()

            try:
                result = func(*args, **kwargs)
                with self._lock:
                    record = self._registry.get(task_id)
                    if record:
                        record.state = TaskState.COMPLETED
                        record.completed_at = time.time()
                        record.result = result if isinstance(result, dict) else {"data": str(result)}
                if on_complete:
                    try:
                        on_complete(task_id, result)
                    except Exception:
                        pass
            except Exception as e:
                logger.error("任务执行失败: %s - %s", task_id, e)
                with self._lock:
                    record = self._registry.get(task_id)
                    if record:
                        record.state = TaskState.FAILED
                        record.completed_at = time.time()
                        record.error = str(e)
                if on_complete:
                    try:
                        on_complete(task_id, None)
                    except Exception:
                        pass
            finally:
                self._queue.task_done()