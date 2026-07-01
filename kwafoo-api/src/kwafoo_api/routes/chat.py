import logging
from typing import List, Optional

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from ..app import get_processor
from ..rag import RAGEngine

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    query: str
    context_news_ids: Optional[List[int]] = None
    history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    rag = RAGEngine(processor)
    result = rag.chat(
        query=request.query,
        context_news_ids=request.context_news_ids,
        history=request.history,
    )
    return ChatResponse(**result)


@router.get("/search")
def search_news(q: str, limit: int = 5):
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    rag = RAGEngine(processor)
    results = rag.search(q, limit=limit)
    return {
        "query": q,
        "results": [
            {
                "id": r["id"],
                "title": r.get("title", ""),
                "summary": r.get("ai_summary", ""),
                "category": r.get("category", ""),
            }
            for r in results
        ],
    }