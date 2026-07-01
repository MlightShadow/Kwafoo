from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TaskMeta:
    name: str
    version: str
    description: str


@dataclass
class TaskConfig:
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    system_prompt: str
    prompt_template: str
    model_params: Dict[str, Any]
    retry: Dict[str, Any]
    pre_process: List[Dict[str, Any]] = field(default_factory=list)
    post_process: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def meta(self) -> TaskMeta:
        return TaskMeta(name=self.name, version=self.version, description=self.description)


@dataclass
class AIResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    raw_response: Optional[str] = None
    retry_count: int = 0
    task_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "retry_count": self.retry_count,
            "task_name": self.task_name,
        }