from abc import ABC, abstractmethod
from typing import Any, Dict, List


class StorageBackend(ABC):
    @abstractmethod
    def insert(self, news_data: Dict[str, Any]) -> int:
        ...

    @abstractmethod
    def batch_insert(self, news_list: List[Dict[str, Any]]) -> List[int]:
        ...

    @abstractmethod
    def exists(self, url: str) -> bool:
        ...