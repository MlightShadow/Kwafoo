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
            
            if should_do_summary and description:
                # 检查描述是否为空
                if not description or not description.strip():
                    logger.debug(f"描述为空，跳过AI摘要: ID={news_id}")
                else:
                    try:
                        summary = ai_summarizer.generate_summary(content, description)
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
                logger.debug(f"无描述，跳过AI摘要: ID={news_id}")
            
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

    def process_all_unprocessed(self) -> Dict[str, Any]:
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
        
        logger.info("开始处理未处理的新闻（自动执行）")
        
        try:
            total_processed = 0
            total_success = 0
            total_failed = 0
            
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
                
                logger.info(
                    f"批次完成: 成功={batch_result['success']}, "
                    f"失败={batch_result['failed']}"
                )
            
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

    def process_all_unprocessed_manual(self) -> Dict[str, Any]:
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
        
        logger.info("开始处理未处理的新闻（手动执行，不受配置限制）")
        
        try:
            total_processed = 0
            total_success = 0
            total_failed = 0
            
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
                
                logger.info(
                    f"批次完成: 成功={batch_result['success']}, "
                    f"失败={batch_result['failed']}"
                )
            
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