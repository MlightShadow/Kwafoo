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
    validate_get_news_detail_params,
    GetNewsParams,
    SearchNewsParams,
    GetNewsByCategoryParams,
    MarkAsReadParams,
    GetReadNewsParams,
    GetUnreadNewsParams,
    GetNewsDetailParams
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
        标记新闻的阅读状态（已读/未读）
        """
        try:
            is_read = params.is_read if hasattr(params, 'is_read') else True
            success = db.mark_news_as_read(params.news_id, is_read)

            if success:
                status_text = '已读' if is_read else '未读'
                handler._send_json_response({
                    'success': True,
                    'message': f'新闻已标记为{status_text}'
                })
            else:
                handler._send_error_response("标记失败")
        except Exception as e:
            logger.error(f"标记新闻阅读状态失败: {e}")
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

    @validate_get_news_detail_params
    def get_news_detail(self, handler, params: GetNewsDetailParams):
        """
        获取新闻详情（包含所有字段和AI处理历史）
        """
        try:
            news_list = db.get_news_by_id(params.id)
            
            if not news_list:
                handler._send_error_response("新闻不存在")
                return
            
            news_data = news_list[0]
            
            # 获取AI处理历史
            ai_history = db.get_ai_processing_history(params.id)
            
            # 构建完整的字段信息（所有数据库字段）
            all_fields = {
                'ID': news_data.get('id'),
                '标题': news_data.get('title'),
                '描述': news_data.get('description'),
                'AI摘要': news_data.get('ai_summary'),
                '正文': news_data.get('content'),
                '压缩正文': news_data.get('compressed_content'),
                'URL': news_data.get('url'),
                '来源': news_data.get('source'),
                '来源URL': news_data.get('source_url'),
                '分类': news_data.get('category') or '未分类',
                '发布时间': news_data.get('publish_time'),
                '抓取时间': news_data.get('fetch_time'),
                '可见状态': '可见' if news_data.get('is_visible') else '不可见',
                'AI处理状态': '已处理' if news_data.get('ai_processed') else '未处理',
                '图片URL': news_data.get('image_url'),
                '图片数据': '有' if news_data.get('image_data') else '无',
                '阅读状态': '已读' if news_data.get('is_read') else '未读',
                '删除状态': '已删除' if news_data.get('is_deleted') else '未删除'
            }
            
            # 构建调试信息（长度和统计）
            debug_info = {
                '正文长度': len(news_data.get('content') or ''),
                '压缩正文长度': len(news_data.get('compressed_content') or ''),
                '描述长度': len(news_data.get('description') or ''),
                'AI摘要长度': len(news_data.get('ai_summary') or ''),
                '标题长度': len(news_data.get('title') or ''),
                'AI处理历史记录数': len(ai_history)
            }
            
            handler._send_json_response({
                'success': True,
                'data': news_data,
                'all_fields': all_fields,
                'debug_info': debug_info,
                'ai_history': ai_history
            })
        except Exception as e:
            logger.error(f"获取新闻详情失败: {e}")
            handler._send_error_response(str(e))


news_api = NewsAPI()