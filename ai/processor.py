import threading
from typing import List, Dict, Any, Optional
from utils.logger import logger
from utils.helpers import config
from database import db

from ai.classifier import ai_classifier
logger.info("ai.classifier导入完成")

from ai.summarizer import ai_summarizer
logger.info("ai.summarizer导入完成")

from ai.scorer import ai_scorer
logger.info("ai.scorer导入完成")


class AINewsProcessor:
    def __init__(self):
        self.auto_process = config.get('ai.auto_process', False)
        
        self.processing = False
        
        # 使用锁保护共享状态
        self._lock = threading.Lock()

    def process_all_unprocessed(self, task_id: str = None, manual: bool = False) -> Dict[str, Any]:
        """
        处理所有未处理的新闻（添加到队列）
        
        Args:
            task_id: 任务ID，用于进度监控
            manual: 是否为手动执行，手动执行不受配置限制
            
        Returns:
            处理结果字典
        """
        # 检查配置，如果自动AI处理未启用，则不执行（仅对自动执行）
        if not manual and not self.auto_process:
            logger.info("自动AI处理未启用，跳过自动处理")
            return {
                'status': 'skipped',
                'message': '自动AI处理未启用'
            }
        
        execution_type = "手动执行" if manual else "自动执行"
        logger.info(f"开始处理未处理的新闻（{execution_type}）")
        
        try:
            # 获取所有未处理的新闻
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
            
            # 将所有未处理的新闻添加到队列
            added_count = 0
            for news in all_unprocessed:
                news_id = news['id']
                # 添加到AI队列（完整分析任务）
                task_priority = 1 if manual else 2
                task_id_result = db.add_to_ai_queue(news_id, 'all', priority=task_priority)
                if task_id_result > 0:
                    added_count += 1
            
            # 更新进度
            if task_id:
                progress_monitor.update_progress(task_id, 100, f"已将 {added_count}/{total_news} 条新闻添加到AI队列")
            
            result = {
                'status': 'completed',
                'total': total_news,
                'success': added_count,
                'failed': total_news - added_count
            }
            
            logger.info(f"AI处理完成（{execution_type}）: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI处理失败: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            # 使用锁保护processing状态的设置
            with self._lock:
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
            
            # 提取常用字段
            title = news_data.get('title', '')
            description = news_data.get('description', '')
            content = news_data.get('content', '')
            compressed_content = news_data.get('compressed_content', '')
            ai_summary = news_data.get('ai_summary', '')

            # 按照顺序处理：1. AI摘要 2. AI分类 3. AI评分
            
            # 1. AI摘要（最先进行）
            if task_type in ('summary', 'all'):
                # AI摘要
                try:
                    description = news_data.get('description', '')
                    content = news_data.get('content', '')
                    title = news_data.get('title', '')
                    summary_result = ai_summarizer.generate_summary(content, description, title)
                    if summary_result:
                        # 保存评价和摘要
                        if summary_result['comment']:
                            db.update_news_comment(news_id, summary_result['comment'])
                            logger.debug(f"新闻评价已更新: ID={news_id}")
                        if summary_result['summary']:
                            db.update_news_summary(news_id, summary_result['summary'])
                            logger.debug(f"新闻摘要已更新: ID={news_id}")
                            # 更新 news_data 中的 ai_summary，以便分类和评分时使用
                            news_data['ai_summary'] = summary_result['summary']
                            # 更新 ai_summary 变量，以便后续分类和评分时使用
                            ai_summary = summary_result['summary']
                    else:
                        logger.debug(f"AI摘要生成失败: ID={news_id}")
                        # 明确设置为None，避免后续误判
                        news_data['ai_summary'] = None
                        ai_summary = None
                except Exception as e:
                    logger.warning(f"AI摘要失败: ID={news_id}, error={e}")
            
            # 2. AI分类（使用AI摘要结果）
            if task_type in ('category', 'all'):
                # AI分类（按照优先获取AI摘要、抓取摘要、压缩正文、抓取正文、标题的顺序缺省替补）
                try:
                    # 按照优先级获取分类输入
                    classify_input = None
                    classify_source = None
                    
                    # 优先级1：AI摘要（必须不为空）
                    if ai_summary and ai_summary.strip():
                        classify_input = ai_summary
                        classify_source = 'ai_summary'
                        logger.debug(f"使用AI摘要进行分类: ID={news_id}")
                    # 优先级2：抓取摘要
                    elif description and description.strip():
                        classify_input = description
                        classify_source = 'description'
                        logger.debug(f"使用抓取摘要进行分类: ID={news_id}")
                    # 优先级3：压缩正文
                    elif compressed_content and compressed_content.strip():
                        classify_input = compressed_content
                        classify_source = 'compressed_content'
                        logger.debug(f"使用压缩正文进行分类: ID={news_id}")
                    # 优先级4：抓取正文
                    elif content and content.strip():
                        classify_input = content
                        classify_source = 'content'
                        logger.debug(f"使用抓取正文进行分类: ID={news_id}")
                    # 优先级5：标题
                    elif title and title.strip():
                        classify_input = title
                        classify_source = 'title'
                        logger.debug(f"使用标题进行分类: ID={news_id}")
                    
                    if classify_input:
                        classify_result = ai_classifier.classify(title, classify_input, None)
                        if classify_result:
                            categories = classify_result.get('categories', [])
                            keywords = classify_result.get('keywords', [])
                            
                            # 如果分类为空，根据关键字命中情况选取合适的分类
                            if not categories and keywords:
                                categories = ai_classifier._classify_by_keywords(keywords)
                                logger.info(f"AI未返回分类，根据关键字命中情况选取分类: ID={news_id}, categories={categories}")
                            
                            if categories:
                                category_str = ','.join(categories)
                                db.update_news_category(news_id, category_str)
                                logger.debug(f"新闻分类已更新: ID={news_id}, category={category_str}, source={classify_source}")
                            
                            # 保存关键字到数据库
                            if keywords:
                                keyword_str = ','.join(keywords)
                                db.update_news_keywords(news_id, keyword_str)
                                logger.info(f"新闻关键字已更新: ID={news_id}, keywords={keyword_str}")
                        else:
                            logger.debug(f"AI分类返回空结果: ID={news_id}")
                    else:
                        logger.debug(f"无分类输入，跳过AI分类: ID={news_id}")
                except Exception as e:
                    logger.warning(f"AI分类失败: ID={news_id}, error={e}")

            # AI评分：手动任务（priority=1）或启用评分时执行
            task_priority = task.get('priority', 0)
            manual = (task_priority == 1)
            should_do_score = manual or ai_scorer.enable_scoring
            
            logger.debug(f"AI评分检查: ID={news_id}, manual={manual}, enable_scoring={ai_scorer.enable_scoring}, should_do_score={should_do_score}")
            
            score_dict = None
            
            if should_do_score:
                try:
                    # 按照优先级获取评分输入：AI摘要 → 抓取摘要 → 压缩正文 → 抓取正文 → 标题
                    score_input = news_data.copy()
                    
                    # 如果没有AI摘要或AI摘要为空，使用其他输入
                    if not ai_summary or not ai_summary.strip():
                        # 优先级2：抓取摘要
                        if description and description.strip():
                            score_input['ai_summary'] = description
                            logger.info(f"使用抓取摘要进行评分: ID={news_id}")
                        # 优先级3：压缩正文
                        elif compressed_content and compressed_content.strip():
                            score_input['ai_summary'] = compressed_content
                            logger.info(f"使用压缩正文进行评分: ID={news_id}")
                        # 优先级4：抓取正文
                        elif content and content.strip():
                            score_input['ai_summary'] = content
                            logger.info(f"使用抓取正文进行评分: ID={news_id}")
                        # 优先级5：标题
                        elif title and title.strip():
                            score_input['ai_summary'] = title
                            logger.info(f"使用标题进行评分: ID={news_id}")
                        else:
                            logger.warning(f"无评分输入，跳过AI评分: ID={news_id}")
                    else:
                        logger.info(f"使用AI摘要进行评分: ID={news_id}")
                        score_dict = ai_scorer.score_news(score_input, manual)
                    
                    if score_dict is not None:
                        db.update_news_score(
                            news_id, 
                            score_dict['total_score'],
                            score_dict['topic_relevance'],
                            score_dict['importance'],
                            score_dict['source_score'],
                            score_dict.get('topic_relevance_reason', ''),
                            score_dict.get('importance_reason', ''),
                            score_dict.get('source_reason', '')
                        )
                        logger.info(f"新闻评分已更新: ID={news_id}, score={score_dict['total_score']}")
                    else:
                        logger.warning(f"AI评分返回空结果: ID={news_id}")
                except Exception as e:
                    logger.warning(f"AI评分失败: ID={news_id}, error={e}")
            else:
                logger.info(f"AI评分未启用，跳过评分: ID={news_id}, manual={manual}, enable_scoring={ai_scorer.enable_scoring}")

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
            'auto_process': self.auto_process
        }


ai_news_processor = AINewsProcessor()