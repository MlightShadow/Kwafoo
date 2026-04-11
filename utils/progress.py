import time
import threading
from typing import Dict, Optional
from datetime import datetime, timedelta
from utils.logger import logger


class ProgressMonitor:
    _instance = None
    _tasks = {}
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start_task(self, task_id: str, task_name: str, total_steps: int = 0):
        with self._lock:
            self._tasks[task_id] = {
                'task_id': task_id,
                'task_name': task_name,
                'status': 'running',
                'progress': 0,
                'current_step': '',
                'total_steps': total_steps,
                'current_step_index': 0,
                'start_time': datetime.now(),
                'estimated_end_time': None
            }
        logger.info(f"任务开始: {task_name} (ID: {task_id})")
        return self._tasks[task_id]

    def update_progress(self, task_id: str, progress: int, message: str = ''):
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return
            
            task = self._tasks[task_id]
            task['progress'] = progress
            task['current_step'] = message
            task['current_step_index'] += 1
            
            if task['total_steps'] > 0:
                elapsed = (datetime.now() - task['start_time']).total_seconds()
                avg_time_per_step = elapsed / task['current_step_index']
                remaining_steps = task['total_steps'] - task['current_step_index']
                estimated_remaining = avg_time_per_step * remaining_steps
                task['estimated_end_time'] = datetime.now() + timedelta(seconds=estimated_remaining)
            
            logger.debug(f"任务进度: {task['task_name']} - {progress}% - {message}")

    def complete_task(self, task_id: str, success: bool = True, error_message: str = ''):
        with self._lock:
            if task_id not in self._tasks:
                logger.warning(f"任务不存在: {task_id}")
                return
            
            task = self._tasks[task_id]
            task['status'] = 'completed' if success else 'failed'
            task['progress'] = 100 if success else task['progress']
            
            if not success:
                task['error_message'] = error_message
                logger.error(f"任务失败: {task['task_name']} - {error_message}")
            else:
                logger.info(f"任务完成: {task['task_name']}")

    def get_task(self, task_id: str) -> Optional[Dict]:
        with self._lock:
            return self._tasks.get(task_id)

    def get_all_tasks(self) -> Dict:
        with self._lock:
            # 将 datetime 对象转换为字符串，以便 JSON 序列化
            tasks_copy = {}
            for task_id, task in self._tasks.items():
                task_copy = task.copy()
                # 转换 datetime 对象为 ISO 格式字符串
                if 'start_time' in task_copy and isinstance(task_copy['start_time'], datetime):
                    task_copy['start_time'] = task_copy['start_time'].isoformat()
                if 'estimated_end_time' in task_copy and isinstance(task_copy['estimated_end_time'], datetime):
                    task_copy['estimated_end_time'] = task_copy['estimated_end_time'].isoformat()
                tasks_copy[task_id] = task_copy
            return tasks_copy

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        with self._lock:
            current_time = datetime.now()
            tasks_to_remove = []
            
            for task_id, task in self._tasks.items():
                if task['status'] == 'completed':
                    age = (current_time - task['start_time']).total_seconds() / 3600
                    if age > max_age_hours:
                        tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
                logger.debug(f"清理旧任务: {task_id}")


progress_monitor = ProgressMonitor()