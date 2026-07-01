import json
import logging
from typing import Any, Dict, List

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: List[WebSocket] = []
        self._processor = None

    def set_processor(self, processor) -> None:
        self._processor = processor
        if processor:
            self._subscribe_events()

    def _subscribe_events(self) -> None:
        if self._processor is None:
            return

        event_bus = self._processor.event_bus

        from kwafoo_data_processor.event import EventType
        event_bus.subscribe(EventType.CRAWL_START, self._on_event)
        event_bus.subscribe(EventType.CRAWL_COMPLETE, self._on_event)
        event_bus.subscribe(EventType.CRAWL_ERROR, self._on_event)
        event_bus.subscribe(EventType.PIPELINE_START, self._on_event)
        event_bus.subscribe(EventType.PIPELINE_COMPLETE, self._on_event)
        event_bus.subscribe(EventType.TASK_ERROR, self._on_event)
        event_bus.subscribe(EventType.TASK_PROGRESS, self._on_event)
        event_bus.subscribe(EventType.CLASSIFY_START, self._on_event)
        event_bus.subscribe(EventType.CLASSIFY_COMPLETE, self._on_event)
        event_bus.subscribe(EventType.SUMMARIZE_START, self._on_event)
        event_bus.subscribe(EventType.SUMMARIZE_COMPLETE, self._on_event)
        event_bus.subscribe(EventType.SCORE_START, self._on_event)
        event_bus.subscribe(EventType.SCORE_COMPLETE, self._on_event)
        event_bus.subscribe(EventType.REPORT_START, self._on_event)
        event_bus.subscribe(EventType.REPORT_COMPLETE, self._on_event)
        logger.info("WebSocket已订阅事件总线")

    def _on_event(self, event: Any) -> None:
        payload = {
            "type": event.type.value,
            "data": event.data,
        }
        self.broadcast(payload)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info("WebSocket客户端已连接 (total=%d)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info("WebSocket客户端已断开 (total=%d)", len(self._connections))

    async def broadcast(self, message: Dict[str, Any]) -> None:
        text = json.dumps(message, ensure_ascii=False, default=str)
        disconnected = []
        for ws in self._connections:
            try:
                await ws.send_text(text)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


ws_manager = WebSocketManager()


def get_ws_manager() -> WebSocketManager:
    return ws_manager