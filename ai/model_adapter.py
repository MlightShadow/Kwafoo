"""
模型适配器模块

为不同的AI模型提供统一的接口和响应解析能力
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from utils.logger import logger
from ai.model_config import get_model_features, is_reasoning_model


class ModelAdapter(ABC):
    """
    模型适配器基类
    
    所有模型适配器都需要实现这些方法，以提供统一的接口
    """
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    def extract_classification(self, response_data: Dict[str, Any], 
                           available_categories: List[str],
                           default_category: str) -> Optional[List[str]]:
        """
        从模型响应中提取分类结果
        
        Args:
            response_data: 模型的原始响应数据
            available_categories: 可用的分类列表
            default_category: 默认分类
            
        Returns:
            提取的分类列表，如果失败返回None
        """
        pass
    
    @abstractmethod
    def extract_summary(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从模型响应中提取摘要结果
        
        Args:
            response_data: 模型的原始响应数据
            
        Returns:
            提取的摘要文本，如果失败返回None
        """
        pass
    
    @abstractmethod
    def supports_reasoning(self) -> bool:
        """
        检查模型是否支持推理模式
        
        Returns:
            是否支持推理模式
        """
        pass
    
    def get_message_content(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        获取消息内容（通用方法）
        
        Args:
            response_data: 模型的原始响应数据
            
        Returns:
            消息内容，如果失败返回None
        """
        try:
            if 'choices' not in response_data or len(response_data['choices']) == 0:
                logger.error("响应格式错误: 缺少choices字段")
                return None
            
            message = response_data['choices'][0]['message']
            
            # 优先使用content字段
            if 'content' in message:
                return message['content'].strip()
            
            logger.warning("响应中没有content字段")
            return None
            
        except Exception as e:
            logger.error(f"获取消息内容失败: {e}")
            return None
    
    def get_reasoning_content(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        获取推理内容（通用方法）
        
        Args:
            response_data: 模型的原始响应数据
            
        Returns:
            推理内容，如果不存在返回None
        """
        try:
            if 'choices' not in response_data or len(response_data['choices']) == 0:
                return None
            
            message = response_data['choices'][0]['message']
            
            # 检查是否有reasoning_content字段
            if 'reasoning_content' in message:
                return message['reasoning_content'].strip()
            
            return None
            
        except Exception as e:
            logger.error(f"获取推理内容失败: {e}")
            return None


class StandardModelAdapter(ModelAdapter):
    """
    标准模型适配器
    
    适用于大多数遵循OpenAI API格式的模型
    这些模型通常直接返回结果，不包含推理过程
    """
    
    def extract_classification(self, response_data: Dict[str, Any], 
                           available_categories: List[str],
                           default_category: str) -> Optional[List[str]]:
        """
        从标准模型响应中提取分类结果
        """
        content = self.get_message_content(response_data)
        if not content:
            return None
        
        # 标准模型通常直接返回分类，如 "科技" 或 "科技,互联网"
        return self._parse_simple_classification(content, available_categories, default_category)
    
    def extract_summary(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从标准模型响应中提取摘要结果
        """
        content = self.get_message_content(response_data)
        if not content:
            return None
        
        # 标准模型通常直接返回摘要
        return content
    
    def supports_reasoning(self) -> bool:
        """
        标准模型通常不支持推理模式
        """
        return False
    
    def _parse_simple_classification(self, content: str, 
                                   available_categories: List[str],
                                   default_category: str) -> Optional[List[str]]:
        """
        解析简单的分类结果
        """
        try:
            content = content.strip()
            
            if not content:
                return None
            
            # 尝试多种分隔符
            categories = []
            for separator in [',', '，', '、']:
                if separator in content:
                    parts = content.split(separator)
                    for part in parts:
                        part = part.strip()
                        if part == '未分类':
                            continue
                        if part in available_categories:
                            categories.append(part)
                        elif part == default_category:
                            categories.append(part)
                    if categories:
                        break
            
            # 如果没有找到，尝试直接匹配
            if not categories:
                for cat in available_categories:
                    if cat in content and len(content) < 100:
                        categories.append(cat)
                if default_category in content and len(content) < 100:
                    categories.append(default_category)
            
            if categories:
                categories = list(set(categories))
                if len(categories) > 2:
                    categories = categories[:2]
                return categories
            
            return None
            
        except Exception as e:
            logger.error(f"解析简单分类失败: {e}")
            return None


class ReasoningModelAdapter(ModelAdapter):
    """
    推理模型适配器
    
    适用于支持推理模式的模型，如Gemma-4、DeepSeek等
    这些模型可能将推理过程和最终结果混合在一起
    """
    
    def extract_classification(self, response_data: Dict[str, Any], 
                           available_categories: List[str],
                           default_category: str) -> Optional[List[str]]:
        """
        从推理模型响应中提取分类结果
        """
        content = self.get_message_content(response_data)
        if not content:
            return None
        
        # 检查是否包含推理标记
        reasoning_markers = ['分析', '评估', '比对', '确定', '选择', '执行', 
                          '自我检查', '步骤', '考虑', '计划', '核心']
        has_reasoning = any(marker in content for marker in reasoning_markers)
        
        if not has_reasoning:
            # 没有推理标记，使用标准解析
            return self._parse_simple_classification(content, available_categories, default_category)
        
        # 包含推理标记，需要从推理过程中提取
        return self._extract_from_reasoning(content, available_categories, default_category)
    
    def extract_summary(self, response_data: Dict[str, Any]) -> Optional[str]:
        """
        从推理模型响应中提取摘要结果
        """
        content = self.get_message_content(response_data)
        if not content:
            return None
        
        # 检查是否包含推理标记
        reasoning_markers = ['分析', '评估', '比对', '确定', '选择', '执行', 
                          '自我检查', '步骤', '考虑', '计划']
        has_reasoning = any(marker in content for marker in reasoning_markers)
        
        if not has_reasoning:
            # 没有推理标记，直接返回
            return content
        
        # 包含推理标记，需要提取真正的摘要
        return self._extract_summary_from_reasoning(content)
    
    def supports_reasoning(self) -> bool:
        """
        推理模型支持推理模式
        """
        return True
    
    def _parse_simple_classification(self, content: str, 
                                   available_categories: List[str],
                                   default_category: str) -> Optional[List[str]]:
        """
        解析简单的分类结果
        """
        try:
            content = content.strip()
            
            if not content:
                return None
            
            # 尝试多种分隔符
            categories = []
            for separator in [',', '，', '、']:
                if separator in content:
                    parts = content.split(separator)
                    for part in parts:
                        part = part.strip()
                        if part == '未分类':
                            continue
                        if part in available_categories:
                            categories.append(part)
                        elif part == default_category:
                            categories.append(part)
                    if categories:
                        break
            
            # 如果没有找到，尝试直接匹配
            if not categories:
                for cat in available_categories:
                    if cat in content and len(content) < 100:
                        categories.append(cat)
                if default_category in content and len(content) < 100:
                    categories.append(default_category)
            
            if categories:
                categories = list(set(categories))
                if len(categories) > 2:
                    categories = categories[:2]
                return categories
            
            return None
            
        except Exception as e:
            logger.error(f"解析简单分类失败: {e}")
            return None
    
    def _extract_from_reasoning(self, reasoning: str, 
                              available_categories: List[str],
                              default_category: str) -> Optional[List[str]]:
        """
        从推理过程中提取分类
        """
        lines = reasoning.split('\n')
        
        # 查找"确定"或"选择"相关的行
        for i, line in enumerate(lines):
            line = line.strip()
            
            if any(keyword in line for keyword in ['确定', '选择', '最终', '结论', '主分类']):
                for j in range(i, min(i + 5, len(lines))):
                    check_line = lines[j].strip()
                    
                    found_cats = []
                    for cat in available_categories:
                        if cat in check_line:
                            found_cats.append(cat)
                    if default_category in check_line:
                        found_cats.append(default_category)
                    
                    if found_cats and len(check_line) < 200:
                        logger.debug(f"从推理过程中找到分类行: {check_line}")
                        result = list(set(found_cats))
                        if len(result) > 2:
                            result = result[:2]
                        return result
        
        # 评分法
        category_scores = {cat: 0 for cat in available_categories}
        category_scores[default_category] = 0
        
        for line in lines:
            line = line.strip()
            
            if any(marker in line for marker in ['分析', '评估', '比对', '步骤', '考虑']):
                continue
            
            for cat in available_categories:
                if cat in line:
                    if any(keyword in line for keyword in ['选择', '确定', '最终', '结论']):
                        category_scores[cat] += 3
                    else:
                        category_scores[cat] += 1
            
            if default_category in line:
                if any(keyword in line for keyword in ['选择', '确定', '最终', '结论']):
                    category_scores[default_category] += 3
                else:
                    category_scores[default_category] += 1
        
        max_score = max(category_scores.values())
        if max_score > 0:
            result_cats = [cat for cat, score in category_scores.items() if score == max_score]
            logger.debug(f"从推理过程中提取到分类（评分法）: {result_cats}")
            if len(result_cats) > 2:
                result_cats = result_cats[:2]
            return result_cats
        
        return None
    
    def _extract_summary_from_reasoning(self, reasoning: str) -> Optional[str]:
        """
        从推理过程中提取摘要
        """
        reasoning_markers = ['步骤', '分析', '评估', '比对', '确定', '选择', 
                          '执行', '自我检查', '考虑', '计划']
        
        lines = reasoning.split('\n')
        
        # 查找包含emoji的行（点评部分）
        emoji_line_index = -1
        for i, line in enumerate(lines):
            if any(emoji in line for emoji in ['💥', '✨', '🎉', '🚀', '💡', '📊', 
                                              '🔥', '⚡', '🌟', '💪', '🤔', '💰']):
                emoji_line_index = i
                logger.debug(f"找到emoji点评行（第{i}行）")
                break
        
        if emoji_line_index >= 0:
            summary_lines = []
            for line in lines[emoji_line_index + 1:]:
                line = line.strip()
                if not line:
                    continue
                
                if any(marker in line for marker in reasoning_markers):
                    continue
                
                if line.startswith('**') and line.endswith('**'):
                    continue
                
                summary_lines.append(line)
                
                if len('\n'.join(summary_lines)) > 500:
                    break
            
            if summary_lines:
                summary = '\n'.join(summary_lines)
                logger.info(f"成功从content中提取到摘要（排除推理过程）")
                return summary
        
        # 从最后部分提取
        summary_lines = []
        for line in reversed(lines[-30:]):
            line = line.strip()
            if not line:
                continue
            
            if any(marker in line for marker in reasoning_markers):
                continue
            
            if line.startswith('**') and line.endswith('**'):
                continue
            
            summary_lines.insert(0, line)
        
        if summary_lines:
            summary = '\n'.join(summary_lines)
            logger.info(f"从content最后部分提取到摘要")
            return summary
        
        logger.warning("无法从content中提取摘要，返回原始内容")
        return reasoning


class ModelAdapterFactory:
    """
    模型适配器工厂
    
    根据模型名称创建合适的适配器
    """
    
    @classmethod
    def create_adapter(cls, model_name: str) -> ModelAdapter:
        """
        根据模型名称创建适配器
        
        Args:
            model_name: 模型名称
            
        Returns:
            合适的模型适配器
        """
        # 使用配置文件中的判断逻辑
        if is_reasoning_model(model_name):
            logger.info(f"为模型 '{model_name}' 创建推理模型适配器")
            return ReasoningModelAdapter(model_name)
        else:
            logger.info(f"为模型 '{model_name}' 创建标准模型适配器")
            return StandardModelAdapter(model_name)
    
    @classmethod
    def register_reasoning_model(cls, model_pattern: str):
        """
        注册推理模型模式
        
        Args:
            model_pattern: 模型名称模式（支持部分匹配）
        """
        from ai.model_config import register_model
        register_model(model_pattern, {
            'supports_reasoning': True,
            'response_format': 'mixed',
            'max_context': 8192,
            'preferred_temperature': 0.7,
            'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
        }, 'reasoning')
        logger.info(f"已注册推理模型模式: {model_pattern}")
    
    @classmethod
    def register_standard_model(cls, model_pattern: str):
        """
        注册标准模型模式
        
        Args:
            model_pattern: 模型名称模式（支持部分匹配）
        """
        from ai.model_config import register_model
        register_model(model_pattern, {
            'supports_reasoning': False,
            'response_format': 'standard',
            'max_context': 8192,
            'preferred_temperature': 0.7,
        }, 'standard')
        logger.info(f"已注册标准模型模式: {model_pattern}")