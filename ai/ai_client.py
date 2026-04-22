"""
统一的AI调用接口
提供标准化的AI调用、响应验证、错误处理和重试机制
"""
import os
# 禁用LiteLLM远程获取模型成本映射，避免启动时网络超时
os.environ['LITELLM_LOG'] = 'ERROR'
os.environ['LITELLM_DROP_PARAMS'] = 'true'
os.environ['LITELLM_MAX_RETRIES'] = '0'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP'] = 'true'
os.environ['LITELLM_CACHE'] = 'false'
os.environ['LITELLM_REQUEST_TIMEOUT'] = '10'

# Patch httpx，让它立即失败，强制使用本地备份
import httpx
_original_httpx_get = httpx.get
def _patched_httpx_get(url, timeout=5, **kwargs):
    """立即抛出异常，强制使用本地备份"""
    raise Exception("Network blocked to force local backup")
httpx.get = _patched_httpx_get

from typing import Dict, Any, Optional, List, Callable
from litellm import completion
from utils.logger import logger
from utils.helpers import config, ConfigObserver
from ai.response_validator import ResponseValidator
from ai.retry_strategy import RetryStrategy


class AIRequest:
    """AI请求封装"""
    
    def __init__(
        self,
        task_type: str,
        prompt: str,
        system_prompt: str = None,
        response_schema: Dict[str, Any] = None,
        **kwargs
    ):
        """
        初始化AI请求
        
        Args:
            task_type: 任务类型（classification/summary/scoring）
            prompt: 用户提示词
            system_prompt: 系统提示词
            response_schema: 响应JSON Schema
            **kwargs: 其他参数
        """
        self.task_type = task_type
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.response_schema = response_schema
        self.kwargs = kwargs


class AIResponse:
    """AI响应封装"""
    
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        raw_response: Optional[str] = None,
        retry_count: int = 0
    ):
        """
        初始化AI响应
        
        Args:
            success: 是否成功
            data: 响应数据
            error: 错误信息
            raw_response: 原始响应文本
            retry_count: 重试次数
        """
        self.success = success
        self.data = data
        self.error = error
        self.raw_response = raw_response
        self.retry_count = retry_count


