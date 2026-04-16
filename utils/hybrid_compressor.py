"""
混合压缩器：智能选择最佳压缩算法
根据配置和可用性自动选择统一压缩器或textrank4zh压缩器
"""

from typing import Optional
from utils.logger import logger
from utils.helpers import config
from utils.default_compressor import DefaultTextCompressor
from utils.textrank_compressor import TextRankCompressor, is_textrank_available


class HybridCompressor:
    """
    混合压缩器：智能选择最佳压缩算法
    """
    
    def __init__(self, target_tokens: int = None, compression_level: str = None, 
                 algorithm: str = None, compression_mode: str = None):
        """初始化混合压缩器"""
        
        # 从配置读取参数，如果没有提供则使用默认值
        self.target_tokens = target_tokens or config.get('compression.target_tokens', 2000)
        self.compression_level = compression_level or config.get('compression.compression_level', 'balanced')
        self.algorithm = algorithm or config.get('compression.algorithm', 'auto')
        self.compression_mode = compression_mode or config.get('compression.mode', 'summary')
        
        # 初始化两个压缩器
        self.default_compressor = DefaultTextCompressor(self.target_tokens, self.compression_level, self.compression_mode)
        
        # 检查textrank4zh是否可用
        self.textrank_available = is_textrank_available()
        if self.textrank_available:
            self.textrank_compressor = TextRankCompressor(self.target_tokens, self.compression_level)
        else:
            self.textrank_compressor = None
            logger.info("textrank4zh不可用，将使用默认压缩器")
        
        # 记录当前使用的算法
        self.current_algorithm = self._select_algorithm()
        
        logger.debug(f"混合压缩器初始化完成，当前算法: {self.current_algorithm}")
    
    def _select_algorithm(self) -> str:
        """根据配置和可用性选择最佳算法"""
        if self.algorithm == 'textrank':
            if self.textrank_available:
                return 'textrank'
            else:
                logger.warning("配置要求使用textrank但不可用，使用默认算法")
                return 'default'
        
        elif self.algorithm == 'default':
            return 'default'
        
        else:  # auto
            if self.textrank_available:
                # 自动选择：textrank可用时优先使用
                return 'textrank'
            else:
                return 'default'
    
    def compress(self, text: str, preserve_structure: bool = True) -> str:
        """
        使用智能选择的算法压缩文本
        
        Args:
            text: 要压缩的文本
            preserve_structure: 是否保留段落结构
        
        Returns:
            压缩后的文本
        """
        # 处理空白文本
        if not text or not text.strip():
            return ""
        
        # 根据选择的算法进行压缩
        if self.current_algorithm == 'textrank' and self.textrank_compressor:
            logger.debug("使用textrank4zh算法压缩文本")
            return self.textrank_compressor.compress(text, preserve_structure)
        else:
            logger.debug("使用默认算法压缩文本")
            return self.default_compressor.compress(text, preserve_structure)
    
    def get_algorithm_info(self) -> dict:
        """获取压缩器信息"""
        return {
            'current_algorithm': self.current_algorithm,
            'textrank_available': self.textrank_available,
            'configured_algorithm': self.algorithm,
            'target_tokens': self.target_tokens,
            'compression_level': self.compression_level
        }
    
    def switch_algorithm(self, algorithm: str) -> bool:
        """切换压缩算法"""
        if algorithm == 'textrank':
            if self.textrank_available:
                self.current_algorithm = 'textrank'
                self.algorithm = 'textrank'
                logger.info("切换到textrank算法")
                return True
            else:
                logger.warning("无法切换到textrank算法，不可用")
                return False
        
        elif algorithm == 'default':
            self.current_algorithm = 'default'
            self.algorithm = 'default'
            logger.info("切换到默认算法")
            return True
        
        elif algorithm == 'auto':
            self.algorithm = 'auto'
            self.current_algorithm = self._select_algorithm()
            logger.info(f"切换到自动选择算法，当前使用: {self.current_algorithm}")
            return True
        
        else:
            logger.warning(f"未知算法: {algorithm}")
            return False


def get_compressor(algorithm: str = 'auto') -> HybridCompressor:
    """
    获取压缩器实例
    
    Args:
        algorithm: 压缩算法（auto/default/textrank）
    
    Returns:
        压缩器实例
    """
    return HybridCompressor(algorithm=algorithm)


def compress_text_hybrid(text: str, target_tokens: int = 2000, 
                        compression_level: str = 'balanced',
                        algorithm: str = 'auto') -> str:
    """
    便捷函数：使用混合压缩器压缩文本
    
    Args:
        text: 要压缩的文本
        target_tokens: 目标token数
        compression_level: 压缩级别
        algorithm: 压缩算法
    
    Returns:
        压缩后的文本
    """
    # 处理空白文本
    if not text or not text.strip():
        return ""
    
    compressor = HybridCompressor(target_tokens, compression_level, algorithm)
    return compressor.compress(text)


def get_available_algorithms() -> dict:
    """获取可用的压缩算法"""
    textrank_available = is_textrank_available()
    
    return {
        'default': {
            'available': True,
            'description': '默认压缩算法：融合基础和高级算法的完整解决方案'
        },
        'textrank': {
            'available': textrank_available,
            'description': '基于textrank4zh的高质量中文压缩算法'
        },
        'auto': {
            'available': True,
            'description': '自动选择最佳可用算法'
        }
    }