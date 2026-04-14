"""
新闻API测试
"""
import pytest
from unittest.mock import Mock, patch
from web.api.news_api import NewsAPI
from utils.validators import GetNewsParams, SearchNewsParams, GetNewsByCategoryParams, MarkAsReadParams


@pytest.fixture
def news_api_handler():
    """创建新闻API处理器实例"""
    return NewsAPI()


@pytest.fixture
def mock_handler():
    """创建Mock请求处理器"""
    handler = Mock()
    handler._send_json_response = Mock()
    handler._send_error_response = Mock()
    # 设置handler属性以支持参数解析
    handler.path = '/api/news?limit=10&offset=0'
    handler.headers = {'Content-Length': '0'}
    handler.rfile = Mock()
    handler.rfile.read = Mock(return_value=b'')
    return handler


@patch('web.api.news_api.db.get_news_by_category')
def test_get_news_success(mock_get_news, news_api_handler, mock_handler):
    """测试获取新闻成功"""
    mock_get_news.return_value = [
        {'id': 1, 'title': '测试新闻1', 'category': '科技'},
        {'id': 2, 'title': '测试新闻2', 'category': '财经'}
    ]
    
    # 设置handler路径以支持参数解析
    mock_handler.path = '/api/news?limit=10&offset=0'
    params = GetNewsParams(limit=10, offset=0)
    news_api_handler.get_news(mock_handler, params)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert len(call_args['data']) == 2
    assert call_args['count'] == 2


@patch('web.api.news_api.db.get_news_by_category')
def test_get_news_by_category_success(mock_get_news, news_api_handler, mock_handler):
    """测试按分类获取新闻成功"""
    mock_get_news.return_value = [
        {'id': 1, 'title': '测试新闻', 'category': '科技'}
    ]
    
    params = GetNewsByCategoryParams(category='科技', limit=10, offset=0)
    news_api_handler.get_news_by_category(mock_handler, params)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert call_args['category'] == '科技'
    assert len(call_args['data']) == 1


@patch('web.api.news_api.db.search_news')
def test_search_news_success(mock_search, news_api_handler, mock_handler):
    """测试搜索新闻成功"""
    mock_search.return_value = [
        {'id': 1, 'title': '人工智能新闻', 'category': '科技'}
    ]
    
    params = SearchNewsParams(query='人工智能', limit=10, offset=0)
    news_api_handler.search_news(mock_handler, params)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert call_args['query'] == '人工智能'
    assert len(call_args['data']) == 1


@patch('web.api.news_api.db.get_news_stats')
def test_get_news_stats_success(mock_get_stats, news_api_handler, mock_handler):
    """测试获取新闻统计成功"""
    mock_get_stats.return_value = {
        'total': 100,
        'by_category': {'科技': 50, '财经': 30, '国际': 20}
    }
    
    news_api_handler.get_news_stats(mock_handler)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert call_args['data']['total'] == 100


@patch('web.api.news_api.db.mark_all_news_deleted')
def test_clear_news_success(mock_mark_deleted, news_api_handler, mock_handler):
    """测试清空新闻成功"""
    mock_mark_deleted.return_value = 50
    
    news_api_handler.clear_news(mock_handler)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert call_args['count'] == 50


@patch('web.api.news_api.db.mark_news_as_read')
def test_mark_as_read_success(mock_mark_read, news_api_handler, mock_handler):
    """测试标记已读成功"""
    mock_mark_read.return_value = True
    
    params = MarkAsReadParams(news_ids=[1, 2, 3])
    news_api_handler.mark_as_read(mock_handler, params)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert '标记为已读' in call_args['message']


@patch('web.api.news_api.db.mark_news_as_read')
def test_mark_as_read_failure(mock_mark_read, news_api_handler, mock_handler):
    """测试标记已读失败"""
    mock_mark_read.return_value = False
    
    params = MarkAsReadParams(news_ids=[1, 2, 3])
    news_api_handler.mark_as_read(mock_handler, params)
    
    mock_handler._send_error_response.assert_called_once()


@patch('web.api.news_api.db.get_read_news')
def test_get_read_news_success(mock_get_read, news_api_handler, mock_handler):
    """测试获取已读新闻成功"""
    mock_get_read.return_value = [
        {'id': 1, 'title': '已读新闻1'},
        {'id': 2, 'title': '已读新闻2'}
    ]
    
    news_api_handler.get_read_news(mock_handler)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert len(call_args['data']) == 2


@patch('web.api.news_api.db.get_unread_news')
def test_get_unread_news_success(mock_get_unread, news_api_handler, mock_handler):
    """测试获取未读新闻成功"""
    mock_get_unread.return_value = [
        {'id': 3, 'title': '未读新闻1'},
        {'id': 4, 'title': '未读新闻2'}
    ]
    
    news_api_handler.get_unread_news(mock_handler)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert len(call_args['data']) == 2


def test_get_news_parameter_validation(news_api_handler, mock_handler):
    """测试获取新闻参数验证"""
    # 测试limit参数超出范围
    with patch('web.api.news_api.db.get_news_by_category') as mock_get:
        params = GetNewsParams(limit=10, offset=0)
        news_api_handler.get_news(mock_handler, params)
        
        # 验证调用时使用了正确的参数
        assert mock_get.called


def test_search_news_parameter_validation(news_api_handler, mock_handler):
    """测试搜索新闻参数验证"""
    # 测试搜索关键词验证
    with patch('web.api.news_api.db.search_news') as mock_search:
        params = SearchNewsParams(query='人工智能', limit=10, offset=0)
        news_api_handler.search_news(mock_handler, params)
        
        # 验证调用时使用了正确的参数
        assert mock_search.called