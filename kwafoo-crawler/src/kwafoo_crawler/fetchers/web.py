import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class WebFetcher(BaseFetcher):
    def fetch(self, url: str, source_name: str,
              selectors: Optional[Dict[str, str]] = None, **kwargs) -> List[Dict[str, Any]]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            selectors = selectors or {}
            container_sel = selectors.get("container", "body")
            title_sel = selectors.get("title", "h2 a, h3 a")
            link_sel = selectors.get("link", "a")
            time_sel = selectors.get("time", "time")

            containers = soup.select(container_sel)
            if not containers:
                containers = [soup]

            news_list = []
            for container in containers:
                items = container.select(title_sel) if title_sel else []
                for item in items:
                    title = item.get_text(strip=True)
                    if not title:
                        continue

                    link_elem = item if item.name == "a" else item.find("a")
                    link = ""
                    if link_elem and link_elem.get("href"):
                        href = link_elem["href"]
                        link = href if href.startswith("http") else requests.compat.urljoin(url, href)

                    news_list.append({
                        "title": title,
                        "description": "",
                        "content": "",
                        "url": link,
                        "source": source_name,
                        "source_url": url,
                        "publish_time": "",
                        "fetch_time": datetime.now().isoformat(),
                        "image_url": "",
                        "category_from_source": "",
                        "raw_data": {},
                    })

            logger.info("Web抓取完成: %s - %d条", source_name, len(news_list))
            return news_list
        except requests.RequestException as e:
            logger.error("Web请求失败: %s - %s", url, e)
            return []
        except Exception as e:
            logger.error("Web解析失败: %s - %s", url, e)
            return []