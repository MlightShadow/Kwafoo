"""
调度器测试
"""
import pytest
from unittest.mock import Mock, patch
from scheduler.scheduler import Scheduler


@pytest.fixture
def scheduler():
    """创建调度器实例"""
    return Scheduler()


def test_scheduler_initialization(scheduler):
    """测试调度器初始化"""
    assert scheduler.running is False
    assert scheduler.thread is None
    assert scheduler.fetch_interval > 0
    assert scheduler.ai_process_interval > 0
    assert scheduler.max_fetch_workers > 0
    assert scheduler.fetching is False
    assert scheduler.ai_processing is False
    assert scheduler._fetching_lock is not None
    assert scheduler._ai_processing_lock is not None


def test_scheduler_config_update(scheduler):
    """测试配置更新"""
    new_config = {
        'scheduler': {
            'fetch_interval': 3600,
            'ai_process_interval': 1200,
            'auto_fetch': True,
            'auto_ai_process': True,
            'auto_ai_after_fetch': True,
            'max_fetch_workers': 30
        }
    }
    
    scheduler.on_config_changed(new_config)
    
    assert scheduler.fetch_interval == 3600
    assert scheduler.ai_process_interval == 1200
    assert scheduler.auto_fetch is True
    assert scheduler.auto_ai_process is True
    assert scheduler.auto_ai_after_fetch is True
    assert scheduler.max_fetch_workers == 30


def test_fetch_news_async_running(scheduler):
    """测试新闻抓取运行中状态"""
    scheduler.fetching = True
    
    result = scheduler.fetch_news_async()
    
    assert result is False


@patch('scheduler.scheduler.config.get')
def test_fetch_news_success(mock_get_config, scheduler):
    """测试成功的新闻抓取"""
    mock_get_config.return_value = {
        'news_sources': {
            'rss': [
                {'name': '测试源', 'type': 'rss', 'url': 'http://test.com/feed', 'enabled': True}
            ],
            'api': [],
            'web': []
        }
    }
    
    with patch('scheduler.scheduler.rss_fetcher.fetch') as mock_fetch, \
         patch('scheduler.scheduler.progress_monitor.create_task') as mock_create, \
         patch('scheduler.scheduler.progress_monitor.complete_task') as mock_complete:
        
        mock_fetch.return_value = []
        mock_create.return_value = 'test-task-id'
        
        scheduler.fetch_news()
        
        # 验证任务被完成
        mock_complete.assert_called_once()


def test_process_ai_news_async_running(scheduler):
    """测试AI处理运行中状态"""
    scheduler.ai_processing = True
    
    result = scheduler.process_ai_news_async()
    
    assert result is False


@patch('scheduler.scheduler.db.get_unprocessed_news')
def test_process_ai_news_no_news(mock_get_news, scheduler):
    """测试没有未处理新闻"""
    mock_get_news.return_value = []
    
    scheduler.process_ai_news()


def test_fetch_single_source_rss(scheduler):
    """测试抓取RSS源"""
    source = {
        'name': '测试RSS',
        'type': 'rss',
        'url': 'http://test.com/feed',
        'enabled': True,
        'fetch_days': 2
    }
    
    with patch('scheduler.scheduler.rss_fetcher.fetch') as mock_fetch, \
         patch('scheduler.scheduler.progress_monitor.update_progress') as mock_update:
        
        mock_fetch.return_value = [
            {'title': '测试新闻', 'description': '测试描述', 'link': 'http://test.com/1'}
        ]
        
        result = scheduler._fetch_single_source(source, 'rss', 'test-task-id')
        
        assert result.source_name == '测试RSS'
        assert result.source_type == 'rss'
        assert result.success is True


def test_fetch_single_source_api(scheduler):
    """测试抓取API源"""
    source = {
        'name': '测试API',
        'type': 'api',
        'url': 'http://test.com/api',
        'enabled': True
    }
    
    with patch('scheduler.scheduler.api_fetcher.fetch') as mock_fetch:
        mock_fetch.return_value = []
        
        result = scheduler._fetch_single_source(source, 'api', 'test-task-id')
        
        assert result.source_name == '测试API'
        assert result.source_type == 'api'


def test_concurrent_fetch_protection(scheduler):
    """测试并发抓取保护"""
    import threading
    
    results = []
    
    def try_fetch():
        result = scheduler.fetch_news_async()
        results.append(result)
    
    # 启动多个线程尝试同时抓取
    threads = [threading.Thread(target=try_fetch) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # 只有一个线程应该成功执行，其他应该返回False
    assert False in results
    assert results.count(False) >= 1


def test_concurrent_ai_process_protection(scheduler):
    """测试并发AI处理保护"""
    import threading
    
    results = []
    
    def try_process():
        result = scheduler.process_ai_news_async()
        results.append(result)
    
    # 启动多个线程尝试同时处理
    threads = [threading.Thread(target=try_process) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # 只有一个线程应该成功执行，其他应该返回False
    assert False in results
    assert results.count(False) >= 1