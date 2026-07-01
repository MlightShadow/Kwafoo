import logging
import os
import sqlite3
from typing import Any, Dict, List

from .base import StorageBackend

logger = logging.getLogger(__name__)

CREATE_NEWS_TABLE = """
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    content TEXT DEFAULT '',
    url TEXT UNIQUE NOT NULL,
    source TEXT DEFAULT '',
    source_url TEXT DEFAULT '',
    publish_time TEXT DEFAULT '',
    fetch_time TEXT DEFAULT '',
    image_url TEXT DEFAULT '',
    category_from_source TEXT DEFAULT '',
    raw_data TEXT DEFAULT '{}',
    ai_processed INTEGER DEFAULT 0,
    is_deleted INTEGER DEFAULT 0,
    is_read INTEGER DEFAULT 0,
    category TEXT DEFAULT '',
    keywords TEXT DEFAULT '[]',
    ai_summary TEXT DEFAULT '',
    ai_comment TEXT DEFAULT '',
    ai_summary_en TEXT DEFAULT '',
    relevance_score REAL DEFAULT 0,
    importance_score REAL DEFAULT 0,
    source_score REAL DEFAULT 0,
    read_count INTEGER DEFAULT 0
)
"""


class SQLiteStorage(StorageBackend):
    def __init__(self, db_path: str = "data/crawler.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(CREATE_NEWS_TABLE)
            conn.commit()

    def insert(self, news_data: Dict[str, Any]) -> int:
        with self._get_conn() as conn:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO news
                   (title, description, content, url, source, source_url,
                    publish_time, fetch_time, image_url, category_from_source, raw_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    news_data.get("title", ""),
                    news_data.get("description", ""),
                    news_data.get("content", ""),
                    news_data.get("url", ""),
                    news_data.get("source", ""),
                    news_data.get("source_url", ""),
                    news_data.get("publish_time", ""),
                    news_data.get("fetch_time", ""),
                    news_data.get("image_url", ""),
                    news_data.get("category_from_source", ""),
                    str(news_data.get("raw_data", {})),
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def batch_insert(self, news_list: List[Dict[str, Any]]) -> List[int]:
        ids = []
        for item in news_list:
            nid = self.insert(item)
            ids.append(nid)
        return ids

    def exists(self, url: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute("SELECT 1 FROM news WHERE url = ?", (url,)).fetchone()
            return row is not None