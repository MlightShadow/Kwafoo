import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .fetchers.rss import RSSFetcher
from .fetchers.web import WebFetcher
from .fetchers.content import ContentFetcher
from .storage.sqlite import SQLiteStorage
from .storage.file import FileStorage

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    total_fetched: int = 0
    success_count: int = 0
    fail_count: int = 0
    data: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class CrawlerEngine:
    def __init__(self, config_path: str = "config/crawler_config.toml"):
        self._config = self._load_config(config_path)
        self._load_params()

        self.rss_fetcher = RSSFetcher(
            user_agent=self.user_agent,
            timeout=self.request_timeout,
            proxy_url=self.proxy_url if self.enable_proxy else None,
        )
        self.web_fetcher = WebFetcher(
            user_agent=self.user_agent,
            timeout=self.request_timeout,
            proxy_url=self.proxy_url if self.enable_proxy else None,
        )
        self.content_fetcher = ContentFetcher(
            user_agent=self.user_agent,
            timeout=self.request_timeout,
            proxy_url=self.proxy_url if self.enable_proxy else None,
        )

        self._storage = self._init_storage()

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
        c = self._config.get("crawler", {})
        self.max_workers = c.get("max_workers", 20)
        self.user_agent = c.get("user_agent", "Kwafoo-Crawler/1.0")
        self.request_timeout = c.get("request_timeout", 30)

        n = self._config.get("network", {})
        self.enable_proxy = n.get("enable_proxy", False)
        self.proxy_url = n.get("proxy_url", "")

        self._sources = self._extract_sources()

    def _extract_sources(self) -> List[Dict[str, Any]]:
        sources = []
        src_section = self._config.get("sources", {})
        if not src_section:
            src_section = self._config

        for key in ["rss", "web", "api"]:
            for src in src_section.get(key, []):
                if src.get("enabled", True):
                    src["type"] = key
                    sources.append(src)

        return sources

    def _init_storage(self):
        s = self._config.get("storage", {})
        backend = s.get("backend", "sqlite")
        if backend == "sqlite":
            return SQLiteStorage(s.get("sqlite_path", "data/crawler.db"))
        else:
            return FileStorage(
                s.get("file_path", "data/raw_news/"),
                s.get("file_format", "json"),
            )

    def crawl_all(self) -> CrawlResult:
        result = CrawlResult()
        if not self._sources:
            logger.warning("没有配置任何新闻源")
            return result

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._crawl_single_source, src): src
                for src in self._sources
            }
            for future in as_completed(futures):
                src = futures[future]
                try:
                    src_result = future.result()
                    result.total_fetched += src_result.total_fetched
                    result.success_count += src_result.success_count
                    result.fail_count += src_result.fail_count
                    result.data.extend(src_result.data)
                    result.errors.extend(src_result.errors)
                except Exception as e:
                    result.fail_count += 1
                    result.errors.append(f"{src.get('name', 'unknown')}: {e}")

        logger.info(
            "抓取完成: total=%d, success=%d, fail=%d",
            result.total_fetched, result.success_count, result.fail_count,
        )
        return result

    def _crawl_single_source(self, src: Dict[str, Any]) -> CrawlResult:
        result = CrawlResult()
        try:
            src_type = src.get("type", "rss")
            src_name = src.get("name", "unknown")
            src_url = src.get("url", "")

            if not src_url:
                return result

            if src_type == "rss":
                news_list = self.rss_fetcher.fetch(src_url, src_name, src.get("fetch_days"))
            elif src_type == "web":
                news_list = self.web_fetcher.fetch(src_url, src_name, src.get("selectors", {}))
            else:
                news_list = []

            if news_list:
                self._storage.batch_insert(news_list)
                result.total_fetched = len(news_list)
                result.success_count = len(news_list)
                result.data = news_list
                logger.info("已存储 %d 条新闻: %s", len(news_list), src_name)

        except Exception as e:
            result.fail_count = 1
            result.errors.append(str(e))
            logger.error("抓取失败 %s: %s", src.get("name", "unknown"), e)

        return result

    def crawl_source(self, source_name: str) -> CrawlResult:
        for src in self._sources:
            if src.get("name") == source_name:
                return self._crawl_single_source(src)
        return CrawlResult()

    def fetch_content(self, url: str) -> Optional[str]:
        return self.content_fetcher.fetch(url)

    def add_source(self, source_config: Dict[str, Any]) -> None:
        self._sources.append(source_config)

    def get_sources(self) -> List[Dict[str, Any]]:
        return list(self._sources)