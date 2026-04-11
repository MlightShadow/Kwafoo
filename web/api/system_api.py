"""
系统相关API模块
"""
import os
from typing import Dict, Any
from datetime import datetime
from utils.logger import logger
from utils.progress import progress_monitor
from utils.image_processor import image_processor


class SystemAPI:
    """系统API处理器"""
    
    def get_progress(self, handler):
        """获取任务进度"""
        try:
            tasks = progress_monitor.get_all_tasks()
            
            handler._send_json_response({
                'success': True,
                'data': tasks
            })
        except Exception as e:
            logger.error(f"获取进度失败: {e}")
            handler._send_error_response(str(e))

    def health_check(self, handler):
        """健康检查"""
        handler._send_json_response({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })

    def manual_fetch(self, handler):
        """手动触发新闻抓取"""
        try:
            from scheduler.scheduler import scheduler
            
            # 调用异步方法，不阻塞主线程
            started = scheduler.fetch_news_async()
            
            if started:
                handler._send_json_response({
                    'success': True,
                    'message': '抓取任务已启动（异步执行）'
                })
            else:
                handler._send_json_response({
                    'success': False,
                    'message': '抓取任务正在运行中，请稍后再试'
                })
        except Exception as e:
            logger.error(f"启动抓取任务失败: {e}")
            handler._send_error_response(str(e))
    
    def get_image(self, handler, filename: str):
        """获取图片文件"""
        try:
            # 从文件名中提取哈希值
            if not filename or not filename.endswith('.jpg'):
                handler._send_error_response('无效的文件名')
                return
            
            # 从文件系统加载图片
            image_data = image_processor.load_from_filesystem(filename)
            
            if not image_data:
                handler._send_error_response('图片不存在')
                return
            
            # 设置响应头
            handler.send_response(200, {
                'Content-Type': 'image/jpeg',
                'Content-Length': len(image_data),
                'Cache-Control': 'public, max-age=86400'  # 缓存24小时
            })
            
            # 发送图片数据
            handler.wfile.write(image_data)
            
        except Exception as e:
            logger.error(f"获取图片失败: {e}")
            handler._send_error_response(str(e))


system_api = SystemAPI()