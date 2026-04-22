"""
AI评分器 - 对新闻进行多维度评分
"""
from typing import Dict, Any, List, Optional
from utils.logger import logger
from utils.helpers import config, ConfigObserver
from ai.ai_client import ai_client, AIRequest


class AIScorer(ConfigObserver):
    """AI评分器"""
    
    def __init__(self) -> None:
        self.timeout: int = config.get('ai.timeout', 120)
        
        # 评分配置
        self.enable_scoring: bool = config.get('ai.scoring.enable_scoring', False)
        self.importance_description: str = config.get('ai.scoring.importance_description', '')
        
        # 评分维度权重
        self.topic_relevance_weight: float = config.get('ai.scoring.topic_relevance_weight', 0.4)
        self.importance_weight: float = config.get('ai.scoring.importance_weight', 0.4)
        self.source_weight: float = config.get('ai.scoring.source_weight', 0.2)
        
        # 注册为配置观察者
        config.add_observer(self)
    
    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置更新回调
        
        Args:
            config: 更新后的配置字典
        """
        logger.info("AIScorer配置已更新")
        ai_config = config.get('ai', {})
        self.timeout = ai_config.get('timeout', 120)
        
        # 更新评分配置
        scoring_config = ai_config.get('scoring', {})
        self.enable_scoring = scoring_config.get('enable_scoring', False)
        self.importance_description = scoring_config.get('importance_description', '')
        self.topic_relevance_weight = scoring_config.get('topic_relevance_weight', 0.4)
        self.importance_weight = scoring_config.get('importance_weight', 0.4)
        self.source_weight = scoring_config.get('source_weight', 0.2)
    
    def score_news(self, news_data: Dict[str, Any], manual: bool = False) -> Optional[Dict[str, float]]:
        """
        对新闻进行综合评分
        
        Args:
            news_data: 新闻数据字典
            manual: 是否手动触发（手动触发时始终评分）
            
        Returns:
            评分字典，包含总分和3个维度的分数，如果评分未启用且非手动触发则返回None
        """
        if not self.enable_scoring and not manual:
            logger.info("AI评分未启用，跳过评分")
            return None
        
        try:
            # 计算各维度评分
            relevance = self._calculate_relevance(news_data)
            importance = self._calculate_importance(news_data)
            source_score = self._calculate_source_score(news_data)
            
            # 综合评分
            total_score = (
                relevance * self.topic_relevance_weight +
                importance * self.importance_weight +
                source_score * self.source_weight
            )
            
            # 限制在0-100范围内
            total_score = max(0, min(100, total_score))
            
            logger.info(
                f"新闻评分: ID={news_data.get('id')}, "
                f"关联度={relevance:.2f}, "
                f"重要程度={importance:.2f}, "
                f"来源分={source_score:.2f}, "
                f"总分={total_score:.2f}"
            )
            
            return {
                'total_score': total_score,
                'topic_relevance': relevance,  # 保持字段名兼容性
                'importance': importance,
                'source_score': source_score
            }
            
        except Exception as e:
            logger.error(f"新闻评分失败: ID={news_data.get('id')}, error={e}")
            return None
    
    def _calculate_relevance(self, news_data: Dict[str, Any]) -> float:
        """
        计算关联度评分（0-100）- AI判断
        
        Args:
            news_data: 新闻数据
            
        Returns:
            关联度评分
        """
        try:
            title = news_data.get('title', '')
            summary = news_data.get('ai_summary', '')
            category = news_data.get('category', '')
            
            # 获取用户兴趣分类
            interest_categories = self._get_interest_categories()
            
            if not interest_categories:
                return 50.0  # 如果没有配置兴趣分类，给中等分数
            
            # 构建提示词
            prompt = self._build_relevance_prompt(title, summary, category, interest_categories)
            
            # 构建系统提示词
            system_prompt = "你是一个专业的新闻分析师，擅长判断新闻与用户兴趣的关联程度。"
            
            # 构建响应Schema
            response_schema = {
                "type": "object",
                "properties": {
                    "relevance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "关联度评分"
                    },
                    "reason": {
                        "type": "string",
                        "description": "评分理由"
                    }
                },
                "required": ["relevance", "reason"]
            }
            
            # 创建AI请求
            request = AIRequest(
                task_type='scoring',
                prompt=prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                timeout=self.timeout
            )
            
            # 调用AI客户端
            response = ai_client.call(request)
            
            if not response.success:
                logger.error(f"AI关联度评分失败: {response.error}")
                return 50.0
            
            # 获取响应数据
            data = response.data
            relevance = data.get('relevance', 50.0)
            
            # 限制在0-100范围内
            relevance = max(0, min(100, relevance))
            
            logger.debug(f"AI关联度评分: {relevance:.2f}, 理由: {data.get('reason', '')}, 重试次数: {response.retry_count}")
            return relevance
            
        except Exception as e:
            logger.error(f"计算关联度失败: {e}")
            return 50.0
    
    def _build_relevance_prompt(self, title: str, summary: str, category: str, interest_categories: List[str]) -> str:
        """
        构建关联度评分提示词
        
        Args:
            title: 新闻标题
            summary: 新闻摘要
            category: 新闻分类
            interest_categories: 用户兴趣分类列表
            
        Returns:
            提示词
        """
        categories_str = '、'.join(interest_categories)
        
        return f"""请根据以下标准，判断这条新闻与用户兴趣的关联程度，给出0-100的数字评分。

用户感兴趣的分类：{categories_str}

新闻标题：{title}
新闻摘要：{summary}
新闻分类：{category}

