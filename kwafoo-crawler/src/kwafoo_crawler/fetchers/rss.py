import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import feedparser
import requests

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    def fetch(self, rss_url: str, source_name: str,
              fetch_days: Optional[int] = None, **kwargs) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(rss_url, timeout=self.timeout)
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            news_list = []
            for entry in feed.entries:
                item = self._parse_entry(entry, source_name, rss_url, fetch_days)
                if item:
                    news_list.append(item)

            logger.info("RSS抓取完成: %s - %d条", source_name, len(news_list))
            return news_list
        except requests.RequestException as e:
            logger.error("RSS请求失败: %s - %s", rss_url, e)
            return []
        except Exception as e:
            logger.error("RSS解析失败: %s - %s", rss_url, e)
            return []

    def _parse_entry(self, entry: Any, source_name: str,
                     source_url: str, fetch_days: Optional[int]) -> Optional[Dict[str, Any]]:
        title = (entry.get("title") or "").strip()
        if not title:
            return None

        link = entry.get("link", "")
        if not link:
            return None

        if fetch_days is not None:
            pub_time = self._parse_pub_time(entry)
            if pub_time:
                cutoff = datetime.now(timezone.utc) - timedelta(days=fetch_days)
                if pub_time.replace(tzinfo=timezone.utc) < cutoff:
                    return None

        raw_desc = entry.get("description") or entry.get("summary") or ""
        description = self._clean_html(raw_desc)
        image_url = self._extract_image(entry, raw_desc)

        pub_time = self._parse_pub_time(entry)

        return {
            "title": title,
            "description": description,
            "content": "",
            "url": link,
            "source": source_name,
            "source_url": source_url,
            "publish_time": pub_time.isoformat() if pub_time else "",
            "fetch_time": datetime.now().isoformat(),
            "image_url": image_url,
            "category_from_source": entry.get("category", ""),
            "raw_data": {},
        }

    def _clean_html(self, text: str) -> str:
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _parse_pub_time(self, entry: Any) -> Optional[datetime]:
        time_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if time_struct:
            try:
                return datetime(*time_struct[:6])
            except Exception:
                pass
        for field in ["published", "updated"]:
            val = entry.get(field, "")
            if val:
                try:
                    from email.utils import parsedate_to_datetime
                    return parsedate_to_datetime(val)
                except Exception:
                    pass
        return None

    def _extract_image(self, entry: Any, raw_html: str) -> str:
        media = entry.get("media_content", [])
        if media:
            for m in media:
                url = m.get("url", "")
                if url:
                    return url
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html, re.IGNORECASE)
        if match:
            return match.group(1)
        return ""