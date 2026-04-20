"""
AI评分器 - 对新闻进行多维度评分
"""
import requests
from typing import Dict, Any, List, Optional
from utils.logger import logger
from utils.helpers import config, ConfigObserver


class AIScorer(ConfigObserver):
    """AI评分器"""
    
    def __init__(self) -> None:
        self.base_url: str = config.get('ai.base_url', 'http://localhost:1234')
        self.model: str = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
        self.api_key: str = config.get('ai.api_key', '')
        self.max_tokens: int = config.get('ai.max_tokens', 4096)
        self.temperature: float = config.get('ai.temperature', 0.7)
        self.timeout: int = config.get('ai.timeout', 120)
        
        # 评分配置
        self.enable_scoring: bool = config.get('ai.scoring.enable_scoring', False)
        self.importance_description: str = config.get('ai.scoring.importance_description', '')
        self.interest_keywords: List[str] = config.get('ai.scoring.interest_keywords', [])
        self.trusted_sources: List[str] = config.get('ai.scoring.trusted_sources', [])
        
        # 评分维度权重
        self.topic_relevance_weight: float = config.get('ai.scoring.topic_relevance_weight', 0.4)
        self.importance_weight: float = config.get('ai.scoring.importance_weight', 0.3)
        self.ai_feeling_weight: float = config.get('ai.scoring.ai_feeling_weight', 0.2)
        self.source_weight: float = config.get('ai.scoring.source_weight', 0.1)
        
        # AI感官分配置
        self.ai_feeling_description: str = config.get('ai.scoring.ai_feeling_description', '')
        
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
        self.base_url = ai_config.get('base_url', 'http://localhost:1234')
        self.model = ai_config.get('model', 'nvidia/nemotron-3-nano-4b')
        self.api_key = ai_config.get('api_key', '')
        self.max_tokens = ai_config.get('max_tokens', 4096)
        self.temperature = ai_config.get('temperature', 0.7)
        self.timeout = ai_config.get('timeout', 120)
        
        # 更新评分配置
        scoring_config = ai_config.get('scoring', {})
        self.enable_scoring = scoring_config.get('enable_scoring', False)
        self.importance_description = scoring_config.get('importance_description', '')
        self.interest_keywords = scoring_config.get('interest_keywords', [])
        self.trusted_sources = scoring_config.get('trusted_sources', [])
        self.topic_relevance_weight = scoring_config.get('topic_relevance_weight', 0.4)
        self.importance_weight = scoring_config.get('importance_weight', 0.3)
        self.ai_feeling_weight = scoring_config.get('ai_feeling_weight', 0.2)
        self.source_weight = scoring_config.get('source_weight', 0.1)
        self.ai_feeling_description = scoring_config.get('ai_feeling_description', '')
    
    def score_news(self, news_data: Dict[str, Any], manual: bool = False) -> Optional[Dict[str, float]]:
        """
        对新闻进行综合评分
        
        Args:
            news_data: 新闻数据字典
            manual: 是否手动触发（手动触发时始终评分）
            
        Returns:
            评分字典，包含总分和4个维度的分数，如果评分未启用且非手动触发则返回None
        """
        if not self.enable_scoring and not manual:
            logger.info("AI评分未启用，跳过评分")
            return None
        
        try:
            # 计算各维度评分
            topic_relevance = self._calculate_topic_relevance(news_data)
            importance = self._calculate_importance(news_data)
            ai_feeling = self._calculate_ai_feeling(news_data)
            source_score = self._calculate_source_score(news_data)
            
            # 综合评分
            total_score = (
                topic_relevance * self.topic_relevance_weight +
                importance * self.importance_weight +
                ai_feeling * self.ai_feeling_weight +
                source_score * self.source_weight
            )
            
            # 限制在0-100范围内
            total_score = max(0, min(100, total_score))
            
            logger.info(
                f"新闻评分: ID={news_data.get('id')}, "
                f"主题相关性={topic_relevance:.2f}, "
                f"重要性={importance:.2f}, "
                f"AI感官分={ai_feeling:.2f}, "
                f"来源={source_score:.2f}, "
                f"总分={total_score:.2f}"
            )
            
            return {
                'total_score': total_score,
                'topic_relevance': topic_relevance,
                'importance': importance,
                'ai_feeling': ai_feeling,
                'source_score': source_score
            }
            
        except Exception as e:
            logger.error(f"新闻评分失败: ID={news_data.get('id')}, error={e}")
            return None
    
    def _calculate_topic_relevance(self, news_data: Dict[str, Any]) -> float:
        """
        计算主题相关性评分（0-100）
        
        Args:
            news_data: 新闻数据
            
        Returns:
            主题相关性评分
        """
        try:
            title = news_data.get('title', '')
            summary = news_data.get('ai_summary', '')
            category = news_data.get('category', '')
            
            # 合并文本
            text = f"{title} {summary} {category}".lower()
            
            # 计算关键词匹配度
            matched_keywords = 0
            for keyword in self.interest_keywords:
                if keyword.lower() in text:
                    matched_keywords += 1
            
            # 计算评分
            if len(self.interest_keywords) == 0:
                return 50.0  # 如果没有配置关键词，给中等分数
            
            score = (matched_keywords / len(self.interest_keywords)) * 100
            return min(100, score)
            
        except Exception as e:
            logger.error(f"计算主题相关性失败: {e}")
            return 50.0
    
    def _calculate_importance(self, news_data: Dict[str, Any]) -> float:
        """
        计算重要性评分（0-100）
        
        Args:
            news_data: 新闻数据
            
        Returns:
            重要性评分
        """
        try:
            title = news_data.get('title', '')
            summary = news_data.get('ai_summary', '')
            
            if not self.importance_description:
                return 50.0  # 如果没有配置重要性描述，给中等分数
            
            # 构建提示词
            prompt = self._build_importance_prompt(title, summary)
            
            # 调用AI
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻分析师，擅长判断新闻的重要性。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.3
            }
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"AI重要性评分失败: status_code={response.status_code}")
                return 50.0
            
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 解析评分
            try:
                score = float(content.strip())
                return max(0, min(100, score))
            except (ValueError, IndexError):
                logger.error(f"AI重要性评分解析失败: content={content}")
                return 50.0
            
        except Exception as e:
            logger.error(f"计算重要性失败: {e}")
            return 50.0
    
    def _build_importance_prompt(self, title: str, summary: str) -> str:
        """
        构建重要性评分提示词
        
        Args:
            title: 新闻标题
            summary: 新闻摘要
            
        Returns:
            提示词
        """
        return f"""请根据以下重要性描述，判断这条新闻的重要性，给出0-100的数字评分。

重要性描述：
{self.importance_description}

新闻标题：{title}
新闻摘要：{summary}

请只返回一个0-100的数字评分，不要添加任何其他内容。"""
    
    def _calculate_ai_feeling(self, news_data: Dict[str, Any]) -> float:
        """
        计算AI感官分（-50到50）
        
        Args:
            news_data: 新闻数据
            
        Returns:
            AI感官分（-50到50，正数表示推荐，负数表示不推荐）
        """
        try:
            title = news_data.get('title', '')
            summary = news_data.get('ai_summary', '')
            
            if not self.ai_feeling_description:
                return 0.0  # 如果没有配置AI感官分描述，给0分
            
            # 构建提示词
            prompt = self._build_ai_feeling_prompt(title, summary)
            
            # 调用AI
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻分析师，擅长判断新闻的阅读价值。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 10,
                "temperature": 0.3
            }
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"AI感官分评分失败: status_code={response.status_code}")
                return 0.0
            
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 解析评分
            try:
                score = float(content.strip())
                # 限制在-50到50范围内
                score = max(-50, min(50, score))
                # 转换为0-100范围（-50到50 -> 0到100）
                normalized_score = score + 50
                return normalized_score
            except (ValueError, IndexError):
                logger.error(f"AI感官分评分解析失败: content={content}")
                return 50.0  # 解析失败，给中等分数
            
        except Exception as e:
            logger.error(f"计算AI感官分失败: {e}")
            return 50.0
    
    def _build_ai_feeling_prompt(self, title: str, summary: str) -> str:
        """
        构建AI感官分提示词
        
        Args:
            title: 新闻标题
            summary: 新闻摘要
            
        Returns:
            提示词
        """
        return f"""请根据以下阅读偏好描述，判断这条新闻的阅读价值，给出-50到50的数字评分。

阅读偏好描述：
{self.ai_feeling_description}

新闻标题：{title}
新闻摘要：{summary}

评分标准：
- 50分：强烈推荐阅读，非常符合阅读偏好
- 25分：推荐阅读，比较符合阅读偏好
- 0分：一般，不推荐也不反对
- -25分：不推荐阅读，不太符合阅读偏好
- -50分：强烈不推荐阅读，完全不符合阅读偏好

请只返回一个-50到50的数字评分，不要添加任何其他内容。"""
    
    def _calculate_source_score(self, news_data: Dict[str, Any]) -> float:
        """
        计算来源可信度评分（0-100）
        
        Args:
            news_data: 新闻数据
            
        Returns:
            来源可信度评分
        """
        try:
            source = news_data.get('source', '')
            
            if not source:
                return 50.0  # 如果没有来源信息，给中等分数
            
            if not self.trusted_sources:
                return 50.0  # 如果没有配置可信来源，给中等分数
            
            # 检查是否在可信来源列表中
            if source in self.trusted_sources:
                return 100.0
            else:
                return 50.0  # 不在可信来源列表中，给中等分数
            
        except Exception as e:
            logger.error(f"计算来源可信度失败: {e}")
            return 50.0


ai_scorer = AIScorer()