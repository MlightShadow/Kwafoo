import schedule
import time
import threading
from typing import Dict, Any, List, Optional, NamedTuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils.logger import logger
from utils.helpers import config, ConfigObserver
from utils.progress import progress_monitor
from database import db
from fetcher.rss_fetcher import rss_fetcher
from fetcher.api_fetcher import api_fetcher
from fetcher.web_fetcher import web_fetcher
from ai.processor import ai_news_processor


class FetchResult(NamedTuple):
    source_name: str
    source_type: str
    news_list: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None


class Scheduler(ConfigObserver):
    def __init__(self) -> None:
        self.running: bool = False
        self.thread: Optional[threading.Thread] = None
        self.fetch_interval: int = config.get('scheduler.fetch_interval', 1800)
        self.ai_process_interval: int = config.get('scheduler.ai_process_interval', 600)
        self.auto_fetch: bool = config.get('scheduler.auto_fetch', False)
        self.auto_ai_process: bool = config.get('scheduler.auto_ai_process', False)
        self.auto_ai_after_fetch: bool = config.get('scheduler.auto_ai_after_fetch', False)
        self.max_fetch_workers: int = config.get('scheduler.max_fetch_workers', 20)
        
        # 任务运行状态
        self.fetching: bool = False
        self.ai_processing: bool = False
        
        # 使用锁保护共享状态
        self._fetching_lock: threading.Lock = threading.Lock()
        self._ai_processing_lock: threading.Lock = threading.Lock()
        
        # 队列处理器
        self.queue_processor_thread: Optional[threading.Thread] = None
        self.queue_processor_running: bool = False
        
        # 注册为配置观察者
        config.add_observer(self)
        
        # 根据配置决定是否启用自动任务
        self._setup_scheduled_tasks()
        
    def _setup_scheduled_tasks(self):
        """根据配置设置定时任务"""
        # 清除所有定时任务
        schedule.clear()
        
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

    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置更新回调
        
        Args:
            config: 更新后的配置字典
        """
        logger.info("Scheduler配置已更新")
        scheduler_config = config.get('scheduler', {})
        self.fetch_interval = scheduler_config.get('fetch_interval', 1800)
        self.ai_process_interval = scheduler_config.get('ai_process_interval', 600)
        self.auto_fetch = scheduler_config.get('auto_fetch', False)
        self.auto_ai_process = scheduler_config.get('auto_ai_process', False)
        self.auto_ai_after_fetch = scheduler_config.get('auto_ai_after_fetch', False)
        self.max_fetch_workers = scheduler_config.get('max_fetch_workers', 20)
        
        # 重新设置定时任务
        self._setup_scheduled_tasks()

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
        # 使用锁保护fetching状态的检查和设置
        with self._fetching_lock:
            if self.fetching:
                logger.warning("新闻抓取任务正在运行中，忽略重复请求")
                return False
            
            self.fetching = True
        
        def run_fetch():
            try:
                self.fetch_news()
            finally:
                # 使用锁保护fetching状态的设置
                with self._fetching_lock:
                    self.fetching = False
        
        # 在新线程中执行，不阻塞主线程
        thread = threading.Thread(target=run_fetch, daemon=True)
        thread.start()
        logger.info("新闻抓取任务已启动（异步）")
        return True

    def _fetch_single_source(self, source: Dict[str, Any], source_type: str, task_id: str) -> FetchResult:
        """抓取单个源"""
        try:
            source_name = source.get('name', 'Unknown')
            logger.info(f"[{task_id}] 开始抓取 {source_type}: {source_name}")
            
            if source_type == 'rss':
                news_list = rss_fetcher.fetch(
                    source['url'],
                    source_name,
                    source.get('fetch_days')
                )
            elif source_type == 'api':
                news_list = api_fetcher.fetch(
                    source['url'],
                    source.get('api_key', ''),
                    source_name,
                    source.get('fetch_days')
                )
            elif source_type == 'web':
                news_list = web_fetcher.fetch(
                    source['url'],
                    source.get('selectors', {}),
                    source_name,
                    source.get('fetch_days')
                )
            else:
                return FetchResult(source_name, source_type, [], False, f"Unknown source type: {source_type}")
            
            logger.info(f"[{task_id}] {source_type} 抓取完成: {source_name}, 获取 {len(news_list)} 条新闻")
            return FetchResult(source_name, source_type, news_list, True)
            
        except Exception as e:
            logger.error(f"[{task_id}] {source_type} 抓取失败: {source.get('name')} - {e}")
            return FetchResult(source.get('name', 'Unknown'), source_type, [], False, str(e))

    def _save_news_to_db(self, news_list: List[Dict[str, Any]], source_name: str, task_id: str) -> int:
        """将新闻保存到数据库"""
        if not news_list:
            return 0
        
        inserted_count = 0
        inserted_news_ids = []
        for news in news_list:
            try:
                news_id = db.insert_news(news)
                if news_id > 0:
                    inserted_count += 1
                    inserted_news_ids.append(news_id)
            except Exception as e:
                logger.error(f"[{task_id}] 保存新闻失败: {news.get('title', 'Unknown')} - {e}")
        
        logger.info(f"[{task_id}] {source_name} - 保存 {inserted_count} 条新闻到数据库")
        
        # 如果启用了自动AI处理，将新闻添加到AI处理队列
        if inserted_news_ids and config.get('ai.auto_process', False):
            try:
                for news_id in inserted_news_ids:
                    # 添加到AI队列（完整分析任务）
                    db.add_to_ai_queue(news_id, 'all', priority=2)
                logger.info(f"[{task_id}] 已将 {len(inserted_news_ids)} 条新闻添加到AI处理队列")
            except Exception as e:
                logger.error(f"[{task_id}] 添加新闻到AI处理队列失败: {e}")
        
        return inserted_count

    def fetch_news(self):
        """并发抓取新闻"""
        task_id = f"fetch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        progress_monitor.start_task(task_id, "抓取新闻", 0)
        logger.info(f"开始抓取新闻 - 任务ID: {task_id}")
        
        try:
            news_sources = config.get('news_sources', {})
            rss_sources = news_sources.get('rss', [])
            api_sources = news_sources.get('api', [])
            web_sources = news_sources.get('web', [])
            
            enabled_rss = [s for s in rss_sources if s.get('enabled', True)]
            enabled_api = [s for s in api_sources if s.get('enabled', True)]
            enabled_web = [s for s in web_sources if s.get('enabled', True)]
            
            all_sources = [
                *[(s, 'rss') for s in enabled_rss],
                *[(s, 'api') for s in enabled_api],
                *[(s, 'web') for s in enabled_web]
            ]
            
            total_sources = len(all_sources)
            if total_sources == 0:
                logger.warning(f"[{task_id}] 没有启用的新闻源")
                progress_monitor.complete_task(task_id, True)
                return
            
            logger.info(f"[{task_id}] 共 {total_sources} 个新闻源需要抓取")
            
            max_workers = min(self.max_fetch_workers, total_sources)
            completed_count = 0
            total_inserted = 0
            lock = threading.Lock()
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_source = {
                    executor.submit(self._fetch_single_source, source, source_type, task_id): (source, source_type)
                    for source, source_type in all_sources
                }
                
                for future in as_completed(future_to_source):
                    source, source_type = future_to_source[future]
                    result = future.result()
                    
                    if result.success and result.news_list:
                        inserted = self._save_news_to_db(result.news_list, result.source_name, task_id)
                        total_inserted += inserted
                    
                    with lock:
                        completed_count += 1
                        progress = int(completed_count / total_sources * 100)
                        progress_monitor.update_progress(
                            task_id,
                            progress,
                            f"完成 {completed_count}/{total_sources}: {result.source_name}"
                        )
            
            progress_monitor.complete_task(task_id, True)
            logger.info(f"[{task_id}] 新闻抓取完成: 共抓取 {total_sources} 个源，插入 {total_inserted} 条新闻")
            
            if self.auto_ai_after_fetch:
                logger.info(f"[{task_id}] 抓取完成，自动将新闻添加到AI队列")
                self.process_ai_news()
            
        except Exception as e:
            logger.error(f"[{task_id}] 新闻抓取失败: {e}")
            progress_monitor.complete_task(task_id, False, str(e))

    def process_ai_news_async(self, manual: bool = False):
        """异步执行AI分析任务"""
        # 使用锁保护ai_processing状态的检查和设置
        with self._ai_processing_lock:
            if self.ai_processing:
                logger.warning("AI分析任务正在运行中，忽略重复请求")
                return False
            
            self.ai_processing = True
        
        def run_ai_process():
            try:
                if manual:
                    self.process_ai_news_manual()
                else:
                    self.process_ai_news()
            finally:
                # 使用锁保护ai_processing状态的设置
                with self._ai_processing_lock:
                    self.ai_processing = False
        
        # 在新线程中执行，不阻塞主线程
        thread = threading.Thread(target=run_ai_process, daemon=True)
        thread.start()
        logger.info(f"AI分析任务已启动（异步），手动={manual}")
        return True

    def process_ai_news(self):
        """
        将所有未处理的新闻添加到AI队列
        """
        try:
            # 获取所有未处理的新闻
            news_list = db.get_unprocessed_news(limit=10000)

            if not news_list:
                logger.info("没有未处理的新闻")
                return

            logger.info(f"将 {len(news_list)} 条未处理新闻添加到AI队列")

            # 添加到AI队列
            for news in news_list:
                db.add_to_ai_queue(news['id'], 'all', priority=0)

            logger.info(f"已将 {len(news_list)} 条新闻添加到AI队列")

        except Exception as e:
            logger.error(f"添加未处理新闻到AI队列失败: {e}")

    def process_all_news_ai(self):
        """
        将所有新闻添加到AI队列
        """
        try:
            # 获取所有新闻
            cursor = db._connection.cursor()
            cursor.execute('''
                SELECT id FROM news
                WHERE is_visible = 1 AND is_deleted = 0
            ''')
            news_list = cursor.fetchall()

            if not news_list:
                logger.info("没有新闻")
                return

            logger.info(f"将 {len(news_list)} 条新闻添加到AI队列")

            # 添加到AI队列（高优先级）
            for news in news_list:
                db.add_to_ai_queue(news['id'], 'all', priority=1)

            logger.info(f"已将 {len(news_list)} 条新闻添加到AI队列")

        except Exception as e:
            logger.error(f"添加所有新闻到AI队列失败: {e}")

    def start_queue_processor(self):
        """
        启动AI队列处理器
        """
        if self.queue_processor_running:
            logger.warning("AI队列处理器已在运行")
            return

        def run_processor():
            try:
                self.queue_processor_running = True
                ai_news_processor.process_queue()
            finally:
                self.queue_processor_running = False

        self.queue_processor_thread = threading.Thread(target=run_processor, daemon=True)
        self.queue_processor_thread.start()
        logger.info("AI队列处理器已启动")

    def process_ai_news_manual(self):
        """手动执行AI分析任务，不受配置限制"""
        task_id = f"ai_process_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        progress_monitor.start_task(task_id, "AI处理新闻（手动）", 0)
        logger.info(f"开始AI分析新闻（手动） - 任务ID: {task_id}")
        
        try:
            logger.info(f"[{task_id}] 正在获取未处理的新闻...")
            result = ai_news_processor.process_all_unprocessed(task_id=task_id, manual=True)
            
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