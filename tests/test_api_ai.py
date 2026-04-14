"""
AI API测试
"""
import pytest
from unittest.mock import Mock, patch
from web.api.ai_api import AIAPI
from utils.validators import ProcessNewsParams


@pytest.fixture
def ai_api_handler():
    """创建AI API处理器实例"""
    return AIAPI()


@pytest.fixture
def mock_handler():
    """创建Mock请求处理器"""
    handler = Mock()
    handler._send_json_response = Mock()
    handler._send_error_response = Mock()
    return handler


def test_get_ai_status(ai_api_handler, mock_handler):
    """测试获取AI状态"""
    with patch('web.api.ai_api.ai_news_processor.get_status') as mock_get_status:
        mock_get_status.return_value = {
            'processing': False,
            'processed_count': 100,
            'failed_count': 5
        }
        
        ai_api_handler.get_ai_status(mock_handler)
        
        mock_handler._send_json_response.assert_called_once()
        call_args = mock_handler._send_json_response.call_args[0][0]
        assert call_args['success'] is True
        assert call_args['data']['processing'] is False


@patch('web.api.ai_api.scheduler.process_ai_news')
def test_process_ai_news_success(mock_process, ai_api_handler, mock_handler):
    """测试处理AI新闻成功"""
    ai_api_handler.process_ai_news(mock_handler)
    
    mock_process.assert_called_once()
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True


@patch('web.api.ai_api.scheduler.process_all_news_ai')
def test_process_all_news_ai_success(mock_process, ai_api_handler, mock_handler):
    """测试处理所有AI新闻成功"""
    ai_api_handler.process_all_news_ai(mock_handler)
    
    mock_process.assert_called_once()
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True


@patch('web.api.ai_api.db.get_ai_queue_stats')
def test_get_ai_queue_stats_success(mock_get_stats, ai_api_handler, mock_handler):
    """测试获取AI队列统计成功"""
    mock_get_stats.return_value = {
        'total': 50,
        'pending': 10,
        'processing': 5,
        'completed': 35
    }
    
    ai_api_handler.get_ai_queue_stats(mock_handler)
    
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert call_args['data']['total'] == 50


@patch('web.api.ai_api.db.get_news_by_id')
@patch('web.api.ai_api.db.add_to_ai_queue')
def test_process_single_news_ai_success(mock_add_queue, mock_get_news, ai_api_handler, mock_handler):
    """测试处理单条AI新闻成功"""
    mock_get_news.return_value = [{'id': 1, 'title': '测试新闻'}]
    mock_add_queue.return_value = 1
    
    params = ProcessNewsParams(news_id=1, force=False)
    ai_api_handler.process_single_news_ai(mock_handler, params)
    
    mock_add_queue.assert_called_once()
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True


@patch('web.api.ai_api.db.get_news_by_id')
def test_process_single_news_ai_not_found(mock_get_news, ai_api_handler, mock_handler):
    """测试处理单条AI新闻不存在"""
    mock_get_news.return_value = []
    
    params = ProcessNewsParams(news_id=1, force=False)
    ai_api_handler.process_single_news_ai(mock_handler, params)
    
    mock_handler._send_error_response.assert_called_once()


@patch('web.api.ai_api.db.get_news_by_id')
@patch('web.api.ai_api.db.add_to_ai_queue')
@patch('web.api.ai_api.db.clear_ai_status')
def test_process_single_news_ai_with_force(mock_clear_status, mock_add_queue, mock_get_news, ai_api_handler, mock_handler):
    """测试强制重新处理单条AI新闻"""
    mock_get_news.return_value = [{'id': 1, 'title': '测试新闻'}]
    mock_add_queue.return_value = 1
    
    params = ProcessNewsParams(news_id=1, force=True)
    ai_api_handler.process_single_news_ai(mock_handler, params)
    
    # 验证调用了clear_ai_status
    mock_clear_status.assert_called_once_with(1)
    # 验证调用了add_to_ai_queue
    assert mock_add_queue.called


