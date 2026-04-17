"""
正文抓取器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fetcher.content_fetcher import ContentFetcher
from bs4 import BeautifulSoup


class TestContentFetcher:
    """测试正文抓取器"""
    
    @pytest.fixture
    def fetcher(self):
        """创建正文抓取器实例"""
        return ContentFetcher()
    
    @pytest.fixture
    def sample_html(self):
        """示例HTML"""
        return """
        <html>
            <head><title>测试页面</title></head>
            <body>
                <header>这是头部</header>
                <nav>这是导航</nav>
                <div class="content">
                    <h1>这是标题</h1>
                    <p>这是第一段正文内容。这是一段很长的文本，用于测试正文提取功能。我们需要确保这段文本足够长，以便能够通过最小长度检查。这段文本应该包含足够多的字符，以便能够被正文提取算法正确识别和处理。</p>
                    <p>这是第二段正文内容。继续测试文本密度算法和DOM评分算法。我们需要更多的文本内容来确保测试的有效性。这段文本应该包含足够的信息，以便能够被正确地提取和处理。我们还需要确保这段文本能够通过各种验证检查。</p>
                    <p>这是第三段正文内容。确保正文能够被正确提取和压缩。这是第三段测试文本，我们需要确保它足够长，并且包含足够的信息。这段文本应该能够帮助验证正文提取算法的正确性和有效性。我们还需要确保这段文本能够通过所有必要的检查。</p>
                    <p>这是第四段正文内容。继续添加更多的文本内容，以确保测试的完整性。这段文本应该包含足够多的字符，以便能够通过最小长度检查。我们还需要确保这段文本能够被正确地处理和压缩。这是为了确保正文提取算法能够正常工作。</p>
                </div>
                <aside>这是侧边栏</aside>
                <footer>这是页脚</footer>
            </body>
        </html>
        """
    
    def test_init(self, fetcher):
        """测试初始化"""
        assert fetcher.enable_content_fetch is True
        assert fetcher.algorithm == 'hybrid'
        assert fetcher.min_content_length == 200
        assert fetcher.max_content_length == 10000
        assert fetcher.timeout == 30
    
    @patch('fetcher.content_fetcher.requests.Session.get')
    def test_fetch_page_success(self, mock_get, fetcher, sample_html):
        """测试网页获取成功"""
        # 模拟响应
        mock_response = Mock()
        mock_response.content = sample_html.encode('utf-8')
        mock_response.apparent_encoding = 'utf-8'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 获取网页
        soup = fetcher._fetch_page('http://example.com/test')
        
        # 验证
        assert soup is not None
        assert isinstance(soup, BeautifulSoup)
        assert soup.title.string == '测试页面'
    
    @patch('fetcher.content_fetcher.requests.Session.get')
    def test_fetch_page_failure(self, mock_get, fetcher):
        """测试网页获取失败"""
        # 模拟请求失败
        mock_get.side_effect = Exception('网络错误')
        
        # 获取网页
        soup = fetcher._fetch_page('http://example.com/test')
        
        # 验证
        assert soup is None
    
    def test_clean_text(self, fetcher):
        """测试文本清理"""
        # 测试用例
        test_cases = [
            ('  多余  空格  ', '多余 空格'),
            ('第一段\n\n第二段\n\n第三段', '第一段\n\n第二段\n\n第三段'),
            ('正常文本', '正常文本'),
        ]
        
        for input_text, expected_output in test_cases:
            result = fetcher._clean_text(input_text)
            assert result == expected_output
    
    def test_extract_by_density(self, fetcher, sample_html):
        """测试文本密度法提取"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        # 提取正文
        content = fetcher._extract_by_density(soup)
        
        # 验证
        assert content is not None
        assert '这是第一段正文内容' in content
        assert '这是第二段正文内容' in content
        assert '这是第三段正文内容' in content
        # 应该过滤掉导航、侧边栏、页脚
        assert '这是导航' not in content
        assert '这是侧边栏' not in content
        assert '这是页脚' not in content
    
    def test_extract_by_dom(self, fetcher, sample_html):
        """测试DOM评分法提取"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        # 提取正文
        content = fetcher._extract_by_dom(soup)
        
        # 验证
        assert content is not None
        assert '这是第一段正文内容' in content
        assert '这是第二段正文内容' in content
        assert '这是第三段正文内容' in content
    
    def test_extract_hybrid(self, fetcher, sample_html):
        """测试混合模式提取"""
        soup = BeautifulSoup(sample_html, 'html.parser')
        
        # 提取正文
        content = fetcher._extract_hybrid(soup)
        
        # 验证
        assert content is not None
        assert len(content) >= fetcher.min_content_length
    
    def test_extract_content_too_short(self, fetcher):
        """测试正文长度不足"""
        # 创建一个很短的HTML
        short_html = '<html><body><p>太短了</p></body></html>'
        soup = BeautifulSoup(short_html, 'html.parser')
        
        # 提取正文
        content = fetcher._extract_content(soup)
        
        # 验证：应该返回None
        assert content is None
    
    @patch('fetcher.content_fetcher.HybridCompressor')
    @patch('fetcher.content_fetcher.requests.Session.get')
    def test_fetch_content_success(self, mock_get, mock_compressor, fetcher, sample_html):
        """测试正文抓取成功"""
        # 模拟响应
        mock_response = Mock()
        mock_response.content = sample_html.encode('utf-8')
        mock_response.apparent_encoding = 'utf-8'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # 模拟压缩器
        mock_compressor_instance = Mock()
        mock_compressor_instance.compress = Mock(return_value='压缩后的内容')
        mock_compressor.return_value = mock_compressor_instance
        
        # 抓取正文
        result = fetcher.fetch_content('http://example.com/test')
        
        # 验证
        assert result['success'] is True
        assert result['content'] is not None
        assert result['compressed_content'] is not None
        assert result['error'] is None
    
    @patch('fetcher.content_fetcher.requests.Session.get')
    def test_fetch_content_failure(self, mock_get, fetcher):
        """测试正文抓取失败"""
        # 模拟请求失败
        mock_get.side_effect = Exception('网络错误')
        
        # 抓取正文
        result = fetcher.fetch_content('http://example.com/test')
        
        # 验证
        assert result['success'] is False
        assert result['content'] is None
        assert result['compressed_content'] is None
        assert result['error'] is not None
    
    def test_cache_enabled(self, fetcher):
        """测试缓存功能"""
        # 启用缓存
        fetcher.enable_cache = True
        fetcher.cache = {}
        
        # 第一次抓取
        with patch.object(fetcher, '_fetch_page') as mock_fetch:
            mock_fetch.return_value = None
            result1 = fetcher.fetch_content('http://example.com/test')
        
        # 第二次抓取（应该使用缓存）
        with patch.object(fetcher, '_fetch_page') as mock_fetch:
            result2 = fetcher.fetch_content('http://example.com/test')
        
        # 验证：第二次应该使用缓存，不会调用_fetch_page
        assert result1 == result2
    
    def test_cache_disabled(self, fetcher):
        """测试禁用缓存"""
        # 禁用缓存
        fetcher.enable_cache = False
        fetcher.cache = None
        
        # 抓取
        with patch.object(fetcher, '_fetch_page') as mock_fetch:
            mock_fetch.return_value = None
            result = fetcher.fetch_content('http://example.com/test')
        
        # 验证：缓存应该为None
        assert fetcher.cache is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])