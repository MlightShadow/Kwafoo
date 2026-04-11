import sys
import os
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger


def check_ai_results():
    logger.info("=" * 60)
    logger.info("查看AI处理结果")
    logger.info("=" * 60)
    
    db_path = 'data/kwafoo.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        logger.info("\n【已分类的新闻】")
        logger.info("-" * 60)
        
        cursor.execute('''
            SELECT id, title, category, ai_summary, ai_processed
            FROM news 
            WHERE category IS NOT NULL AND category != ''
            ORDER BY id DESC
        ''')
        
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                logger.info(f"\nID: {row[0]}")
                logger.info(f"标题: {row[1][:80]}...")
                logger.info(f"分类: {row[2]}")
                logger.info(f"摘要: {row[3][:100] if row[3] else '无'}...")
                logger.info(f"AI处理状态: {row[4]}")
        else:
            logger.info("没有已分类的新闻")
        
        logger.info("\n【已生成摘要的新闻】")
        logger.info("-" * 60)
        
        cursor.execute('''
            SELECT id, title, category, ai_summary, ai_processed
            FROM news 
            WHERE ai_summary IS NOT NULL AND ai_summary != ''
            ORDER BY id DESC
        ''')
        
        rows = cursor.fetchall()
        
        if rows:
            for row in rows:
                logger.info(f"\nID: {row[0]}")
                logger.info(f"标题: {row[1][:80]}...")
                logger.info(f"分类: {row[2]}")
                logger.info(f"摘要: {row[3]}")
                logger.info(f"AI处理状态: {row[4]}")
        else:
            logger.info("没有已生成摘要的新闻")
        
        logger.info("\n【统计信息】")
        logger.info("-" * 60)
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ai_processed = 1 THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN category IS NOT NULL AND category != '' THEN 1 ELSE 0 END) as categorized,
                SUM(CASE WHEN ai_summary IS NOT NULL AND ai_summary != '' THEN 1 ELSE 0 END) as summarized
            FROM news
        ''')
        
        stats = cursor.fetchone()
        logger.info(f"总新闻数: {stats[0]}")
        logger.info(f"已处理: {stats[1]}")
        logger.info(f"已分类: {stats[2]}")
        logger.info(f"已生成摘要: {stats[3]}")
        
    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise
    finally:
        conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("查询完成")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        check_ai_results()
        print("\n✓ 查询完成！")
    except Exception as e:
        logger.error(f"查询失败: {e}")
        print(f"\n✗ 查询失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)