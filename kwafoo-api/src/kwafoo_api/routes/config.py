import logging

from fastapi import APIRouter, HTTPException

from ..app import get_processor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/categories")
def get_categories():
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    try:
        categories = processor._config.get("apple", {}).get("categories", [])
        return {"categories": categories}
    except Exception as e:
        logger.error("获取分类配置失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/tasks")
def get_ai_tasks():
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    if processor._ai_engine is None:
        return {"tasks": []}

    try:
        task_metas = processor._ai_engine.list_tasks()
        return {
            "tasks": [
                {"name": t.name, "version": t.version, "description": t.description}
                for t in task_metas
            ]
        }
    except Exception as e:
        logger.error("获取AI任务列表失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))