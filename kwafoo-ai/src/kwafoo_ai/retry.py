import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RetryManager:

    ERROR_PATTERNS: Dict[str, list] = {
        "timeout": ["timeout", "超时", "timed out"],
        "connection": ["connection", "连接", "connect", "network"],
        "json_parse": ["json", "parse", "解析", "格式", "Expecting value"],
        "validation": ["validation", "验证", "invalid", "无效"],
        "service_unavailable": ["unavailable", "不可用", "503", "502"],
        "rate_limit": ["rate limit", "频率", "429"],
        "empty_response": ["empty", "空", "null"],
    }

    def __init__(self):
        self.base_delays: Dict[str, float] = {
            "timeout": 2.0,
            "connection": 3.0,
            "json_parse": 1.0,
            "validation": 1.0,
            "service_unavailable": 5.0,
            "rate_limit": 10.0,
            "empty_response": 1.0,
            "default": 1.0,
        }

    def identify_error_type(self, error_message: str) -> str:
        msg_lower = error_message.lower()
        for err_type, keywords in self.ERROR_PATTERNS.items():
            for kw in keywords:
                if kw.lower() in msg_lower:
                    return err_type
        return "default"

    def get_delay(self, error_message: str, retry_count: int, backoff_base: float = 1.5, max_delay: float = 30.0) -> float:
        error_type = self.identify_error_type(error_message)
        base = self.base_delays.get(error_type, self.base_delays["default"])
        delay = base * (backoff_base ** (retry_count - 1))
        return min(delay, max_delay)

    def should_retry(self, error_message: str, retry_count: int, max_retries: int) -> bool:
        return retry_count < max_retries