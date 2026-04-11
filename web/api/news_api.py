"""
新闻相关API模块
"""
from typing import Dict, Any, List
from datetime import datetime
from utils.logger import logger
from database import db


class NewsAPI:
    """新闻API处理器"""
    
    def get_news(self, handler):
        """获取今日新闻"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            news_list = db.get_news_by_date(today)
            
            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list)
            })
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            handler._send_error_response(str(e))

    def get_news_by_category(self, handler):
        """按分类获取新闻"""
        try:
            from urllib.parse import parse_qs, urlparse
            params = parse_qs(urlparse(handler.path).query)
            category = params.get('category', [''])[0]
            
            if not category:
                handler._send_error_response("缺少category参数")
                return
            
            news_list = db.get_news_by_category(category)
            
            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'category': category
            })
        except Exception as e:
            logger.error(f"获取分类新闻失败: {e}")
            handler._send_error_response(str(e))

    def search_news(self, handler):
        """搜索新闻"""
        try:
            from urllib.parse import parse_qs, urlparse
            params = parse_qs(urlparse(handler.path).query)
            query = params.get('q', [''])[0]
            limit = int(params.get('limit', [10])[0])
            
            if not query:
                handler._send_error_response("缺少q参数")
                return
            
            news_list = db.search_news(query, limit)
            
            handler._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'query': query
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


news_api = NewsAPI()