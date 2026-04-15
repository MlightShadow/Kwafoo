"""
AI相关API模块
"""
from typing import Dict, Any
from utils.logger import logger
from ai.processor import ai_news_processor
from utils.validators import (
    validate_process_news_params,
    validate_process_news_category_params,
    validate_process_news_summary_params,
    validate_process_news_reanalyze_params,
    ProcessNewsParams
)


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
        """
        将未处理新闻添加到AI队列
        """
        try:
            from scheduler.scheduler import scheduler

            scheduler.process_ai_news()

            handler._send_json_response({
                'success': True,
                'message': '已将未处理新闻添加到AI队列'
            })
        except Exception as e:
            logger.error(f"添加未处理新闻到AI队列失败: {e}")
            handler._send_error_response(str(e))

    def process_all_news_ai(self, handler):
        """
        将所有新闻添加到AI队列
        """
        try:
            from scheduler.scheduler import scheduler

            scheduler.process_all_news_ai()

            handler._send_json_response({
                'success': True,
                'message': '已将所有新闻添加到AI队列'
            })
        except Exception as e:
            logger.error(f"添加所有新闻到AI队列失败: {e}")
            handler._send_error_response(str(e))

    def get_ai_queue_stats(self, handler):
        """
        获取AI队列统计信息
        """
        try:
            from database import db

            stats = db.get_ai_queue_stats()

            handler._send_json_response({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"获取AI队列统计失败: {e}")
            handler._send_error_response(str(e))

    @validate_process_news_params
    def process_single_news_ai(self, handler, params: ProcessNewsParams):
        """
        将单条新闻添加到AI队列
        """
        try:
            from database import db

            # 检查新闻是否存在
            news_list = db.get_news_by_id(params.news_id)
            if not news_list:
                handler._send_error_response("新闻不存在")
                return

            # 如果强制重新处理，先清除AI处理状态
            if params.force:
                db.clear_ai_status(params.news_id)

            # 添加到AI队列
            task_id = db.add_to_ai_queue(params.news_id, 'all', priority=1)

            if task_id > 0:
                handler._send_json_response({
                    'success': True,
                    'message': '已将新闻添加到AI队列'
                })
            else:
                handler._send_error_response("添加到AI队列失败")
        except Exception as e:
            logger.error(f"添加单条新闻到AI队列失败: {e}")
            handler._send_error_response(str(e))

    @validate_process_news_category_params
    def process_news_category(self, handler, params: ProcessNewsParams):
        """
        对单条新闻进行AI分类
        """
        try:
            from database import db

            # 检查新闻是否存在
            news_list = db.get_news_by_id(params.news_id)
            if not news_list:
                handler._send_error_response("新闻不存在")
                return

            # 添加到AI队列（分类任务）
            task_id = db.add_to_ai_queue(params.news_id, 'category', priority=1)

            if task_id > 0:
                handler._send_json_response({
                    'success': True,
                    'message': '已将新闻添加到AI分类队列'
                })
            else:
                handler._send_error_response("添加到AI队列失败")
        except Exception as e:
            logger.error(f"添加新闻分类任务失败: {e}")
            handler._send_error_response(str(e))

    @validate_process_news_summary_params
    def process_news_summary(self, handler, params: ProcessNewsParams):
        """
        对单条新闻进行AI摘要
        """
        try:
            from database import db

            # 检查新闻是否存在
            news_list = db.get_news_by_id(params.news_id)
            if not news_list:
                handler._send_error_response("新闻不存在")
                return

            # 添加到AI队列（摘要任务）
            task_id = db.add_to_ai_queue(params.news_id, 'summary', priority=1)

            if task_id > 0:
                handler._send_json_response({
                    'success': True,
                    'message': '已将新闻添加到AI摘要队列'
                })
            else:
                handler._send_error_response("添加到AI队列失败")
        except Exception as e:
            logger.error(f"添加新闻摘要任务失败: {e}")
            handler._send_error_response(str(e))

    @validate_process_news_reanalyze_params
    def process_news_reanalyze(self, handler, params: ProcessNewsParams):
        """
        重新分析单条新闻（分类+摘要）
        """
        try:
            from database import db

            # 检查新闻是否存在
            news_list = db.get_news_by_id(params.news_id)
            if not news_list:
                logger.error(f"新闻不存在: news_id={params.news_id}")
                handler._send_error_response("新闻不存在")
                return

            # 如果强制重新处理，先清除AI处理状态
            if params.force:
                logger.info(f"清除AI处理状态: news_id={params.news_id}")
                if not db.clear_ai_status(params.news_id):
                    logger.error(f"清除AI处理状态失败: news_id={params.news_id}")
                    handler._send_error_response("清除AI处理状态失败")
                    return

            # 添加到AI队列（完整分析任务）
            logger.info(f"添加到AI队列: news_id={params.news_id}, task_type=all, priority=1")
            task_id = db.add_to_ai_queue(params.news_id, 'all', priority=1)

            if task_id > 0:
                logger.info(f"成功添加到AI队列: task_id={task_id}, news_id={params.news_id}")
                handler._send_json_response({
                    'success': True,
                    'message': '已将新闻添加到AI重新分析队列'
                })
            else:
                logger.error(f"添加到AI队列失败: task_id={task_id}, news_id={params.news_id}")
                handler._send_error_response("添加到AI队列失败")
        except Exception as e:
            logger.error(f"重新分析新闻时发生错误: {e}", exc_info=True)
            handler._send_error_response(f"重新分析失败: {str(e)}")


ai_api = AIAPI()