@patch('web.api.ai_api.db.get_news_by_id')
@patch('web.api.ai_api.db.add_to_ai_queue')
def test_process_news_category_success(mock_add_queue, mock_get_news, ai_api_handler, mock_handler):
    """测试处理新闻分类成功"""
    mock_get_news.return_value = [{'id': 1, 'title': '测试新闻'}]
    mock_add_queue.return_value = 1
    
    params = ProcessNewsParams(news_id=1, force=False)
    ai_api_handler.process_news_category(mock_handler, params)
    
    mock_add_queue.assert_called_once()
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert '分类' in call_args['message']


@patch('web.api.ai_api.db.get_news_by_id')
@patch('web.api.ai_api.db.add_to_ai_queue')
def test_process_news_summary_success(mock_add_queue, mock_get_news, ai_api_handler, mock_handler):
    """测试处理新闻摘要成功"""
    mock_get_news.return_value = [{'id': 1, 'title': '测试新闻'}]
    mock_add_queue.return_value = 1
    
    params = ProcessNewsParams(news_id=1, force=False)
    ai_api_handler.process_news_summary(mock_handler, params)
    
    mock_add_queue.assert_called_once()
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert '摘要' in call_args['message']


@patch('web.api.ai_api.db.get_news_by_id')
@patch('web.api.ai_api.db.add_to_ai_queue')
def test_process_news_reanalyze_success(mock_add_queue, mock_get_news, ai_api_handler, mock_handler):
    """测试重新分析新闻成功"""
    mock_get_news.return_value = [{'id': 1, 'title': '测试新闻'}]
    mock_add_queue.return_value = 1
    
    params = ProcessNewsParams(news_id=1, force=False)
    ai_api_handler.process_news_reanalyze(mock_handler, params)
    
    mock_add_queue.assert_called_once()
    mock_handler._send_json_response.assert_called_once()
    call_args = mock_handler._send_json_response.call_args[0][0]
    assert call_args['success'] is True
    assert '重新分析' in call_args['message']


def test_process_single_news_ai_parameter_validation(ai_api_handler, mock_handler):
    """测试处理单条AI新闻参数验证"""
    # 测试news_id参数验证
    with patch('web.api.ai_api.db.get_news_by_id') as mock_get:
        params = ProcessNewsParams(news_id=1, force=False)
        ai_api_handler.process_single_news_ai(mock_handler, params)
        
        # 验证调用了get_news_by_id
        assert mock_get.called


def test_process_news_category_parameter_validation(ai_api_handler, mock_handler):
    """测试处理新闻分类参数验证"""
    # 测试news_id参数验证
    with patch('web.api.ai_api.db.get_news_by_id') as mock_get:
        params = ProcessNewsParams(news_id=1, force=False)
        ai_api_handler.process_news_category(mock_handler, params)
        
        # 验证调用了get_news_by_id
        assert mock_get.called


def test_process_news_summary_parameter_validation(ai_api_handler, mock_handler):
    """测试处理新闻摘要参数验证"""
    # 测试news_id参数验证
    with patch('web.api.ai_api.db.get_news_by_id') as mock_get:
        params = ProcessNewsParams(news_id=1, force=False)
        ai_api_handler.process_news_summary(mock_handler, params)
        
        # 验证调用了get_news_by_id
        assert mock_get.called


def test_process_news_reanalyze_parameter_validation(ai_api_handler, mock_handler):
    """测试重新分析新闻参数验证"""
    # 测试news_id和force参数验证
    with patch('web.api.ai_api.db.get_news_by_id') as mock_get:
        params = ProcessNewsParams(news_id=1, force=False)
        ai_api_handler.process_news_reanalyze(mock_handler, params)
        
        # 验证调用了get_news_by_id
        assert mock_get.called