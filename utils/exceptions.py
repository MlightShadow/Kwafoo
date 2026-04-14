"""
Kwafoo异常体系和错误码定义
"""
from enum import Enum
from typing import Optional


class KwafooException(Exception):
    """Kwafoo基础异常类"""
    
    def __init__(self, code: str, message: str, details: Optional[str] = None):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(f"[{code}] {message}")


class DatabaseException(KwafooException):
    """数据库异常"""
    pass


class AIException(KwafooException):
    """AI处理异常"""
    pass


class APIException(KwafooException):
    """API异常"""
    pass


class ConfigException(KwafooException):
    """配置异常"""
    pass


class SchedulerException(KwafooException):
    """调度器异常"""
    pass


class ErrorCode(Enum):
    """错误码枚举"""
    
    # 数据库错误 (DB001-DB099)
    DATABASE_CONNECTION_ERROR = ("DB001", "数据库连接失败")
    DATABASE_QUERY_ERROR = ("DB002", "数据库查询失败")
    DATABASE_INSERT_ERROR = ("DB003", "数据库插入失败")
    DATABASE_UPDATE_ERROR = ("DB004", "数据库更新失败")
    DATABASE_DELETE_ERROR = ("DB005", "数据库删除失败")
    DATABASE_CONNECTION_TIMEOUT = ("DB006", "数据库连接超时")
    DATABASE_CONNECTION_LOST = ("DB007", "数据库连接丢失")
    DATABASE_TRANSACTION_ERROR = ("DB008", "数据库事务错误")
    DATABASE_SCHEMA_ERROR = ("DB009", "数据库结构错误")
    
    # AI处理错误 (AI001-AI099)
    AI_TIMEOUT_ERROR = ("AI001", "AI处理超时")
    AI_CONNECTION_ERROR = ("AI002", "AI服务连接失败")
    AI_REQUEST_ERROR = ("AI003", "AI请求失败")
    AI_RESPONSE_ERROR = ("AI004", "AI响应格式错误")
    AI_CLASSIFICATION_ERROR = ("AI005", "AI分类失败")
    AI_SUMMARY_ERROR = ("AI006", "AI摘要生成失败")
    AI_SERVICE_UNAVAILABLE = ("AI007", "AI服务不可用")
    AI_RATE_LIMIT_EXCEEDED = ("AI008", "AI请求频率超限")
    
    # API错误 (API001-API099)
    INVALID_PARAMETER = ("API001", "参数无效")
    MISSING_PARAMETER = ("API002", "缺少必需参数")
    RESOURCE_NOT_FOUND = ("API003", "资源不存在")
    METHOD_NOT_ALLOWED = ("API004", "请求方法不允许")
    UNAUTHORIZED = ("API005", "未授权")
    FORBIDDEN = ("API006", "禁止访问")
    RATE_LIMIT_EXCEEDED = ("API007", "请求频率超限")
    INTERNAL_SERVER_ERROR = ("API008", "服务器内部错误")
    
    # 配置错误 (CFG001-CFG099)
    CONFIG_FILE_NOT_FOUND = ("CFG001", "配置文件不存在")
    CONFIG_PARSE_ERROR = ("CFG002", "配置文件解析失败")
    CONFIG_INVALID_VALUE = ("CFG003", "配置值无效")
    CONFIG_MISSING_SECTION = ("CFG004", "配置节缺失")
    CONFIG_MISSING_KEY = ("CFG005", "配置键缺失")
    
    # 调度器错误 (SCH001-SCH099)
    SCHEDULER_ALREADY_RUNNING = ("SCH001", "调度器已在运行")
    SCHEDULER_NOT_RUNNING = ("SCH002", "调度器未运行")
    TASK_ALREADY_RUNNING = ("SCH003", "任务已在运行")
    TASK_NOT_FOUND = ("SCH004", "任务不存在")
    TASK_EXECUTION_ERROR = ("SCH005", "任务执行失败")
    
    # 新闻抓取错误 (FET001-FET099)
    FETCH_SOURCE_ERROR = ("FET001", "新闻源抓取失败")
    FETCH_PARSE_ERROR = ("FET002", "新闻解析失败")
    FETCH_TIMEOUT = ("FET003", "抓取超时")
    FETCH_CONNECTION_ERROR = ("FET004", "抓取连接失败")
    
    # 图片处理错误 (IMG001-IMG099)
    IMAGE_DOWNLOAD_ERROR = ("IMG001", "图片下载失败")
    IMAGE_PROCESS_ERROR = ("IMG002", "图片处理失败")
    IMAGE_SIZE_EXCEEDED = ("IMG003", "图片大小超限")
    IMAGE_FORMAT_UNSUPPORTED = ("IMG004", "不支持的图片格式")
    
    @classmethod
    def get_message(cls, code: str) -> Optional[str]:
        """根据错误码获取错误消息"""
        for error_code in cls:
            if error_code.value[0] == code:
                return error_code.value[1]
        return None
    
    @classmethod
    def get_error(cls, code: str, details: Optional[str] = None) -> KwafooException:
        """根据错误码创建异常实例"""
        message = cls.get_message(code)
        if not message:
            message = "未知错误"
        
        # 根据错误码前缀确定异常类型
        if code.startswith("DB"):
            return DatabaseException(code, message, details)
        elif code.startswith("AI"):
            return AIException(code, message, details)
        elif code.startswith("API"):
            return APIException(code, message, details)
        elif code.startswith("CFG"):
            return ConfigException(code, message, details)
        elif code.startswith("SCH"):
            return SchedulerException(code, message, details)
        else:
            return KwafooException(code, message, details)