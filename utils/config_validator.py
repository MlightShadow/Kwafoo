"""
配置验证器模块
验证配置文件的有效性，提供友好的错误提示
"""

from typing import Dict, Any, List, Optional, Tuple
from utils.logger import logger


class ConfigValidationError(Exception):
    """配置验证错误"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"配置错误 [{field}]: {message}")


class ConfigValidator:
    """配置验证器"""
    
    @staticmethod
    def validate_database(config: Dict[str, Any]) -> List[ConfigValidationError]:
        """验证数据库配置"""
        errors = []
        
        if 'path' not in config:
            errors.append(ConfigValidationError('database.path', '数据库路径不能为空'))
        elif not isinstance(config['path'], str):
            errors.append(ConfigValidationError('database.path', '数据库路径必须是字符串'))
        
        return errors
    
    @staticmethod
    def validate_server(config: Dict[str, Any]) -> List[ConfigValidationError]:
        """验证服务器配置"""
        errors = []
        
        if 'host' not in config:
            errors.append(ConfigValidationError('server.host', '服务器地址不能为空'))
        elif not isinstance(config['host'], str):
            errors.append(ConfigValidationError('server.host', '服务器地址必须是字符串'))
        
        if 'port' not in config:
            errors.append(ConfigValidationError('server.port', '服务器端口不能为空'))
        elif not isinstance(config['port'], int):
            errors.append(ConfigValidationError('server.port', '服务器端口必须是整数'))
        elif config['port'] < 1 or config['port'] > 65535:
            errors.append(ConfigValidationError('server.port', '服务器端口必须在1-65535之间'))
        
        if 'enable_websocket' in config:
            if not isinstance(config['enable_websocket'], bool):
                errors.append(ConfigValidationError('server.enable_websocket', 'WebSocket开关必须是布尔值'))
        
        return errors
    
    @staticmethod
    def validate_scheduler(config: Dict[str, Any]) -> List[ConfigValidationError]:
        """验证调度器配置"""
        errors = []
        
        if 'fetch_interval' in config:
            if not isinstance(config['fetch_interval'], int):
                errors.append(ConfigValidationError('scheduler.fetch_interval', '抓取间隔必须是整数'))
            elif config['fetch_interval'] < 60:
                errors.append(ConfigValidationError('scheduler.fetch_interval', '抓取间隔不能小于60秒'))
        
        if 'ai_process_interval' in config:
            if not isinstance(config['ai_process_interval'], int):
                errors.append(ConfigValidationError('scheduler.ai_process_interval', 'AI处理间隔必须是整数'))
            elif config['ai_process_interval'] < 60:
                errors.append(ConfigValidationError('scheduler.ai_process_interval', 'AI处理间隔不能小于60秒'))
        
        if 'auto_fetch' in config:
            if not isinstance(config['auto_fetch'], bool):
                errors.append(ConfigValidationError('scheduler.auto_fetch', '自动抓取开关必须是布尔值'))
        
        if 'auto_ai_process' in config:
            if not isinstance(config['auto_ai_process'], bool):
                errors.append(ConfigValidationError('scheduler.auto_ai_process', '自动AI处理开关必须是布尔值'))
        
        if 'auto_ai_after_fetch' in config:
            if not isinstance(config['auto_ai_after_fetch'], bool):
                errors.append(ConfigValidationError('scheduler.auto_ai_after_fetch', '抓取后自动AI处理开关必须是布尔值'))
        
        return errors
    
    @staticmethod
    def validate_ai(config: Dict[str, Any]) -> List[ConfigValidationError]:
        """验证AI配置"""
        errors = []
        
        if 'base_url' in config:
            if not isinstance(config['base_url'], str):
                errors.append(ConfigValidationError('ai.base_url', 'AI服务地址必须是字符串'))
            elif not config['base_url'].startswith(('http://', 'https://')):
                errors.append(ConfigValidationError('ai.base_url', 'AI服务地址必须以http://或https://开头'))
        
        if 'model' in config:
            if not isinstance(config['model'], str):
                errors.append(ConfigValidationError('ai.model', '模型名称必须是字符串'))
            elif not config['model'].strip():
                errors.append(ConfigValidationError('ai.model', '模型名称不能为空'))
        
        if 'max_tokens' in config:
            if not isinstance(config['max_tokens'], int):
                errors.append(ConfigValidationError('ai.max_tokens', '最大Token数必须是整数'))
            elif config['max_tokens'] < 1:
                errors.append(ConfigValidationError('ai.max_tokens', '最大Token数必须大于0'))
        
        if 'temperature' in config:
            if not isinstance(config['temperature'], (int, float)):
                errors.append(ConfigValidationError('ai.temperature', '温度参数必须是数字'))
            elif config['temperature'] < 0 or config['temperature'] > 2:
                errors.append(ConfigValidationError('ai.temperature', '温度参数必须在0-2之间'))
        
        if 'max_workers' in config:
            if not isinstance(config['max_workers'], int):
                errors.append(ConfigValidationError('ai.max_workers', '最大并发数必须是整数'))
            elif config['max_workers'] < 1:
                errors.append(ConfigValidationError('ai.max_workers', '最大并发数必须大于0'))
        
        if 'batch_size' in config:
            if not isinstance(config['batch_size'], int):
                errors.append(ConfigValidationError('ai.batch_size', '批量大小必须是整数'))
            elif config['batch_size'] < 1:
                errors.append(ConfigValidationError('ai.batch_size', '批量大小必须大于0'))
        
        if 'nationality' in config:
            if not isinstance(config['nationality'], str):
                errors.append(ConfigValidationError('ai.nationality', '国籍必须是字符串'))
            elif not config['nationality'].strip():
                errors.append(ConfigValidationError('ai.nationality', '国籍不能为空'))
        
        return errors
    
    @staticmethod
    def validate_image(config: Dict[str, Any]) -> List[ConfigValidationError]:
        """验证图片配置"""
        errors = []
        
        if 'thumbnail_size' in config:
            size = config['thumbnail_size']
            if not isinstance(size, dict):
                errors.append(ConfigValidationError('image.thumbnail_size', '缩略图尺寸必须是字典'))
            else:
                if 'width' in size:
                    if not isinstance(size['width'], int):
                        errors.append(ConfigValidationError('image.thumbnail_size.width', '宽度必须是整数'))
                    elif size['width'] < 1:
                        errors.append(ConfigValidationError('image.thumbnail_size.width', '宽度必须大于0'))
                
                if 'height' in size:
                    if not isinstance(size['height'], int):
                        errors.append(ConfigValidationError('image.thumbnail_size.height', '高度必须是整数'))
                    elif size['height'] < 1:
                        errors.append(ConfigValidationError('image.thumbnail_size.height', '高度必须大于0'))
        
        if 'max_image_size' in config:
            if not isinstance(config['max_image_size'], int):
                errors.append(ConfigValidationError('image.max_image_size', '最大图片大小必须是整数'))
            elif config['max_image_size'] < 1:
                errors.append(ConfigValidationError('image.max_image_size', '最大图片大小必须大于0'))
        
        return errors
    
    @staticmethod
    def validate_categories(config: Dict[str, Any]) -> List[ConfigValidationError]:
        """验证分类配置"""
        errors = []
        
        if 'categories' in config:
            if not isinstance(config['categories'], dict):
                errors.append(ConfigValidationError('categories', '分类配置必须是字典'))
            else:
                for category_name, category_config in config['categories'].items():
                    if not isinstance(category_config, dict):
                        errors.append(ConfigValidationError(f'categories.{category_name}', '分类配置必须是字典'))
                    else:
                        if 'icon' in category_config and not isinstance(category_config['icon'], str):
                            errors.append(ConfigValidationError(f'categories.{category_name}.icon', '图标必须是字符串'))
                        
                        if 'color' in category_config and not isinstance(category_config['color'], str):
                            errors.append(ConfigValidationError(f'categories.{category_name}.color', '颜色必须是字符串'))
        
        return errors
    
    @staticmethod
    def validate_all(config: Dict[str, Any]) -> Tuple[bool, List[ConfigValidationError]]:
        """验证所有配置"""
        all_errors = []
        
        if 'database' in config:
            all_errors.extend(ConfigValidator.validate_database(config['database']))
        
        if 'server' in config:
            all_errors.extend(ConfigValidator.validate_server(config['server']))
        
        if 'scheduler' in config:
            all_errors.extend(ConfigValidator.validate_scheduler(config['scheduler']))
        
        if 'ai' in config:
            all_errors.extend(ConfigValidator.validate_ai(config['ai']))
        
        if 'image' in config:
            all_errors.extend(ConfigValidator.validate_image(config['image']))
        
        if 'categories' in config:
            all_errors.extend(ConfigValidator.validate_categories(config))
        
        return (len(all_errors) == 0, all_errors)
    
    @staticmethod
    def validate_and_report(config: Dict[str, Any]) -> bool:
        """验证配置并报告错误"""
        is_valid, errors = ConfigValidator.validate_all(config)
        
        if not is_valid:
            logger.error("配置验证失败:")
            for error in errors:
                logger.error(f"  - {error.message}")
            
            # 提供友好的错误提示
            print("\n配置验证失败，请检查以下问题：")
            for error in errors:
                print(f"  ❌ {error.message}")
            
            print("\n请修改配置文件后重试。")
            return False
        
        logger.info("配置验证通过")
        return True


# 全局配置验证器实例
config_validator = ConfigValidator()