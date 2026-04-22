"""
重试策略管理器
根据错误类型提供不同的重试策略
"""
from typing import Dict, Any, Optional
from utils.logger import logger


class RetryStrategy:
    """重试策略管理器"""
    
    def __init__(self):
        """初始化重试策略"""
        # 错误类型映射
        self.error_types = {
            'timeout': ['timeout', '超时', 'timed out'],
            'connection': ['connection', '连接', 'connect', 'network'],
            'json_parse': ['json', 'parse', '解析', '格式'],
            'validation': ['validation', '验证', 'invalid', '无效'],
            'service_unavailable': ['unavailable', '不可用', '503', '502'],
            'rate_limit': ['rate limit', '频率', '429'],
            'empty_response': ['empty', '空', 'null']
        }
        
        # 重试延迟配置（秒）
        self.retry_delays = {
            'timeout': 2.0,
            'connection': 3.0,
            'json_parse': 1.0,
            'validation': 1.0,
            'service_unavailable': 5.0,
            'rate_limit': 10.0,
            'empty_response': 1.0,
            'default': 1.0
        }
        
        # 最大重试次数配置
        self.max_retries = {
            'timeout': 3,
            'connection': 3,
            'json_parse': 2,
            'validation': 2,
            'service_unavailable': 5,
            'rate_limit': 3,
            'empty_response': 2,
            'default': 3
        }
        
        logger.info("重试策略管理器初始化完成")
    
    def get_retry_delay(
        self,
        task_type: str,
        retry_count: int,
        error_message: str
    ) -> float:
        """
        获取重试延迟时间
        
        Args:
            task_type: 任务类型
            retry_count: 重试次数
            error_message: 错误消息
            
        Returns:
            延迟时间（秒）
        """
        # 识别错误类型
        error_type = self._identify_error_type(error_message)
        
        # 获取基础延迟
        base_delay = self.retry_delays.get(error_type, self.retry_delays['default'])
        
        # 根据重试次数增加延迟（指数退避）
        delay = base_delay * (1.5 ** (retry_count - 1))
        
        # 限制最大延迟
        delay = min(delay, 30.0)
        
        logger.debug(f"重试延迟: task_type={task_type}, error_type={error_type}, retry_count={retry_count}, delay={delay:.2f}s")
        return delay
    
    def adjust_request(
        self,
        request: Any,
        retry_count: int,
        error_message: str
    ) -> Any:
        """
        根据错误类型调整请求参数
        
        Args:
            request: AI请求对象
            retry_count: 重试次数
            error_message: 错误消息
            
        Returns:
            调整后的请求对象
        """
        # 识别错误类型
        error_type = self._identify_error_type(error_message)
        
        # 根据错误类型调整请求
        if error_type == 'json_parse':
            request = self._adjust_for_json_parse(request, retry_count)
        elif error_type == 'validation':
            request = self._adjust_for_validation(request, retry_count)
        elif error_type == 'empty_response':
            request = self._adjust_for_empty_response(request, retry_count)
        elif error_type == 'timeout':
            request = self._adjust_for_timeout(request, retry_count)
        
        return request
    
    def should_retry(
        self,
        error_type: str,
        retry_count: int
    ) -> bool:
        """
        判断是否应该重试
        
        Args:
            error_type: 错误类型
            retry_count: 重试次数
            
        Returns:
            是否应该重试
        """
        max_retry = self.max_retries.get(error_type, self.max_retries['default'])
        return retry_count < max_retry
    
    def _identify_error_type(self, error_message: str) -> str:
        """
        识别错误类型
        
        Args:
            error_message: 错误消息
            
        Returns:
            错误类型
        """
        error_message_lower = error_message.lower()
        
        # 检查每种错误类型
        for error_type, keywords in self.error_types.items():
            for keyword in keywords:
                if keyword.lower() in error_message_lower:
                    return error_type
        
        # 无法识别，返回默认类型
        return 'default'
    
    def _adjust_for_json_parse(self, request: Any, retry_count: int) -> Any:
        """
        调整请求以解决JSON解析错误
        
        Args:
            request: AI请求对象
            retry_count: 重试次数
            
        Returns:
            调整后的请求对象
        """
        # 在提示词中添加更强的JSON格式要求
        json_instruction = """
重要：必须严格按照JSON格式返回结果，不要包含任何其他内容！
不要使用markdown代码块，不要添加任何解释，只返回纯JSON格式。
"""
        
        if retry_count == 1:
            request.prompt = f"{json_instruction}\n\n{request.prompt}"
        elif retry_count >= 2:
            # 第二次重试，添加更详细的说明
            detailed_instruction = """
重要：必须严格按照JSON格式返回结果！

格式要求：
1. 只返回JSON对象，不要包含任何其他内容
2. 不要使用markdown代码块（```json ... ```）
3. 不要添加任何解释或说明
4. 确保所有字符串都使用双引号
5. 确保所有数字都是有效的数字格式

示例：
{{
  "categories": ["科技"],
  "keywords": ["AI"]
}}
"""
            request.prompt = f"{detailed_instruction}\n\n{request.prompt}"
        
        logger.debug(f"调整请求以解决JSON解析错误，重试次数: {retry_count}")
        return request
    
    def _adjust_for_validation(self, request: Any, retry_count: int) -> Any:
        """
        调整请求以解决验证错误
        
        Args:
            request: AI请求对象
            retry_count: 重试次数
            
        Returns:
            调整后的请求对象
        """
        # 在提示词中添加更详细的约束说明
        if request.task_type == 'classification':
            constraint = """
约束说明：
1. categories字段：必须是字符串数组，包含1-2个分类
2. keywords字段：必须是字符串数组，包含1-10个关键字
3. 所有分类和关键字都不能为空字符串
"""
        elif request.task_type == 'summary':
            constraint = """
约束说明：
1. comment字段：必须是字符串，包含emoji表情，长度不超过100字
2. summary字段：必须是字符串，长度在120-160字之间
3. 两个字段都不能为空
"""
        elif request.task_type == 'scoring':
            constraint = """
约束说明：
1. relevance：数字，范围0-100
2. importance：数字，范围0-100
3. source_score：数字，范围0-100
4. 所有字段都必须是有效数字
"""
        else:
            constraint = """
请确保返回的数据符合预期的格式和约束条件。
"""
        
        request.prompt = f"{constraint}\n\n{request.prompt}"
        
        logger.debug(f"调整请求以解决验证错误，重试次数: {retry_count}")
        return request
    
    def _adjust_for_empty_response(self, request: Any, retry_count: int) -> Any:
        """
        调整请求以解决空响应错误
        
        Args:
            request: AI请求对象
            retry_count: 重试次数
            
        Returns:
            调整后的请求对象
        """
        # 在提示词中添加明确的输出要求
        output_instruction = """
重要：必须返回有效的响应内容，不要返回空内容或null值！
请确保按照要求生成完整的结果。
"""
        
        request.prompt = f"{output_instruction}\n\n{request.prompt}"
        
        logger.debug(f"调整请求以解决空响应错误，重试次数: {retry_count}")
        return request
    
    def _adjust_for_timeout(self, request: Any, retry_count: int) -> Any:
        """
        调整请求以解决超时错误
        
        Args:
            request: AI请求对象
            retry_count: 重试次数
            
        Returns:
            调整后的请求对象
        """
        # 减少输入长度以加快处理速度
        if 'max_input_length' in request.kwargs:
            original_length = request.kwargs['max_input_length']
            reduced_length = int(original_length * 0.8)
            request.kwargs['max_input_length'] = reduced_length
            logger.debug(f"减少输入长度以避免超时: {original_length} -> {reduced_length}")
        
        # 降低温度参数以加快响应
        if 'temperature' in request.kwargs:
            original_temp = request.kwargs['temperature']
            reduced_temp = max(original_temp * 0.9, 0.1)
            request.kwargs['temperature'] = reduced_temp
            logger.debug(f"降低温度参数以加快响应: {original_temp} -> {reduced_temp}")
        
        return request
    
    def get_max_retries(self, error_type: str) -> int:
        """
        获取最大重试次数
        
        Args:
            error_type: 错误类型
            
        Returns:
            最大重试次数
        """
        return self.max_retries.get(error_type, self.max_retries['default'])
    
    def set_retry_delay(self, error_type: str, delay: float):
        """
        设置重试延迟
        
        Args:
            error_type: 错误类型
            delay: 延迟时间（秒）
        """
        self.retry_delays[error_type] = delay
        logger.info(f"设置重试延迟: error_type={error_type}, delay={delay}s")
    
    def set_max_retries(self, error_type: str, max_retries: int):
        """
        设置最大重试次数
        
        Args:
            error_type: 错误类型
            max_retries: 最大重试次数
        """
        self.max_retries[error_type] = max_retries
        logger.info(f"设置最大重试次数: error_type={error_type}, max_retries={max_retries}")