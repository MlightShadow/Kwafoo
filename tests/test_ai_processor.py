"""
AI处理器测试
"""
import pytest
from unittest.mock import Mock, patch
from ai.processor import AINewsProcessor


@pytest.fixture
def ai_processor():
    """创建AI处理器实例"""
    return AINewsProcessor()


def test_processor_initialization(ai_processor):
    """测试处理器初始化"""
    assert ai_processor.max_workers > 0
    assert ai_processor.batch_size > 0
    assert ai_processor.processing is False
    assert ai_processor.processed_count == 0
    assert ai_processor.failed_count == 0
    assert ai_processor._lock is not None


def test_process_news_success(ai_processor):
    """测试成功的新闻处理"""
    news_data = {
        'title': '测试标题',
        'description': '测试描述',
        'content': '测试内容'
    }
    
    with patch('ai.processor.ai_classifier.classify') as mock_classify, \
         patch('ai.processor.ai_summarizer.generate_summary') as mock_summarize, \
         patch('ai.processor.db.update_news_category') as mock_update_cat, \
         patch('ai.processor.db.update_news_summary') as mock_update_sum, \
         patch('ai.processor.db.update_news_ai_status') as mock_update_ai_status:
        
        mock_classify.return_value = ['科技']
        mock_summarize.return_value = '测试摘要'
        mock_update_cat.return_value = True
        mock_update_sum.return_value = True
        mock_update_ai_status.return_value = True
        
        result = ai_processor.process_news(1, news_data, manual=True)
        
        assert result['success'] is True
        assert result['category_updated'] is True
        assert result['summary_updated'] is True


def test_process_news_with_empty_description(ai_processor):
    """测试空描述的新闻处理"""
    news_data = {
        'title': '测试标题',
        'description': '',
        'content': ''
    }
    
    with patch('ai.processor.ai_classifier.classify') as mock_classify, \
         patch('ai.processor.ai_summarizer.generate_summary') as mock_summarize, \
         patch('ai.processor.db.update_news_ai_status') as mock_update_ai_status:
        
        mock_classify.return_value = ['科技']
        mock_summarize.return_value = None
        mock_update_ai_status.return_value = True
        
        result = ai_processor.process_news(1, news_data, manual=True)
        
        assert result['success'] is True
        assert result['category_updated'] is True
        assert result['summary_updated'] is False


def test_process_all_unprocessed_skipped(ai_processor):
    """测试跳过自动处理"""
    ai_processor.enable_ai_category = False
    ai_processor.enable_ai_summary = False
    
    result = ai_processor.process_all_unprocessed(manual=False)
    
    assert result['status'] == 'skipped'


def test_process_all_unprocessed_running(ai_processor):
    """测试处理中状态"""
    ai_processor.processing = True
    
    result = ai_processor.process_all_unprocessed(manual=True)
    
    assert result['status'] == 'running'


@patch('ai.processor.db.get_unprocessed_news')
def test_process_all_unprocessed_no_news(mock_get_news, ai_processor):
    """测试没有未处理新闻"""
    mock_get_news.return_value = []
    
    result = ai_processor.process_all_unprocessed(manual=True)
    
    assert result['status'] == 'completed'
    assert result['total'] == 0


def test_process_batch(ai_processor):
    """测试批次处理"""
    news_list = [
        {'id': 1, 'title': '标题1', 'description': '描述1', 'content': '内容1'},
        {'id': 2, 'title': '标题2', 'description': '描述2', 'content': '内容2'}
    ]
    
    with patch('ai.processor.ai_classifier.classify') as mock_classify, \
         patch('ai.processor.ai_summarizer.generate_summary') as mock_summarize, \
         patch('ai.processor.db.update_news_category') as mock_update_cat, \
         patch('ai.processor.db.update_news_summary') as mock_update_sum, \
         patch('ai.processor.db.update_news_ai_status') as mock_update_ai_status:
        
        mock_classify.return_value = ['科技']
        mock_summarize.return_value = '测试摘要'
        mock_update_cat.return_value = True
        mock_update_sum.return_value = True
        mock_update_ai_status.return_value = True
        
        result = ai_processor.process_batch(news_list, manual=True)
        
        assert result['total'] == 2
        assert result['success'] == 2
        assert result['failed'] == 0


def test_get_status(ai_processor):
    """测试获取状态"""
    with patch('ai.processor.db.get_unprocessed_news') as mock_get_unprocessed:
        mock_get_unprocessed.return_value = []
        
        ai_processor.processing = True
        ai_processor.processed_count = 10
        ai_processor.failed_count = 2
        
        status = ai_processor.get_status()
        
        assert status['processing'] is True
        assert status['processed_count'] == 10
        assert status['failed_count'] == 2


def test_concurrent_processing_protection(ai_processor):
    """测试并发处理保护"""
    import threading
    
    results = []
    
    def try_process():
        result = ai_processor.process_all_unprocessed(manual=True)
        results.append(result['status'])
    
    # 启动多个线程尝试同时处理
    threads = [threading.Thread(target=try_process) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # 只有一个线程应该成功执行，其他应该返回running
    assert 'running' in results
    assert results.count('running') >= 1