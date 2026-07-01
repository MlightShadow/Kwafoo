import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

from .db import ProcessorDB
from .event import EventBus, EventType
from .scheduler import TaskScheduler
from .task_queue import TaskQueue
from .tasks.classify import ClassifyTask
from .tasks.summarize import SummarizeTask
from .tasks.score import ScoreTask
from .tasks.report import ReportTask
from .tasks.crawl import CrawlTask

logger = logging.getLogger(__name__)


class ProcessorEngine:
    def __init__(self, config_path: str = "config/processor_config.toml"):
        self._config = self._load_config(config_path)
        self._load_params()

        self.db = ProcessorDB(self.db_path)
        self.event_bus = EventBus.get_instance()
        self.scheduler = TaskScheduler()
        self.task_queue = TaskQueue()

        self._ai_engine = None
        self._crawler_engine = None

        self._classify = None
        self._summarize = None
        self._score = None
        self._report = None
        self._crawl = None

        self._pipeline_running = False
        self._pipeline_lock = threading.Lock()

        if self._config:
            self._init_engines()
            self._init_tasks()
            self._setup_scheduled_tasks()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        if not os.path.exists(config_path):
            return {}
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        with open(config_path, "rb") as f:
            return tomllib.load(f)

    def _load_params(self) -> None:
        p = self._config.get("processor", {})
        self.db_path = p.get("db_path", "data/crawler.db")
        self.batch_size = p.get("batch_size", 10)
        self.pipeline_interval = p.get("pipeline_interval", 3600)
        self.max_scoring_retries = p.get("max_scoring_retries", 3)
        self.crawler_config_path = p.get("crawler_config_path", "config/crawler_config.toml")
        self.ai_config_path = p.get("ai_config_path", "config/ai_config.toml")

    def _init_engines(self) -> None:
        try:
            from kwafoo_ai import AIEngine
            self._ai_engine = AIEngine(
                config_path=self.ai_config_path,
                tasks_dir="tasks",
            )
            logger.info("AI引擎初始化完成")
        except Exception as e:
            logger.warning("AI引擎初始化失败: %s", e)

        try:
            from kwafoo_crawler import CrawlerEngine
            self._crawler_engine = CrawlerEngine(
                config_path=self.crawler_config_path,
            )
            logger.info("爬虫引擎初始化完成")
        except Exception as e:
            logger.warning("爬虫引擎初始化失败: %s", e)

    def _init_tasks(self) -> None:
        categories = self._config.get("apple", {}).get("categories", [])
        category_names = [c.get("name", "") for c in categories if c.get("name")]

        if self._ai_engine:
            self._classify = ClassifyTask(self._ai_engine, category_names)
            self._summarize = SummarizeTask(self._ai_engine)
            self._score = ScoreTask(self._ai_engine)
            self._report = ReportTask(self._ai_engine, self.db)

        if self._crawler_engine:
            self._crawl = CrawlTask(self._crawler_engine, self.db)

    def _setup_scheduled_tasks(self) -> None:
        s = self._config.get("scheduler", {})

        if s.get("enable_crawl", False) and self._crawl:
            self.scheduler.add_interval_job(
                "scheduled_crawl", self.crawl_pipeline,
                seconds=s.get("crawl_interval", 3600),
            )

        if s.get("enable_process", False):
            self.scheduler.add_interval_job(
                "scheduled_process", self.process_pipeline,
                seconds=s.get("process_interval", 600),
            )

        if s.get("enable_daily_report", False):
            self.scheduler.add_cron_job(
                "daily_report", self.generate_daily_report,
                cron_expr=s.get("daily_report_cron", "0 8 * * *"),
            )

        if s.get("enable_weekly_report", False):
            self.scheduler.add_cron_job(
                "weekly_report", self.generate_weekly_report,
                cron_expr=s.get("weekly_report_cron", "0 9 * * 0"),
            )

    def start(self) -> None:
        self.scheduler.start()
        self.task_queue.start()
        logger.info("数据处理引擎已启动")

    def shutdown(self) -> None:
        self.scheduler.shutdown()
        self.task_queue.shutdown()
        logger.info("数据处理引擎已关闭")

    def crawl_pipeline(self) -> Dict[str, Any]:
        self.event_bus.emit_type(EventType.CRAWL_START)
        try:
            if self._crawl is None:
                self.event_bus.emit_type(EventType.CRAWL_ERROR, {"error": "爬虫任务未初始化"})
                return {"error": "爬虫任务未初始化"}

            result = self._crawl.execute()
            self.event_bus.emit_type(EventType.CRAWL_COMPLETE, result)
            logger.info("爬虫管道完成: %d条", result.get("success_count", 0))
            return result
        except Exception as e:
            logger.error("爬虫管道异常: %s", e)
            self.event_bus.emit_type(EventType.CRAWL_ERROR, {"error": str(e)})
            return {"error": str(e)}

    def process_pipeline(self) -> Dict[str, Any]:
        with self._pipeline_lock:
            if self._pipeline_running:
                return {"status": "already_running"}

            self._pipeline_running = True
            self.event_bus.emit_type(EventType.PIPELINE_START)

            try:
                stats = {"classify": 0, "summarize": 0, "score": 0, "total": 0, "errors": []}

                news_list = self.db.get_unprocessed(self.batch_size)
                stats["total"] = len(news_list)
                logger.info("管道处理开始: %d条未处理新闻", stats["total"])

                for news_item in news_list:
                    try:
                        processed_data = self._process_single(news_item, stats)
                        self.db.update_processed(news_item["id"], processed_data)
                    except Exception as e:
                        stats["errors"].append(f"{news_item.get('title', 'unknown')}: {e}")
                        logger.error("处理新闻失败: %s - %s", news_item.get("title"), e)

                self.event_bus.emit_type(EventType.PIPELINE_COMPLETE, stats)
                logger.info("管道处理完成: %s", stats)
                return stats
            except Exception as e:
                self.event_bus.emit_type(EventType.TASK_ERROR, {"error": str(e)})
                return {"error": str(e)}
            finally:
                self._pipeline_running = False

    def _process_single(self, news_item: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
        title = news_item.get("title", "")
        description = news_item.get("description", "")

        result = {
            "categories": [],
            "keywords": [],
            "ai_summary": "",
            "ai_comment": "",
            "ai_summary_en": "",
            "relevance_score": 0,
            "importance_score": 0,
            "source_score": 0,
        }

        if self._classify:
            self.event_bus.emit_type(EventType.CLASSIFY_START, {"title": title})
            cls_result = self._classify.execute(title, description)
            result["categories"] = cls_result.get("categories", [])
            result["keywords"] = cls_result.get("keywords", [])
            stats["classify"] += 1

        if self._summarize and (description or news_item.get("content")):
            content = news_item.get("content") or description
            self.event_bus.emit_type(EventType.SUMMARIZE_START, {"title": title})
            sum_result = self._summarize.execute(content, title=title)
            result["ai_summary"] = sum_result.get("summary", "")
            result["ai_comment"] = sum_result.get("comment", "")
            result["ai_summary_en"] = sum_result.get("summary_en", "")
            stats["summarize"] += 1

        if self._score:
            self.event_bus.emit_type(EventType.SCORE_START, {"title": title})
            cat = ", ".join(result.get("categories", []))
            score_result = self._score.execute(
                title=title,
                summary=result.get("ai_summary", description),
                category=cat,
                source_score=0,
            )
            result["relevance_score"] = score_result.get("relevance", 0)
            result["importance_score"] = score_result.get("importance", 0)
            result["source_score"] = score_result.get("source_score", 0)
            stats["score"] += 1

        return result

    def generate_daily_report(self) -> Dict[str, Any]:
        if self._report is None:
            return {"error": "报告任务未初始化"}
        self.event_bus.emit_type(EventType.REPORT_START, {"type": "daily"})
        report = self._report.generate("daily")
        self.event_bus.emit_type(EventType.REPORT_COMPLETE, report)
        return report

    def generate_weekly_report(self) -> Dict[str, Any]:
        if self._report is None:
            return {"error": "报告任务未初始化"}
        self.event_bus.emit_type(EventType.REPORT_START, {"type": "weekly"})
        report = self._report.generate("weekly")
        self.event_bus.emit_type(EventType.REPORT_COMPLETE, report)
        return report

    def get_stats(self) -> Dict[str, Any]:
        return {
            "unprocessed_count": len(self.db.get_unprocessed(limit=0)),
            "total_count": self.db.count_news(),
            "scheduler_jobs": self.scheduler.list_jobs(),
            "pipeline_running": self._pipeline_running,
            "active_tasks": self.task_queue.get_active(),
        }

    def submit_process_task(self, news_ids: List[int], task_type: str = "all") -> str:
        from uuid import uuid4
        task_id = f"task_{uuid4().hex[:12]}"
        self.task_queue.submit(
            task_type=f"process_{task_type}",
            func=self._process_by_ids,
            args=(news_ids, task_type),
            kwargs={"_task_id": task_id},
            on_complete=self._on_task_complete,
            task_id=task_id,
        )
        self.event_bus.emit_type(EventType.TASK_PROGRESS, {
            "task_id": task_id,
            "type": task_type,
            "news_ids": news_ids,
        })
        return task_id

    def submit_batch_process(self, news_ids: List[int]) -> str:
        return self.submit_process_task(news_ids, task_type="all")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.task_queue.get_status(task_id)

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        return self.task_queue.get_active()

    def _process_by_ids(self, news_ids: List[int], task_type: str, _task_id: str = "") -> Dict[str, Any]:
        stats = {"classify": 0, "summarize": 0, "score": 0, "total": 0, "errors": []}
        total = len(news_ids)

        for i, news_id in enumerate(news_ids):
            self.task_queue.update_progress(
                task_id=_task_id, progress=(i + 1) / total if total > 0 else 0,
                msg=f"处理中 {i + 1}/{total}",
            )

            import sqlite3
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
                conn.close()
                if row is None:
                    continue
                news_item = dict(row)
            except Exception as e:
                stats["errors"].append(f"news_id={news_id}: {e}")
                continue

            try:
                processed_data = self._process_single(news_item, stats)
                self.db.update_processed(news_id, processed_data)
            except Exception as e:
                stats["errors"].append(f"{news_item.get('title', 'unknown')}: {e}")

        stats["total"] = total
        return stats

    def _on_task_complete(self, task_id: str, result: Any) -> None:
        if result and isinstance(result, dict) and "error" not in str(result):
            self.event_bus.emit_type(EventType.PIPELINE_COMPLETE, {
                "task_id": task_id,
                "result": result,
            })
        else:
            self.event_bus.emit_type(EventType.TASK_ERROR, {
                "task_id": task_id,
                "error": str(result) if result else "unknown",
            })