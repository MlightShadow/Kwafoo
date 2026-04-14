"""
新闻相关API模块
"""
from typing import Dict, Any, List
from datetime import datetime
from utils.logger import logger
from database import db
from utils.validators import (
    validate_get_news_params,
    validate_search_news_params,
    validate_get_news_by_category_params,
    validate_mark_as_read_params,
    validate_get_read_news_params,
    validate_get_unread_news_params,
    GetNewsParams,
    SearchNewsParams,
    GetNewsByCategoryParams,
    MarkAsReadParams,
    GetReadNewsParams,
    GetUnreadNewsParams
)


class NewsAPI:
    """新闻API处理器"""
    
    @validate_get_news_params
    def get_news(self, handler, params: GetNewsParams):
        """获取全部新闻"""
        try:
            news_list = db.get_news_by_category('全部', limit=params.limit, offset=params.offset)
            
            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'limit': params.limit,
                'offset': params.offset
            })
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            handler._send_error_response(str(e))

    @validate_get_news_by_category_params
    def get_news_by_category(self, handler, params: GetNewsByCategoryParams):
        """按分类获取新闻"""
        try:
            news_list = db.get_news_by_category(params.category, limit=params.limit, offset=params.offset)
            
            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'category': params.category,
                'limit': params.limit,
                'offset': params.offset
            })
        except Exception as e:
            logger.error(f"获取分类新闻失败: {e}")
            handler._send_error_response(str(e))

    @validate_search_news_params
    def search_news(self, handler, params: SearchNewsParams):
        """搜索新闻"""
        try:
            news_list = db.search_news(params.q, limit=params.limit)
            
            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'query': params.q
            })
        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            handler._send_error_response(str(e))

    def get_news_stats(self, handler):
        """获取新闻统计"""
        try:
            stats = db.get_news_stats()
            
            handler._send_json_response({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"获取新闻统计失败: {e}")
            handler._send_error_response(str(e))

    def clear_news(self, handler):
        """清空新闻"""
        try:
            count = db.mark_all_news_deleted()
            
            handler._send_json_response({
                'success': True,
                'message': f'已标记 {count} 条新闻为删除状态',
                'count': count
            })
        except Exception as e:
            logger.error(f"清空新闻失败: {e}")
            handler._send_error_response(str(e))

    @validate_mark_as_read_params
    def mark_as_read(self, handler, params: MarkAsReadParams):
        """
        标记新闻为已读
        """
        try:
            success = db.mark_news_as_read(params.news_id)

            if success:
                handler._send_json_response({
                    'success': True,
                    'message': '新闻已标记为已读'
                })
            else:
                handler._send_error_response("标记失败")
        except Exception as e:
            logger.error(f"标记新闻为已读失败: {e}")
            handler._send_error_response(str(e))

    @validate_get_read_news_params
    def get_read_news(self, handler, params: GetReadNewsParams):
        """
        获取已读新闻
        """
        try:
            news_list = db.get_read_news(params.limit)

            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list)
            })
        except Exception as e:
            logger.error(f"获取已读新闻失败: {e}")
            handler._send_error_response(str(e))

    @validate_get_unread_news_params
    def get_unread_news(self, handler, params: GetUnreadNewsParams):
        """
        获取未读新闻
        """
        try:
            news_list = db.get_unread_news(params.limit)

            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list)
            })
        except Exception as e:
            logger.error(f"获取未读新闻失败: {e}")
            handler._send_error_response(str(e))


news_api = NewsAPI()