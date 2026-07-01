import requests
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    def __init__(self, user_agent: str = "Kwafoo-Crawler/1.0", timeout: int = 30,
                 proxy_url: Optional[str] = None):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        if proxy_url:
            self.session.proxies = {"http": proxy_url, "https": proxy_url}

    @abstractmethod
    def fetch(self, url: str, source_name: str, **kwargs) -> List[Dict[str, Any]]:
        ...