class AIClient(ConfigObserver):
    """统一的AI调用客户端"""
    
    def __init__(self):
        """初始化AI客户端"""
        self.base_url: str = config.get('ai.base_url', 'http://localhost:1234')
        self.model: str = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
        self.api_key: str = config.get('ai.api_key', '')
        self.max_tokens: int = config.get('ai.max_tokens', 4096)
        self.temperature: float = config.get('ai.temperature', 0.7)
        self.timeout: int = config.get('ai.timeout', 120)
        
        # AI客户端配置
        self.enable_json_response: bool = config.get('ai.enable_json_response', True)
        self.enable_response_validation: bool = config.get('ai.enable_response_validation', True)
        self.max_retries: int = config.get('ai.max_retries', 3)
        self.retry_delay: float = config.get('ai.retry_delay', 1.0)
        
        # 初始化验证器和重试策略
        self.validator = ResponseValidator()
        self.retry_strategy = RetryStrategy()
        
        # 注册为配置观察者
        config.add_observer(self)
        
        logger.info("AI客户端初始化完成")
    
    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置更新回调
        
        Args:
            config: 更新后的配置字典
        """
        logger.info("AIClient配置已更新")
        ai_config = config.get('ai', {})
        self.base_url = ai_config.get('base_url', 'http://localhost:1234')
        self.model = ai_config.get('model', 'nvidia/nemotron-3-nano-4b')
        self.api_key = ai_config.get('api_key', '')
        self.max_tokens = ai_config.get('max_tokens', 4096)
        self.temperature = ai_config.get('temperature', 0.7)
        self.timeout = ai_config.get('timeout', 120)
        self.enable_json_response = ai_config.get('enable_json_response', True)
        self.enable_response_validation = ai_config.get('enable_response_validation', True)
        self.max_retries = ai_config.get('max_retries', 3)
        self.retry_delay = ai_config.get('retry_delay', 1.0)
    
    def call(self, request: AIRequest) -> AIResponse:
        """
        调用AI接口（带重试机制）
        
        Args:
            request: AI请求对象
            
        Returns:
            AI响应对象
        """
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # 构建消息
                messages = self._build_messages(request)
                
                # 构建调用参数
                call_kwargs = self._build_call_kwargs(request, retry_count)
                
                logger.debug(f"AI调用: task_type={request.task_type}, retry_count={retry_count}")
                
                # 调用AI
                response = completion(**call_kwargs)
                
                # 解析响应
                parsed_response = self._parse_response(response, request)
                
                # 验证响应
                if self.enable_response_validation:
                    validation_result = self.validator.validate(
                        parsed_response,
                        request.task_type,
                        request.response_schema
                    )
                    
                    if not validation_result['valid']:
                        logger.warning(f"响应验证失败: {validation_result['error']}")
                        raise ValueError(f"响应验证失败: {validation_result['error']}")
                
                # 成功返回
                logger.info(f"AI调用成功: task_type={request.task_type}, retry_count={retry_count}")
                return AIResponse(
                    success=True,
                    data=parsed_response,
                    raw_response=str(response),
                    retry_count=retry_count
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"AI调用失败: task_type={request.task_type}, retry_count={retry_count}, error={e}")
                
                # 检查是否可以重试
                if retry_count < self.max_retries:
                    retry_count += 1
                    
                    # 获取重试延迟
                    delay = self.retry_strategy.get_retry_delay(
                        request.task_type,
                        retry_count,
                        str(e)
                    )
                    
                    logger.info(f"等待 {delay:.2f} 秒后重试...")
                    import time
                    time.sleep(delay)
                    
                    # 调整请求参数（根据错误类型）
                    request = self.retry_strategy.adjust_request(
                        request,
                        retry_count,
                        str(e)
                    )
                else:
                    # 超过最大重试次数
                    logger.error(f"AI调用失败，超过最大重试次数: task_type={request.task_type}, error={e}")
                    break
        
        # 所有重试都失败
        return AIResponse(
            success=False,
            error=str(last_error),
            retry_count=retry_count
        )
    
    def _build_messages(self, request: AIRequest) -> List[Dict[str, str]]:
        """
        构建消息列表
        
        Args:
            request: AI请求对象
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加系统消息
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # 添加用户消息
        if self.enable_json_response:
            # 强制要求JSON格式
            json_instruction = self._build_json_instruction(request)
            enhanced_prompt = f"{json_instruction}\n\n{request.prompt}"
            messages.append({
                "role": "user",
                "content": enhanced_prompt
            })
        else:
            messages.append({
                "role": "user",
                "content": request.prompt
            })
        
        return messages
    
    def _build_json_instruction(self, request: AIRequest) -> str:
        """
        构建JSON格式指令
        
        Args:
            request: AI请求对象
            
        Returns:
            JSON格式指令
        """
        instruction = "请严格按照以下JSON格式返回结果，不要包含任何其他内容：\n\n"
        
        if request.response_schema:
            # 使用提供的Schema
            schema_str = self._format_schema(request.response_schema)
            instruction += f"JSON Schema:\n```json\n{schema_str}\n```\n\n"
        else:
            # 使用默认Schema
            default_schema = self._get_default_schema(request.task_type)
            schema_str = self._format_schema(default_schema)
            instruction += f"JSON Schema:\n```json\n{schema_str}\n```\n\n"
        
        instruction += "示例：\n```json\n"
        instruction += self._get_example(request.task_type, request.response_schema)
        instruction += "\n```\n\n"
        instruction += "重要：只返回JSON，不要包含任何解释、标记或其他内容。"
        
        return instruction
    
    def _format_schema(self, schema: Dict[str, Any]) -> str:
        """
        格式化Schema为字符串
        
        Args:
            schema: Schema字典
            
        Returns:
            格式化后的Schema字符串
        """
        import json
        return json.dumps(schema, ensure_ascii=False, indent=2)
    
    def _get_default_schema(self, task_type: str) -> Dict[str, Any]:
        """
        获取默认的JSON Schema
        
        Args:
            task_type: 任务类型
            
        Returns:
            默认Schema
        """
        schemas = {
            'classification': {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "新闻分类列表，最多2个"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关键词列表，最多10个"
                    }
                },
                "required": ["categories", "keywords"]
            },
            'summary': {
                "type": "object",
                "properties": {
                    "comment": {
                        "type": "string",
                        "description": "一句话评价，包含emoji表情"
                    },
                    "summary": {
                        "type": "string",
                        "description": "新闻摘要，120-160字"
                    }
                },
                "required": ["comment", "summary"]
            },
            'scoring': {
                "type": "object",
                "properties": {
                    "relevance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "关联度评分"
                    },
                    "importance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "重要程度评分"
                    },
                    "source_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "来源可信度评分"
                    }
                },
                "required": ["relevance", "importance", "source_score"]
            }
        }
        
        return schemas.get(task_type, {})
    
    def _get_example(self, task_type: str, response_schema: Optional[Dict[str, Any]] = None) -> str:
        """
        获取示例JSON
        
        Args:
            task_type: 任务类型
            response_schema: 响应Schema（可选）
            
        Returns:
            示例JSON字符串
        """
        # 如果提供了response_schema，根据schema生成示例
        if response_schema:
            example = {}
            properties = response_schema.get('properties', {})
            for field_name, field_schema in properties.items():
                field_type = field_schema.get('type', 'string')
                description = field_schema.get('description', '')
                
                if field_type == 'string':
                    if 'emoji' in description.lower():
                        example[field_name] = "📰 示例文本"
                    elif '摘要' in description or 'summary' in description.lower():
                        example[field_name] = "这是一段示例摘要文本，长度在120-160字之间。"
                    elif '理由' in description or 'reason' in description.lower():
                        example[field_name] = "这是评分的理由说明。"
                    else:
                        example[field_name] = "示例文本"
                elif field_type == 'number':
                    minimum = field_schema.get('minimum', 0)
                    maximum = field_schema.get('maximum', 100)
                    example[field_name] = (minimum + maximum) / 2
                elif field_type == 'array':
                    example[field_name] = ["示例1", "示例2"]
                elif field_type == 'object':
                    example[field_name] = {}
            
            import json
            return json.dumps(example, ensure_ascii=False)
        
        # 默认示例（向后兼容）
        examples = {
            'classification': '{"categories": ["科技", "人工智能"], "keywords": ["AI", "机器学习", "深度学习"]}',
            'summary': '{"comment": "📰 这是一篇值得关注的新闻", "summary": "本文介绍了人工智能领域的最新进展，包括大语言模型的应用和发展趋势。"}',
            'scoring': '{"relevance": 85.0, "importance": 75.0, "source_score": 90.0}'
        }
        
        return examples.get(task_type, '{}')
    
    def _build_call_kwargs(self, request: AIRequest, retry_count: int) -> Dict[str, Any]:
        """
        构建调用参数
        
        Args:
            request: AI请求对象
            retry_count: 重试次数
            
        Returns:
            调用参数字典
        """
        kwargs = {
            "model": f'openai/{self.model}',
            "messages": self._build_messages(request),
            "api_base": f"{self.base_url}/v1",
            "api_key": self.api_key if self.api_key else "not-needed",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }
        
        # 添加额外参数
        kwargs.update(request.kwargs)
        
        # 根据重试次数调整超时时间
        if retry_count > 0:
            kwargs['timeout'] = min(self.timeout * (retry_count + 1), 300)
        
        return kwargs
    
    def _parse_response(self, response: Any, request: AIRequest) -> Any:
        """
        解析AI响应
        
        Args:
            response: litellm响应对象
            request: AI请求对象
            
        Returns:
            解析后的数据
        """
        # 检查响应是否有效
        if not response or not response.choices or len(response.choices) == 0:
            raise ValueError("AI响应无效")
        
        message = response.choices[0].message
        if not message:
            raise ValueError("AI响应消息为空")
        
        content = message.content
        
        # 如果content为空，尝试从reasoning_content中提取
        if not content or not content.strip():
            reasoning_content = getattr(message, 'reasoning_content', None) or message.provider_specific_fields.get('reasoning_content', None)
            if reasoning_content and reasoning_content.strip():
                logger.debug("AI返回的content为空，尝试从reasoning_content中提取")
                content = reasoning_content
            else:
                raise ValueError("AI返回内容为空")
        
        # 如果启用JSON响应，解析JSON
        if self.enable_json_response:
            return self._parse_json_response(content, request)
        else:
            # 返回原始文本
            return content
    
    def _parse_json_response(self, content: str, request: AIRequest) -> Dict[str, Any]:
        """
        解析JSON响应
        
        Args:
            content: 响应内容
            request: AI请求对象
            
        Returns:
            解析后的JSON数据
        """
        import json
        import re
        
        # 尝试直接解析JSON
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试提取JSON代码块
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, content, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0].strip())
            except json.JSONDecodeError:
                pass
        
        # 尝试提取花括号内的内容
        brace_pattern = r'\{.*\}'
        matches = re.findall(brace_pattern, content, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[-1].strip())
            except json.JSONDecodeError:
                pass
        
        # 所有尝试都失败
        raise ValueError(f"无法解析JSON响应: {content[:200]}...")


# 创建全局AI客户端实例
ai_client = AIClient()