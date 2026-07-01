import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from litellm import completion

from .task_loader import TaskLoader
from .validator import ResponseValidator
from .retry import RetryManager
from .types import AIResult, TaskConfig, TaskMeta

logger = logging.getLogger(__name__)


class AIEngine:
    def __init__(self, config_path: str = "config/ai_config.toml", tasks_dir: str = "tasks"):
        self._config = self._load_toml_config(config_path)
        self._load_ai_params()
        self._setup_litellm_env()

        self.loader = TaskLoader(tasks_dir)
        self.validator = ResponseValidator()
        self.retry_mgr = RetryManager()

        self.loader.load_all()
        logger.info("AIEngine初始化完成，已加载 %d 个任务", len(self._tasks))

    def _load_toml_config(self, config_path: str) -> Dict[str, Any]:
        if not os.path.exists(config_path):
            logger.warning("配置文件不存在: %s，使用默认配置", config_path)
            return {}

        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(config_path, "rb") as f:
            return tomllib.load(f)

    def _load_ai_params(self) -> None:
        ai_cfg = self._config.get("ai", self._config)
        self.base_url = ai_cfg.get("base_url", "http://localhost:1234")
        self.model = ai_cfg.get("model", "google/gemma-4-e4b")
        self.api_key = ai_cfg.get("api_key", "")
        self.default_max_tokens = ai_cfg.get("max_tokens", 4096)
        self.default_temperature = ai_cfg.get("temperature", 0.7)
        self.default_timeout = ai_cfg.get("timeout", 120)
        self.global_max_retries = ai_cfg.get("max_retries", 3)
        self.global_backoff_base = ai_cfg.get("backoff_base", 1.5)
        self.global_max_delay = ai_cfg.get("max_delay", 30.0)

    def _setup_litellm_env(self) -> None:
        os.environ.setdefault("LITELLM_LOG", "ERROR")
        os.environ.setdefault("LITELLM_DROP_PARAMS", "true")
        os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "true")
        os.environ.setdefault("LITELLM_CACHE", "false")

    @property
    def _tasks(self) -> Dict[str, TaskConfig]:
        return self.loader.get_tasks()

    def execute(self, task_name: str, **params) -> AIResult:
        task = self.loader.get_task(task_name)
        if task is None:
            return AIResult(success=False, error=f"未知任务: {task_name}", task_name=task_name)

        try:
            rendered_params = self._apply_pre_process(task, params)
            messages = self._build_messages(task, rendered_params)
            call_kwargs = self._build_kwargs(task, messages=messages)

            retry_cfg = task.retry
            max_retries = retry_cfg.get("max_retries", self.global_max_retries)
            backoff_base = retry_cfg.get("backoff_base", self.global_backoff_base)
            max_delay = retry_cfg.get("max_delay", self.global_max_delay)

            retry_count = 0
            last_error = None

            while retry_count <= max_retries:
                try:
                    logger.debug("AI调用: task=%s, retry=%d", task_name, retry_count)
                    response = completion(**call_kwargs)

                    parsed = self._parse_response(response)

                    validated = self.validator.validate(parsed, task.output_schema)
                    if not validated["valid"]:
                        raise ValueError(f"响应验证失败: {validated['error']}")

                    data = self._apply_post_process(task, parsed, params)

                    return AIResult(
                        success=True,
                        data=data,
                        raw_response=str(response),
                        retry_count=retry_count,
                        task_name=task_name,
                    )

                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    logger.warning("AI调用失败: task=%s, retry=%d, error=%s", task_name, retry_count, error_msg)

                    if not self.retry_mgr.should_retry(error_msg, retry_count, max_retries):
                        break

                    retry_count += 1
                    delay = self.retry_mgr.get_delay(error_msg, retry_count, backoff_base, max_delay)
                    logger.info("等待 %.2f 秒后重试...", delay)
                    time.sleep(delay)

            return AIResult(
                success=False,
                error=str(last_error),
                retry_count=retry_count,
                task_name=task_name,
            )

        except Exception as e:
            logger.error("执行任务异常: task=%s, error=%s", task_name, e)
            return AIResult(success=False, error=str(e), task_name=task_name)

    def _build_messages(self, task: TaskConfig, params: Dict[str, Any]) -> List[Dict[str, str]]:
        messages = []
        if task.system_prompt:
            messages.append({"role": "system", "content": task.system_prompt})

        try:
            user_content = task.prompt_template.format(**params)
        except KeyError as e:
            raise ValueError(f"提示词模板缺少参数: {e}") from e

        user_content += "\n\n请严格按照JSON格式返回结果，不要包含任何其他内容。"

        json_instruction = self._build_json_instruction(task)
        user_content = f"{json_instruction}\n\n{user_content}"

        messages.append({"role": "user", "content": user_content})
        return messages

    def _build_json_instruction(self, task: TaskConfig) -> str:
        schema_str = json.dumps(task.output_schema, ensure_ascii=False, indent=2)
        return (
            f"返回格式要求：\n"
            f"JSON Schema:\n```json\n{schema_str}\n```\n"
            f"重要：只返回JSON，不要包含任何解释或标记。"
        )

    def _build_kwargs(self, task: TaskConfig, messages: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        model_params = task.model_params
        if messages is None:
            messages = self._build_messages(task, {})
        return {
            "model": f"openai/{self.model}",
            "messages": messages,
            "api_base": f"{self.base_url}/v1",
            "api_key": self.api_key if self.api_key else "not-needed",
            "max_tokens": model_params.get("max_tokens", self.default_max_tokens),
            "temperature": model_params.get("temperature", self.default_temperature),
            "timeout": model_params.get("timeout", self.default_timeout),
        }

    def _parse_response(self, response: Any) -> Any:
        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError):
            try:
                content = response["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                return str(response)

        return self.validator.extract_json(content)

    def _apply_pre_process(self, task: TaskConfig, params: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(params)
        for step in task.pre_process:
            step_type = step.get("type", "")
            if step_type == "conditional_block":
                condition = step.get("condition", "")
                try:
                    condition_val = eval(condition, {"__builtins__": {}}, result)
                except Exception:
                    condition_val = True
                if condition_val:
                    template = step.get("template", "")
                    target_var = step.get("target_var", "")
                    if target_var:
                        try:
                            result[target_var] = template.format(**result)
                        except KeyError:
                            result[target_var] = template
                else:
                    target_var = step.get("target_var", "")
                    if target_var:
                        result[target_var] = ""
        return result

    def _apply_post_process(self, task: TaskConfig, data: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        result = dict(data)
        for step in task.post_process:
            step_type = step.get("type", "")
            if step_type == "validate_categories":
                allowed = params.get("categories", [])
                if allowed and "categories" in result:
                    result["categories"] = [c for c in result["categories"] if c in allowed]
            elif step_type == "keyword_fallback":
                if not result.get("categories") and result.get("keywords"):
                    pass
        return result

    def build_kwargs_for_task(self, task_name: str, **params) -> Dict[str, Any]:
        task = self.loader.get_task(task_name)
        if task is None:
            return {}
        messages = self._build_messages(task, self._apply_pre_process(task, params))
        kwargs = self._build_kwargs(task, messages=messages)
        kwargs["messages"] = messages
        return kwargs

    def list_tasks(self) -> List[TaskMeta]:
        return [t.meta for t in self.loader.list_tasks()]

    def get_task_info(self, task_name: str) -> Optional[TaskConfig]:
        return self.loader.get_task(task_name)

    def reload_tasks(self) -> None:
        self.loader.reload()