import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from utils.logger import logger
try:
    import tomllib
    HAS_TOML = True
    USE_TOMLLIB = True
except ImportError:
    try:
        import tomli
        HAS_TOML = True
        USE_TOMLLIB = False
    except ImportError:
        HAS_TOML = False
        USE_TOMLLIB = False

try:
    import tomli_w
    HAS_TOML_W = True
except ImportError:
    HAS_TOML_W = False

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("环境变量文件 .env 加载成功")
except ImportError:
    logger.warning("python-dotenv 未安装，.env 文件将被忽略")
    logger.warning("请运行: pip install python-dotenv")
    logger.warning("或执行: pip install -r requirements.txt")


class ConfigObserver(ABC):
    """配置观察者抽象基类"""
    
    @abstractmethod
    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置更新回调
        
        Args:
            config: 更新后的配置字典
        """
        pass


class Config:
    _instance: Optional['Config'] = None
    _config: Optional[Dict[str, Any]] = None
    _observers: List[ConfigObserver] = []

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._config is None:
            self._config = self._load_config()

    def add_observer(self, observer: ConfigObserver):
        """
        添加配置观察者
        
        Args:
            observer: 观察者对象
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"添加配置观察者: {observer.__class__.__name__}")

    def remove_observer(self, observer: ConfigObserver):
        """
        移除配置观察者
        
        Args:
            observer: 观察者对象
        """
        if observer in self._observers:
            self._observers.remove(observer)
            logger.debug(f"移除配置观察者: {observer.__class__.__name__}")

    def notify_observers(self):
        """通知所有观察者配置已更新"""
        logger.debug(f"通知 {len(self._observers)} 个配置观察者")
        for observer in self._observers:
            try:
                observer.on_config_changed(self._config)
            except Exception as e:
                logger.error(f"通知观察者 {observer.__class__.__name__} 失败: {e}")

    def _load_config(self, config_path: str = 'config.toml') -> Dict[str, Any]:
        try:
            with open(config_path, 'rb') as f:
                if HAS_TOML:
                    if USE_TOMLLIB:
                        config = tomllib.load(f)
                    else:
                        config = tomli.load(f)
                    logger.info(f"配置文件加载成功: {config_path}")
                else:
                    logger.error("未安装toml解析库，请运行: pip install tomli")
                    return self._get_default_config()
            
            config = self._apply_env_overrides(config)
            
            return config
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {config_path}")
            return self._get_default_config()
        except Exception as e:
            logger.error(f"配置文件格式错误: {e}")
            return self._get_default_config()

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        env_mappings = {
            'DATABASE_PATH': ('database', 'path'),
            'AI_BASE_URL': ('ai', 'base_url'),
            'AI_MODEL': ('ai', 'model'),
            'AI_API_KEY': ('ai', 'api_key'),
            'AI_MAX_TOKENS': ('ai', 'max_tokens'),
            'AI_TEMPERATURE': ('ai', 'temperature'),
            'AI_MAX_WORKERS': ('ai', 'max_workers'),
            'AI_BATCH_SIZE': ('ai', 'batch_size'),
            'AI_ENABLE_SUMMARY': ('ai', 'enable_summary'),
            'AI_ENABLE_SUMMARY_COMMENT': ('ai', 'enable_summary_comment'),
            'AI_ENABLE_CLASSIFIER_REASONING': ('ai', 'enable_classifier_reasoning'),
            'AI_ENABLE_SUMMARIZER_REASONING': ('ai', 'enable_summarizer_reasoning'),
            'AI_COMMENT_STANCE_NATIONALITY': ('ai.comment_stance', 'nationality'),
            'AI_COMMENT_STANCE_GENDER': ('ai.comment_stance', 'gender'),
            'AI_COMMENT_STANCE_AGE': ('ai.comment_stance', 'age'),
            'AI_COMMENT_STANCE_FAMILY_STATUS': ('ai.comment_stance', 'family_status'),
            'AI_COMMENT_STANCE_INCOME': ('ai.comment_stance', 'income'),
            'AI_COMMENT_STANCE_HEALTH_STATUS': ('ai.comment_stance', 'health_status'),
            'AI_COMMENT_STANCE_RELIGION': ('ai.comment_stance', 'religion'),
            'AI_COMMENT_STANCE_CUSTOM_DESCRIPTION': ('ai.comment_stance', 'custom_description'),
            'SERVER_HOST': ('server', 'host'),
            'SERVER_PORT': ('server', 'port'),
            'SERVER_ENABLE_WEBSOCKET': ('server', 'enable_websocket'),
            'SCHEDULER_FETCH_INTERVAL': ('scheduler', 'fetch_interval'),
            'SCHEDULER_AI_PROCESS_INTERVAL': ('scheduler', 'ai_process_interval'),
            'SCHEDULER_AUTO_FETCH': ('scheduler', 'auto_fetch'),
            'SCHEDULER_AUTO_AI_PROCESS': ('scheduler', 'auto_ai_process'),
            'LOGGING_LEVEL': ('logging', 'level'),
            'LOGGING_FILE': ('logging', 'file'),
            'RAG_TOP_K': ('rag', 'top_k'),
            'RAG_USE_FTS': ('rag', 'use_fts'),
            'NETWORK_ENABLE_PROXY': ('network', 'enable_proxy'),
            'NETWORK_PROXY_URL': ('network', 'proxy_url'),
            'IMAGE_ENABLE_FETCH': ('image', 'enable_fetch'),
            'REPORT_ENABLE_AUTO_GENERATE': ('report', 'enable_auto_generate'),
            'REPORT_AUTO_GENERATE_TYPES': ('report', 'auto_generate_types'),
            'REPORT_DAILY_GENERATE_TIME': ('report', 'daily_generate_time'),
            'REPORT_WEEKLY_GENERATE_DAY': ('report', 'weekly_generate_day'),
            'REPORT_WEEKLY_GENERATE_TIME': ('report', 'weekly_generate_time'),
            'REPORT_MONTHLY_GENERATE_DAY': ('report', 'monthly_generate_day'),
            'REPORT_MONTHLY_GENERATE_TIME': ('report', 'monthly_generate_time'),
            'REPORT_MAX_NEWS_COUNT': ('report', 'max_news_count'),
            'REPORT_AI_MODEL': ('report', 'report_ai_model'),
            'REPORT_AI_TEMPERATURE': ('report', 'report_ai_temperature'),
            'REPORT_AI_TIMEOUT': ('report', 'report_ai_timeout'),
            'CONTENT_FETCH_ENABLE': ('content_fetch', 'enable_content_fetch'),
            'CONTENT_FETCH_ALGORITHM': ('content_fetch', 'algorithm'),
            'CONTENT_FETCH_MIN_CONTENT_LENGTH': ('content_fetch', 'min_content_length'),
            'CONTENT_FETCH_MAX_CONTENT_LENGTH': ('content_fetch', 'max_content_length'),
            'CONTENT_FETCH_TIMEOUT': ('content_fetch', 'timeout'),
            'CONTENT_FETCH_USE_PROXY': ('content_fetch', 'use_proxy'),
            'CONTENT_FETCH_ENABLE_CACHE': ('content_fetch', 'enable_cache'),
            'IMAGE_DISPLAY_POSITION': ('image.display', 'position'),
            'IMAGE_DISPLAY_SHOW_THUMBNAIL': ('image.display', 'show_thumbnail'),
            'COMPRESSION_ENABLE_COMPRESSION': ('compression', 'enable_compression'),
            'COMPRESSION_TARGET_TOKENS': ('compression', 'target_tokens'),
            'COMPRESSION_COMPRESSION_LEVEL': ('compression', 'compression_level'),
            'COMPRESSION_ALGORITHM': ('compression', 'algorithm'),
            'COMPRESSION_MODE': ('compression', 'mode'),
            'COMPRESSION_MAX_IMAGE_SIZE': ('compression', 'max_image_size'),
        }
        
        for env_key, (section, key) in env_mappings.items():
            value = os.environ.get(env_key)
            if value is not None:
                if '.' in section:
                    parts = section.split('.')
                    config_section = config
                    for part in parts:
                        if part not in config_section:
                            config_section[part] = {}
                        config_section = config_section[part]
                    
                    if key in ['enable_summary', 'auto_fetch', 'auto_ai_process', 'auto_ai_after_fetch', 'enable_websocket', 'use_fts', 'enable_proxy', 'enable_fetch', 'enable_summary_comment', 'enable_classifier_reasoning', 'enable_summarizer_reasoning', 'enable_auto_generate', 'enable_content_fetch', 'use_proxy', 'enable_cache', 'show_thumbnail', 'enable_compression']:
                        config_section[key] = value.lower() in ('true', '1', 'yes')
                    elif key == 'auto_generate_types':
                        try:
                            import json
                            config_section[key] = json.loads(value)
                        except (json.JSONDecodeError, ValueError):
                            config_section[key] = value.split(',')
                    elif key in ['max_tokens', 'fetch_interval', 'ai_process_interval', 'port', 'top_k', 'max_size', 'backup_count', 'width', 'height', 'max_image_size', 'max_workers', 'batch_size', 'max_news_count', 'report_ai_timeout', 'min_content_length', 'max_content_length', 'timeout', 'target_tokens', 'max_image_size']:
                        try:
                            config_section[key] = int(value)
                        except ValueError:
                            pass
                    elif key in ['report_ai_temperature', 'temperature']:
                        try:
                            config_section[key] = float(value)
                        except ValueError:
                            pass
                    else:
                        config_section[key] = value
                elif section in config:
                    if key in ['max_tokens', 'fetch_interval', 'ai_process_interval', 'port', 'top_k', 'max_size', 'backup_count', 'width', 'height', 'max_image_size', 'max_workers', 'batch_size', 'max_news_count', 'report_ai_timeout', 'min_content_length', 'max_content_length', 'timeout', 'target_tokens', 'max_image_size']:
                        try:
                            config[section][key] = int(value)
                        except ValueError:
                            pass
                    elif key in ['enable_summary', 'auto_fetch', 'auto_ai_process', 'auto_ai_after_fetch', 'enable_websocket', 'use_fts', 'enable_proxy', 'enable_fetch', 'enable_summary_comment', 'enable_classifier_reasoning', 'enable_summarizer_reasoning', 'enable_auto_generate', 'enable_content_fetch', 'use_proxy', 'enable_cache', 'show_thumbnail', 'enable_compression']:
                        config[section][key] = value.lower() in ('true', '1', 'yes')
                    elif key == 'auto_generate_types':
                        try:
                            import json
                            config[section][key] = json.loads(value)
                        except (json.JSONDecodeError, ValueError):
                            config[section][key] = value.split(',')
                    elif key in ['report_ai_temperature', 'temperature']:
                        try:
                            config[section][key] = float(value)
                        except ValueError:
                            pass
                    else:
                        config[section][key] = value
        
        return config

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'database': {
                'path': 'data/kwafoo.db'
            },
            'news_sources': {
                'rss': [],
                'api': [],
                'web': []
            },
            'categories': {},
            'default_category': '未分类',
            'enable_ai_category': False,
            'ai_summary_threshold': 140,
            'ai_category_prompt': '',
            'enable_ai_summary': False,
            'scheduler': {
                'fetch_interval': 1800,
                'ai_process_interval': 600,
                'auto_fetch': False,
                'auto_ai_process': False,
                'auto_ai_after_fetch': False,
                'max_fetch_workers': 20
            },
            'network': {
                'enable_proxy': False,
                'proxy_url': ''
            },
            'image': {
                'enable_fetch': True,
                'thumbnail_size': {
                    'width': 256,
                    'height': 256
                },
                'default_image': '',
                'supported_formats': ['jpg', 'jpeg', 'png', 'webp', 'gif'],
                'max_image_size': 5242880
            },
            'ai': {
                'base_url': 'http://localhost:1234',
                'model': 'nvidia/nemotron-3-nano-4b',
                'api_key': '',
                'max_tokens': 4096,
                'temperature': 0.7,
                'max_workers': 1,
                'batch_size': 1,
                'enable_summary': True
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'enable_websocket': True
            },
            'rag': {
                'top_k': 5,
                'use_fts': True
            },
            'logging': {
                'level': 'INFO',
                'file': 'data/logs/kwafoo.log',
                'max_size': 10485760,
                'backup_count': 5
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.debug(f"配置更新: {key} = {value}")

    def save(self, config_path: str = 'config.toml'):
        try:
            if HAS_TOML_W:
                with open(config_path, 'wb') as f:
                    tomli_w.dump(self._config, f)
                logger.info(f"配置文件保存成功: {config_path}")
            else:
                logger.warning("未安装tomli_w库，无法保存配置文件，请运行: pip install tomli-w")
        except Exception as e:
            logger.error(f"配置文件保存失败: {e}")

    def reload(self):
        """
        重新加载配置文件并通知所有观察者
        """
        self._config = self._load_config()
        logger.info("配置文件重新加载")
        self.notify_observers()

    def get_config_path(self) -> str:
        return 'config.toml'

    def get_categories(self) -> list:
        """从配置中读取分类列表（数组格式）"""
        categories = self.get('categories', [])
        if isinstance(categories, dict):
            # 向后兼容：如果是对象格式，转换为数组格式
            return self._convert_categories_dict_to_list(categories)
        return categories

    def _convert_categories_dict_to_list(self, categories_dict: dict) -> list:
        """将旧的对象格式分类配置转换为新的数组格式"""
        categories_list = []
        for key, value in categories_dict.items():
            category = {
                'name': value.get('name', key),
                'description': value.get('description', ''),
                'keywords': value.get('keywords', []),
                'icon': value.get('icon', '📰'),
                'color': value.get('color', '#95a5a6')
            }
            categories_list.append(category)
        return categories_list

    def get_category_names(self) -> list:
        """获取所有分类名称列表"""
        categories = self.get_categories()
        return [cat['name'] for cat in categories]

    def get_default_category(self) -> str:
        """获取默认分类"""
        return self.get('default_category', '未分类')


config = Config()

def get_categories() -> list:
    """获取分类列表（数组格式）"""
    return config.get_categories()

def get_category_names() -> list:
    """获取所有分类名称列表"""
    return config.get_category_names()

def get_default_category() -> str:
    """获取默认分类"""
    return config.get_default_category()