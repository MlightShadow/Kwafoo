"""
WebSocket服务器模块
提供实时通信功能，用于任务进度更新、系统状态广播等
"""

import asyncio
import json
import logging
from typing import Set, Dict, Any
from datetime import datetime
import websockets
from websockets.server import WebSocketServerProtocol

from utils.logger import logger


class WebSocketServer:
    """WebSocket服务器类"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8001):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.is_running = False
        
    async def register(self, websocket: WebSocketServerProtocol):
        """注册新的WebSocket连接"""
        self.clients.add(websocket)
        logger.info(f"新的WebSocket连接: {websocket.remote_address}")
        
        # 发送欢迎消息
        await websocket.send(json.dumps({
            'type': 'connected',
            'message': '已连接到Kwafoo服务器',
            'timestamp': datetime.now().isoformat()
        }))
        
    async def unregister(self, websocket: WebSocketServerProtocol):
        """注销WebSocket连接"""
        self.clients.discard(websocket)
        logger.info(f"WebSocket连接断开: {websocket.remote_address}")
        
    async def broadcast(self, message: Dict[str, Any]):
        """向所有连接的客户端广播消息"""
        if not self.clients:
            return
            
        message_str = json.dumps(message)
        disconnected = set()
        
        for client in self.clients:
            try:
                await client.send(message_str)
            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                disconnected.add(client)
        
        # 移除断开的连接
        for client in disconnected:
            await self.unregister(client)
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理客户端消息"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')
            
            if msg_type == 'ping':
                # 心跳检测
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            elif msg_type == 'subscribe':
                # 订阅特定频道
                channel = data.get('channel', 'all')
                await websocket.send(json.dumps({
                    'type': 'subscribed',
                    'channel': channel,
                    'timestamp': datetime.now().isoformat()
                }))
            else:
                logger.warning(f"未知消息类型: {msg_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    async def handler(self, websocket: WebSocketServerProtocol, path: str):
        """WebSocket连接处理器"""
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket连接正常关闭")
        except Exception as e:
            logger.error(f"WebSocket连接错误: {e}")
        finally:
            await self.unregister(websocket)
    
    async def broadcast_progress(self, task_id: str, task_name: str, progress: int, message: str = ''):
        """广播任务进度"""
        await self.broadcast({
            'type': 'progress',
            'task_id': task_id,
            'task_name': task_name,
            'progress': progress,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_task_completed(self, task_id: str, task_name: str, success: bool, message: str = ''):
        """广播任务完成"""
        await self.broadcast({
            'type': 'task_completed',
            'task_id': task_id,
            'task_name': task_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_system_status(self, status: str, message: str = ''):
        """广播系统状态"""
        await self.broadcast({
            'type': 'system_status',
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_news_update(self, count: int, category: str = ''):
        """广播新闻更新"""
        await self.broadcast({
            'type': 'news_update',
            'count': count,
            'category': category,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_ai_status(self, status: str, processing_count: int = 0):
        """广播AI状态"""
        await self.broadcast({
            'type': 'ai_status',
            'status': status,
            'processing_count': processing_count,
            'timestamp': datetime.now().isoformat()
        })
    
    async def start(self):
        """启动WebSocket服务器"""
        if self.is_running:
            logger.warning("WebSocket服务器已经在运行")
            return
            
        self.is_running = True
        logger.info(f"启动WebSocket服务器: ws://{self.host}:{self.port}")
        
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10
        )
        
        logger.info("WebSocket服务器启动成功")
    
    async def stop(self):
        """停止WebSocket服务器"""
        if not self.is_running:
            return
            
        self.is_running = False
        logger.info("正在停止WebSocket服务器...")
        
        # 关闭所有客户端连接
        for client in self.clients:
            try:
                await client.close()
            except Exception as e:
                logger.error(f"关闭客户端连接失败: {e}")
        
        self.clients.clear()
        
        # 关闭服务器
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        
        logger.info("WebSocket服务器已停止")


# 全局WebSocket服务器实例
ws_server = WebSocketServer()