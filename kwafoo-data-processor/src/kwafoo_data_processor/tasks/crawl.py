import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class CrawlTask:
    def __init__(self, crawler_engine, db):
        self.crawler = crawler_engine
        self.db = db

    def execute(self, source_name: Optional[str] = None) -> Dict[str, Any]:
        try:
            if source_name:
                result = self.crawler.crawl_source(source_name)
            else:
                result = self.crawler.crawl_all()

            return {
                "total_fetched": result.total_fetched,
                "success_count": result.success_count,
                "fail_count": result.fail_count,
                "errors": result.errors,
            }
        except Exception as e:
            logger.error("爬虫任务失败: %s", e)
            return {"total_fetched": 0, "success_count": 0, "fail_count": 1, "errors": [str(e)]}