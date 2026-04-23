from typing import List, Optional, Dict, Any
from utils.logger import logger
from utils.helpers import config, get_category_names, get_default_category, ConfigObserver
from ai.ai_client import ai_client, AIRequest


class AIClassifier(ConfigObserver):
    def __init__(self) -> None:
        self.categories: List[str] = get_category_names()
        self.categories_config: List[Dict[str, Any]] = config.get('categories', [])
        self.default_category: str = get_default_category()
        
        self.max_input_length: int = config.get('ai.max_input_length', 800)
        
        # 获取用户信息（国籍和宗教）
        self.user_info = self._get_user_info()
        
        # 注册为配置观察者
        config.add_observer(self)

    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置更新回调
        
        Args:
            config: 更新后的配置字典
        """
        logger.info("AIClassifier配置已更新")
        
        # 更新分类信息
        self.categories = get_category_names()
        self.categories_config = config.get('categories', [])
        self.default_category = get_default_category()
        self.max_input_length = config.get('ai.max_input_length', 800)
        
        # 更新用户信息
        self.user_info = self._get_user_info()

    def classify(self, title: str, description: str, 
                 source_category: str = None) -> Optional[Dict[str, Any]]:
        """
        AI分类
        
        Args:
            title: 新闻标题
            description: 新闻描述
            source_category: 源分类（可选）
            
        Returns:
            包含分类和关键字的字典，格式：{'categories': [...], 'keywords': [...]}
        """
        try:
            # AI分类始终可以执行（不受配置控制）
            # 配置只影响自动执行，不影响手动调用
            
            # 限制输入长度
            truncated_title = title[:200] if title else ''
            truncated_description = description[:self.max_input_length] if description else ''
            
            logger.debug(f"AI分类输入: title={truncated_title[:50]}..., description_length={len(truncated_description)}")
            
            # 构建提示词
            prompt = self._build_classify_prompt(truncated_title, truncated_description)
            
            # 构建系统提示词
            system_prompt = "你是一个专业的新闻分类助手，负责准确识别新闻的分类和提取关键字。"
            
            # 构建响应Schema
            response_schema = {
                "type": "object",
                "properties": {
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "新闻分类列表，最多2个"
                    },
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "关键词列表，最多10个"
                    }
                },
                "required": ["categories", "keywords"]
            }
            
            # 创建AI请求
            request = AIRequest(
                task_type='classification',
                prompt=prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                max_input_length=self.max_input_length
            )
            
            logger.debug("开始AI分类")
            
            # 调用AI客户端
            response = ai_client.call(request)
            
            if not response.success:
                logger.error(f"AI分类失败: {response.error}")
                return None
            
            # 获取响应数据
            data = response.data
            categories = data.get('categories', [])
            keywords = data.get('keywords', [])
            
            # 验证分类是否在允许的列表中
            validation_result = ai_client.validator.validate_categories(
                categories,
                self.categories
            )
            
            if not validation_result['valid']:
                logger.warning(f"分类验证失败: {validation_result['error']}")
                # 根据关键字命中情况选取分类
                if keywords:
                    categories = self._classify_by_keywords(keywords)
                    logger.info(f"使用关键字命中情况选取分类: {categories}")
                else:
                    # 使用默认分类
                    categories = [self.default_category]
                    logger.info(f"使用默认分类: {categories}")
            
            # 如果AI没有返回分类，则根据关键字命中情况选取1-2个标签
            if not categories and keywords:
                categories = self._classify_by_keywords(keywords)
                logger.info(f"AI未返回分类，根据关键字命中情况选取分类: {categories}")
            
            logger.info(f"AI分类完成: {categories}, 关键字: {keywords}, 重试次数: {response.retry_count}")
            return {
                'categories': categories,
                'keywords': keywords
            }
            
        except Exception as e:
            logger.error(f"AI分类失败: {e}")
            return None

    def _classify_by_keywords(self, keywords: List[str]) -> List[str]:
        """
        根据关键字命中情况选取1-2个分类
        
        Args:
            keywords: AI提取的关键字列表
            
        Returns:
            分类列表
        """
        if not keywords:
            logger.warning("关键字列表为空，返回默认分类")
            return [self.default_category]
        
        logger.debug(f"根据关键字分类: keywords={keywords}")
        
        # 统计每个分类的关键字命中次数
        category_scores = {}
        
        for cat_config in self.categories_config:
            category_name = cat_config.get('name', '')
            category_keywords = cat_config.get('keywords', [])
            
            if not category_keywords:
                continue
            
            score = 0
            for keyword in keywords:
                for cat_keyword in category_keywords:
                    if keyword.lower() in cat_keyword.lower() or cat_keyword.lower() in keyword.lower():
                        score += 1
                        break
            
            if score > 0:
                category_scores[category_name] = score
                logger.debug(f"分类 {category_name} 命中 {score} 次")
        
        # 按命中次数排序
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选取前1-2个分类
        if sorted_categories:
            result = [sorted_categories[0][0]]
            if len(sorted_categories) > 1 and sorted_categories[1][1] > 0:
                result.append(sorted_categories[1][0])
            logger.info(f"根据关键字命中情况选取分类: {result}, 命中次数: {sorted_categories[:2]}")
            return result
        
        # 如果没有命中任何分类，返回默认分类
        logger.warning("没有命中任何分类，返回默认分类")
        return [self.default_category]

    def _build_classify_prompt(self, title: str, description: str) -> str:
        """
        构建分类提示词
        
        Args:
            title: 新闻标题
            description: 新闻描述
            
        Returns:
            提示词
        """
        categories_str = '、'.join(self.categories)
        
        # 从配置中读取分类描述（不包含关键字）
        category_descriptions = []
        for cat_config in self.categories_config:
            name = cat_config.get('name', '')
            cat_description = cat_config.get('description', '')
            
            if cat_description:
                category_descriptions.append(f"- {name}：{cat_description}")
        
        category_desc_str = '\n'.join(category_descriptions)
        
        # 从配置中读取提示词模板
        prompt_template = config.get('ai_category_prompt', '')
        
        # 处理description为空的情况
        desc_text = description[:500] if description else '（无描述）'
        
        if prompt_template:
            # 使用配置的提示词模板
            return prompt_template.format(
                categories=categories_str,
                category_descriptions=category_desc_str,
                title=title,
                description=desc_text
            )
        else:
            # 使用默认提示词
            return f"""请根据以下新闻的标题和描述，判断它属于哪个分类，并提取10个关键字。

