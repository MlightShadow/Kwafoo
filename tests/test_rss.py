import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetcher.rss_fetcher import rss_fetcher
from database.manager import db
from utils.logger import logger
from utils.helpers import config


def test_rss_fetch():
    logger.info("=" * 60)
    logger.info("开始测试RSS抓取功能")
    logger.info("=" * 60)
    
    db.create_tables()
    
    rss_sources = config.get('news_sources.rss', [])
    
    if not rss_sources:
        logger.warning("没有配置RSS源")
        return
    
    total_news_count = 0
    
    for rss_source in rss_sources:
        if not rss_source.get('enabled', True):
            logger.info(f"RSS源已禁用，跳过: {rss_source.get('name')}")
            continue
        
        url = rss_source.get('url')
        name = rss_source.get('name')
        fetch_days = rss_source.get('fetch_days')
        
        logger.info(f"\n处理RSS源: {name}")
        logger.info(f"URL: {url}")
        if fetch_days is not None:
            logger.info(f"抓取天数: {fetch_days} 天")
        
        news_list = rss_fetcher.fetch(url, name, fetch_days)
        
        if not news_list:
            logger.warning(f"未获取到新闻: {name}")
            continue
        
        logger.info(f"成功获取 {len(news_list)} 条新闻")
        
        inserted_count = 0
        skipped_count = 0
        
        for news_data in news_list:
            news_id = db.insert_news(news_data)
            if news_id > 0:
                inserted_count += 1
                logger.debug(f"插入新闻: {news_data['title'][:50]}...")
            else:
                skipped_count += 1
        
        total_news_count += inserted_count
        
        logger.info(f"插入 {inserted_count} 条新新闻")
        logger.info(f"跳过 {skipped_count} 条已存在新闻")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"测试完成！总计插入 {total_news_count} 条新闻")
    logger.info("=" * 60)
    
    return total_news_count


if __name__ == '__main__':
    try:
        count = test_rss_fetch()
        print(f"\n✓ 测试成功！共插入 {count} 条新闻")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)