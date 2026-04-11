import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from utils.helpers import config
from utils.progress import progress_monitor
from database import db
from scheduler.scheduler import scheduler
from web.server import http_server


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
        
        logger.info("启动HTTP服务器...")
        http_server.start()
        
        logger.info("=" * 50)
        logger.info("系统启动完成")
        logger.info(f"HTTP服务器: http://{config.get('server.host', '0.0.0.0')}:{config.get('server.port', 8000)}")
        logger.info("=" * 50)
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到停止信号")
            scheduler.stop()
            http_server.stop()
            db.close()
            logger.info("系统已停止")
            
    except Exception as e:
        logger.error(f"系统启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()