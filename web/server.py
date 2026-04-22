import json
import os
import mimetypes
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Dict, Any, Callable, List, Tuple
import threading
from functools import wraps
from utils.logger import logger
from utils.helpers import config
from utils.progress import progress_monitor
from database import db
from rag.engine import rag_engine
from web.api import news_api, ai_api, chat_api, config_api, system_api, report_api

_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
_DIST_DIR = os.path.join(_SERVER_DIR, 'dist')


class Router:
    """路由管理器"""
    
    def __init__(self):
        self.get_routes: Dict[str, Callable] = {}
        self.post_routes: Dict[str, Callable] = {}
    
    def route(self, path: str, methods: List[str] = None):
        """
        路由装饰器
        
        Args:
            path: 路由路径
            methods: 允许的HTTP方法列表，默认为['GET']
        """
        if methods is None:
            methods = ['GET']
        
        def decorator(func: Callable):
            for method in methods:
                if method.upper() == 'GET':
                    self.get_routes[path] = func
                elif method.upper() == 'POST':
                    self.post_routes[path] = func
            return func
        return decorator
    
    def get(self, path: str):
        """
        GET路由装饰器
        
        Args:
            path: 路由路径
        """
        return self.route(path, ['GET'])
    
    def post(self, path: str):
        """
        POST路由装饰器
        
        Args:
            path: 路由路径
        """
        return self.route(path, ['POST'])
    
    def register_get(self, path: str, handler: Callable):
        """
        注册GET路由
        
        Args:
            path: 路由路径
            handler: 处理函数
        """
        self.get_routes[path] = handler
    
    def register_post(self, path: str, handler: Callable):
        """
        注册POST路由
        
        Args:
            path: 路由路径
            handler: 处理函数
        """
        self.post_routes[path] = handler
    
    def get_handler(self, method: str, path: str) -> Callable:
        """
        获取路由处理函数
        
        Args:
            method: HTTP方法
            path: 路由路径
            
        Returns:
            处理函数，如果不存在则返回None
        """
        if method.upper() == 'GET':
            return self.get_routes.get(path)
        elif method.upper() == 'POST':
            return self.post_routes.get(path)
        return None


# 全局路由实例
router = Router()


class KwafooRequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # 处理根路径 - 直接读取并返回index.html
        if path == '/':
            index_path = os.path.join(_DIST_DIR, 'index.html')
            if os.path.exists(index_path):
                try:
                    with open(index_path, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(content)))
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    logger.error(f"Error serving index.html: {e}")
                    self.send_error(500, str(e))
                    return
            else:
                self.send_error(404, "index.html not found")
                return
        
        # 处理API请求
        handler = router.get_handler('GET', path)
        if handler:
            handler(self)
        elif path.startswith('/api/images/'):
            filename = path.replace('/api/images/', '')
            system_api.get_image(self, filename)
        elif path.startswith('/api/'):
            self.send_error(404, "API endpoint not found")
        else:
            # 对于单页应用，所有非API、非静态文件的请求都返回index.html
            # 让前端路由处理
            if not os.path.exists(os.path.join(_DIST_DIR, path.lstrip('/'))):
                # 文件不存在，返回index.html
                index_path = os.path.join(_DIST_DIR, 'index.html')
                if os.path.exists(index_path):
                    try:
                        with open(index_path, 'rb') as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html; charset=utf-8')
                        self.send_header('Content-Length', str(len(content)))
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    except Exception as e:
                        logger.error(f"Error serving index.html: {e}")
                        self.send_error(500, str(e))
                        return
            
            # 处理静态文件
            self.serve_static_file(path)

    def serve_static_file(self, path):
        # 移除前导斜杠
        file_path = path.lstrip('/')
        full_path = os.path.join(_DIST_DIR, file_path)
        
        # 安全检查：确保文件在dist目录内
        if not os.path.commonpath([full_path, _DIST_DIR]).startswith(_DIST_DIR):
            self.send_error(403, "Forbidden")
            return
        
        if os.path.exists(full_path) and os.path.isfile(full_path):
            try:
                with open(full_path, 'rb') as f:
                    content = f.read()
                
                # 猜测MIME类型
                content_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                logger.error(f"Error serving static file {full_path}: {e}")
                self.send_error(500, str(e))
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        handler = router.get_handler('POST', path)
        if handler:
            handler(self)
        else:
            self.send_error(404, "API endpoint not found")

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
        
        # 立即注册路由
        self._register_routes()
        
        host = config.get('server.host', '0.0.0.0')
        port = config.get('server.port', 8000)
        
        self._server = ThreadingHTTPServer((host, port), KwafooRequestHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        
        logger.info(f"HTTP服务器已启动: http://{host}:{port}")

    def _register_routes(self):
        """注册所有API路由"""
        # GET路由
        router.register_get('/api/news', news_api.get_news)
        router.register_get('/api/news/category', news_api.get_news_by_category)
        router.register_get('/api/news/search', news_api.search_news)
        router.register_get('/api/news/stats', news_api.get_news_stats)
        router.register_get('/api/news/read', news_api.get_read_news)
        router.register_get('/api/news/unread', news_api.get_unread_news)
        router.register_get('/api/news/detail', news_api.get_news_detail)
        router.register_get('/api/reports', report_api.get_reports)
        router.register_get('/api/reports/detail', report_api.get_report_detail)
        router.register_get('/api/reports/latest', report_api.get_latest_report)
        router.register_get('/api/chat', chat_api.chat)
        router.register_get('/api/progress', system_api.get_progress)
        router.register_get('/api/health', system_api.health_check)
        router.register_get('/api/config', config_api.get_config)
        router.register_get('/api/ai/status', ai_api.get_ai_status)
        router.register_get('/api/ai/process', ai_api.process_ai_news)
        router.register_get('/api/ai/queue/stats', ai_api.get_ai_queue_stats)
        
        # POST路由
        router.register_post('/api/chat', chat_api.chat)
        router.register_post('/api/fetch', system_api.manual_fetch)
        router.register_post('/api/ai/process', ai_api.process_ai_news)
        router.register_post('/api/ai/process/all', ai_api.process_all_news_ai)
        router.register_post('/api/ai/process/single', ai_api.process_single_news_ai)
        router.register_post('/api/ai/process/category', ai_api.process_news_category)
        router.register_post('/api/ai/process/summary', ai_api.process_news_summary)
        router.register_post('/api/ai/process/reanalyze', ai_api.process_news_reanalyze)
        router.register_post('/api/news/clear', news_api.clear_news)
        router.register_post('/api/news/mark-read', news_api.mark_as_read)
        router.register_post('/api/config', config_api.update_config)
        router.register_post('/api/reports/generate', report_api.generate_report)
        router.register_post('/api/reports/delete', report_api.delete_report)

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None
            logger.info("HTTP服务器已停止")


http_server = HTTPServerManager()