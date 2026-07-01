import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self):
        self._scheduler = BackgroundScheduler(daemon=True)
        self._jobs: Dict[str, dict] = {}

    def add_interval_job(self, job_id: str, func: Callable, seconds: int = 3600,
                         args: tuple = (), kwargs: Dict[str, Any] = None) -> None:
        job = self._scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            args=args,
            kwargs=kwargs or {},
            replace_existing=True,
        )
        self._jobs[job_id] = {"job": job, "type": "interval", "seconds": seconds}
        logger.info("已添加定时任务: %s (每%d秒)", job_id, seconds)

    def add_cron_job(self, job_id: str, func: Callable, cron_expr: str = "0 */6 * * *",
                     args: tuple = (), kwargs: Dict[str, Any] = None) -> None:
        parts = cron_expr.split()
        cron_fields = ["minute", "hour", "day", "month", "day_of_week"]
        cron_kwargs = {}
        for i, part in enumerate(parts):
            if i < len(cron_fields):
                cron_kwargs[cron_fields[i]] = part

        job = self._scheduler.add_job(
            func,
            trigger=CronTrigger(**cron_kwargs),
            id=job_id,
            args=args,
            kwargs=kwargs or {},
            replace_existing=True,
        )
        self._jobs[job_id] = {"job": job, "type": "cron", "cron": cron_expr}
        logger.info("已添加Cron任务: %s (%s)", job_id, cron_expr)

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            self._scheduler.remove_job(job_id)
            del self._jobs[job_id]
            return True
        return False

    def list_jobs(self) -> List[dict]:
        return [{"id": k, "type": v["type"]} for k, v in self._jobs.items()]

    def start(self) -> None:
        self._scheduler.start()
        logger.info("调度器已启动")

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=True)
        logger.info("调度器已关闭")

    @property
    def running(self) -> bool:
        return self._scheduler.running