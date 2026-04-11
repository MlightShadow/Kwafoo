import schedule
import time
import threading
from typing import Dict, Any, List
from datetime import datetime
from utils.logger import logger
from utils.helpers import config
from utils.progress import progress_monitor
from database import db
from fetcher.rss_fetcher import rss_fetcher
from fetcher.api_fetcher import api_fetcher
from fetcher.web_fetcher import web_fetcher
from ai.processor import ai_news_processor


class Scheduler:
    def __init__(self):
        self.running = False
        self.thread = None
        self.fetch_interval = config.get('scheduler.fetch_interval', 1800)
        self.ai_process_interval = config.get('scheduler.ai_process_interval', 600)
        self.auto_fetch = config.get('scheduler.auto_fetch', False)
        self.auto_ai_process = config.get('scheduler.auto_ai_process', False)
        self.auto_ai_after_fetch = config.get('scheduler.auto_ai_after_fetch', False)
        
        # 任务运行状态
        self.fetching = False
        self.ai_processing = False
        
        # 根据配置决定是否启用自动任务
        if self.auto_fetch:
            schedule.every(self.fetch_interval // 60).minutes.do(self.fetch_news_async)
            logger.info(f"自动抓取已启用，间隔: {self.fetch_interval}秒")
        else:
            logger.info("自动抓取已禁用，可通过管理界面手动触发")
        
        if self.auto_ai_process:
            schedule.every(self.ai_process_interval // 60).minutes.do(self.process_ai_news_async)
            logger.info(f"自动AI分析已启用，间隔: {self.ai_process_interval}秒")
        else:
            logger.info("自动AI分析已禁用，可通过管理界面手动触发")
        
        logger.info(f"抓取完成后自动AI分析: {'启用' if self.auto_ai_after_fetch else '禁用'}")

    def start(self):
        if self.running:
            logger.warning("调度器已在运行")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("调度器已启动")

    def stop(self):
        if not self.running:
            return
        
        self.running = False
        schedule.clear()
        logger.info("调度器已停止")

    def _run(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def fetch_news_async(self):
        """异步执行新闻抓取任务"""
        if self.fetching:
            logger.warning("新闻抓取任务正在运行中，忽略重复请求")
            return False
        
        def run_fetch():
            try:
                self.fetch_news()
            finally:
                self.fetching = False
        
        # 在新线程中执行，不阻塞主线程
        self.fetching = True
        thread = threading.Thread(target=run_fetch, daemon=True)
        thread.start()
        logger.info("新闻抓取任务已启动（异步）")
        return True

    def fetch_news(self):
        task_id = f"fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        progress_monitor.start_task(task_id, "抓取新闻", 0)
        logger.info(f"开始抓取新闻 - 任务ID: {task_id}")
        
        try:
            news_sources = config.get('news_sources', {})
            all_news = []
            
            rss_sources = news_sources.get('rss', [])
            api_sources = news_sources.get('api', [])
            web_sources = news_sources.get('web', [])
            
            total_sources = len(rss_sources) + len(api_sources) + len(web_sources)
            current_source = 0
            
            for source in rss_sources:
                if not source.get('enabled', True):
                    continue
                
                current_source += 1
                logger.info(f"[{task_id}] 正在抓取RSS: {source.get('name')}")
                progress_monitor.update_progress(
                    task_id,
                    int(current_source / total_sources * 100),
                    f"抓取RSS: {source.get('name')}"
                )
                
                news_list = rss_fetcher.fetch(
                    source['url'],
                    source['name'],
                    source.get('fetch_days')
                )
                
                logger.info(f"[{task_id}] RSS抓取完成: {source.get('name')}, 获取 {len(news_list)} 条新闻")
                all_news.extend(news_list)
            
            for source in api_sources:
                if not source.get('enabled', True):
                    continue
                
                current_source += 1
                logger.info(f"[{task_id}] 正在抓取API: {source.get('name')}")
                progress_monitor.update_progress(
                    task_id,
                    int(current_source / total_sources * 100),
                    f"抓取API: {source.get('name')}"
                )
                
                news_list = api_fetcher.fetch(
                    source['url'],
                    source.get('api_key', ''),
                    source['name'],
                    source.get('fetch_days')
                )
                
                logger.info(f"[{task_id}] API抓取完成: {source.get('name')}, 获取 {len(news_list)} 条新闻")
                all_news.extend(news_list)
            
            for source in web_sources:
                if not source.get('enabled', True):
                    continue
                
                current_source += 1
                logger.info(f"[{task_id}] 正在抓取网页: {source.get('name')}")
                progress_monitor.update_progress(
                    task_id,
                    int(current_source / total_sources * 100),
                    f"抓取网页: {source.get('name')}"
                )
                
                news_list = web_fetcher.fetch(
                    source['url'],
                    source.get('selectors', {}),
                    source['name'],
                    source.get('fetch_days')
                )
                
                logger.info(f"[{task_id}] 网页抓取完成: {source.get('name')}, 获取 {len(news_list)} 条新闻")
                all_news.extend(news_list)
            
            logger.info(f"[{task_id}] 所有新闻源抓取完成，共获取 {len(all_news)} 条新闻")
            progress_monitor.update_progress(task_id, 90, "保存新闻数据")
            
            inserted_count = 0
            for news in all_news:
                news_id = db.insert_news(news)
                if news_id > 0:
                    inserted_count += 1
            
            progress_monitor.complete_task(task_id, True)
            logger.info(f"[{task_id}] 新闻抓取完成: 共获取 {len(all_news)} 条新闻，插入 {inserted_count} 条")
            
            # 如果配置了抓取完成后自动AI分析，则触发AI分析
            # 检查是否启用了AI分类或AI摘要
            enable_ai_category = config.get('enable_ai_category', False)
            enable_ai_summary = config.get('enable_ai_summary', False)
            
            if self.auto_ai_after_fetch and (enable_ai_category or enable_ai_summary):
                logger.info(f"[{task_id}] 抓取完成，自动开始AI分析 (分类: {enable_ai_category}, 摘要: {enable_ai_summary})")
                self.process_ai_news_async()
            elif self.auto_ai_after_fetch:
                logger.info(f"[{task_id}] 抓取完成，但AI分类和摘要均未启用，跳过AI分析")
            
        except Exception as e:
            logger.error(f"[{task_id}] 新闻抓取失败: {e}")
            progress_monitor.complete_task(task_id, False, str(e))

    def process_ai_news_async(self, manual: bool = False):
        """异步执行AI分析任务"""
        if self.ai_processing:
            logger.warning("AI分析任务正在运行中，忽略重复请求")
            return False
        
        def run_ai_process():
            try:
                if manual:
                    self.process_ai_news_manual()
                else:
                    self.process_ai_news()
            finally:
                self.ai_processing = False
        
        # 在新线程中执行，不阻塞主线程
        self.ai_processing = True
        thread = threading.Thread(target=run_ai_process, daemon=True)
        thread.start()
        logger.info(f"AI分析任务已启动（异步），手动={manual}")
        return True

    def process_ai_news(self):
        task_id = f"ai_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        progress_monitor.start_task(task_id, "AI处理新闻", 0)
        logger.info(f"开始AI分析新闻 - 任务ID: {task_id}")
        
        try:
            logger.info(f"[{task_id}] 正在获取未处理的新闻...")
            result = ai_news_processor.process_all_unprocessed()
            
            if result['status'] == 'completed':
                progress_monitor.update_progress(task_id, 100, "AI处理完成")
                progress_monitor.complete_task(task_id, True)
                logger.info(f"[{task_id}] AI处理完成: 成功={result['success']}, 失败={result['failed']}")
            elif result['status'] == 'error':
                progress_monitor.complete_task(task_id, False, result.get('error'))
                logger.error(f"[{task_id}] AI处理失败: {result.get('error')}")
            else:
                progress_monitor.complete_task(task_id, True)
                logger.info(f"[{task_id}] {result.get('message')}")
            
        except Exception as e:
            logger.error(f"[{task_id}] AI处理异常: {e}")
            progress_monitor.complete_task(task_id, False, str(e))

    def process_ai_news_manual(self):
        """手动执行AI分析任务，不受配置限制"""
        task_id = f"ai_process_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        progress_monitor.start_task(task_id, "AI处理新闻（手动）", 0)
        logger.info(f"开始AI分析新闻（手动） - 任务ID: {task_id}")
        
        try:
            logger.info(f"[{task_id}] 正在获取未处理的新闻...")
            result = ai_news_processor.process_all_unprocessed_manual()
            
            if result['status'] == 'completed':
                progress_monitor.update_progress(task_id, 100, "AI处理完成")
                progress_monitor.complete_task(task_id, True)
                logger.info(f"[{task_id}] AI处理完成（手动）: 成功={result['success']}, 失败={result['failed']}")
            elif result['status'] == 'error':
                progress_monitor.complete_task(task_id, False, result.get('error'))
                logger.error(f"[{task_id}] AI处理失败: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"[{task_id}] AI处理异常: {e}")
            progress_monitor.complete_task(task_id, False, str(e))


scheduler = Scheduler()