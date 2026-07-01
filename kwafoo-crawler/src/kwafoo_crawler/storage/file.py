import hashlib
import json
import logging
import os
from typing import Any, Dict, List

from .base import StorageBackend

logger = logging.getLogger(__name__)


class FileStorage(StorageBackend):
    def __init__(self, base_dir: str = "data/raw_news/", file_format: str = "json"):
        self.base_dir = base_dir
        self.file_format = file_format
        os.makedirs(self.base_dir, exist_ok=True)

    def _file_path(self, url: str) -> str:
        hash_val = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.base_dir, f"{hash_val}.{self.file_format}")

    def insert(self, news_data: Dict[str, Any]) -> int:
        filepath = self._file_path(news_data.get("url", ""))
        try:
            if self.file_format == "json":
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(news_data, f, ensure_ascii=False, indent=2)
            elif self.file_format == "csv":
                import csv
                exists = os.path.exists(filepath)
                with open(filepath, "a", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=news_data.keys())
                    if not exists:
                        writer.writeheader()
                    writer.writerow(news_data)
            return hash(filepath) % (2 ** 31)
        except Exception as e:
            logger.error("文件存储失败: %s - %s", filepath, e)
            return 0

    def batch_insert(self, news_list: List[Dict[str, Any]]) -> List[int]:
        return [self.insert(item) for item in news_list]

    def exists(self, url: str) -> bool:
        return os.path.exists(self._file_path(url))