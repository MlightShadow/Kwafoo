import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .routes import news, tasks, config, chat
from .websocket import ws_manager

logger = logging.getLogger(__name__)


def load_api_config(config_path: str) -> Dict[str, Any]:
    if not os.path.exists(config_path):
        return {}
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    with open(config_path, "rb") as f:
        return tomllib.load(f)


_processor = None


def get_processor():
    return _processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _processor
    try:
        from kwafoo_data_processor import ProcessorEngine
        config_path = app.state.api_config.get("api", {}).get(
            "processor_config_path", "config/processor_config.toml"
        )
        _processor = ProcessorEngine(config_path)
        _processor.start()
        ws_manager.set_processor(_processor)
        logger.info("数据处理引擎已启动")
    except Exception as e:
        logger.warning("数据处理引擎启动失败: %s", e)

    yield

    if _processor:
        try:
            _processor.shutdown()
        except Exception:
            pass


def create_app(config_path: str = "config/api_config.toml") -> FastAPI:
    cfg = load_api_config(config_path)

    app = FastAPI(
        title="Kwafoo API",
        version="1.0.0",
        description="新闻聚合系统API服务",
        lifespan=lifespan,
    )

    app.state.api_config = cfg

    api_cfg = cfg.get("api", {})
    cors_origins = api_cfg.get("cors_origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(news.router, prefix="/api/news", tags=["news"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
    app.include_router(config.router, prefix="/api/config", tags=["config"])
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    return app