评分标准：
- 90-100分：新闻分类与用户兴趣分类高度匹配，内容与用户兴趣高度相关
- 70-90分：新闻分类与用户兴趣分类部分匹配，内容与用户兴趣相关
- 60-70分：新闻分类与用户兴趣分类有一定关联，内容与用户兴趣有一定关系
- 40-60分：新闻分类与用户兴趣分类关联较弱，内容与用户兴趣关系不大
- 0-40分：新闻分类与用户兴趣分类不匹配，内容与用户兴趣无关

请同时提供评分理由，说明为什么给出这个分数。

请返回JSON格式，包含relevance（关联度评分）和reason（评分理由）两个字段。"""
    
    def _calculate_importance(self, news_data: Dict[str, Any]) -> float:
        """
        计算重要程度评分（0-100）- AI判断
        
        Args:
            news_data: 新闻数据
            
        Returns:
            重要程度评分
        """
        try:
            title = news_data.get('title', '')
            summary = news_data.get('ai_summary', '')
            
            if not self.importance_description:
                return 50.0  # 如果没有配置重要性描述，给中等分数
            
            # 构建提示词
            prompt = self._build_importance_prompt(title, summary)
            
            # 构建系统提示词
            system_prompt = "你是一个专业的新闻分析师，擅长判断新闻的重要程度。"
            
            # 构建响应Schema
            response_schema = {
                "type": "object",
                "properties": {
                    "importance": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "重要程度评分"
                    },
                    "reason": {
                        "type": "string",
                        "description": "评分理由"
                    }
                },
                "required": ["importance", "reason"]
            }
            
            # 创建AI请求
            request = AIRequest(
                task_type='scoring',
                prompt=prompt,
                system_prompt=system_prompt,
                response_schema=response_schema,
                timeout=self.timeout
            )
            
            # 调用AI客户端
            response = ai_client.call(request)
            
            if not response.success:
                logger.error(f"AI重要程度评分失败: {response.error}")
                return 50.0
            
            # 获取响应数据
            data = response.data
            importance = data.get('importance', 50.0)
            
            # 限制在0-100范围内
            importance = max(0, min(100, importance))
            
            logger.debug(f"AI重要程度评分: {importance:.2f}, 理由: {data.get('reason', '')}, 重试次数: {response.retry_count}")
            return importance
            
        except Exception as e:
            logger.error(f"计算重要程度失败: {e}")
            return 50.0
    
    def _build_importance_prompt(self, title: str, summary: str) -> str:
        """
        构建重要程度评分提示词
        
        Args:
            title: 新闻标题
            summary: 新闻摘要
            
        Returns:
            提示词
        """
        # 获取用户信息
        user_info = self._get_user_info()
        
        return f"""请根据以下标准，判断这条新闻的重要程度，给出0-100的数字评分。

用户信息：
- 国籍：{user_info.get('nationality', '未知')}
- 宗教：{user_info.get('religion', '未知')}

{self.importance_description}

新闻标题：{title}
新闻摘要：{summary}

评分标准：
- 90-100分：全球性重大事件，影响范围极广，涉及人数众多，长期影响深远
- 80-90分：国家级重大事件，影响范围广，涉及人数多，中期影响明显
- 70-80分：地区性重要事件，影响范围中等，涉及人数较多，有一定影响
- 60-70分：局部重要事件，影响范围有限，涉及人数一般，影响较小
- 0-60分：一般新闻，影响范围小，涉及人数少，影响有限

请同时提供评分理由，说明为什么给出这个分数。

请返回JSON格式，包含importance（重要程度评分）和reason（评分理由）两个字段。"""
    
    def _calculate_source_score(self, news_data: Dict[str, Any]) -> float:
        """
        计算来源分（0-100）- 从配置读取
        
        Args:
            news_data: 新闻数据
            
        Returns:
            来源分
        """
        try:
            source = news_data.get('source', '')
            
            if not source:
                return 50.0  # 如果没有来源信息，给中等分数
            
            # 从新闻源配置中读取来源分
            source_score = self._get_source_score_from_config(source)
            
            if source_score is None:
                return 100.0  # 如果没有配置来源分，默认100分
            
            logger.debug(f"来源分: source={source}, score={source_score}")
            return source_score
            
        except Exception as e:
            logger.error(f"计算来源分失败: {e}")
            return 50.0
    
    def _get_source_score_from_config(self, source: str) -> Optional[float]:
        """
        从配置中获取来源分
        
        Args:
            source: 来源名称
            
        Returns:
            来源分，如果未配置则返回None
        """
        try:
            # 搜索RSS源
            rss_sources = config.get('news_sources.rss', [])
            for rss_source in rss_sources:
                if rss_source.get('name') == source:
                    return rss_source.get('score', 100.0)
            
            # 搜索API源
            api_sources = config.get('news_sources.api', [])
            for api_source in api_sources:
                if api_source.get('name') == source:
                    return api_source.get('score', 100.0)
            
            # 搜索Web源
            web_sources = config.get('news_sources.web', [])
            for web_source in web_sources:
                if web_source.get('name') == source:
                    return web_source.get('score', 100.0)
            
            return None
            
        except Exception as e:
            logger.error(f"获取来源分配置失败: {e}")
            return None
    
    def _get_interest_categories(self) -> List[str]:
        """
        获取用户兴趣分类列表
        
        Returns:
            用户兴趣分类列表
        """
        try:
            categories_config = config.get('categories', [])
            return [cat.get('name', '') for cat in categories_config]
        except Exception as e:
            logger.error(f"获取兴趣分类失败: {e}")
            return []
    
    def _get_user_info(self) -> Dict[str, str]:
        """
        获取用户信息
        
        Returns:
            用户信息字典
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


ai_scorer = AIScorer()