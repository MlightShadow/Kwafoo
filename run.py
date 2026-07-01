#!/usr/bin/env python
"""
Kwafoo 新闻聚合系统 - 统一启动入口

用法:
    python run.py api       # 启动API服务
    python run.py crawl     # 执行一次爬虫
    python run.py process   # 执行一次数据处理
    python run.py pipeline  # 执行完整管道
    python run.py all       # 启动完整系统（API + 定时任务）
"""

import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "kwafoo-ai", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "kwafoo-crawler", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "kwafoo-data-processor", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "kwafoo-api", "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("kwafoo")


def run_api():
    from kwafoo_api import create_app
    import uvicorn

    app = create_app("config/api_config.toml")

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    if os.path.exists("config/api_config.toml"):
        with open("config/api_config.toml", "rb") as f:
            cfg = tomllib.load(f)
    else:
        cfg = {}

    api_cfg = cfg.get("api", {})
    host = api_cfg.get("host", "0.0.0.0")
    port = api_cfg.get("port", 8000)

    logger.info("启动API服务: %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


def run_crawl():
    from kwafoo_crawler import CrawlerEngine
    engine = CrawlerEngine("config/crawler_config.toml")
    result = engine.crawl_all()
    logger.info("抓取完成: total=%d, success=%d, fail=%d",
                result.total_fetched, result.success_count, result.fail_count)


def run_process():
    from kwafoo_data_processor import ProcessorEngine
    engine = ProcessorEngine("config/processor_config.toml")
    result = engine.process_pipeline()
    logger.info("处理完成: %s", result)


def run_pipeline():
    from kwafoo_data_processor import ProcessorEngine
    engine = ProcessorEngine("config/processor_config.toml")
    crawl_result = engine.crawl_pipeline()
    logger.info("爬虫阶段: %s", crawl_result)
    process_result = engine.process_pipeline()
    logger.info("处理阶段: %s", process_result)


def run_all():
    import threading
    from kwafoo_data_processor import ProcessorEngine
    from kwafoo_api import create_app
    import uvicorn

    processor = ProcessorEngine("config/processor_config.toml")
    processor.start()
    logger.info("数据处理引擎已启动（含定时任务）")

    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    if os.path.exists("config/api_config.toml"):
        with open("config/api_config.toml", "rb") as f:
            cfg = tomllib.load(f)
    else:
        cfg = {}

    api_cfg = cfg.get("api", {})
    host = api_cfg.get("host", "0.0.0.0")
    port = api_cfg.get("port", 8000)

    app = create_app("config/api_config.toml")
    app.state._processor = processor

    def start_api():
        uvicorn.run(app, host=host, port=port, log_level="info")

    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    logger.info("API服务已启动: %s:%d", host, port)

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("正在关闭...")
        processor.shutdown()
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="Kwafoo 新闻聚合系统")
    parser.add_argument("command", nargs="?", default="api",
                        choices=["api", "crawl", "process", "pipeline", "all"],
                        help="运行模式: api(默认), crawl, process, pipeline, all")
    args = parser.parse_args()

    commands = {
        "api": run_api,
        "crawl": run_crawl,
        "process": run_process,
        "pipeline": run_pipeline,
        "all": run_all,
    }

    commands[args.command]()


if __name__ == "__main__":
    main()