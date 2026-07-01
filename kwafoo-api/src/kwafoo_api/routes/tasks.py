import logging
import threading
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..app import get_processor

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/crawl")
def trigger_crawl(background_tasks: BackgroundTasks,
                  source_name: Optional[str] = None):
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    background_tasks.add_task(_run_crawl, processor, source_name)
    return {"status": "accepted", "message": "爬虫任务已提交"}


def _run_crawl(processor, source_name: Optional[str]):
    try:
        result = processor.crawl_pipeline()
        logger.info("手动爬虫完成: %s", result)
    except Exception as e:
        logger.error("手动爬虫失败: %s", e)


@router.post("/process")
def trigger_process(background_tasks: BackgroundTasks):
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    def _run():
        try:
            result = processor.process_pipeline()
            logger.info("手动处理完成: %s", result)
        except Exception as e:
            logger.error("手动处理失败: %s", e)

    background_tasks.add_task(_run)
    return {"status": "accepted", "message": "处理任务已提交"}


@router.post("/pipeline")
def trigger_full_pipeline(background_tasks: BackgroundTasks):
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    def _run():
        try:
            crawl_result = processor.crawl_pipeline()
            logger.info("管道-爬虫完成: %s", crawl_result)
            process_result = processor.process_pipeline()
            logger.info("管道-处理完成: %s", process_result)
        except Exception as e:
            logger.error("全管道失败: %s", e)

    background_tasks.add_task(_run)
    return {"status": "accepted", "message": "全管道任务已提交"}


@router.get("/status")
def get_task_status():
    processor = get_processor()
    if processor is None:
        raise HTTPException(status_code=503, detail="数据处理引擎未就绪")

    try:
        return processor.get_stats()
    except Exception as e:
        logger.error("获取任务状态失败: %s", e)
        raise HTTPException(status_code=500, detail=str(e))