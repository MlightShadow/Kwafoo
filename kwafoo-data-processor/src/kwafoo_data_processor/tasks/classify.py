import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ClassifyTask:
    def __init__(self, ai_engine, categories: list):
        self.ai = ai_engine
        self.categories = categories

    def execute(self, title: str, content: str,
                context: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        result = self.ai.execute(
            "classify",
            title=title[:200] if title else "",
            content=content[:2000] if content else "",
            categories=json.dumps(self.categories, ensure_ascii=False),
            context=context or {},
        )

        if result.success and result.data:
            return {
                "categories": result.data.get("categories", []),
                "keywords": result.data.get("keywords", []),
            }

        logger.warning("分类失败: %s", result.error)
        return {"categories": [], "keywords": []}