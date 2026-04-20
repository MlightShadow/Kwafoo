"""检查数据库中的评分数据"""
import sqlite3

def check_ai_scores():
    conn = sqlite3.connect('data/kwafoo.db')
    cursor = conn.cursor()
    
    # 检查数据库表结构
    print("=== 数据库表结构 ===")
    cursor.execute("PRAGMA table_info(news)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    print("\n=== 检查评分数据 ===")
    cursor.execute('''
        SELECT id, title, ai_score, ai_processed, category, ai_summary
        FROM news
        ORDER BY id DESC
        LIMIT 10
    ''')
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"\nID: {row[0]}")
            print(f"  标题: {row[1][:60]}...")
            print(f"  AI评分: {row[2]}")
            print(f"  AI处理状态: {row[3]}")
            print(f"  分类: {row[4]}")
            print(f"  摘要: {row[5][:50] if row[5] else '无'}...")
    else:
        print("没有找到新闻数据")
    
    # 统计评分数据
    print("\n=== 评分统计 ===")
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN ai_score IS NOT NULL THEN 1 ELSE 0 END) as scored,
            SUM(CASE WHEN ai_score IS NULL THEN 1 ELSE 0 END) as not_scored
        FROM news
    ''')
    
    stats = cursor.fetchone()
    print(f"  总新闻数: {stats[0]}")
    print(f"  已评分: {stats[1]}")
    print(f"  未评分: {stats[2]}")
    
    conn.close()

if __name__ == '__main__':
    check_ai_scores()