"""
基于textrank4zh的文本压缩器
提供比TF-IDF更高质量的中文文本压缩
"""

import re
from typing import Optional
from utils.logger import logger
from utils.helpers import config
from utils.default_compressor import DefaultTextCompressor


# 在模块级别定义TEXT_RANK_AVAILABLE
try:
    from textrank4zh import TextRank4Sentence
    TEXT_RANK_AVAILABLE = True
except ImportError:
    TEXT_RANK_AVAILABLE = False
    logger.warning("textrank4zh库未安装，将使用统一压缩器")


class TextRankCompressor:
    """
    基于textrank4zh的文本压缩器
    提供比TF-IDF更高质量的中文文本压缩
    """
    
    def __init__(self, target_tokens: int = None, compression_level: str = None):
        """初始化textrank压缩器"""
        # 从配置读取参数，如果没有提供则使用默认值
        self.target_tokens = target_tokens or config.get('compression.target_tokens', 2000)
        self.compression_level = compression_level or config.get('compression.compression_level', 'balanced')
        
        # 平均字符每token（中文约2-3字符/token）
        self.avg_chars_per_token = 2.5
        self.target_chars = int(self.target_tokens * self.avg_chars_per_token)
        
        # 根据压缩级别调整参数
        self._set_compression_level()
        
        # 检查textrank4zh是否可用
        if not TEXT_RANK_AVAILABLE:
            logger.warning("textrank4zh不可用，将使用默认压缩器")
            self.fallback_compressor = DefaultTextCompressor(target_tokens, compression_level)
        else:
            self.fallback_compressor = None
            self.tr4s = TextRank4Sentence()
    
    def _set_compression_level(self):
        """根据压缩级别设置参数"""
        if self.compression_level == 'aggressive':
            # 激进压缩：选择更少的句子
            self.sentence_count_factor = 0.1
            self.min_sentence_length = 50
        elif self.compression_level == 'conservative':
            # 保守压缩：选择更多的句子
            self.sentence_count_factor = 0.3
            self.min_sentence_length = 20
        else:  # balanced
            # 平衡压缩：默认设置
            self.sentence_count_factor = 0.2
            self.min_sentence_length = 30
    
    def compress(self, text: str, preserve_structure: bool = True) -> str:
        """
        使用textrank4zh压缩文本
        
        Args:
            text: 要压缩的文本
            preserve_structure: 是否保留段落结构（textrank4zh不支持此功能）
        
        Returns:
            压缩后的文本
        """
        # 处理空白文本
        if not text or not text.strip():
            return ""
        
        # 清理文本
        cleaned_text = text.strip()
        
        # 检查文本长度是否需要进行压缩
        if len(cleaned_text) <= self.target_chars:
            logger.debug("文本长度在目标范围内，无需压缩")
            return cleaned_text
        
        # 如果textrank4zh不可用，使用默认压缩器
        if self.fallback_compressor:
            logger.debug("textrank4zh不可用，使用默认压缩器")
            return self.fallback_compressor.compress(cleaned_text, preserve_structure)
        
        logger.debug(f"开始使用textrank4zh压缩文本，原始长度: {len(cleaned_text)} 字符，目标: {self.target_chars} 字符")
        
        try:
            # 使用textrank4zh进行关键句提取
            self.tr4s.analyze(cleaned_text, lower=True, source='all_filters')
            
            # 获取关键句
            key_sentences = self.tr4s.get_key_sentences(num=20)  # 获取最多20个关键句
            
            if not key_sentences:
                logger.warning("textrank4zh未提取到关键句，使用默认压缩器")
                return self._fallback_compress(cleaned_text, preserve_structure)
            
            # 计算需要选择的句子数量
            total_sentences = len(key_sentences)
            target_sentence_count = max(3, int(total_sentences * self.sentence_count_factor))
            
            # 按重要性排序并选择关键句
            sorted_sentences = sorted(key_sentences, key=lambda x: x.weight, reverse=True)
            selected_sentences = sorted_sentences[:target_sentence_count]
            
            # 按原始顺序排序
            selected_sentences.sort(key=lambda x: x.index)
            
            # 构建压缩文本
            compressed_text = '。'.join([s.sentence for s in selected_sentences]) + '。'
            
            # 如果压缩后文本仍然太长，使用智能截断
            if len(compressed_text) > self.target_chars:
                compressed_text = self._smart_truncate(compressed_text)
            
            compression_ratio = len(compressed_text) / len(cleaned_text)
            logger.debug(f"textrank4zh压缩完成，压缩比: {compression_ratio:.2%}，最终长度: {len(compressed_text)} 字符")
            
            return compressed_text
            
        except Exception as e:
            logger.error(f"textrank4zh压缩失败: {e}，使用默认压缩器")
            return self._fallback_compress(cleaned_text, preserve_structure)
    
    def _fallback_compress(self, text: str, preserve_structure: bool) -> str:
        """降级到默认压缩器"""
        if not hasattr(self, '_fallback_compressor'):
            self._fallback_compressor = DefaultTextCompressor(self.target_tokens, self.compression_level)
        
        logger.debug("使用默认压缩器作为降级方案")
        return self._fallback_compressor.compress(text, preserve_structure)
    
    def _smart_truncate(self, text: str) -> str:
        """智能截断"""
        if len(text) <= self.target_chars:
            return text
        
        # 简单的截断策略：在句子边界截断
        sentences = text.split('。')
        
        current_length = 0
        result_sentences = []
        
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue
                
            sent_with_period = sent + '。'
            sent_length = len(sent_with_period)
            
            if current_length + sent_length <= self.target_chars:
                result_sentences.append(sent)
                current_length += sent_length
            else:
                # 计算还能容纳的字符数
                remaining_chars = self.target_chars - current_length
                if remaining_chars > 30:  # 至少保留30字符才有意义
                    # 截断句子
                    truncated = sent[:remaining_chars].rstrip()
                    if truncated:
                        result_sentences.append(truncated + "...")
                break
        
        result = '。'.join(result_sentences) + '。'
        
        # 如果结果还是太长，直接截断
        if len(result) > self.target_chars:
            result = result[:self.target_chars].rstrip() + "..."
        
        return result


def is_textrank_available() -> bool:
    """检查textrank4zh是否可用"""
    return TEXT_RANK_AVAILABLE


def compress_with_textrank(text: str, target_tokens: int = 2000, 
                          compression_level: str = 'balanced') -> str:
    """
    便捷函数：使用textrank4zh压缩文本
    
    Args:
        text: 要压缩的文本
        target_tokens: 目标token数
        compression_level: 压缩级别
    
    Returns:
        压缩后的文本
    """
    # 处理空白文本
    if not text or not text.strip():
        return ""
    
    compressor = TextRankCompressor(target_tokens, compression_level)
    return compressor.compress(text)