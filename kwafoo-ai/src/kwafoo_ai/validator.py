import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ResponseValidator:

    def validate(self, data: Any, output_schema: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if not isinstance(data, dict):
                return {"valid": False, "error": f"响应数据必须是字典类型，实际类型: {type(data).__name__}"}

            required = output_schema.get("required", [])
            properties = output_schema.get("properties", {})

            for field in required:
                if field not in data:
                    return {"valid": False, "error": f"缺少必需字段: {field}"}

            for field_name, field_schema in properties.items():
                if field_name not in data:
                    continue

                value = data[field_name]
                field_type = field_schema.get("type", "string")

                if field_type == "string":
                    if not isinstance(value, str):
                        return {"valid": False, "error": f"字段 {field_name} 必须是字符串类型"}

                    max_len = field_schema.get("max_length", 0)
                    if max_len > 0 and len(value) > max_len:
                        return {"valid": False, "error": f"字段 {field_name} 长度({len(value)})超过最大限制({max_len})"}

                    min_len = field_schema.get("min_length", 0)
                    if min_len > 0 and len(value) < min_len:
                        return {"valid": False, "error": f"字段 {field_name} 长度({len(value)})不足最小要求({min_len})"}

                    enum_vals = field_schema.get("enum", [])
                    if enum_vals and value not in enum_vals:
                        return {"valid": False, "error": f"字段 {field_name} 的值 '{value}' 不在允许范围内: {enum_vals}"}

                elif field_type == "number":
                    if not isinstance(value, (int, float)):
                        return {"valid": False, "error": f"字段 {field_name} 必须是数字类型"}

                    minimum = field_schema.get("minimum")
                    if minimum is not None and value < minimum:
                        return {"valid": False, "error": f"字段 {field_name} 的值({value})小于最小值({minimum})"}

                    maximum = field_schema.get("maximum")
                    if maximum is not None and value > maximum:
                        return {"valid": False, "error": f"字段 {field_name} 的值({value})大于最大值({maximum})"}

                elif field_type == "array":
                    if not isinstance(value, list):
                        return {"valid": False, "error": f"字段 {field_name} 必须是数组类型"}

                    max_items = field_schema.get("max_items", 0)
                    if max_items > 0 and len(value) > max_items:
                        return {"valid": False, "error": f"字段 {field_name} 的元素数量({len(value)})超过最大限制({max_items})"}

                    min_items = field_schema.get("min_items", 0)
                    if min_items > 0 and len(value) < min_items:
                        return {"valid": False, "error": f"字段 {field_name} 的元素数量({len(value)})不足最小要求({min_items})"}

            logger.debug("响应验证通过")
            return {"valid": True, "error": None}

        except Exception as e:
            logger.error("响应验证异常: %s", e)
            return {"valid": False, "error": f"验证异常: {e}"}

    @staticmethod
    def extract_json(text: str) -> Any:
        if not isinstance(text, str):
            return text

        text = text.strip()

        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            text = json_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:

            try:
                match = re.search(r'\{[\s\S]*\}', text)
                if match:
                    return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

            return text