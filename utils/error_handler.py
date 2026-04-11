"""
全局异常处理模块
提供统一的错误处理和响应格式
"""

from typing import Dict, Any, Optional
from utils.logger import logger


class APIError(Exception):
    """API错误基类"""
    def __init__(self, message: str, status_code: int = 500, error_code: str = 'INTERNAL_ERROR'):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(APIError):
    """验证错误"""
    def __init__(self, message: str):
        super().__init__(message, 400, 'VALIDATION_ERROR')


class NotFoundError(APIError):
    """资源未找到错误"""
    def __init__(self, message: str = '资源未找到'):
        super().__init__(message, 404, 'NOT_FOUND')


class ConflictError(APIError):
    """冲突错误"""
    def __init__(self, message: str):
        super().__init__(message, 409, 'CONFLICT')


class UnauthorizedError(APIError):
    """未授权错误"""
    def __init__(self, message: str = '未授权'):
        super().__init__(message, 401, 'UNAUTHORIZED')


class ForbiddenError(APIError):
    """禁止访问错误"""
    def __init__(self, message: str = '禁止访问'):
        super().__init__(message, 403, 'FORBIDDEN')


class RateLimitError(APIError):
    """限流错误"""
    def __init__(self, message: str = '请求过于频繁'):
        super().__init__(message, 429, 'RATE_LIMIT_EXCEEDED')


class ServiceUnavailableError(APIError):
    """服务不可用错误"""
    def __init__(self, message: str = '服务暂时不可用'):
        super().__init__(message, 503, 'SERVICE_UNAVAILABLE')


def handle_api_error(error: Exception) -> Dict[str, Any]:
    """
    处理API错误，返回统一的错误响应格式
    
    Args:
        error: 异常对象
        
    Returns:
        标准化的错误响应字典
    """
    if isinstance(error, APIError):
        # 已知的API错误
        logger.warning(f"API错误: {error.error_code} - {error.message}")
        return {
            'success': False,
            'error': {
                'code': error.error_code,
                'message': error.message,
                'status_code': error.status_code
            }
        }
    else:
        # 未知错误
        logger.error(f"未处理的异常: {type(error).__name__} - {str(error)}", exc_info=True)
        return {
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': '服务器内部错误',
                'status_code': 500
            }
        }


def create_error_response(error: Exception) -> tuple[Dict[str, Any], int]:
    """
    创建错误HTTP响应
    
    Args:
        error: 异常对象
        
    Returns:
        (响应字典, HTTP状态码)
    """
    error_data = handle_api_error(error)
    status_code = error_data['error']['status_code']
    return error_data, status_code


def log_request(method: str, path: str, status_code: int, duration: float, user_agent: str = ''):
    """
    记录API请求日志
    
    Args:
        method: HTTP方法
        path: 请求路径
        status_code: 响应状态码
        duration: 请求处理时间（秒）
        user_agent: 用户代理字符串
    """
    log_level = 'info' if status_code < 400 else 'warning' if status_code < 500 else 'error'
    
    log_message = f"{method} {path} - {status_code} - {duration:.3f}s"
    if user_agent:
        log_message += f" - {user_agent}"
    
    getattr(logger, log_level)(log_message)