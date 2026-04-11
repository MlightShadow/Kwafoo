import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.processor import ai_news_processor
from database import db
from utils.logger import logger
import json


def test_ai_processor():
    logger.info("=" * 60)
    logger.info("开始测试AI并行处理功能")
    logger.info("=" * 60)
    
    db.create_tables()
    
    logger.info("\n1. 检查AI处理状态")
    status = ai_news_processor.get_status()
    logger.info(f"AI处理状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    if status['unprocessed_count'] == 0:
        logger.warning("没有未处理的新闻，先抓取一些新闻...")
        from scheduler.scheduler import scheduler
        scheduler.fetch_news()
        
        status = ai_news_processor.get_status()
        logger.info(f"抓取后的状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    if status['unprocessed_count'] == 0:
        logger.warning("仍然没有未处理的新闻，无法测试AI处理")
        return
    
    logger.info(f"\n2. 开始AI处理 {status['unprocessed_count']} 条新闻")
    result = ai_news_processor.process_all_unprocessed()
    
    logger.info(f"\n3. AI处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    logger.info("\n4. 验证处理结果")
    news_list = db.get_unprocessed_news(limit=10)
    logger.info(f"未处理的新闻数量: {len(news_list)}")
    
    if len(news_list) == 0:
        logger.info("✓ 所有新闻都已处理完成")
        
        logger.info("\n5. 查看已处理的新闻示例")
        import sqlite3
        conn = sqlite3.connect('data/kwafoo.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, title, category, ai_summary, ai_processed 
            FROM news 
            WHERE ai_processed = 1 
            LIMIT 5
        ''')
        rows = cursor.fetchall()
        
        for row in rows:
            logger.info(f"\nID: {row[0]}")
            logger.info(f"标题: {row[1][:60]}...")
            logger.info(f"分类: {row[2]}")
            logger.info(f"摘要: {row[3][:100] if row[3] else '无'}...")
            logger.info(f"AI处理状态: {row[4]}")
        
        conn.close()
    else:
        logger.warning(f"仍有 {len(news_list)} 条新闻未处理")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        test_ai_processor()
        print("\n✓ 测试成功！")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)