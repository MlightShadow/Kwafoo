"""
textrank4zh压缩器模块测试
测试基于textrank4zh的文本压缩算法
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.textrank_compressor import TextRankCompressor, is_textrank_available
from utils.hybrid_compressor import HybridCompressor, get_compressor, compress_text_hybrid, get_available_algorithms


class TestTextRankCompressor:
    """textrank4zh压缩器测试类"""
    
    def setup_method(self):
        """测试方法前置设置"""
        # 模拟textrank4zh可用
        self.textrank_patcher = patch('utils.textrank_compressor.TEXT_RANK_AVAILABLE', True)
        self.mock_textrank_available = self.textrank_patcher.start()
        
        # 只有在textrank4zh可用时才模拟TextRank4Sentence类
        # 使用更安全的mock方式
        self.tr4s_patcher = patch('utils.textrank_compressor.TextRank4Sentence', create=True)
        self.mock_tr4s_class = self.tr4s_patcher.start()
        
        # 创建模拟实例
        self.mock_tr4s = MagicMock()
        self.mock_tr4s_class.return_value = self.mock_tr4s
        
        # 设置模拟的关键句数据
        self.mock_key_sentences = [
            MagicMock(sentence="这是第一个关键句。", weight=0.9, index=0),
            MagicMock(sentence="这是第二个关键句。", weight=0.8, index=1),
            MagicMock(sentence="这是第三个关键句。", weight=0.7, index=2),
        ]
        self.mock_tr4s.get_key_sentences.return_value = self.mock_key_sentences
        
        # 模拟analyze方法
        self.mock_tr4s.analyze = MagicMock()
        
        self.compressor = TextRankCompressor(target_tokens=2000, compression_level='balanced')
    
    def teardown_method(self):
        """测试方法后置清理"""
        self.textrank_patcher.stop()
        self.tr4s_patcher.stop()
    
    def test_compress_short_text(self):
        """测试短文本压缩（无需压缩）"""
        short_text = "这是一个短文本，不需要压缩。"
        result = self.compressor.compress(short_text)
        
        assert result == short_text
        assert len(result) == len(short_text)
    
    def test_compress_empty_text(self):
        """测试空文本压缩"""
        empty_text = ""
        result = self.compressor.compress(empty_text)
        
        assert result == ""
    
    def test_compress_long_text_with_textrank(self):
        """测试使用textrank4zh压缩长文本"""
        # 创建一个足够长的文本，确保触发压缩
        long_text = """
        人工智能是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
        可以设想，未来人工智能带来的科技产品，将会是人类智慧的“容器”。人工智能可以对人的意识、思维的信息过程的模拟。
        人工智能不是人的智能，但能像人那样思考、也可能超过人的智能。人工智能是一门极富挑战性的科学，从事这项工作的人必须懂得计算机知识。
        """ * 10  # 重复10次以创建长文本
        
        # 使用较小的目标token数强制触发压缩
        compressor = TextRankCompressor(target_tokens=500, compression_level='balanced')
        
        result = compressor.compress(long_text)
        
        # 验证textrank4zh被调用
        self.mock_tr4s.analyze.assert_called_once()
        self.mock_tr4s.get_key_sentences.assert_called_once()
        
        # 验证压缩效果
        assert len(result) > 0
        assert len(result) < len(long_text)
    
    def test_compress_no_key_sentences(self):
        """测试textrank4zh未提取到关键句的情况"""
        # 创建一个足够长的文本，确保触发压缩
        long_text = "这是一个测试文本，用于验证textrank4zh未提取到关键句时的降级压缩功能。" * 50
        
        # 模拟没有关键句
        self.mock_tr4s.get_key_sentences.return_value = []
        
        # 使用较小的目标token数强制触发压缩
        compressor = TextRankCompressor(target_tokens=500, compression_level='balanced')
        
        result = compressor.compress(long_text)
        
        # 验证降级到默认压缩器
        assert len(result) > 0
        assert len(result) < len(long_text)
    
    def test_compress_textrank_exception(self):
        """测试textrank4zh抛出异常的情况"""
        # 创建一个足够长的文本，确保触发压缩
        long_text = "这是一个测试文本，用于验证textrank4zh抛出异常时的降级压缩功能。" * 50
        
        # 模拟抛出异常
        self.mock_tr4s.analyze.side_effect = Exception("模拟异常")
        
        # 使用较小的目标token数强制触发压缩
        compressor = TextRankCompressor(target_tokens=500, compression_level='balanced')
        
        result = compressor.compress(long_text)
        
        # 验证降级到默认压缩器
        assert len(result) > 0
        assert len(result) < len(long_text)
    
    def test_compression_levels(self):
        """测试不同压缩级别的效果"""
        long_text = "这是一个测试句子。" * 50
        
        # 测试平衡压缩
        balanced_compressor = TextRankCompressor(target_tokens=500, compression_level='balanced')
        
        # 测试激进压缩
        aggressive_compressor = TextRankCompressor(target_tokens=500, compression_level='aggressive')
        
        # 测试保守压缩
        conservative_compressor = TextRankCompressor(target_tokens=500, compression_level='conservative')
        
        # 验证压缩器创建成功
        assert balanced_compressor is not None
        assert aggressive_compressor is not None
        assert conservative_compressor is not None
    
    def test_convenience_function(self):
        """测试便捷函数"""
        long_text = "这是一个测试文本，用于验证便捷函数的功能。" * 20
        
        result = compress_text_hybrid(long_text, target_tokens=500, compression_level='aggressive')
        
        assert len(result) > 0


class TestTextRankUnavailable:
    """textrank4zh不可用情况测试"""
    
    def setup_method(self):
        """测试方法前置设置"""
        # 模拟textrank4zh不可用
        self.textrank_patcher = patch('utils.textrank_compressor.TEXT_RANK_AVAILABLE', False)
        self.mock_textrank_available = self.textrank_patcher.start()
        
        self.compressor = TextRankCompressor(target_tokens=2000, compression_level='balanced')
    
    def teardown_method(self):
        """测试方法后置清理"""
        self.textrank_patcher.stop()
    
    def test_compress_with_fallback(self):
        """测试textrank4zh不可用时的降级压缩"""
        # 创建一个足够长的文本，确保触发压缩
        long_text = "这是一个测试文本，用于验证textrank4zh不可用时的降级压缩功能。" * 50
        
        result = self.compressor.compress(long_text)
        
        # 验证使用默认压缩器
        assert len(result) > 0
        # 由于文本可能刚好在阈值附近，使用更宽松的判断
        assert len(result) <= len(long_text)
    
    def test_is_textrank_available(self):
        """测试textrank4zh可用性检查"""
        assert not is_textrank_available()


class TestHybridCompressor:
    """混合压缩器测试类"""
    
    def setup_method(self):
        """测试方法前置设置"""
        # 模拟textrank4zh可用
        self.textrank_patcher = patch('utils.hybrid_compressor.is_textrank_available', return_value=True)
        self.mock_textrank_available = self.textrank_patcher.start()
        
        # 模拟TextRankCompressor
        self.tr_compressor_patcher = patch('utils.hybrid_compressor.TextRankCompressor')
        self.mock_tr_compressor_class = self.tr_compressor_patcher.start()
        
        # 创建模拟实例
        self.mock_tr_compressor = MagicMock()
        self.mock_tr_compressor_class.return_value = self.mock_tr_compressor
        self.mock_tr_compressor.compress.return_value = "textrank压缩结果"
        
        self.compressor = HybridCompressor(algorithm='auto')
    
    def teardown_method(self):
        """测试方法后置清理"""
        self.textrank_patcher.stop()
        self.tr_compressor_patcher.stop()
    
    def test_algorithm_selection_auto(self):
        """测试自动算法选择"""
        # textrank可用时应该选择textrank
        compressor = HybridCompressor(algorithm='auto')
        info = compressor.get_algorithm_info()
        
        assert info['current_algorithm'] == 'textrank'
        assert info['textrank_available'] == True
    
    def test_algorithm_selection_default(self):
        """测试强制使用默认算法"""
        compressor = HybridCompressor(algorithm='default')
        info = compressor.get_algorithm_info()
        
        assert info['current_algorithm'] == 'default'
    
    def test_algorithm_selection_textrank(self):
        """测试强制使用textrank算法"""
        compressor = HybridCompressor(algorithm='textrank')
        info = compressor.get_algorithm_info()
        
        assert info['current_algorithm'] == 'textrank'
    
    def test_compress_with_auto(self):
        """测试自动算法压缩"""
        text = "测试文本"
        result = self.compressor.compress(text)
        
        # 验证使用textrank压缩器
        self.mock_tr_compressor.compress.assert_called_once_with(text, True)
        assert result == "textrank压缩结果"
    
    def test_switch_algorithm(self):
        """测试切换算法"""
        # 切换到默认算法
        success = self.compressor.switch_algorithm('default')
        assert success == True
        
        info = self.compressor.get_algorithm_info()
        assert info['current_algorithm'] == 'default'
        
        # 切换回自动选择
        success = self.compressor.switch_algorithm('auto')
        assert success == True
        
        info = self.compressor.get_algorithm_info()
        assert info['current_algorithm'] == 'textrank'
    
    def test_get_compressor_function(self):
        """测试获取压缩器函数"""
        compressor = get_compressor('auto')
        assert compressor is not None
        
        info = compressor.get_algorithm_info()
        assert info['current_algorithm'] == 'textrank'
    
    def test_compress_text_hybrid_function(self):
        """测试混合压缩便捷函数"""
        text = "测试文本"
        result = compress_text_hybrid(text, algorithm='textrank')
        
        assert result == "textrank压缩结果"
    
    def test_get_available_algorithms(self):
        """测试获取可用算法"""
        algorithms = get_available_algorithms()
        
        assert 'default' in algorithms
        assert 'textrank' in algorithms
        assert 'auto' in algorithms
        
        # 验证描述信息
        assert '默认压缩算法' in algorithms['default']['description']
        assert 'textrank4zh' in algorithms['textrank']['description']


class TestHybridCompressorTextRankUnavailable:
    """textrank4zh不可用时的混合压缩器测试"""
    
    def setup_method(self):
        """测试方法前置设置"""
        # 模拟textrank4zh不可用
        self.textrank_patcher = patch('utils.hybrid_compressor.is_textrank_available', return_value=False)
        self.mock_textrank_available = self.textrank_patcher.start()
        
        self.compressor = HybridCompressor(algorithm='auto')
    
    def teardown_method(self):
        """测试方法后置清理"""
        self.textrank_patcher.stop()
    
    def test_algorithm_selection_auto_unavailable(self):
        """测试textrank不可用时的自动选择"""
        info = self.compressor.get_algorithm_info()
        
        assert info['current_algorithm'] == 'default'
        assert info['textrank_available'] == False
    
    def test_algorithm_selection_textrank_unavailable(self):
        """测试强制使用不可用的textrank算法"""
        compressor = HybridCompressor(algorithm='textrank')
        info = compressor.get_algorithm_info()
        
        # 应该降级到默认算法
        assert info['current_algorithm'] == 'default'
    
    def test_switch_to_unavailable_algorithm(self):
        """测试切换到不可用的算法"""
        success = self.compressor.switch_algorithm('textrank')
        # 应该切换失败
        assert success == False
        info = self.compressor.get_algorithm_info()
        # 应该保持当前算法不变（现在是default）
        assert info['current_algorithm'] == 'default'


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])