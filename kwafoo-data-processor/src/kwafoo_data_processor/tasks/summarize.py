import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def contains_chinese(text: str) -> bool:
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            return True
    return False


def smart_truncate(text: str, max_length: int = 2000) -> str:
    if len(text) <= max_length:
        return text

    paragraphs = []
    current = ""
    for char in text:
        current += char
        if char in ("。", "！", "？", "；", ".", "!", "?", ";", "\n"):
            paragraphs.append(current.strip())
            current = ""
    if current.strip():
        paragraphs.append(current.strip())

    if len(paragraphs) >= 2:
        first = paragraphs[0][:max_length // 2]
        last = paragraphs[-1][:max_length - len(first)]
        return first + "\n...\n" + last
    else:
        return text[:max_length]


class SummarizeTask:
    def __init__(self, ai_engine):
        self.ai = ai_engine

    def execute(self, content: str, title: str = "",
                enable_comment: bool = True,
                personality: str = "") -> Dict[str, Any]:
        truncated = smart_truncate(content, 2000)

        result = self.ai.execute(
            "summarize",
            content=truncated,
            title=title,
            enable_comment=enable_comment,
            personality=personality,
        )

        if result.success and result.data:
            return {
                "comment": result.data.get("comment", ""),
                "summary": result.data.get("summary", ""),
                "summary_en": result.data.get("summary_en", ""),
            }

        logger.warning("摘要生成失败: %s", result.error)
        return {"comment": "", "summary": "", "summary_en": ""}