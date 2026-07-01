import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self, processor):
        self._processor = processor
        self._ai_engine = None

    def _ensure_ai(self) -> bool:
        if self._ai_engine is not None:
            return True
        try:
            from kwafoo_ai import AIEngine
            self._ai_engine = AIEngine(
                config_path=self._processor.ai_config_path,
                tasks_dir="tasks",
            )
            return True
        except Exception as e:
            logger.warning("RAG AI引擎初始化失败: %s", e)
            return False

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        db = self._processor.db
        keywords = [kw.strip() for kw in query.split() if kw.strip()]
        if not keywords:
            return []

        results = []
        for keyword in keywords:
            items = db.get_news_processed(
                limit=limit, offset=0, keyword=keyword
            )
            results.extend(items)

        seen = set()
        unique = []
        for item in results:
            if item["id"] not in seen:
                seen.add(item["id"])
                unique.append(item)

        return unique[:limit]

    def chat(self, query: str, context_news_ids: Optional[List[int]] = None,
             history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        if not self._ensure_ai():
            return {"answer": "AI引擎未就绪", "sources": []}

        if context_news_ids:
            contexts = self._get_contexts_by_ids(context_news_ids)
        else:
            contexts = self.search(query, limit=3)

        context_text = self._build_context(contexts)
        messages = self._build_chat_messages(query, context_text, history or [])

        try:
            result = self._ai_engine.execute(
                "summarize",
                content=messages[-1]["content"],
                title=query,
                enable_comment=True,
                personality="知识助手",
            )
            if result.success and result.data:
                return {
                    "answer": result.data.get("summary", result.data.get("comment", "")),
                    "sources": [
                        {"id": c["id"], "title": c.get("title", "")}
                        for c in contexts
                    ],
                }
        except Exception as e:
            logger.error("RAG聊天失败: %s", e)

        return {"answer": "抱歉，无法生成回复", "sources": []}

    def _get_contexts_by_ids(self, news_ids: List[int]) -> List[Dict[str, Any]]:
        import sqlite3
        contexts = []
        try:
            conn = sqlite3.connect(self._processor.db_path)
            conn.row_factory = sqlite3.Row
            for nid in news_ids:
                row = conn.execute("SELECT id, title, ai_summary, category FROM news WHERE id = ?", (nid,)).fetchone()
                if row:
                    contexts.append(dict(row))
            conn.close()
        except Exception as e:
            logger.error("获取上下文失败: %s", e)
        return contexts

    def _build_context(self, contexts: List[Dict[str, Any]]) -> str:
        if not contexts:
            return "暂无相关新闻上下文。"
        parts = []
        for i, ctx in enumerate(contexts, 1):
            parts.append(
                f"[{i}] {ctx.get('title', '')}\n"
                f"分类: {ctx.get('category', '')}\n"
                f"摘要: {ctx.get('ai_summary', '')}\n"
            )
        return "\n".join(parts)

    def _build_chat_messages(self, query: str, context: str,
                             history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        messages = [{"role": "system", "content": "你是一个新闻知识助手，基于提供的新闻上下文回答用户问题。"}]
        for h in history[-5:]:
            messages.append(h)
        messages.append({
            "role": "user",
            "content": f"相关新闻上下文：\n\n{context}\n\n用户问题：{query}",
        })
        return messages