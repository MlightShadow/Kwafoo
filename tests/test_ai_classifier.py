"""
AI分类器测试
"""
import pytest
from unittest.mock import Mock, patch
from ai.classifier import AIClassifier


@pytest.fixture
def ai_classifier():
    """创建AI分类器实例"""
    return AIClassifier()


def test_classifier_initialization(ai_classifier):
    """测试分类器初始化"""
    assert ai_classifier.base_url is not None
    assert ai_classifier.model is not None
    assert ai_classifier.max_tokens > 0
    assert ai_classifier.temperature >= 0
    assert ai_classifier.timeout > 0
    assert len(ai_classifier.categories) > 0


def test_classifier_config_update(ai_classifier):
    """测试配置更新"""
    new_config = {
        'ai': {
            'base_url': 'http://test:1234',
            'model': 'test-model',
            'max_tokens': 2048,
            'temperature': 0.5,
            'ai_summary_threshold': 200,
            'timeout': 60
        },
        'categories': [],
        'default_category': '未分类'
    }
    
    ai_classifier.on_config_changed(new_config)
    
    assert ai_classifier.base_url == 'http://test:1234'
    assert ai_classifier.model == 'test-model'
    assert ai_classifier.max_tokens == 2048
    assert ai_classifier.temperature == 0.5
    assert ai_classifier.timeout == 60


@patch('ai.classifier.requests.post')
def test_classify_success(mock_post, ai_classifier):
    """测试成功的分类"""
    # Mock响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{
            'message': {
                'content': '科技,财经'
            }
        }]
    }
    mock_post.return_value = mock_response
    
    result = ai_classifier.classify('测试标题', '测试描述')
    
    assert result is not None
    assert '科技' in result or '财经' in result


@patch('ai.classifier.requests.post')
def test_classify_timeout(mock_post, ai_classifier):
    """测试分类超时"""
    import requests
    mock_post.side_effect = requests.Timeout("请求超时")
    
    result = ai_classifier.classify('测试标题', '测试描述')
    
    assert result is None


@patch('ai.classifier.requests.post')
def test_classify_connection_error(mock_post, ai_classifier):
    """测试分类连接错误"""
    import requests
    mock_post.side_effect = requests.ConnectionError("连接失败")
    
    result = ai_classifier.classify('测试标题', '测试描述')
    
    assert result is None


def test_parse_result_valid(ai_classifier):
    """测试解析有效结果"""
    result = "科技,财经"
    categories = ai_classifier._parse_result(result)
    
    assert categories is not None
    assert len(categories) >= 1


def test_parse_result_empty(ai_classifier):
    """测试解析空结果"""
    result = ""
    categories = ai_classifier._parse_result(result)
    
    assert categories is None


def test_parse_result_invalid(ai_classifier):
    """测试解析无效结果"""
    result = "不存在的分类"
    categories = ai_classifier._parse_result(result)
    
    assert categories is None or len(categories) == 0