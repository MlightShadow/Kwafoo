import sys
import os
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger


def reset_ai_status():
    logger.info("=" * 60)
    logger.info("重置AI处理状态")
    logger.info("=" * 60)
    
    db_path = 'data/kwafoo.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        logger.info("检查当前AI处理状态...")
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ai_processed = 1 THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN ai_processed = 0 THEN 1 ELSE 0 END) as unprocessed
            FROM news
        ''')
        
        stats = cursor.fetchone()
        logger.info(f"总新闻数: {stats[0]}")
        logger.info(f"已处理: {stats[1]}")
        logger.info(f"未处理: {stats[2]}")
        
        if stats[2] > 0:
            logger.info("\n已经有未处理的新闻，无需重置")
            return
        
        logger.info("\n开始重置AI处理状态...")
        
        cursor.execute('''
            UPDATE news 
            SET ai_processed = 0, category = NULL, ai_summary = NULL
            WHERE ai_processed = 1
        ''')
        
        updated = cursor.rowcount
        conn.commit()
        
        logger.info(f"✓ 已重置 {updated} 条新闻的AI处理状态")
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN ai_processed = 1 THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN ai_processed = 0 THEN 1 ELSE 0 END) as unprocessed
            FROM news
        ''')
        
        stats = cursor.fetchone()
        logger.info(f"\n重置后状态:")
        logger.info(f"总新闻数: {stats[0]}")
        logger.info(f"已处理: {stats[1]}")
        logger.info(f"未处理: {stats[2]}")
        
    except Exception as e:
        logger.error(f"重置失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    logger.info("\n" + "=" * 60)
    logger.info("重置完成")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        reset_ai_status()
        print("\n✓ 重置成功！")
    except Exception as e:
        logger.error(f"重置失败: {e}")
        print(f"\n✗ 重置失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)