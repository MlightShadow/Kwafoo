"""
配置相关API模块
"""
import json
import os
from typing import Dict, Any
from utils.logger import logger
from utils.helpers import config
from utils.config_validator import ConfigValidator, ConfigValidationError


class ConfigAPI:
    """配置API处理器"""
    
    def get_config(self, handler):
        """获取配置"""
        try:
            categories = config.get('categories', {})
            default_category = config.get('default_category', '未分类')
            enable_ai_category = config.get('enable_ai_category', False)
            
            # 获取图片显示配置
            image_display = config.get('image.display', {})
            
            # 返回完整的分类配置（包含icon和color）
            handler._send_json_response({
                'success': True,
                'data': {
                    'categories': categories,
                    'default_category': default_category,
                    'enable_ai_category': enable_ai_category,
                    'image_display': image_display
                }
            })
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            handler._send_error_response(str(e))

    def update_config(self, handler):
        """更新配置"""
        try:
            import toml
            content_length = int(handler.headers['Content-Length'])
            post_data = handler.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            config_path = config.get_config_path()
            
            # 读取当前配置
            current_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    current_config = toml.load(f)
            
            # 更新配置
            for key, value in data.items():
                if key in ['categories', 'default_category', 'enable_ai_category', 'image_display']:
                    current_config[key] = value
            
            # 验证配置
            is_valid, errors = ConfigValidator.validate_all(current_config)
            if not is_valid:
                error_messages = [error.message for error in errors]
                logger.error(f"配置验证失败: {error_messages}")
                handler._send_json_response({
                    'success': False,
                    'message': '配置验证失败',
                    'errors': error_messages
                })
                return
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                toml.dump(current_config, f)
            
            # 重新加载配置
            config.reload()
            
            handler._send_json_response({
                'success': True,
                'message': '配置更新成功',
                'data': current_config
            })
            
        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            handler._send_error_response(str(e))


config_api = ConfigAPI()