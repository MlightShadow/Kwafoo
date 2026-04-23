#!/usr/bin/env python3
"""
修复数据库表结构的脚本
解决ID字段失去自增属性的问题
"""

import sqlite3
import sys
import os

def fix_database():
    """修复数据库表结构"""
    db_path = 'data/kwafoo.db'
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False
    
    print("开始修复数据库...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查当前表结构
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='news'")
        current_sql = cursor.fetchone()[0]
        print(f"当前表结构:\n{current_sql}")
        
        # 检查是否有损坏的ID字段
        if 'PRIMARY KEY AUTOINCREMENT' not in current_sql:
            print("检测到ID字段损坏，开始修复...")
            
            # 1. 备份数据到临时表
            print("1. 备份数据...")
            cursor.execute('''
                CREATE TABLE news_backup AS
                SELECT id, title, description, ai_summary, content, url, source, source_url,
                       category, publish_time, fetch_time, is_visible, ai_processed,
                       image_url, image_data, is_deleted, is_read,
                       compressed_content, keywords, ai_comment, ai_score,
                       ai_score_topic_relevance, ai_score_importance, ai_score_source
                FROM news
            ''')
            
            # 验证备份
            cursor.execute('SELECT COUNT(*) FROM news_backup')
            backup_count = cursor.fetchone()[0]
            print(f"   已备份 {backup_count} 条记录")
            
            if backup_count == 0:
                raise Exception("备份失败，没有数据被备份")
            
            # 2. 删除损坏的表
            print("2. 删除损坏的表...")
            cursor.execute('DROP TABLE news')
            
            # 3. 创建正确的新表
            print("3. 创建正确的新表...")
            cursor.execute('''
                CREATE TABLE news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    ai_summary TEXT,
                    content TEXT,
                    url TEXT UNIQUE,
                    source TEXT NOT NULL,
                    source_url TEXT,
                    category TEXT,
                    publish_time DATETIME,
                    fetch_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_visible BOOLEAN DEFAULT 1,
                    ai_processed BOOLEAN DEFAULT 0,
                    image_url TEXT,
                    image_data BLOB,
                    is_deleted BOOLEAN DEFAULT 0,
                    is_read BOOLEAN DEFAULT 0,
                    compressed_content TEXT,
                    keywords TEXT,
                    ai_comment TEXT,
                    ai_score REAL,
                    ai_score_topic_relevance REAL,
                    ai_score_importance REAL,
                    ai_score_source REAL
                )
            ''')
            
            # 4. 恢复数据（处理重复URL）
            print("4. 恢复数据...")
            
            # 检查备份表中的重复URL
            cursor.execute('''
                SELECT url, COUNT(*) as cnt FROM news_backup 
                GROUP BY url HAVING cnt > 1
            ''')
            duplicates = cursor.fetchall()
            if duplicates:
                print(f"   发现 {len(duplicates)} 个重复URL")
                for url, cnt in duplicates[:3]:
                    print(f"     {url[:50]}...: {cnt}条")
                
                # 使用ROWID删除重复的URL记录，保留第一个
                cursor.execute('''
                    DELETE FROM news_backup 
                    WHERE ROWID NOT IN (
                        SELECT MIN(ROWID) FROM news_backup GROUP BY url
                    )
                ''')
                deleted_count = cursor.rowcount
                print(f"   已删除 {deleted_count} 条重复URL记录")
            else:
                print("   没有发现重复URL")
            
            cursor.execute('''
                INSERT INTO news (
                    id, title, description, ai_summary, content, url, source, source_url,
                    category, publish_time, fetch_time, is_visible, ai_processed,
                    image_url, image_data, is_deleted, is_read,
                    compressed_content, keywords, ai_comment, ai_score,
                    ai_score_topic_relevance, ai_score_importance, ai_score_source
                )
                SELECT id, title, description, ai_summary, content, url, source, source_url,
                       category, publish_time, fetch_time, is_visible, ai_processed,
                       image_url, image_data, is_deleted, is_read,
                       compressed_content, keywords, ai_comment, ai_score,
                       ai_score_topic_relevance, ai_score_importance, ai_score_source
                FROM news_backup
            ''')
            restored_count = cursor.rowcount
            print(f"   已恢复 {restored_count} 条记录")
            
            # 5. 删除备份表
            print("5. 删除备份表...")
            cursor.execute('DROP TABLE news_backup')
            
            # 6. 重建索引
            print("6. 重建索引...")
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_fetch_time ON news(fetch_time DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_publish_time ON news(publish_time DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_category ON news(category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_source ON news(source)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_visible ON news(is_visible, is_deleted)')
            
            # 7. 重建全文搜索表
            print("7. 重建全文搜索表...")
            cursor.execute('DROP TABLE IF EXISTS news_fts')
            cursor.execute('''
                CREATE VIRTUAL TABLE news_fts USING fts5(
                    title, description, ai_summary, content, keywords,
                    content='news', content_rowid='id'
                )
            ''')
            cursor.execute('''
                INSERT INTO news_fts(rowid, title, description, ai_summary, content, keywords)
                SELECT id, title, description, ai_summary, content, keywords FROM news
            ''')
            
            # 8. 验证修复结果
            print("8. 验证修复结果...")
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='news'")
            new_sql = cursor.fetchone()[0]
            print(f"新表结构:\n{new_sql}")
            
            cursor.execute("SELECT COUNT(*) FROM news")
            total_count = cursor.fetchone()[0]
            print(f"总记录数: {total_count}")
            
            cursor.execute("SELECT COUNT(*) FROM news WHERE id IS NULL")
            null_id_count = cursor.fetchone()[0]
            print(f"ID为NULL的记录数: {null_id_count}")
            
            if null_id_count > 0:
                print("警告: 仍有ID为NULL的记录，需要手动处理")
                # 为NULL的ID分配新的ID
                print("9. 为NULL的ID分配新的ID...")
                cursor.execute('''
                    UPDATE news SET id = (
                        SELECT COALESCE(MAX(id), 0) + 1 FROM (SELECT id FROM news)
                    ) WHERE id IS NULL
                ''')
                print(f"   已更新 {cursor.rowcount} 条记录")
            
            conn.commit()
            print("✅ 数据库修复完成!")
            return True
            
        else:
            print("✅ 表结构正常，无需修复")
            return True
            
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    success = fix_database()
    sys.exit(0 if success else 1)