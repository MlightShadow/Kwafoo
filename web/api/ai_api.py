"""
AI相关API模块
"""
from typing import Dict, Any
from utils.logger import logger
from ai.processor import ai_news_processor


class AIAPI:
    """AI API处理器"""
    
    def get_ai_status(self, handler):
        """获取AI处理状态"""
        try:
            status = ai_news_processor.get_status()
            
            handler._send_json_response({
                'success': True,
                'data': status
            })
        except Exception as e:
            logger.error(f"获取AI状态失败: {e}")
            handler._send_error_response(str(e))

    def process_ai_news(self, handler):
        """手动触发AI新闻处理"""
        try:
            from scheduler.scheduler import scheduler
            
            # 调用异步方法，不阻塞主线程，手动执行不受配置限制
            started = scheduler.process_ai_news_async(manual=True)
            
            if started:
                handler._send_json_response({
                    'success': True,
                    'message': 'AI分析任务已启动（手动执行，不受配置限制）'
                })
            else:
                handler._send_json_response({
                    'success': False,
                    'message': 'AI分析任务正在运行中，请稍后再试'
                })
        except Exception as e:
            logger.error(f"启动AI分析任务失败: {e}")
            handler._send_error_response(str(e))


ai_api = AIAPI()