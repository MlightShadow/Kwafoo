import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

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
                
                # 检查正文抓取结果
                if config.get('content_fetch.enable_content_fetch', False):
                    if news_data.get('content'):
                        logger.debug(f"  - 正文已抓取，长度: {len(news_data['content'])}")
                    if news_data.get('compressed_content'):
                        logger.debug(f"  - 压缩正文已生成，长度: {len(news_data['compressed_content'])}")
                    if not news_data.get('content'):
                        logger.debug(f"  - 正文未抓取（可能失败或未启用）")
            else:
                skipped_count += 1
        
        total_news_count += inserted_count
        
        logger.info(f"插入 {inserted_count} 条新新闻")
        logger.info(f"跳过 {skipped_count} 条已存在新闻")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"测试完成！总计插入 {total_news_count} 条新闻")
    logger.info("=" * 60)
    
    return total_news_count


def test_rss_with_content_fetch():
    """测试RSS抓取器与正文抓取器的集成"""
    logger.info("=" * 60)
    logger.info("开始测试RSS抓取与正文抓取集成")
    logger.info("=" * 60)
    
    # 确保启用正文抓取
    original_enable = config.get('content_fetch.enable_content_fetch', False)
    config.set('content_fetch.enable_content_fetch', True)
    
    db.create_tables()
    
    # 使用第一个RSS源进行测试
    rss_sources = config.get('news_sources.rss', [])
    if not rss_sources:
        logger.warning("没有配置RSS源")
        config.set('content_fetch.enable_content_fetch', original_enable)
        return 0
    
    rss_source = rss_sources[0]
    if not rss_source.get('enabled', True):
        logger.warning(f"RSS源已禁用: {rss_source.get('name')}")
        config.set('content_fetch.enable_content_fetch', original_enable)
        return 0
    
    url = rss_source.get('url')
    name = rss_source.get('name')
    fetch_days = rss_source.get('fetch_days')
    
    logger.info(f"\n处理RSS源: {name}")
    logger.info(f"URL: {url}")
    
    news_list = rss_fetcher.fetch(url, name, fetch_days)
    
    if not news_list:
        logger.warning(f"未获取到新闻: {name}")
        config.set('content_fetch.enable_content_fetch', original_enable)
        return 0
    
    logger.info(f"成功获取 {len(news_list)} 条新闻")
    
    # 统计正文抓取情况
    content_fetch_count = 0
    compressed_count = 0
    description_count = 0
    
    for news_data in news_list:
        news_id = db.insert_news(news_data)
        if news_id > 0:
            if news_data.get('content'):
                content_fetch_count += 1
            if news_data.get('compressed_content'):
                compressed_count += 1
            if news_data.get('description'):
                description_count += 1
    
    logger.info(f"\n正文抓取统计:")
    logger.info(f"  - 总新闻数: {len(news_list)}")
    logger.info(f"  - 成功抓取正文: {content_fetch_count}")
    logger.info(f"  - 成功压缩正文: {compressed_count}")
    logger.info(f"  - 有描述字段: {description_count}")
    
    # 恢复原始配置
    config.set('content_fetch.enable_content_fetch', original_enable)
    
    logger.info("\n" + "=" * 60)
    logger.info("集成测试完成！")
    logger.info("=" * 60)
    
    return len(news_list)


if __name__ == '__main__':
    try:
        count = test_rss_fetch()
        print(f"\n✓ 测试成功！共插入 {count} 条新闻")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)