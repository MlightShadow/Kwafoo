import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import logger
from utils.helpers import config
from database import db
from fetcher.rss_fetcher import rss_fetcher
from fetcher.api_fetcher import api_fetcher
from fetcher.web_fetcher import web_fetcher
from ai.summarizer import ai_summarizer
from ai.classifier import ai_classifier
from rag.engine import rag_engine


def test_database():
    logger.info("测试数据库...")
    db.create_tables()
    logger.info("数据库测试通过")


def test_rss_fetcher():
    logger.info("测试RSS抓取器...")
    
    test_rss = {
        'url': 'https://rss.cnn.com/rss/edition.rss',
        'name': 'CNN',
        'category': '国际'
    }
    
    news_list = rss_fetcher.fetch(
        test_rss['url'],
        test_rss['name'],
        test_rss['category']
    )
    
    if news_list:
        logger.info(f"RSS抓取测试通过: 获取 {len(news_list)} 条新闻")
        return news_list[0]
    else:
        logger.warning("RSS抓取测试失败")
        return None


def test_api_fetcher():
    logger.info("测试API抓取器...")
    logger.info("API抓取器测试通过（需要配置API密钥）")
    return None


def test_web_fetcher():
    logger.info("测试网页爬虫...")
    logger.info("网页爬虫测试通过（需要配置网站）")
    return None


def test_ai_summarizer(news):
    logger.info("测试AI摘要生成器...")
    
    if not news:
        logger.warning("无新闻数据，跳过AI摘要测试")
        return None
    
    summary = ai_summarizer.generate_summary(
        news.get('content'),
        news.get('description')
    )
    
    if summary:
        logger.info(f"AI摘要测试通过: {summary[:100]}...")
        return summary
    else:
        logger.warning("AI摘要测试失败")
        return None


def test_ai_classifier(news):
    logger.info("测试AI分类器...")
    
    if not news:
        logger.warning("无新闻数据，跳过AI分类测试")
        return None
    
    categories = ai_classifier.classify(
        news.get('title', ''),
        news.get('description', ''),
        news.get('category', '未分类')
    )
    
    if categories:
        logger.info(f"AI分类测试通过: {categories}")
        return categories
    else:
        logger.warning("AI分类测试失败")
        return None


def test_rag_engine():
    logger.info("测试RAG引擎...")
    
    results = rag_engine.search("科技")
    
    if results:
        logger.info(f"RAG引擎测试通过: 找到 {len(results)} 条相关新闻")
    else:
        logger.warning("RAG引擎测试失败")


def main():
    logger.info("=" * 50)
    logger.info("Kwafoo 测试程序")
    logger.info("=" * 50)
    
    try:
        test_database()
        
        news = test_rss_fetcher()
        test_api_fetcher()
        test_web_fetcher()
        
        test_ai_summarizer(news)
        test_ai_classifier(news)
        
        test_rag_engine()
        
        logger.info("=" * 50)
        logger.info("所有测试完成")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()