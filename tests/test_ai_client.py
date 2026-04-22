"""
AI客户端单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ai.ai_client import AIClient, AIRequest, AIResponse
from ai.response_validator import ResponseValidator
from ai.retry_strategy import RetryStrategy


class TestAIRequest:
    """测试AIRequest类"""
    
    def test_init_basic(self):
        """测试基本初始化"""
        request = AIRequest(
            task_type='classification',
            prompt='测试提示词'
        )
        
        assert request.task_type == 'classification'
        assert request.prompt == '测试提示词'
        assert request.system_prompt is None
        assert request.response_schema is None
    
    def test_init_with_all_params(self):
        """测试完整参数初始化"""
        schema = {
            "type": "object",
            "properties": {
                "categories": {"type": "array"}
            }
        }
        
        request = AIRequest(
            task_type='classification',
            prompt='测试提示词',
            system_prompt='系统提示词',
            response_schema=schema,
            max_tokens=2048
        )
        
        assert request.task_type == 'classification'
        assert request.prompt == '测试提示词'
        assert request.system_prompt == '系统提示词'
        assert request.response_schema == schema
        assert request.kwargs['max_tokens'] == 2048


class TestAIResponse:
    """测试AIResponse类"""
    
    def test_init_success(self):
        """测试成功响应"""
        response = AIResponse(
            success=True,
            data={'categories': ['科技']},
            raw_response='{"categories": ["科技"]}',
            retry_count=0
        )
        
        assert response.success is True
        assert response.data == {'categories': ['科技']}
        assert response.error is None
        assert response.raw_response == '{"categories": ["科技"]}'
        assert response.retry_count == 0
    
    def test_init_failure(self):
        """测试失败响应"""
        response = AIResponse(
            success=False,
            error='连接失败',
            retry_count=3
        )
        
        assert response.success is False
        assert response.data is None
        assert response.error == '连接失败'
        assert response.raw_response is None
        assert response.retry_count == 3


class TestResponseValidator:
    """测试ResponseValidator类"""
    
    def test_init(self):
        """测试初始化"""
        validator = ResponseValidator()
        assert validator.validation_errors == []
    
    def test_validate_classification_success(self):
        """测试分类验证成功"""
        validator = ResponseValidator()
        data = {
            'categories': ['科技', '人工智能'],
            'keywords': ['AI', '机器学习', '深度学习']
        }
        
        result = validator.validate(data, 'classification')
        
        assert result['valid'] is True
        assert result['error'] is None
    
    def test_validate_classification_missing_field(self):
        """测试分类验证缺少字段"""
        validator = ResponseValidator()
        data = {
            'categories': ['科技']
            # 缺少keywords字段
        }
        
        result = validator.validate(data, 'classification')
        
        assert result['valid'] is False
        assert '缺少必需字段' in result['error']
    
    def test_validate_classification_too_many_categories(self):
        """测试分类验证分类过多"""
        validator = ResponseValidator()
        data = {
            'categories': ['科技', '人工智能', '财经'],
            'keywords': ['AI']
        }
        
        result = validator.validate(data, 'classification')
        
        assert result['valid'] is False
        assert '分类数量不能超过2个' in result['error']
    
    def test_validate_summary_success(self):
        """测试摘要验证成功"""
        validator = ResponseValidator()
        data = {
            'comment': '📰 这是一篇值得关注的新闻',
            'summary': '本文介绍了人工智能领域的最新进展，包括大语言模型的应用和发展趋势，以及相关技术突破。文章深入分析了当前AI技术的应用场景，探讨了未来发展方向，为读者提供了全面的行业洞察和前瞻性思考，具有重要的参考价值和指导意义。同时，文章还讨论了AI技术面临的挑战和机遇，为相关从业者提供了宝贵的经验分享。'
        }
        
        result = validator.validate(data, 'summary')
        
        assert result['valid'] is True
        assert result['error'] is None
    
    def test_validate_summary_missing_emoji(self):
        """测试摘要验证缺少emoji"""
        validator = ResponseValidator()
        data = {
            'comment': '这是一篇值得关注的新闻',
            'summary': '本文介绍了人工智能领域的最新进展，包括大语言模型的应用和发展趋势，以及相关技术突破。文章深入分析了当前AI技术的应用场景，探讨了未来发展方向，为读者提供了全面的行业洞察和前瞻性思考，具有重要的参考价值和指导意义。同时，文章还讨论了AI技术面临的挑战和机遇，为相关从业者提供了宝贵的经验分享。'
        }
        
        result = validator.validate(data, 'summary')
        
        assert result['valid'] is False
        assert 'emoji' in result['error']
    
    def test_validate_summary_wrong_length(self):
        """测试摘要验证长度错误"""
        validator = ResponseValidator()
        data = {
            'comment': '📰 新闻',
            'summary': '太短了'
        }
        
        result = validator.validate(data, 'summary')
        
        assert result['valid'] is False
        assert '长度应在120-160字之间' in result['error']
    
    def test_validate_scoring_success(self):
        """测试评分验证成功"""
        validator = ResponseValidator()
        data = {
            'relevance': 85.0,
            'importance': 75.0,
            'source_score': 90.0
        }
        
        result = validator.validate(data, 'scoring')
        
        assert result['valid'] is True
        assert result['error'] is None
    
    def test_validate_scoring_out_of_range(self):
        """测试评分验证超出范围"""
        validator = ResponseValidator()
        data = {
            'relevance': 150.0,
            'importance': 75.0,
            'source_score': 90.0
        }
        
        result = validator.validate(data, 'scoring')
        
        assert result['valid'] is False
        assert '必须在0-100范围内' in result['error']
    
    def test_validate_categories_success(self):
        """测试分类列表验证成功"""
        validator = ResponseValidator()
        categories = ['科技', '人工智能']
        available_categories = ['科技', '人工智能', '财经', '体育']
        
        result = validator.validate_categories(categories, available_categories)
        
        assert result['valid'] is True
        assert result['error'] is None
    
    def test_validate_categories_invalid(self):
        """测试分类列表验证无效分类"""
        validator = ResponseValidator()
        categories = ['科技', '无效分类']
        available_categories = ['科技', '人工智能', '财经', '体育']
        
        result = validator.validate_categories(categories, available_categories)
        
        assert result['valid'] is False
        assert '无效的分类' in result['error']


class TestRetryStrategy:
    """测试RetryStrategy类"""
    
    def test_init(self):
        """测试初始化"""
        strategy = RetryStrategy()
        assert strategy.error_types is not None
        assert strategy.retry_delays is not None
        assert strategy.max_retries is not None
    
    def test_identify_error_type_timeout(self):
        """测试识别超时错误"""
        strategy = RetryStrategy()
        error_type = strategy._identify_error_type('timeout error')
        
        assert error_type == 'timeout'
    
    def test_identify_error_type_connection(self):
        """测试识别连接错误"""
        strategy = RetryStrategy()
        error_type = strategy._identify_error_type('connection failed')
        
        assert error_type == 'connection'
    
    def test_identify_error_type_json_parse(self):
        """测试识别JSON解析错误"""
        strategy = RetryStrategy()
        error_type = strategy._identify_error_type('JSON parse error')
        
        assert error_type == 'json_parse'
    
    def test_identify_error_type_default(self):
        """测试识别默认错误类型"""
        strategy = RetryStrategy()
        error_type = strategy._identify_error_type('unknown error')
        
        assert error_type == 'default'
    
    def test_get_retry_delay(self):
        """测试获取重试延迟"""
        strategy = RetryStrategy()
        delay = strategy.get_retry_delay('classification', 1, 'timeout')
        
        assert delay > 0
        assert delay <= 30  # 最大延迟30秒
    
    def test_should_retry(self):
        """测试是否应该重试"""
        strategy = RetryStrategy()
        
        assert strategy.should_retry('timeout', 0) is True
        assert strategy.should_retry('timeout', 1) is True
        assert strategy.should_retry('timeout', 2) is True
        assert strategy.should_retry('timeout', 3) is False
    
    def test_set_retry_delay(self):
        """测试设置重试延迟"""
        strategy = RetryStrategy()
        strategy.set_retry_delay('timeout', 5.0)
        
        assert strategy.retry_delays['timeout'] == 5.0
    
    def test_set_max_retries(self):
        """测试设置最大重试次数"""
        strategy = RetryStrategy()
        strategy.set_max_retries('timeout', 5)
        
        assert strategy.max_retries['timeout'] == 5


class TestAIClient:
    """测试AIClient类"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        with patch('ai.ai_client.config') as mock:
            mock.get.side_effect = lambda key, default=None: {
                'ai.base_url': 'http://localhost:1234',
                'ai.model': 'test-model',
                'ai.api_key': 'test-key',
                'ai.max_tokens': 4096,
                'ai.temperature': 0.7,
                'ai.timeout': 120,
                'ai.enable_json_response': True,
                'ai.enable_response_validation': True,
                'ai.max_retries': 3,
                'ai.retry_delay': 1.0
            }.get(key, default)
            yield mock
    
    def test_init(self, mock_config):
        """测试初始化"""
        client = AIClient()
        
        assert client.base_url == 'http://localhost:1234'
        assert client.model == 'test-model'
        assert client.api_key == 'test-key'
        assert client.max_tokens == 4096
        assert client.temperature == 0.7
        assert client.timeout == 120
        assert client.enable_json_response is True
        assert client.enable_response_validation is True
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
    
    def test_build_messages_with_json(self, mock_config):
        """测试构建消息（JSON模式）"""
        client = AIClient()
        request = AIRequest(
            task_type='classification',
            prompt='测试提示词',
            system_prompt='系统提示词'
        )
        
        messages = client._build_messages(request)
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == '系统提示词'
        assert messages[1]['role'] == 'user'
        assert 'JSON格式' in messages[1]['content']
        assert '测试提示词' in messages[1]['content']
    
    def test_build_messages_without_json(self, mock_config):
        """测试构建消息（非JSON模式）"""
        client = AIClient()
        client.enable_json_response = False
        
        request = AIRequest(
            task_type='classification',
            prompt='测试提示词',
            system_prompt='系统提示词'
        )
        
        messages = client._build_messages(request)
        
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == '系统提示词'
        assert messages[1]['role'] == 'user'
        assert 'JSON格式' not in messages[1]['content']
        assert '测试提示词' in messages[1]['content']
    
    def test_get_default_schema(self, mock_config):
        """测试获取默认Schema"""
        client = AIClient()
        
        classification_schema = client._get_default_schema('classification')
        assert classification_schema['type'] == 'object'
        assert 'categories' in classification_schema['properties']
        assert 'keywords' in classification_schema['properties']
        
        summary_schema = client._get_default_schema('summary')
        assert summary_schema['type'] == 'object'
        assert 'comment' in summary_schema['properties']
        assert 'summary' in summary_schema['properties']
        
        scoring_schema = client._get_default_schema('scoring')
        assert scoring_schema['type'] == 'object'
        assert 'relevance' in scoring_schema['properties']
        assert 'importance' in scoring_schema['properties']
        assert 'source_score' in scoring_schema['properties']
    
    def test_parse_json_response_valid(self, mock_config):
        """测试解析有效的JSON响应"""
        client = AIClient()
        content = '{"categories": ["科技"], "keywords": ["AI"]}'
        
        request = AIRequest(task_type='classification', prompt='测试')
        result = client._parse_json_response(content, request)
        
        assert result == {'categories': ['科技'], 'keywords': ['AI']}
    
    def test_parse_json_response_with_code_block(self, mock_config):
        """测试解析带代码块的JSON响应"""
        client = AIClient()
        content = '```json\n{"categories": ["科技"], "keywords": ["AI"]}\n```'
        
        request = AIRequest(task_type='classification', prompt='测试')
        result = client._parse_json_response(content, request)
        
        assert result == {'categories': ['科技'], 'keywords': ['AI']}
    
    def test_parse_json_response_invalid(self, mock_config):
        """测试解析无效的JSON响应"""
        client = AIClient()
        content = '这不是有效的JSON'
        
        request = AIRequest(task_type='classification', prompt='测试')
        
        with pytest.raises(ValueError, match='无法解析JSON响应'):
            client._parse_json_response(content, request)
    
    def test_build_call_kwargs(self, mock_config):
        """测试构建调用参数"""
        client = AIClient()
        request = AIRequest(
            task_type='classification',
            prompt='测试',
            temperature=0.5
        )
        
        kwargs = client._build_call_kwargs(request, 0)
        
        assert kwargs['model'] == 'openai/test-model'
        assert kwargs['api_base'] == 'http://localhost:1234/v1'
        assert kwargs['api_key'] == 'test-key'
        assert kwargs['max_tokens'] == 4096
        assert kwargs['temperature'] == 0.5  # 使用请求中的温度
        assert kwargs['timeout'] == 120
    
    def test_build_call_kwargs_with_retry(self, mock_config):
        """测试构建调用参数（带重试）"""
        client = AIClient()
        request = AIRequest(task_type='classification', prompt='测试')
        
        kwargs = client._build_call_kwargs(request, 2)
        
        assert kwargs['timeout'] == 300  # min(120 * (2 + 1), 300) = min(360, 300) = 300
    
    @patch('ai.ai_client.completion')
    def test_call_success(self, mock_completion, mock_config):
        """测试成功调用"""
        # 模拟成功的响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '{"categories": ["科技"], "keywords": ["AI"]}'
        mock_completion.return_value = mock_response
        
        client = AIClient()
        request = AIRequest(
            task_type='classification',
            prompt='测试提示词',
            system_prompt='系统提示词'
        )
        
        response = client.call(request)
        
        assert response.success is True
        assert response.data == {'categories': ['科技'], 'keywords': ['AI']}
        assert response.retry_count == 0
    
    @patch('ai.ai_client.completion')
    def test_call_with_retry(self, mock_completion, mock_config):
        """测试带重试的调用"""
        # 第一次调用失败，第二次成功
        mock_completion.side_effect = [
            Exception('timeout error'),
            Mock(choices=[Mock(message=Mock(content='{"categories": ["科技"], "keywords": ["AI"]}'))])
        ]
        
        client = AIClient()
        request = AIRequest(
            task_type='classification',
            prompt='测试提示词',
            system_prompt='系统提示词'
        )
        
        response = client.call(request)
        
        assert response.success is True
        assert response.data == {'categories': ['科技'], 'keywords': ['AI']}
        assert response.retry_count == 1
        assert mock_completion.call_count == 2
    
    @patch('ai.ai_client.completion')
    def test_call_failure(self, mock_completion, mock_config):
        """测试调用失败"""
        mock_completion.side_effect = Exception('connection failed')
        
        client = AIClient()
        request = AIRequest(
            task_type='classification',
            prompt='测试提示词',
            system_prompt='系统提示词'
        )
        
        response = client.call(request)
        
        assert response.success is False
        assert 'connection failed' in response.error
        assert response.retry_count == 3  # 最大重试次数


if __name__ == '__main__':
    pytest.main([__file__, '-v'])