"""
响应验证器
提供双层验证机制：格式验证和内容验证
"""
from typing import Dict, Any, Optional, List
from utils.logger import logger


class ResponseValidator:
    """响应验证器"""
    
    def __init__(self):
        """初始化验证器"""
        self.validation_errors = []
    
    def validate(
        self,
        data: Any,
        task_type: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        验证响应数据
        
        Args:
            data: 响应数据
            task_type: 任务类型
            schema: 自定义Schema（可选）
            
        Returns:
            验证结果字典，包含valid和error字段
        """
        self.validation_errors = []
        
        try:
            # 如果提供了自定义Schema，使用自定义验证
            if schema:
                if not self._validate_with_schema(data, schema):
                    return {
                        'valid': False,
                        'error': f"格式验证失败: {', '.join(self.validation_errors)}"
                    }
            else:
                # 第一层：格式验证
                if not self._validate_format(data, task_type):
                    return {
                        'valid': False,
                        'error': f"格式验证失败: {', '.join(self.validation_errors)}"
                    }
                
                # 第二层：内容验证
                if not self._validate_content(data, task_type, schema):
                    return {
                        'valid': False,
                        'error': f"内容验证失败: {', '.join(self.validation_errors)}"
                    }
            
            # 验证通过
            logger.debug(f"响应验证通过: task_type={task_type}")
            return {
                'valid': True,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"响应验证异常: {e}")
            return {
                'valid': False,
                'error': f"验证异常: {str(e)}"
            }
    
    def _validate_format(self, data: Any, task_type: str) -> bool:
        """
        格式验证
        
        Args:
            data: 响应数据
            task_type: 任务类型
            
        Returns:
            是否通过格式验证
        """
        # 检查数据是否为字典
        if not isinstance(data, dict):
            self.validation_errors.append(f"响应数据必须是字典类型，实际类型: {type(data)}")
            return False
        
        # 根据任务类型验证格式
        validators = {
            'classification': self._validate_classification_format,
            'summary': self._validate_summary_format,
            'scoring': self._validate_scoring_format
        }
        
        validator = validators.get(task_type)
        if validator:
            return validator(data)
        else:
            logger.warning(f"未知的任务类型: {task_type}，跳过格式验证")
            return True
    
    def _validate_content(
        self,
        data: Dict[str, Any],
        task_type: str,
        schema: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        内容验证
        
        Args:
            data: 响应数据
            task_type: 任务类型
            schema: 自定义Schema
            
        Returns:
            是否通过内容验证
        """
        # 如果提供了自定义Schema，使用自定义验证
        if schema:
            return self._validate_with_schema(data, schema)
        
        # 根据任务类型验证内容
        validators = {
            'classification': self._validate_classification_content,
            'summary': self._validate_summary_content,
            'scoring': self._validate_scoring_content
        }
        
        validator = validators.get(task_type)
        if validator:
            return validator(data)
        else:
            logger.warning(f"未知的任务类型: {task_type}，跳过内容验证")
            return True
    
    def _validate_classification_format(self, data: Dict[str, Any]) -> bool:
        """
        验证分类任务格式
        
        Args:
            data: 响应数据
            
        Returns:
            是否通过格式验证
        """
        # 检查必需字段
        required_fields = ['categories', 'keywords']
        for field in required_fields:
            if field not in data:
                self.validation_errors.append(f"缺少必需字段: {field}")
                return False
        
        # 检查字段类型
        if not isinstance(data['categories'], list):
            self.validation_errors.append(f"categories字段必须是列表类型")
            return False
        
        if not isinstance(data['keywords'], list):
            self.validation_errors.append(f"keywords字段必须是列表类型")
            return False
        
        return True
    
    def _validate_classification_content(self, data: Dict[str, Any]) -> bool:
        """
        验证分类任务内容
        
        Args:
            data: 响应数据
            
        Returns:
            是否通过内容验证
        """
        categories = data.get('categories', [])
        keywords = data.get('keywords', [])
        
        # 验证分类数量
        if len(categories) > 2:
            self.validation_errors.append(f"分类数量不能超过2个，实际数量: {len(categories)}")
            return False
        
        # 验证分类不为空
        if len(categories) == 0:
            self.validation_errors.append("分类列表不能为空")
            return False
        
        # 验证分类不为空字符串
        for i, category in enumerate(categories):
            if not isinstance(category, str) or not category.strip():
                self.validation_errors.append(f"分类[{i}]不能为空")
                return False
        
        # 验证关键字数量
        if len(keywords) > 10:
            self.validation_errors.append(f"关键字数量不能超过10个，实际数量: {len(keywords)}")
            return False
        
        # 验证关键字不为空字符串
        for i, keyword in enumerate(keywords):
            if not isinstance(keyword, str) or not keyword.strip():
                self.validation_errors.append(f"关键字[{i}]不能为空")
                return False
        
        return True
    
    def _validate_summary_format(self, data: Dict[str, Any]) -> bool:
        """
        验证摘要任务格式
        
        Args:
            data: 响应数据
            
        Returns:
            是否通过格式验证
        """
        # 检查必需字段
        required_fields = ['comment', 'summary']
        for field in required_fields:
            if field not in data:
                self.validation_errors.append(f"缺少必需字段: {field}")
                return False
        
        # 检查字段类型
        if not isinstance(data['comment'], str):
            self.validation_errors.append(f"comment字段必须是字符串类型")
            return False
        
        if not isinstance(data['summary'], str):
            self.validation_errors.append(f"summary字段必须是字符串类型")
            return False
        
        return True
    
    def _validate_summary_content(self, data: Dict[str, Any]) -> bool:
        """
        验证摘要任务内容
        
        Args:
            data: 响应数据
            
        Returns:
            是否通过内容验证
        """
        comment = data.get('comment', '')
        summary = data.get('summary', '')
        
        # 验证评价不为空
        if not comment.strip():
            self.validation_errors.append("评价不能为空")
            return False
        
        # 验证摘要不为空
        if not summary.strip():
            self.validation_errors.append("摘要不能为空")
            return False
        
        # 验证评价包含emoji（先检查emoji，再检查长度）
        emoji_pattern = r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF]'
        import re
        if not re.search(emoji_pattern, comment):
            self.validation_errors.append("评价应包含emoji表情")
            return False
        
        # 验证评价长度
        if len(comment) > 100:
            self.validation_errors.append(f"评价长度不能超过100字，实际长度: {len(comment)}")
            return False
        
        # 验证摘要长度（120-160字）
        summary_len = len(summary)
        if summary_len < 120 or summary_len > 160:
            self.validation_errors.append(f"摘要长度应在120-160字之间，实际长度: {summary_len}")
            return False
        
        return True
    
    def _validate_scoring_format(self, data: Dict[str, Any]) -> bool:
        """
        验证评分任务格式
        
        Args:
            data: 响应数据
            
        Returns:
            是否通过格式验证
        """
        # 检查必需字段
        required_fields = ['relevance', 'importance', 'source_score']
        for field in required_fields:
            if field not in data:
                self.validation_errors.append(f"缺少必需字段: {field}")
                return False
        
        # 检查字段类型
        for field in required_fields:
            if not isinstance(data[field], (int, float)):
                self.validation_errors.append(f"{field}字段必须是数字类型")
                return False
        
        return True
    
    def _validate_scoring_content(self, data: Dict[str, Any]) -> bool:
        """
        验证评分任务内容
        
        Args:
            data: 响应数据
            
        Returns:
            是否通过内容验证
        """
        # 验证relevance范围（0-100）
        relevance = data.get('relevance', 0)
        if not (0 <= relevance <= 100):
            self.validation_errors.append(f"relevance必须在0-100范围内，实际值: {relevance}")
            return False
        
        # 验证importance范围（0-100）
        importance = data.get('importance', 0)
        if not (0 <= importance <= 100):
            self.validation_errors.append(f"importance必须在0-100范围内，实际值: {importance}")
            return False
        
        # 验证source_score范围（0-100）
        source_score = data.get('source_score', 0)
        if not (0 <= source_score <= 100):
            self.validation_errors.append(f"source_score必须在0-100范围内，实际值: {source_score}")
            return False
        
        return True
    
    def _validate_with_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        使用自定义Schema验证
        
        Args:
            data: 响应数据
            schema: 自定义Schema
            
        Returns:
            是否通过验证
        """
        # 检查必需字段
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                self.validation_errors.append(f"缺少必需字段: {field}")
                return False
        
        # 检查字段类型和约束
        properties = schema.get('properties', {})
        for field_name, field_schema in properties.items():
            if field_name not in data:
                continue
            
            field_value = data[field_name]
            field_type = field_schema.get('type')
            
            # 验证类型
            if field_type == 'string':
                if not isinstance(field_value, str):
                    self.validation_errors.append(f"{field_name}字段必须是字符串类型")
                    return False
            elif field_type == 'number':
                if not isinstance(field_value, (int, float)):
                    self.validation_errors.append(f"{field_name}字段必须是数字类型")
                    return False
            elif field_type == 'array':
                if not isinstance(field_value, list):
                    self.validation_errors.append(f"{field_name}字段必须是数组类型")
                    return False
            elif field_type == 'object':
                if not isinstance(field_value, dict):
                    self.validation_errors.append(f"{field_name}字段必须是对象类型")
                    return False
            
            # 验证最小值
            if 'minimum' in field_schema:
                minimum = field_schema['minimum']
                if field_value < minimum:
                    self.validation_errors.append(f"{field_name}必须大于等于{minimum}，实际值: {field_value}")
                    return False
            
            # 验证最大值
            if 'maximum' in field_schema:
                maximum = field_schema['maximum']
                if field_value > maximum:
                    self.validation_errors.append(f"{field_name}必须小于等于{maximum}，实际值: {field_value}")
                    return False
            
            # 验证数组元素类型
            if field_type == 'array' and 'items' in field_schema:
                item_type = field_schema['items'].get('type')
                if item_type == 'string':
                    for i, item in enumerate(field_value):
                        if not isinstance(item, str):
                            self.validation_errors.append(f"{field_name}[{i}]必须是字符串类型")
                            return False
        
        return True
    
    def validate_categories(
        self,
        categories: List[str],
        available_categories: List[str]
    ) -> Dict[str, Any]:
        """
        验证分类是否在允许的列表中
        
        Args:
            categories: 分类列表
            available_categories: 允许的分类列表
            
        Returns:
            验证结果字典
        """
        invalid_categories = []
        for category in categories:
            if category not in available_categories:
                invalid_categories.append(category)
        
        if invalid_categories:
            return {
                'valid': False,
                'error': f"无效的分类: {', '.join(invalid_categories)}"
            }
        
        return {
            'valid': True,
            'error': None
        }