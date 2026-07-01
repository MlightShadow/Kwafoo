import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ProcessorDB:
    def __init__(self, db_path: str = "data/crawler.db"):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_unprocessed(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM news
                   WHERE ai_processed = 0 AND is_deleted = 0
                   LIMIT ?""",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_processed(self, news_id: int, data: Dict[str, Any]) -> None:
        with self._get_conn() as conn:
            conn.execute(
                """UPDATE news SET
                   ai_processed = 1, category = ?, keywords = ?,
                   ai_summary = ?, ai_comment = ?, ai_summary_en = ?,
                   relevance_score = ?, importance_score = ?, source_score = ?
                   WHERE id = ?""",
                (
                    json.dumps(data.get("categories", []), ensure_ascii=False),
                    json.dumps(data.get("keywords", []), ensure_ascii=False),
                    data.get("ai_summary", ""),
                    data.get("ai_comment", ""),
                    data.get("ai_summary_en", ""),
                    data.get("relevance_score", 0),
                    data.get("importance_score", 0),
                    data.get("source_score", 0),
                    news_id,
                ),
            )
            conn.commit()

    def get_news_between(self, start: str, end: str) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM news
                   WHERE publish_time BETWEEN ? AND ?
                   AND is_deleted = 0
                   ORDER BY publish_time DESC""",
                (start, end),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_news_processed(self, limit: int = 50, offset: int = 0,
                           category: str = "", keyword: str = "") -> List[Dict[str, Any]]:
        conditions = ["ai_processed = 1", "is_deleted = 0"]
        params: List[Any] = []

        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        if keyword:
            conditions.append("keywords LIKE ?")
            params.append(f"%{keyword}%")

        where = " AND ".join(conditions)
        with self._get_conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM news WHERE {where} ORDER BY publish_time DESC LIMIT ? OFFSET ?",
                (*params, limit, offset),
            ).fetchall()
            return [dict(r) for r in rows]

    def count_news(self, category: str = "", keyword: str = "") -> int:
        conditions = ["ai_processed = 1", "is_deleted = 0"]
        params: List[Any] = []

        if category:
            conditions.append("category LIKE ?")
            params.append(f"%{category}%")
        if keyword:
            conditions.append("keywords LIKE ?")
            params.append(f"%{keyword}%")

        where = " AND ".join(conditions)
        with self._get_conn() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM news WHERE {where}", params
            ).fetchone()
            return row["cnt"] if row else 0

    def batch_update_raw(self, news_list: List[Dict[str, Any]]) -> None:
        with self._get_conn() as conn:
            for item in news_list:
                conn.execute(
                    """INSERT OR IGNORE INTO news
                       (title, description, url, source, source_url,
                        publish_time, fetch_time, image_url, category_from_source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.get("title", ""),
                        item.get("description", ""),
                        item.get("url", ""),
                        item.get("source", ""),
                        item.get("source_url", ""),
                        item.get("publish_time", ""),
                        item.get("fetch_time", ""),
                        item.get("image_url", ""),
                        item.get("category_from_source", ""),
                    ),
                )
            conn.commit()