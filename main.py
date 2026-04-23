import sys
import os
import asyncio
import threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from utils.helpers import config
from utils.progress import progress_monitor

print("开始导入database模块...")
try:
    from database import db
    print("database模块导入完成")
except Exception as e:
    print(f"database模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    raise

print("开始导入scheduler模块...")
try:
    from scheduler.scheduler import scheduler
    print("scheduler模块导入完成")
    print(f"Scheduler实例: {scheduler}")
except Exception as e:
    print(f"scheduler模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    raise

print("开始导入web.server模块...")
try:
    from web.server import http_server
    print("web.server模块导入完成")
    print(f"HTTPServer实例: {http_server}")
except Exception as e:
    print(f"web.server模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    raise

print("开始导入web.websocket模块...")
try:
    from web.websocket import ws_server
    print("web.websocket模块导入完成")
    print(f"WebSocketServer实例: {ws_server}")
except Exception as e:
    print(f"web.websocket模块导入失败: {e}")
    import traceback
    traceback.print_exc()
    raise


async def start_websocket():
    """启动WebSocket服务器"""
    try:
        await ws_server.start()
        # 启用进度监控器的WebSocket广播
        progress_monitor.enable_websocket(ws_server.broadcast_sync)
        # 启用数据库管理器的WebSocket广播
        db.enable_websocket_broadcast(ws_server.broadcast_sync)
        
        # 保持WebSocket服务器运行
        logger.info("WebSocket服务器正在运行...")
        while ws_server.is_running:
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket服务器运行失败: {e}")


def main():
    try:
        logger.info("=" * 50)
        logger.info("Kwafoo 新闻聚合系统启动")
        logger.info("=" * 50)
        
        # 检查AI配置
        logger.info("检查AI配置...")
        ai_base_url = config.get('ai.base_url')
        ai_model = config.get('ai.model')
        
        if not ai_base_url:
            logger.error("AI服务地址未配置！请在config.toml中设置ai.base_url")
            return
        
        if not ai_model:
            logger.error("AI模型未配置！请在config.toml中设置ai.model")
            logger.error("例如：model = \"google/gemma-4-e4b\" 或 model = \"nvidia/nemotron-3-nano-4b\"")
            return
        
        logger.info(f"AI配置检查通过：base_url={ai_base_url}, model={ai_model}")
        
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
        stuck_count = db.reset_stuck_ai_tasks()
        if stuck_count > 0:
            logger.info(f"已清理 {stuck_count} 个卡住的AI任务（服务器重启导致）")
        scheduler.start_queue_processor()
        
        logger.info("启动HTTP服务器...")
        http_server.start()
        
        logger.info("启动WebSocket服务器...")
        # 在新线程中启动WebSocket服务器
        ws_thread = threading.Thread(target=lambda: asyncio.run(start_websocket()), daemon=True)
        ws_thread.start()
        
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
            ws_server.is_running = False
            ws_thread.join(timeout=2)
            
            db.close()
            logger.info("系统已停止")
            
    except Exception as e:
        logger.error(f"系统启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()