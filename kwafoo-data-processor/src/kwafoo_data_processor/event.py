import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventType(Enum):
    CRAWL_START = "crawl_start"
    CRAWL_COMPLETE = "crawl_complete"
    CRAWL_ERROR = "crawl_error"

    CLASSIFY_START = "classify_start"
    CLASSIFY_COMPLETE = "classify_complete"

    SUMMARIZE_START = "summarize_start"
    SUMMARIZE_COMPLETE = "summarize_complete"

    SCORE_START = "score_start"
    SCORE_COMPLETE = "score_complete"

    REPORT_START = "report_start"
    REPORT_COMPLETE = "report_complete"

    PIPELINE_START = "pipeline_start"
    PIPELINE_COMPLETE = "pipeline_complete"

    TASK_ERROR = "task_error"
    TASK_PROGRESS = "task_progress"


@dataclass
class Event:
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[Event], None]


class EventBus:
    _instance = None

    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {et: [] for et in EventType}

    @classmethod
    def get_instance(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def emit(self, event: Event) -> None:
        handlers = self._handlers.get(event.type, [])
        logger.debug("事件触发: %s", event.type.value)
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("事件处理器异常: %s - %s", event.type.value, e)

    def emit_type(self, event_type: EventType, data: Dict[str, Any] | None = None) -> None:
        self.emit(Event(type=event_type, data=data or {}))

    def subscribe_many(self, event_types: List[EventType], handler: EventHandler) -> None:
        for et in event_types:
            self.subscribe(et, handler)