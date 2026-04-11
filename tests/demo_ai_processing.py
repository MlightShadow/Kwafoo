import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler.scheduler import scheduler
from ai.processor import ai_news_processor
from database import db
from utils.logger import logger
import json


def demo_workflow():
    logger.info("=" * 70)
    logger.info("Kwafoo AI并行处理演示")
    logger.info("=" * 70)
    
    db.create_tables()
    
    logger.info("\n【步骤1】抓取新闻")
    logger.info("-" * 70)
    
    scheduler.fetch_news()
    
    time.sleep(1)
    
    logger.info("\n【步骤2】检查AI处理状态")
    logger.info("-" * 70)
    
    status = ai_news_processor.get_status()
    logger.info(f"AI处理状态:\n{json.dumps(status, indent=2, ensure_ascii=False)}")
    
    if status['unprocessed_count'] == 0:
        logger.info("\n✓ 没有未处理的新闻，所有新闻都已处理完成")
        return
    
    logger.info(f"\n发现 {status['unprocessed_count']} 条未处理的新闻")
    
    logger.info("\n【步骤3】查看未处理的新闻示例")
    logger.info("-" * 70)
    
    unprocessed_news = db.get_unprocessed_news(limit=3)
    for news in unprocessed_news:
        logger.info(f"\nID: {news['id']}")
        logger.info(f"标题: {news['title'][:60]}...")
        logger.info(f"来源: {news['source']}")
        logger.info(f"AI处理状态: {news['ai_processed']}")
        logger.info(f"分类: {news['category']}")
        logger.info(f"摘要: {news['ai_summary'][:50] if news['ai_summary'] else '无'}...")
    
    logger.info("\n【步骤4】开始AI并行处理")
    logger.info("-" * 70)
    logger.info(f"配置参数:")
    logger.info(f"  - 并发线程数: {status['max_workers']}")
    logger.info(f"  - 批处理大小: {status['batch_size']}")
    logger.info(f"  - 启用AI分类: {status['enable_ai_category']}")
    logger.info(f"  - 启用AI摘要: {status['enable_ai_summary']}")
    
    start_time = time.time()
    result = ai_news_processor.process_all_unprocessed()
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    logger.info(f"\nAI处理完成，耗时: {processing_time:.2f}秒")
    logger.info(f"处理结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    
    logger.info("\n【步骤5】验证处理结果")
    logger.info("-" * 70)
    
    status_after = ai_news_processor.get_status()
    logger.info(f"处理后的AI状态:\n{json.dumps(status_after, indent=2, ensure_ascii=False)}")
    
    if status_after['unprocessed_count'] == 0:
        logger.info("\n✓ 所有新闻都已处理完成")
        
        logger.info("\n【步骤6】查看已处理的新闻示例")
        logger.info("-" * 70)
        
        import sqlite3
        conn = sqlite3.connect('data/kwafoo.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, category, ai_summary, ai_processed 
            FROM news 
            WHERE ai_processed = 1 
            ORDER BY id DESC
            LIMIT 5
        ''')
        rows = cursor.fetchall()
        
        for row in rows:
            logger.info(f"\nID: {row[0]}")
            logger.info(f"标题: {row[1][:60]}...")
            logger.info(f"分类: {row[2]}")
            logger.info(f"摘要: {row[3][:100] if row[3] else '无'}...")
            logger.info(f"AI处理状态: {row[4]}")
        
        logger.info("\n【步骤7】统计处理结果")
        logger.info("-" * 70)
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN category IS NOT NULL AND category != '' THEN 1 ELSE 0 END) as categorized,
                SUM(CASE WHEN ai_summary IS NOT NULL AND ai_summary != '' THEN 1 ELSE 0 END) as summarized
            FROM news 
            WHERE ai_processed = 1
        ''')
        stats = cursor.fetchone()
        
        logger.info(f"已处理新闻总数: {stats[0]}")
        logger.info(f"已分类新闻数: {stats[1]}")
        logger.info(f"已生成摘要数: {stats[2]}")
        
        conn.close()
    else:
        logger.warning(f"\n仍有 {status_after['unprocessed_count']} 条新闻未处理")
    
    logger.info("\n" + "=" * 70)
    logger.info("演示完成")
    logger.info("=" * 70)


if __name__ == '__main__':
    try:
        demo_workflow()
        print("\n✓ 演示成功！")
    except Exception as e:
        logger.error(f"演示失败: {e}")
        print(f"\n✗ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)