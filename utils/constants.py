"""
常量定义模块
"""
from typing import List


class AIConstants:
    """AI相关常量"""
    
    # 默认AI配置
    DEFAULT_BASE_URL = "http://localhost:1234"
    DEFAULT_MODEL = "nvidia/nemotron-3-nano-4b"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_MAX_WORKERS = 1
    DEFAULT_BATCH_SIZE = 1
    
    # AI处理配置
    DEFAULT_SUMMARY_THRESHOLD = 140
    DEFAULT_MAX_INPUT_LENGTH = 2000
    DEFAULT_TIMEOUT = 120
    
    # AI分类配置
    DEFAULT_MAX_INPUT_LENGTH_CLASSIFIER = 800
    DEFAULT_CLASSIFY_MAX_TOKENS = 256
    
    # AI摘要配置
    DEFAULT_SUMMARY_MAX_TOKENS = 512


class DatabaseConstants:
    """数据库相关常量"""
    
    # 数据库文件路径
    DEFAULT_DB_PATH = "data/kwafoo.db"
    
    # 查询限制
    DEFAULT_QUERY_LIMIT = 30
    DEFAULT_QUERY_OFFSET = 0
    MAX_QUERY_LIMIT = 100
    
    # 批量操作大小
    DEFAULT_BATCH_SIZE = 10
    MAX_BATCH_SIZE = 50


class ServerConstants:
    """服务器相关常量"""
    
    # 服务器配置
    DEFAULT_HOST = "0.0.0.0"
    DEFAULT_PORT = 8000
    
    # WebSocket配置
    DEFAULT_WEBSOCKET_ENABLED = True
    
    # 响应头
    CONTENT_TYPE_JSON = "application/json"
    CONTENT_TYPE_HTML = "text/html; charset=utf-8"
    ACCESS_CONTROL_ALLOW_ORIGIN = "*"


class SchedulerConstants:
    """调度器相关常量"""
    
    # 调度间隔
    DEFAULT_FETCH_INTERVAL = 1800  # 30分钟
    DEFAULT_AI_PROCESS_INTERVAL = 600  # 10分钟
    
    # 并发控制
    DEFAULT_MAX_FETCH_WORKERS = 20
    MIN_FETCH_WORKERS = 1
    MAX_FETCH_WORKERS = 50
    
    # 自动任务配置
    DEFAULT_AUTO_FETCH = False
    DEFAULT_AUTO_AI_PROCESS = False
    DEFAULT_AUTO_AI_AFTER_FETCH = False


class NetworkConstants:
    """网络相关常量"""
    
    # 代理配置
    DEFAULT_ENABLE_PROXY = False
    DEFAULT_PROXY_URL = ""
    
    # 超时配置
    DEFAULT_REQUEST_TIMEOUT = 30
    DEFAULT_CONNECT_TIMEOUT = 10


class ImageConstants:
    """图片相关常量"""
    
    # 存储配置
    DEFAULT_STORAGE_MODE = "filesystem"
    DEFAULT_STORAGE_PATH = "data/images"
    
    # 缩略图配置
    DEFAULT_THUMBNAIL_WIDTH = 128
    DEFAULT_THUMBNAIL_HEIGHT = 128
    
    # 图片大小限制
    DEFAULT_MAX_IMAGE_SIZE = 5242880  # 5MB
    
    # 支持的图片格式
    SUPPORTED_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp", "gif"]
    
    # 显示配置
    DEFAULT_DISPLAY_POSITION = "right"
    DEFAULT_SHOW_THUMBNAIL = True


class LoggingConstants:
    """日志相关常量"""
    
    # 日志配置
    DEFAULT_LOG_LEVEL = "INFO"
    DEFAULT_LOG_FILE = "data/logs/kwafoo.log"
    
    # 日志文件大小限制
    DEFAULT_MAX_SIZE = 10485760  # 10MB
    DEFAULT_BACKUP_COUNT = 5
    
    # 日志级别
    LOG_LEVEL_DEBUG = "DEBUG"
    LOG_LEVEL_INFO = "INFO"
    LOG_LEVEL_WARNING = "WARNING"
    LOG_LEVEL_ERROR = "ERROR"
    LOG_LEVEL_CRITICAL = "CRITICAL"


class APIConstants:
    """API相关常量"""
    
    # 分页参数
    DEFAULT_PAGE_SIZE = 30
    DEFAULT_PAGE_OFFSET = 0
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1
    
    # 搜索参数
    DEFAULT_SEARCH_LIMIT = 10
    MAX_SEARCH_LIMIT = 50
    MIN_SEARCH_QUERY_LENGTH = 1
    MAX_SEARCH_QUERY_LENGTH = 100
    
    # 对话参数
    DEFAULT_CHAT_HISTORY_LIMIT = 50
    MAX_CHAT_HISTORY_LIMIT = 100
    MIN_CHAT_HISTORY_LIMIT = 1
    MAX_MESSAGE_LENGTH = 1000


class RAGConstants:
    """RAG相关常量"""
    
    # 检索配置
    DEFAULT_TOP_K = 5
    MIN_TOP_K = 1
    MAX_TOP_K = 20
    
    # FTS配置
    DEFAULT_USE_FTS = True


class ErrorCodeConstants:
    """错误码常量"""
    
    # 数据库错误
    DB_CONNECTION_ERROR = "DB001"
    DB_QUERY_ERROR = "DB002"
    DB_INSERT_ERROR = "DB003"
    DB_UPDATE_ERROR = "DB004"
    DB_DELETE_ERROR = "DB005"
    
    # AI错误
    AI_CONNECTION_ERROR = "AI001"
    AI_API_ERROR = "AI002"
    AI_TIMEOUT_ERROR = "AI003"
    AI_MODEL_ERROR = "AI004"
    AI_CLASSIFICATION_ERROR = "AI005"
    AI_SUMMARY_ERROR = "AI006"
    
    # 网络错误
    NETWORK_CONNECTION_ERROR = "NET001"
    NETWORK_TIMEOUT_ERROR = "NET002"
    NETWORK_PROXY_ERROR = "NET003"
    
    # API错误
    API_INVALID_PARAMS = "API001"
    API_MISSING_PARAMS = "API002"
    API_NOT_FOUND = "API003"
    API_SERVER_ERROR = "API004"
    
    # 配置错误
    CONFIG_LOAD_ERROR = "CFG001"
    CONFIG_SAVE_ERROR = "CFG002"
    CONFIG_INVALID_VALUE = "CFG003"
    
    # 文件错误
    FILE_NOT_FOUND = "FILE001"
    FILE_READ_ERROR = "FILE002"
    FILE_WRITE_ERROR = "FILE003"
    FILE_SIZE_EXCEEDED = "FILE004"


class HTTPStatusConstants:
    """HTTP状态码常量"""
    
    # 成功响应
    OK = 200
    
    # 客户端错误
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    
    # 服务器错误
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503