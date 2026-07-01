import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, processor):
        self._processor = processor

    def trigger_crawl(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        processor = self._processor
        if processor._crawl is None:
            return {"status": "error", "message": "爬虫任务未初始化"}
        processor.crawl_pipeline()
        return {"status": "accepted", "message": "爬虫任务已提交"}

    def trigger_process(self) -> Dict[str, Any]:
        unprocessed = self._processor.db.get_unprocessed(limit=0)
        if not unprocessed:
            return {"status": "accepted", "message": "无待处理数据"}
        task_id = self._processor.submit_process_task(
            [n["id"] for n in self._processor.db.get_unprocessed(limit=50)],
        )
        return {"status": "accepted", "message": "处理任务已提交", "task_id": task_id}

    def trigger_pipeline(self) -> Dict[str, Any]:
        self._processor.crawl_pipeline()
        unprocessed = self._processor.db.get_unprocessed(limit=50)
        if unprocessed:
            self._processor.submit_process_task([n["id"] for n in unprocessed])
        return {"status": "accepted", "message": "全管道任务已提交"}

    def get_status(self) -> Dict[str, Any]:
        return self._processor.get_stats()

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._processor.get_task_status(task_id)

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        return self._processor.get_active_tasks()