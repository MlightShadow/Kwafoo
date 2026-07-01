import logging
import re
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

from .base import BaseFetcher

logger = logging.getLogger(__name__)


class ContentFetcher(BaseFetcher):
    def fetch(self, url: str, source_name: str = "", **kwargs) -> Optional[str]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            body = soup.find("body")
            if not body:
                body = soup

            candidates = body.find_all(["article", "main", "div"], class_=re.compile(r"content|article|post|body", re.I))
            if candidates:
                text = candidates[0].get_text(separator="\n", strip=True)
            else:
                text = body.get_text(separator="\n", strip=True)

            text = re.sub(r"\n{3,}", "\n\n", text)
            text = re.sub(r"[ \t]+", " ", text)

            if len(text) < 100:
                return None

            logger.debug("正文提取完成: %s - %d字符", url, len(text))
            return text

        except requests.RequestException as e:
            logger.error("正文获取失败: %s - %s", url, e)
            return None
        except Exception as e:
            logger.error("正文解析失败: %s - %s", url, e)
            return None