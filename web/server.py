import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional
import threading
from datetime import datetime
from utils.logger import logger
from utils.helpers import config
from utils.progress import progress_monitor
from database import db
from ai.processor import ai_news_processor
from rag.engine import rag_engine


class KwafooRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.api_routes = {
            '/api/news': self.get_news,
            '/api/news/category': self.get_news_by_category,
            '/api/news/search': self.search_news,
            '/api/news/stats': self.get_news_stats,
            '/api/chat': self.chat,
            '/api/progress': self.get_progress,
            '/api/health': self.health_check,
            '/api/config': self.get_config,
            '/api/ai/status': self.get_ai_status,
            '/api/ai/process': self.process_ai_news
        }
        self.post_routes = {
            '/api/chat': self.chat,
            '/api/fetch': self.manual_fetch,
            '/api/ai/process': self.process_ai_news,
            '/api/news/clear': self.clear_news
        }
        super().__init__(*args, directory='web')

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path in self.api_routes:
            self.api_routes[path]()
        elif path.startswith('/api/'):
            self.send_error(404, "API endpoint not found")
        else:
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path in self.post_routes:
            self.post_routes[path]()
        else:
            self.send_error(404, "API endpoint not found")

    def get_news(self):
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            news_list = db.get_news_by_date(today)
            
            self._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list)
            })
        except Exception as e:
            logger.error(f"获取新闻失败: {e}")
            self._send_error_response(str(e))

    def get_news_by_category(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            category = params.get('category', [''])[0]
            
            if not category:
                self._send_error_response("缺少category参数")
                return
            
            news_list = db.get_news_by_category(category)
            
            self._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'category': category
            })
        except Exception as e:
            logger.error(f"获取分类新闻失败: {e}")
            self._send_error_response(str(e))

    def search_news(self):
        try:
            params = parse_qs(urlparse(self.path).query)
            query = params.get('q', [''])[0]
            limit = int(params.get('limit', [10])[0])
            
            if not query:
                self._send_error_response("缺少q参数")
                return
            
            news_list = db.search_news(query, limit)
            
            self._send_json_response({
                'success': True,
                'data': news_list,
                'count': len(news_list),
                'query': query
            })
        except Exception as e:
            logger.error(f"搜索新闻失败: {e}")
            self._send_error_response(str(e))

    def chat(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            message = data.get('message', '')
            category = data.get('category', None)
            session_id = data.get('session_id', None)
            
            if not message:
                self._send_error_response("缺少message参数")
                return
            
            if not session_id:
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                db.create_chat_session(session_id)
            
            context = rag_engine.build_context(message, category)
            
            response = {
                'success': True,
                'message': message,
                'context': context,
                'session_id': session_id,
                'response': f"基于以下新闻回答：\n{context}"
            }
            
            db.add_chat_message(
                session_id,
                'user',
                message
            )
            
            db.add_chat_message(
                session_id,
                'assistant',
                response['response']
            )
            
            self._send_json_response(response)
            
        except Exception as e:
            logger.error(f"对话失败: {e}")
            self._send_error_response(str(e))

    def get_progress(self):
        try:
            tasks = progress_monitor.get_all_tasks()
            
            self._send_json_response({
                'success': True,
                'data': tasks
            })
        except Exception as e:
            logger.error(f"获取进度失败: {e}")
            self._send_error_response(str(e))

    def health_check(self):
        self._send_json_response({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat()
        })

    def get_config(self):
        try:
            categories = config.get('categories', {})
            default_category = config.get('default_category', '未分类')
            enable_ai_category = config.get('enable_ai_category', False)
            
            # 返回完整的分类配置（包含icon和color）
            self._send_json_response({
                'success': True,
                'data': {
                    'categories': categories,
                    'default_category': default_category,
                    'enable_ai_category': enable_ai_category
                }
            })
        except Exception as e:
            logger.error(f"获取配置失败: {e}")
            self._send_error_response(str(e))

    def get_ai_status(self):
        try:
            status = ai_news_processor.get_status()
            
            self._send_json_response({
                'success': True,
                'data': status
            })
        except Exception as e:
            logger.error(f"获取AI状态失败: {e}")
            self._send_error_response(str(e))

    def get_news_stats(self):
        try:
            stats = db.get_news_stats()
            
            self._send_json_response({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"获取新闻统计失败: {e}")
            self._send_error_response(str(e))

    def clear_news(self):
        try:
            count = db.mark_all_news_deleted()
            
            self._send_json_response({
                'success': True,
                'message': f'已标记 {count} 条新闻为删除状态',
                'count': count
            })
        except Exception as e:
            logger.error(f"清空新闻失败: {e}")
            self._send_error_response(str(e))

    def process_ai_news(self):
        try:
            from scheduler.scheduler import scheduler
            
            # 调用异步方法，不阻塞主线程，手动执行不受配置限制
            started = scheduler.process_ai_news_async(manual=True)
            
            if started:
                self._send_json_response({
                    'success': True,
                    'message': 'AI分析任务已启动（手动执行，不受配置限制）'
                })
            else:
                self._send_json_response({
                    'success': False,
                    'message': 'AI分析任务正在运行中，请稍后再试'
                })
        except Exception as e:
            logger.error(f"启动AI分析任务失败: {e}")
            self._send_error_response(str(e))

    def manual_fetch(self):
        try:
            from scheduler.scheduler import scheduler
            
            # 调用异步方法，不阻塞主线程
            started = scheduler.fetch_news_async()
            
            if started:
                self._send_json_response({
                    'success': True,
                    'message': '抓取任务已启动（异步执行）'
                })
            else:
                self._send_json_response({
                    'success': False,
                    'message': '抓取任务正在运行中，请稍后再试'
                })
        except Exception as e:
            logger.error(f"启动抓取任务失败: {e}")
            self._send_error_response(str(e))

    def _send_json_response(self, data: Dict[str, Any]):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
            logger.warning(f"客户端已断开连接: {e}")

    def _send_error_response(self, message: str):
        try:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': message
            }, ensure_ascii=False).encode('utf-8'))
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError) as e:
            logger.warning(f"客户端已断开连接: {e}")

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


class HTTPServerManager:
    _instance = None
    _server = None
    _thread = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start(self):
        if self._server:
            logger.warning("HTTP服务器已在运行")
            return
        
        host = config.get('server.host', '0.0.0.0')
        port = config.get('server.port', 8000)
        
        self._server = HTTPServer((host, port), KwafooRequestHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        
        logger.info(f"HTTP服务器已启动: http://{host}:{port}")

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None
            logger.info("HTTP服务器已停止")


http_server = HTTPServerManager()