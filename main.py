import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from utils.helpers import config
from utils.progress import progress_monitor
from database import db
from scheduler.scheduler import scheduler
from web.server import http_server
from web.websocket import ws_server


async def start_websocket():
    """启动WebSocket服务器"""
    try:
        await ws_server.start()
        # 启用进度监控器的WebSocket广播
        progress_monitor.enable_websocket(ws_server.broadcast)
    except Exception as e:
        logger.error(f"WebSocket服务器启动失败: {e}")


def main():
    try:
        logger.info("=" * 50)
        logger.info("Kwafoo 新闻聚合系统启动")
        logger.info("=" * 50)
        
        logger.info("初始化数据库...")
        db.create_tables()
        
        logger.info("配置日志系统...")
        log_file = config.get('logging.file', 'data/logs/kwafoo.log')
        max_size = config.get('logging.max_size', 10485760)
        backup_count = config.get('logging.backup_count', 5)
        logger.setup_file_handler(log_file, max_size, backup_count)
        
        logger.info("启动调度器...")
        scheduler.start()
        
        logger.info("启动AI队列处理器...")
        # 在启动队列处理器之前，清理卡住的任务
        db.reset_stuck_ai_tasks()
        scheduler.start_queue_processor()
        
        logger.info("启动HTTP服务器...")
        http_server.start()
        
        logger.info("启动WebSocket服务器...")
        # 在新的事件循环中启动WebSocket服务器
        asyncio.run(start_websocket())
        
        logger.info("=" * 50)
        logger.info("系统启动完成")
        logger.info(f"HTTP服务器: http://{config.get('server.host', '0.0.0.0')}:{config.get('server.port', 8000)}")
        logger.info(f"WebSocket服务器: ws://{config.get('server.host', '0.0.0.0')}:{config.get('server.port', 8000) + 1}")
        logger.info("=" * 50)
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
            scheduler.stop()
            http_server.stop()
            
            # 停止WebSocket服务器
            asyncio.run(ws_server.stop())
            
            db.close()
            logger.info("系统已停止")
            
    except Exception as e:
        logger.error(f"系统启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()