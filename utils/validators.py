"""
参数验证装饰器和模型定义
"""
from functools import wraps
from typing import Dict, Any, Type, Optional
from urllib.parse import parse_qs, urlparse


try:
    from pydantic import BaseModel, Field, ValidationError
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    ValidationError = Exception


def validate_params(model_class: Type[BaseModel]):
    """
    参数验证装饰器（用于类方法）
    
    Args:
        model_class: pydantic模型类
        
    Returns:
        装饰器函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, handler):
            try:
                # 解析请求参数
                params = parse_request_params(handler)
                
                # 验证参数
                if HAS_PYDANTIC:
                    validated = model_class(**params)
                    return func(self, handler, validated)
                else:
                    # 如果没有pydantic，直接传递原始参数
                    return func(self, handler, params)
                    
            except ValidationError as e:
                error_msg = f"参数验证失败: {str(e)}"
                handler._send_error_response(error_msg)
            except Exception as e:
                handler._send_error_response(f"参数解析失败: {str(e)}")
        return wrapper
    return decorator


def parse_request_params(handler) -> Dict[str, Any]:
    """
    解析请求参数
    
    Args:
        handler: HTTP请求处理器
        
    Returns:
        参数字典
    """
    params = {}
    
    # 解析GET参数
    if hasattr(handler, 'path'):
        parsed_path = urlparse(handler.path)
        query_params = parse_qs(parsed_path.query)
        for key, values in query_params.items():
            if len(values) == 1:
                params[key] = values[0]
            else:
                params[key] = values
    
    # 解析POST参数
    if hasattr(handler, 'headers') and hasattr(handler, 'rfile'):
        content_length = handler.headers.get('Content-Length', 0)
        if content_length:
            try:
                import json
                post_data = handler.rfile.read(int(content_length))
                post_params = json.loads(post_data.decode('utf-8'))
                params.update(post_params)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
    
    # 类型转换：将字符串转换为适当的类型
    type_conversions = {
        'limit': int,
        'offset': int,
        'news_id': int,
        'force': lambda x: x.lower() in ('true', '1', 'yes') if isinstance(x, str) else bool(x),
        'use_rag': lambda x: x.lower() in ('true', '1', 'yes') if isinstance(x, str) else bool(x),
    }
    
    for key, converter in type_conversions.items():
        if key in params and isinstance(params[key], str):
            try:
                params[key] = converter(params[key])
            except (ValueError, TypeError):
                pass
    
    return params


# 参数模型定义
if HAS_PYDANTIC:
    class GetNewsParams(BaseModel):
        """获取新闻列表参数"""
        limit: int = Field(default=30, ge=1, le=100, description="返回数量")
        offset: int = Field(default=0, ge=0, description="偏移量")
    
    class SearchNewsParams(BaseModel):
        """搜索新闻参数"""
        q: str = Field(..., min_length=1, max_length=100, description="搜索关键词")
        limit: int = Field(default=10, ge=1, le=50, description="返回数量")
    
    class GetNewsByCategoryParams(BaseModel):
        """按分类获取新闻参数"""
        category: str = Field(..., min_length=1, max_length=50, description="分类名称")
        limit: int = Field(default=30, ge=1, le=100, description="返回数量")
        offset: int = Field(default=0, ge=0, description="偏移量")
    
    class ProcessNewsParams(BaseModel):
        """处理新闻参数"""
        news_id: int = Field(..., gt=0, description="新闻ID")
        force: bool = Field(default=False, description="是否强制重新处理")
    
    class MarkAsReadParams(BaseModel):
        """标记已读参数"""
        news_id: int = Field(..., gt=0, description="新闻ID")
        is_read: bool = Field(default=True, description="是否已读")
    
    class ChatParams(BaseModel):
        """对话参数"""
        session_id: Optional[str] = Field(None, description="会话ID")
        message: str = Field(..., min_length=1, max_length=1000, description="用户消息")
        use_rag: bool = Field(default=True, description="是否使用RAG")
    
    class GetChatHistoryParams(BaseModel):
        """获取对话历史参数"""
        session_id: str = Field(..., min_length=1, description="会话ID")
        limit: int = Field(default=50, ge=1, le=100, description="返回数量")
    
    class GetReadNewsParams(BaseModel):
        """获取已读新闻参数"""
        limit: int = Field(default=100, ge=1, le=500, description="返回数量")
    
    class GetUnreadNewsParams(BaseModel):
        """获取未读新闻参数"""
        limit: int = Field(default=100, ge=1, le=500, description="返回数量")
    
    class GetNewsDetailParams(BaseModel):
        """获取新闻详情参数"""
        id: int = Field(..., gt=0, description="新闻ID")
    
    class GenerateReportParams(BaseModel):
        """生成报告参数"""
        report_type: str = Field(default='daily', description="报告类型")
        hours: int = Field(default=24, ge=1, le=720, description="时间范围（小时）")
    
    class GetReportsParams(BaseModel):
        """获取报告列表参数"""
        type: str = Field(default='daily', description="报告类型")
        limit: int = Field(default=10, ge=1, le=100, description="返回数量")
        offset: int = Field(default=0, ge=0, description="偏移量")
    
    class GetReportDetailParams(BaseModel):
        """获取报告详情参数"""
        id: int = Field(..., gt=0, description="报告ID")
    
    class DeleteReportParams(BaseModel):
        """删除报告参数"""
        id: int = Field(..., gt=0, description="报告ID")
    
    class GetLatestReportParams(BaseModel):
        """获取最新报告参数"""
        type: str = Field(default='daily', description="报告类型")
    
    class UpdateConfigParams(BaseModel):
        """更新配置参数"""
        config: Dict[str, Any] = Field(..., description="配置数据")
else:
    # 如果没有pydantic，使用简单的字典类型
    GetNewsParams = Dict[str, Any]
    SearchNewsParams = Dict[str, Any]
    GetNewsByCategoryParams = Dict[str, Any]
    ProcessNewsParams = Dict[str, Any]
    MarkAsReadParams = Dict[str, Any]
    ChatParams = Dict[str, Any]
    GetChatHistoryParams = Dict[str, Any]
    UpdateConfigParams = Dict[str, Any]


def validate_get_news_params(func):
    """获取新闻列表参数验证装饰器"""
    return validate_params(GetNewsParams)(func)


def validate_search_news_params(func):
    """搜索新闻参数验证装饰器"""
    return validate_params(SearchNewsParams)(func)


def validate_get_news_by_category_params(func):
    """按分类获取新闻参数验证装饰器"""
    return validate_params(GetNewsByCategoryParams)(func)


def validate_process_news_params(func):
    """处理新闻参数验证装饰器"""
    return validate_params(ProcessNewsParams)(func)


def validate_process_news_category_params(func):
    """处理新闻分类参数验证装饰器"""
    return validate_params(ProcessNewsParams)(func)


def validate_process_news_summary_params(func):
    """处理新闻摘要参数验证装饰器"""
    return validate_params(ProcessNewsParams)(func)


def validate_process_news_reanalyze_params(func):
    """处理新闻重新分析参数验证装饰器"""
    return validate_params(ProcessNewsParams)(func)


def validate_get_news_detail_params(func):
    """获取新闻详情参数验证装饰器"""
    return validate_params(GetNewsDetailParams)(func)


def validate_mark_as_read_params(func):
    """标记已读参数验证装饰器"""
    return validate_params(MarkAsReadParams)(func)


def validate_get_read_news_params(func):
    """获取已读新闻参数验证装饰器"""
    return validate_params(GetReadNewsParams)(func)


def validate_get_unread_news_params(func):
    """获取未读新闻参数验证装饰器"""
    return validate_params(GetUnreadNewsParams)(func)


def validate_update_config_params(func):
    """更新配置参数验证装饰器"""
    return validate_params(UpdateConfigParams)(func)


def validate_mark_as_read_params(func):
    """标记已读参数验证装饰器"""
    return validate_params(MarkAsReadParams)(func)


def validate_chat_params(func):
    """对话参数验证装饰器"""
    return validate_params(ChatParams)(func)


def validate_get_chat_history_params(func):
    """获取对话历史参数验证装饰器"""
    return validate_params(GetChatHistoryParams)(func)


def validate_update_config_params(func):
    """更新配置参数验证装饰器"""
    return validate_params(UpdateConfigParams)(func)


def validate_generate_report_params(func):
    """生成报告参数验证装饰器"""
    return validate_params(GenerateReportParams)(func)


def validate_get_reports_params(func):
    """获取报告列表参数验证装饰器"""
    return validate_params(GetReportsParams)(func)


def validate_get_report_detail_params(func):
    """获取报告详情参数验证装饰器"""
    return validate_params(GetReportDetailParams)(func)


def validate_delete_report_params(func):
    """删除报告参数验证装饰器"""
    return validate_params(DeleteReportParams)(func)


def validate_get_latest_report_params(func):
    """获取最新报告参数验证装饰器"""
    return validate_params(GetLatestReportParams)(func)


def validate_update_config_params(func):
    """更新配置参数验证装饰器"""
    return validate_params(UpdateConfigParams)(func)