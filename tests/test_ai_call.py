import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.classifier import ai_classifier
from ai.summarizer import ai_summarizer
from database import db
from utils.logger import logger


def test_ai_call():
    logger.info("=" * 60)
    logger.info("测试AI调用")
    logger.info("=" * 60)
    
    logger.info("\n【测试1】AI分类测试")
    logger.info("-" * 60)
    
    test_title = "海底捞：控股股东张勇拟增持不少于1亿港元"
    test_description = "海底捞在港交所公告，公司控股股东张勇拟增持公司股份，增持金额不少于1亿港元。"
    
    logger.info(f"测试标题: {test_title}")
    logger.info(f"测试描述: {test_description}")
    
    try:
        categories = ai_classifier.classify(test_title, test_description, None)
        logger.info(f"AI分类结果: {categories}")
        
        if categories:
            logger.info("✓ AI分类成功")
        else:
            logger.warning("✗ AI分类返回空结果")
    except Exception as e:
        logger.error(f"✗ AI分类失败: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n【测试2】AI摘要测试")
    logger.info("-" * 60)
    
    test_content = "海底捞在港交所公告，公司控股股东张勇拟增持公司股份，增持金额不少于1亿港元。此次增持是基于对公司未来发展前景的信心和对公司价值的认可。"
    test_description = "海底捞控股股东张勇拟增持不少于1亿港元"
    
    logger.info(f"测试内容: {test_content}")
    logger.info(f"测试描述: {test_description}")
    
    try:
        summary = ai_summarizer.generate_summary(test_content, test_description)
        logger.info(f"AI摘要结果: {summary}")
        
        if summary:
            logger.info("✓ AI摘要成功")
        else:
            logger.warning("✗ AI摘要返回空结果")
    except Exception as e:
        logger.error(f"✗ AI摘要失败: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n【测试3】数据库中新闻处理测试")
    logger.info("-" * 60)
    
    news_list = db.get_unprocessed_news(limit=1)
    
    if news_list:
        news = news_list[0]
        logger.info(f"测试新闻ID: {news['id']}")
        logger.info(f"测试标题: {news['title']}")
        logger.info(f"测试描述: {news['description'][:100]}...")
        
        try:
            categories = ai_classifier.classify(news['title'], news['description'], None)
            logger.info(f"AI分类结果: {categories}")
            
            if categories:
                category_str = ','.join(categories)
                if db.update_news_category(news['id'], category_str):
                    logger.info(f"✓ 新闻分类已更新: {category_str}")
            else:
                logger.warning("✗ AI分类返回空结果")
        except Exception as e:
            logger.error(f"✗ AI分类失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        logger.info("没有未处理的新闻")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        test_ai_call()
        print("\n✓ 测试完成！")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)