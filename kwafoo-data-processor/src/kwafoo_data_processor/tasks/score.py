import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ScoreTask:
    def __init__(self, ai_engine):
        self.ai = ai_engine

    def execute(self, title: str, summary: str, category: str = "",
                source_score: float = 0, interest_keywords: list = None) -> Dict[str, Any]:
        result = self.ai.execute(
            "score",
            title=title,
            summary=summary,
            category=category,
            source_score=source_score,
            interest_keywords=interest_keywords or [],
        )

        if result.success and result.data:
            return {
                "relevance": float(result.data.get("relevance", 0)),
                "importance": float(result.data.get("importance", 0)),
                "source_score": float(result.data.get("source_score", source_score)),
            }

        logger.warning("评分失败: %s", result.error)
        return {"relevance": 0, "importance": 0, "source_score": source_score}