可用分类：
{categories_str}

分类说明（请仔细阅读以下每个分类的详细描述）：
{category_desc_str}

标题：{title}

描述：{desc_text}

用户信息：
- 国籍：{self.user_info.get('nationality', '未知')}
- 宗教：{self.user_info.get('religion', '未知')}

要求：
1. **首先仔细阅读上述"分类说明"中每个分类的详细描述，理解每个分类的适用范围**
2. **特别注意：在判断"国内民生"和"国际政治"分类时，必须考虑用户的国籍信息**
   - 如果用户国籍是"中国"，则涉及中国的事件应归类为"国内民生"
   - 如果用户国籍是"中国"，则涉及其他国家的事件应归类为"国际政治"
   - 如果用户国籍是"中国"，则涉及德国、美国等外国的事件应归类为"国际政治"，而不是"国内民生"
   - 如果新闻涉及多个国家，但主要涉及用户所在国家，应优先考虑"国内民生"
3. **特别注意：在判断涉及宗教内容的分类时，必须考虑用户的宗教信仰**
   - 如果用户宗教是"无"，则宗教相关内容应归类为"教育文化"或"国际政治"
   - 如果用户有特定宗教信仰，则涉及该宗教的内容应考虑归类到相关分类
4. 根据新闻的核心内容，选择最相关的1-2个分类
5. 如果新闻主要涉及一个分类，只返回一个分类
6. 如果新闻确实涉及多个分类，最多返回2个分类，用逗号分隔
7. 不要为了保险而选择多个分类，只选择真正相关的
8. **重要：必须从以下分类中选择一个：{categories_str}**
9. **不要返回"未分类"，即使新闻看起来不相关，也要选择最接近的分类**
10. 提取10个与新闻内容相关的关键字
11. 关键字应该简洁、准确，能够体现新闻的核心内容
12. 关键字可以是名词、动词、形容词等，但要确保与新闻内容相关"""
    
    def _get_user_info(self) -> Dict[str, str]:
        """
        获取用户信息
        
        Returns:
            用户信息字典，包含国籍和宗教信仰
        """
        try:
            scoring_config = config.get('ai.scoring', {})
            return {
                'nationality': scoring_config.get('user_nationality', '未知'),
                'religion': scoring_config.get('user_religion', '未知')
            }
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return {}


ai_classifier = AIClassifier()