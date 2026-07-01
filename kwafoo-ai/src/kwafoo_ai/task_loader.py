import os
import glob
import logging
from typing import Any, Dict, List

import yaml

from .types import TaskConfig

logger = logging.getLogger(__name__)


class TaskLoader:
    def __init__(self, tasks_dir: str):
        self.tasks_dir = tasks_dir
        self._tasks: Dict[str, TaskConfig] = {}

    def load_all(self) -> Dict[str, TaskConfig]:
        self._tasks = {}
        if not os.path.isdir(self.tasks_dir):
            logger.warning("任务目录不存在: %s", self.tasks_dir)
            return self._tasks

        yaml_files = sorted(glob.glob(os.path.join(self.tasks_dir, "*.yaml")))
        yaml_files += sorted(glob.glob(os.path.join(self.tasks_dir, "*.yml")))

        for filepath in yaml_files:
            try:
                task = self._load_file(filepath)
                if task is None:
                    continue
                self._validate_task(task, filepath)
                self._tasks[task.name] = task
                logger.info("已加载任务: %s (v%s) from %s", task.name, task.version, os.path.basename(filepath))
            except Exception as e:
                logger.error("加载任务文件失败 %s: %s", filepath, e)

        logger.info("共加载 %d 个任务: %s", len(self._tasks), list(self._tasks.keys()))
        return self._tasks

    def _load_file(self, filepath: str) -> TaskConfig | None:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if raw is None:
            return None
        if not isinstance(raw, dict) or "name" not in raw:
            logger.warning("跳过无效任务文件（缺少name字段）: %s", filepath)
            return None

        return TaskConfig(
            name=raw["name"],
            version=raw.get("version", "1.0"),
            description=raw.get("description", ""),
            input_schema=raw.get("input_schema", {"type": "object", "properties": {}}),
            output_schema=raw.get("output_schema", {"type": "object", "properties": {}}),
            system_prompt=raw.get("system_prompt", ""),
            prompt_template=raw.get("prompt_template", ""),
            model_params=raw.get("model_params", {}),
            retry=raw.get("retry", {}),
            pre_process=raw.get("pre_process", []),
            post_process=raw.get("post_process", []),
        )

    def _validate_task(self, task: TaskConfig, filepath: str) -> None:
        if not task.prompt_template:
            raise ValueError(f"缺少 prompt_template: {filepath}")

    def get_task(self, task_name: str) -> TaskConfig | None:
        return self._tasks.get(task_name)

    def get_tasks(self) -> Dict[str, TaskConfig]:
        return dict(self._tasks)

    def list_tasks(self) -> List[TaskConfig]:
        return list(self._tasks.values())

    def reload(self) -> Dict[str, TaskConfig]:
        logger.info("重新加载所有任务配置...")
        return self.load_all()