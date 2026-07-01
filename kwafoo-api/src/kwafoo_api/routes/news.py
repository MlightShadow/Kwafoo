import logging
from typing import Optional

from fastapi import APIRouter, HTTPException

from ..app import get_processor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def list_news(
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
):
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    try:
        items = processor.db.get_news_processed(limit=limit, offset=offset,
                                                 category=category or "", keyword=keyword or "")
        total = processor.db.count_news(category=category or "", keyword=keyword or "")

        serialized = [_serialize_news(item) for item in items]

        return {
            "data": serialized,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error("获取新闻列表失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{news_id}")
def get_news(news_id: int):
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    import sqlite3
    try:
        conn = sqlite3.connect(processor.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
        conn.close()

        if row is None:
            raise HTTPException(status_code=404, detail="新闻不存在")

        return _serialize_news(dict(row))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取新闻详情失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
def get_stats():
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    try:
        stats = processor.get_stats()
        return stats
    except Exception as e:
        logger.error("获取统计信息失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


def _serialize_news(item: dict) -> dict:
    import json
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


def _parse_json_field(value):
    import json
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    return []