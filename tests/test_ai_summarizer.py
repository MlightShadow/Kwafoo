"""
AI摘要器测试
"""
import pytest
from unittest.mock import Mock, patch
from ai.summarizer import AISummarizer


@pytest.fixture
def ai_summarizer():
    """创建AI摘要器实例"""
    return AISummarizer()


def test_summarizer_initialization(ai_summarizer):
    """测试摘要器初始化"""
    assert ai_summarizer.base_url is not None
    assert ai_summarizer.model is not None
    assert ai_summarizer.max_tokens > 0
    assert ai_summarizer.temperature >= 0
    assert ai_summarizer.description_threshold > 0
    assert ai_summarizer.max_input_length > 0
    assert ai_summarizer.timeout > 0


def test_summarizer_config_update(ai_summarizer):
    """测试配置更新"""
    new_config = {
        'ai': {
            'base_url': 'http://test:1234',
            'model': 'test-model',
            'max_tokens': 2048,
            'temperature': 0.5,
            'max_input_length': 2000,
            'timeout': 60
        },
        'ai_summary_threshold': 200,
        'categories': [],
        'default_category': '未分类'
    }
    
    ai_summarizer.on_config_changed(new_config)
    
    assert ai_summarizer.base_url == 'http://test:1234'
    assert ai_summarizer.model == 'test-model'
    assert ai_summarizer.max_tokens == 2048
    assert ai_summarizer.temperature == 0.5
    assert ai_summarizer.description_threshold == 200
    assert ai_summarizer.timeout == 60


@patch('ai.summarizer.requests.post')
def test_generate_summary_success(mock_post, ai_summarizer):
    """测试成功的摘要生成"""
    # Mock响应
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{
            'message': {
                'content': '这是一个测试摘要'
            }
        }]
    }
    mock_post.return_value = mock_response
    
    # 测试英文描述（会触发AI摘要）
    result = ai_summarizer.generate_summary('Test content', 'Test description')
    
    assert result is not None
    assert '测试摘要' in result


@patch('ai.summarizer.requests.post')
def test_generate_summary_timeout(mock_post, ai_summarizer):
    """测试摘要生成超时"""
    import requests
    mock_post.side_effect = requests.Timeout("请求超时")
    
    result = ai_summarizer.generate_summary('测试内容', '测试描述')
    
    assert result is None


def test_smart_truncate_short_text(ai_summarizer):
    """测试短文本智能截取"""
    from ai.summarizer import smart_truncate
    short_text = "这是一段短文本"
    result = smart_truncate(short_text, max_length=200)
    
    assert result == short_text


def test_smart_truncate_long_text(ai_summarizer):
    """测试长文本智能截取"""
    from ai.summarizer import smart_truncate
    long_text = "这是一段很长的文本。" * 100
    result = smart_truncate(long_text, max_length=200)
    
    assert len(result) <= 200
    assert '...' in result or len(result) == len(long_text)


def test_contains_chinese(ai_summarizer):
    """测试中文检测"""
    from ai.summarizer import contains_chinese
    assert contains_chinese("这是中文") is True
    assert contains_chinese("This is English") is False
    assert contains_chinese("这是中文 and English") is True


def test_build_translate_and_summarize_prompt(ai_summarizer):
    """测试翻译和摘要提示词构建"""
    prompt = ai_summarizer._build_translate_and_summarize_prompt("Test content")
    
    assert "翻译" in prompt or "translate" in prompt.lower()
    assert "Test content" in prompt


def test_build_rewrite_prompt(ai_summarizer):
    """测试重写提示词构建"""
    prompt = ai_summarizer._build_rewrite_prompt("这是一段很长的描述文本" * 10)
    
    assert "改写" in prompt or "rewrite" in prompt.lower()
    assert len(prompt) > 0