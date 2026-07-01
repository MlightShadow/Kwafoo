import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReportTask:
    def __init__(self, ai_engine, db):
        self.ai = ai_engine
        self.db = db

    def generate(self, report_type: str = "daily",
                 custom_instruction: str = "") -> Dict[str, Any]:
        now = datetime.now()
        if report_type == "daily":
            start = (now - timedelta(days=1)).strftime("%Y-%m-%d") + "T00:00:00"
        elif report_type == "weekly":
            start = (now - timedelta(days=7)).strftime("%Y-%m-%d") + "T00:00:00"
        else:
            start = (now - timedelta(days=30)).strftime("%Y-%m-%d") + "T00:00:00"

        end = now.strftime("%Y-%m-%d") + "T23:59:59"

        news_list = self.db.get_news_between(start, end)
        if not news_list:
            return {"report": "", "highlights": []}

        news_items = [
            {
                "title": n.get("title", ""),
                "summary": n.get("ai_summary", ""),
                "category": n.get("category", ""),
                "score": n.get("relevance_score", 0),
            }
            for n in news_list[:50]
        ]

        result = self.ai.execute(
            "report",
            news_list=json.dumps(news_items, ensure_ascii=False, indent=2),
            report_type=report_type,
            custom_instruction=custom_instruction,
        )

        if result.success and result.data:
            return result.data

        logger.warning("报告生成失败: %s", result.error)
        return {"report": "", "highlights": []}