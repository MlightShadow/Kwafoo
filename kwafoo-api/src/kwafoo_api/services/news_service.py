import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self, processor):
        self._processor = processor

    def list_news(self, limit: int = 20, offset: int = 0,
                  category: str = "", keyword: str = "") -> Dict[str, Any]:
        db = self._processor.db
        items = db.get_news_processed(limit=limit, offset=offset,
                                       category=category, keyword=keyword)
        total = db.count_news(category=category, keyword=keyword)
        return {
            "data": [_serialize_news(item) for item in items],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_news(self, news_id: int) -> Optional[Dict[str, Any]]:
        import sqlite3
        try:
            conn = sqlite3.connect(self._processor.db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
            conn.close()
            if row is None:
                return None
            return _serialize_news(dict(row))
        except Exception as e:
            logger.error("获取新闻详情失败: %s", e)
            return None


def _serialize_news(item: dict) -> dict:
    result = {
        "id": item.get("id"),
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "url": item.get("url", ""),
        "source": item.get("source", ""),
        "publish_time": item.get("publish_time", ""),
        "fetch_time": item.get("fetch_time", ""),
        "image_url": item.get("image_url", ""),
        "category_from_source": item.get("category_from_source", ""),
        "is_read": bool(item.get("is_read", 0)),
        "category": _parse_json_field(item.get("category", "[]")),
        "keywords": _parse_json_field(item.get("keywords", "[]")),
        "ai_summary": item.get("ai_summary", ""),
        "ai_comment": item.get("ai_comment", ""),
        "ai_summary_en": item.get("ai_summary_en", ""),
        "relevance_score": item.get("relevance_score", 0),
        "importance_score": item.get("importance_score", 0),
        "source_score": item.get("source_score", 0),
    }
    return result


def _parse_json_field(value: str) -> Any:
    if not value:
        return []
    try:
        return json.loads(value) if isinstance(value, str) else value
    except (json.JSONDecodeError, TypeError):
        return value