import threading
from typing import List, Dict, Any, Optional
from utils.logger import logger
from utils.helpers import config
from database import db
from ai.classifier import ai_classifier
from ai.summarizer import ai_summarizer


class AINewsProcessor:
    def __init__(self):
        self.max_workers = config.get('ai.max_workers', 4)
        self.batch_size = config.get('ai.batch_size', 10)
        self.enable_ai_category = config.get('enable_ai_category', False)
        self.enable_ai_summary = config.get('enable_ai_summary', False)
        
        self.processing = False
        self.processed_count = 0
        self.failed_count = 0

    def process_news(self, news_id: int, news_data: Dict[str, Any], manual: bool = False) -> Dict[str, Any]:
        try:
            title = news_data.get('title', '')
            description = news_data.get('description', '')
            content = news_data.get('content', '')
            
            result = {
                'news_id': news_id,
                'success': False,
                'category_updated': False,
                'summary_updated': False,
                'error': None
            }
            
            category_updated = False
            summary_updated = False
            
            # AI分类：手动执行时始终执行，自动执行时根据配置决定
            should_do_category = manual or self.enable_ai_category
            
            if should_do_category:
                try:
                    categories = ai_classifier.classify(title, description, None)
                    if categories:
                        category_str = ','.join(categories)
                        if db.update_news_category(news_id, category_str):
                            result['category_updated'] = True
                            category_updated = True
                            logger.debug(f"新闻分类已更新: ID={news_id}, category={category_str}")
                    else:
                        logger.debug(f"AI分类返回空结果: ID={news_id}")
                except Exception as e:
                    logger.warning(f"AI分类失败: ID={news_id}, error={e}")
            else:
                logger.debug(f"AI分类未启用，跳过: ID={news_id}")
            
            # AI摘要：手动执行时始终执行，自动执行时根据配置决定
            should_do_summary = manual or self.enable_ai_summary
            
            if should_do_summary:
                # 检查描述是否为空，如果为空则使用标题
                text_to_summarize = description or content or title
                
                if not text_to_summarize or not text_to_summarize.strip():
                    logger.debug(f"描述和标题均为空，跳过AI摘要: ID={news_id}")
                else:
                    try:
                        summary = ai_summarizer.generate_summary(content, text_to_summarize)
                        if summary:
                            if db.update_news_summary(news_id, summary):
                                result['summary_updated'] = True
                                summary_updated = True
                                logger.debug(f"新闻摘要已更新: ID={news_id}")
                        else:
                            logger.debug(f"AI摘要返回空结果: ID={news_id}")
                    except Exception as e:
                        logger.warning(f"AI摘要失败: ID={news_id}, error={e}")
            elif not should_do_summary:
                logger.debug(f"AI摘要未启用，跳过: ID={news_id}")
            else:
                logger.debug(f"无描述和标题，跳过AI摘要: ID={news_id}")
            
            if db.update_news_ai_status(news_id, True):
                result['success'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"处理新闻失败: ID={news_id}, error={e}")
            return {
                'news_id': news_id,
                'success': False,
                'category_updated': False,
                'summary_updated': False,
                'error': str(e)
            }

    def process_batch(self, news_list: List[Dict[str, Any]], manual: bool = False) -> Dict[str, Any]:
        results = {
            'total': len(news_list),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for news in news_list:
            result = self.process_news(news['id'], news, manual)
            results['details'].append(result)
            
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            logger.info(f"新闻处理完成: ID={news['id']}, 成功={result['success']}, 分类={result['category_updated']}, 摘要={result['summary_updated']}")
        
        return results

    def process_all_unprocessed(self, task_id: str = None) -> Dict[str, Any]:
        # 检查配置，如果AI分类和摘要都未启用，则不执行
        if not self.enable_ai_category and not self.enable_ai_summary:
            logger.info("AI分类和摘要均未启用，跳过自动处理")
            return {
                'status': 'skipped',
                'message': 'AI分类和摘要均未启用'
            }
        
        if self.processing:
            logger.warning("AI处理器正在运行中")
            return {
                'status': 'running',
                'message': 'AI处理器正在运行中'
            }
        
        self.processing = True
        self.processed_count = 0
        self.failed_count = 0
        
        # 导入 progress_monitor
        from utils.progress import progress_monitor
        
        logger.info("开始处理未处理的新闻（自动执行）")
        
        try:
            # 先获取所有未处理的新闻总数
            all_unprocessed = db.get_unprocessed_news(limit=10000)
            total_news = len(all_unprocessed)
            
            if total_news == 0:
                logger.info("没有未处理的新闻")
                return {
                    'status': 'completed',
                    'total': 0,
                    'success': 0,
                    'failed': 0
                }
            
            logger.info(f"总共需要处理 {total_news} 条新闻")
            
            total_processed = 0
            total_success = 0
            total_failed = 0
            
            batch_index = 0
            while True:
                news_list = db.get_unprocessed_news(self.batch_size)
                
                if not news_list:
                    logger.info("没有更多未处理的新闻")
                    break
                
                logger.info(f"处理批次: {len(news_list)} 条新闻")
                
                # 自动执行，manual=False，受配置控制
                batch_result = self.process_batch(news_list, manual=False)
                
                total_processed += batch_result['total']
                total_success += batch_result['success']
                total_failed += batch_result['failed']
                
                # 更新进度
                progress = int((total_processed / total_news) * 100)
                logger.info(f"AI处理进度: {progress}% ({total_processed}/{total_news})")
                
                # 如果提供了task_id，更新进度监控
                if task_id:
                    progress_monitor.update_progress(task_id, progress, f"已处理 {total_processed}/{total_news} 条新闻")
                
                logger.info(
                    f"批次完成: 成功={batch_result['success']}, "
                    f"失败={batch_result['failed']}"
                )
                
                batch_index += 1
            
            result = {
                'status': 'completed',
                'total': total_processed,
                'success': total_success,
                'failed': total_failed
            }
            
            logger.info(f"AI处理完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI处理失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            self.processing = False

    def process_all_unprocessed_manual(self, task_id: str = None) -> Dict[str, Any]:
        """手动处理所有未处理的新闻，不受配置限制"""
        if self.processing:
            logger.warning("AI处理器正在运行中")
            return {
                'status': 'running',
                'message': 'AI处理器正在运行中'
            }
        
        self.processing = True
        self.processed_count = 0
        self.failed_count = 0
        
        # 导入 progress_monitor
        from utils.progress import progress_monitor
        
        logger.info("开始处理未处理的新闻（手动执行，不受配置限制）")
        
        try:
            # 先获取所有未处理的新闻总数
            all_unprocessed = db.get_unprocessed_news(limit=10000)
            total_news = len(all_unprocessed)
            
            if total_news == 0:
                logger.info("没有未处理的新闻")
                return {
                    'status': 'completed',
                    'total': 0,
                    'success': 0,
                    'failed': 0
                }
            
            logger.info(f"总共需要处理 {total_news} 条新闻")
            
            total_processed = 0
            total_success = 0
            total_failed = 0
            
            batch_index = 0
            while True:
                news_list = db.get_unprocessed_news(self.batch_size)
                
                if not news_list:
                    logger.info("没有更多未处理的新闻")
                    break
                
                logger.info(f"处理批次: {len(news_list)} 条新闻")
                
                # 手动执行，manual=True，不受配置限制
                batch_result = self.process_batch(news_list, manual=True)
                
                total_processed += batch_result['total']
                total_success += batch_result['success']
                total_failed += batch_result['failed']
                
                # 更新进度
                progress = int((total_processed / total_news) * 100)
                logger.info(f"AI处理进度: {progress}% ({total_processed}/{total_news})")
                
                # 如果提供了task_id，更新进度监控
                if task_id:
                    progress_monitor.update_progress(task_id, progress, f"已处理 {total_processed}/{total_news} 条新闻")
                
                logger.info(
                    f"批次完成: 成功={batch_result['success']}, "
                    f"失败={batch_result['failed']}"
                )
                
                batch_index += 1
            
            result = {
                'status': 'completed',
                'total': total_processed,
                'success': total_success,
                'failed': total_failed
            }
            
            logger.info(f"AI处理完成（手动执行）: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI处理失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            self.processing = False

    def process_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单条AI任务

        Args:
            task: 任务字典

        Returns:
            处理结果
        """
        task_id = task['id']
        news_id = task['news_id']
        task_type = task['task_type']

        try:
            # 获取新闻数据
            news_list = db.get_news_by_id(news_id)
            if not news_list:
                logger.error(f"新闻不存在: ID={news_id}")
                return {
                    'task_id': task_id,
                    'success': False,
                    'error': '新闻不存在'
                }

            news_data = news_list[0]

            # 根据任务类型处理
            if task_type in ('category', 'all'):
                # AI分类
                try:
                    categories = ai_classifier.classify(
                        news_data.get('title', ''),
                        news_data.get('description', ''),
                        None
                    )
                    if categories:
                        category_str = ','.join(categories)
                        db.update_news_category(news_id, category_str)
                        logger.debug(f"新闻分类已更新: ID={news_id}, category={category_str}")
                except Exception as e:
                    logger.warning(f"AI分类失败: ID={news_id}, error={e}")

            if task_type in ('summary', 'all'):
                # AI摘要
                try:
                    description = news_data.get('description', '')
                    content = news_data.get('content', '')
                    title = news_data.get('title', '')
                    # 如果description为空，使用title作为输入
                    text_to_summarize = description or content or title
                    summary = ai_summarizer.generate_summary(content, text_to_summarize)
                    if summary:
                        db.update_news_summary(news_id, summary)
                        logger.debug(f"新闻摘要已更新: ID={news_id}")
                except Exception as e:
                    logger.warning(f"AI摘要失败: ID={news_id}, error={e}")

            # 更新AI处理状态
            db.update_news_ai_status(news_id, True)

            return {
                'task_id': task_id,
                'success': True,
                'news_id': news_id
            }

        except Exception as e:
            logger.error(f"处理AI任务失败: task_id={task_id}, error={e}")
            return {
                'task_id': task_id,
                'success': False,
                'error': str(e)
            }

    def process_queue(self):
        """
        处理AI队列中的任务（持续运行）
        """
        logger.info("AI队列处理器已启动")

        while True:
            try:
                # 获取下一个任务
                task = db.get_next_ai_task()

                if not task:
                    # 没有任务，等待2秒
                    import time
                    time.sleep(2)
                    continue

                task_id = task['id']
                logger.info(f"开始处理AI任务: task_id={task_id}, news_id={task['news_id']}")

                # 处理任务
                result = self.process_single_task(task)

                if result['success']:
                    # 更新任务状态为已完成
                    db.update_ai_task_status(task_id, 'completed')
                    logger.info(f"AI任务完成: task_id={task_id}")
                else:
                    # 更新任务状态为失败
                    error_message = result.get('error', '未知错误')
                    retry_count = task.get('retry_count', 0)

                    if retry_count < 3:
                        # 重试
                        db.update_ai_task_status(task_id, 'pending', error_message)
                        # 增加重试次数
                        cursor = db._connection.cursor()
                        cursor.execute('''
                            UPDATE ai_processing_queue
                            SET retry_count = retry_count + 1
                            WHERE id = ?
                        ''', (task_id,))
                        db._connection.commit()
                        logger.warning(f"AI任务失败，将重试: task_id={task_id}, retry_count={retry_count + 1}")
                    else:
                        # 超过重试次数，标记为失败
                        db.update_ai_task_status(task_id, 'failed', error_message)
                        logger.error(f"AI任务失败，超过重试次数: task_id={task_id}")

            except Exception as e:
                logger.error(f"AI队列处理器异常: {e}")
                import time
                time.sleep(5)

    def get_status(self) -> Dict[str, Any]:
        unprocessed_count = len(db.get_unprocessed_news(limit=1000))
        
        return {
            'processing': self.processing,
            'unprocessed_count': unprocessed_count,
            'max_workers': self.max_workers,
            'batch_size': self.batch_size,
            'enable_ai_category': self.enable_ai_category,
            'enable_ai_summary': self.enable_ai_summary
        }


ai_news_processor = AINewsProcessor()