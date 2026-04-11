import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.processor import ai_news_processor
from database import db
from utils.logger import logger
import json


def test_serial_processing():
    logger.info("=" * 60)
    logger.info("测试AI串行处理（低速慢处理）")
    logger.info("=" * 60)
    
    db.create_tables()
    
    logger.info("\n【步骤1】检查AI处理状态")
    logger.info("-" * 60)
    
    status = ai_news_processor.get_status()
    logger.info(f"AI处理状态:\n{json.dumps(status, indent=2, ensure_ascii=False)}")
    
    if status['unprocessed_count'] == 0:
        logger.info("\n没有未处理的新闻，先抓取一些新闻...")
        from scheduler.scheduler import scheduler
        scheduler.fetch_news()
        
        status = ai_news_processor.get_status()
        logger.info(f"抓取后的状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    if status['unprocessed_count'] == 0:
        logger.warning("仍然没有未处理的新闻，无法测试")
        return
    
    logger.info(f"\n发现 {status['unprocessed_count']} 条未处理的新闻")
    
    logger.info("\n【步骤2】开始串行处理（单条处理）")
    logger.info("-" * 60)
    logger.info(f"配置参数:")
    logger.info(f"  - 并发线程数: {status['max_workers']} (串行处理)")
    logger.info(f"  - 批处理大小: {status['batch_size']} (单条处理)")
    logger.info(f"  - 启用AI分类: {status['enable_ai_category']}")
    logger.info(f"  - 启用AI摘要: {status['enable_ai_summary']}")
    
    import time
    start_time = time.time()
    result = ai_news_processor.process_all_unprocessed()
    end_time = time.time()
    
    processing_time = end_time - start_time
    
    logger.info(f"\nAI处理完成，耗时: {processing_time:.2f}秒")
    logger.info(f"处理结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    
    logger.info("\n【步骤3】验证处理结果")
    logger.info("-" * 60)
    
    status_after = ai_news_processor.get_status()
    logger.info(f"处理后的AI状态:\n{json.dumps(status_after, indent=2, ensure_ascii=False)}")
    
    if status_after['unprocessed_count'] == 0:
        logger.info("\n✓ 所有新闻都已处理完成")
        
        logger.info("\n【步骤4】统计处理结果")
        logger.info("-" * 60)
        
        import sqlite3
        conn = sqlite3.connect('data/kwafoo.db')
        cursor = conn.cursor()
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
        
        if stats[0] > 0:
            logger.info(f"\n分类成功率: {stats[1]/stats[0]*100:.1f}%")
            logger.info(f"摘要成功率: {stats[2]/stats[0]*100:.1f}%")
            logger.info(f"平均处理时间: {processing_time/stats[0]:.2f}秒/条")
        
        conn.close()
    else:
        logger.warning(f"\n仍有 {status_after['unprocessed_count']} 条新闻未处理")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        test_serial_processing()
        print("\n✓ 测试成功！")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)