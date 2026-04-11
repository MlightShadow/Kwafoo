import json
import os
from typing import Dict, Any, Optional
from utils.logger import logger
try:
    from jsoncomment import JsonComment
    HAS_JSONCOMMENT = True
except ImportError:
    HAS_JSONCOMMENT = False


class Config:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._load_config()

    def _load_config(self, config_path: str = 'config.json') -> Dict[str, Any]:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if HAS_JSONCOMMENT:
                    # 使用jsoncomment库处理带注释的JSON
                    parser = JsonComment()
                    config = parser.loads(f.read())
                    logger.info(f"配置文件加载成功: {config_path} (支持注释)")
                else:
                    # 回退到标准JSON解析
                    config = json.load(f)
                    logger.info(f"配置文件加载成功: {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            return self._get_default_config()

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
            'scheduler': {
                'fetch_interval': 1800,
                'generate_interval': 1800
            },
            'ai': {
                'base_url': 'http://localhost:1234',
                'model': 'nvidia/nemotron-3-nano-4b',
                'api_key': '',
                'max_tokens': 4096,
                'temperature': 0.7
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'enable_websocket': True
            },
            'json': {
                'output_path': 'data/json/current.json',
                'snapshot_path': 'data/json/snapshots/'
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

    def save(self, config_path: str = 'config.json'):
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置文件保存成功: {config_path}")
        except Exception as e:
            logger.error(f"配置文件保存失败: {e}")

    def reload(self):
        self._config = self._load_config()
        logger.info("配置文件重新加载")


config = Config()