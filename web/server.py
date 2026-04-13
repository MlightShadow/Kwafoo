import json
import os
import mimetypes
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Dict, Any
import threading
from utils.logger import logger
from utils.helpers import config
from utils.progress import progress_monitor
from database import db
from ai.processor import ai_news_processor
from rag.engine import rag_engine
from web.api import news_api, ai_api, chat_api, config_api, system_api


_SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
_DIST_DIR = os.path.join(_SERVER_DIR, 'dist')


class KwafooRequestHandler(BaseHTTPRequestHandler):
    # 定义API路由
    api_routes = {
        '/api/news': news_api.get_news,
        '/api/news/category': news_api.get_news_by_category,
        '/api/news/search': news_api.search_news,
        '/api/news/stats': news_api.get_news_stats,
        '/api/news/read': news_api.get_read_news,
        '/api/news/unread': news_api.get_unread_news,
        '/api/chat': chat_api.chat,
        '/api/progress': system_api.get_progress,
        '/api/health': system_api.health_check,
        '/api/config': config_api.get_config,
        '/api/ai/status': ai_api.get_ai_status,
        '/api/ai/process': ai_api.process_ai_news,
        '/api/ai/queue/stats': ai_api.get_ai_queue_stats
    }
    post_routes = {
        '/api/chat': chat_api.chat,
        '/api/fetch': system_api.manual_fetch,
        '/api/ai/process': ai_api.process_ai_news,
        '/api/ai/process/all': ai_api.process_all_news_ai,
        '/api/ai/process/single': ai_api.process_single_news_ai,
        '/api/news/clear': news_api.clear_news,
        '/api/news/mark-read': news_api.mark_as_read,
        '/api/config': config_api.update_config
    }
    
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
        if path in self.api_routes:
            self.api_routes[path](self)
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
        
        if path in self.post_routes:
            self.post_routes[path](self)
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
        
        host = config.get('server.host', '0.0.0.0')
        port = config.get('server.port', 8000)
        
        self._server = ThreadingHTTPServer((host, port), KwafooRequestHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        
        logger.info(f"HTTP服务器已启动: http://{host}:{port}")

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None
            logger.info("HTTP服务器已停止")


http_server = HTTPServerManager()