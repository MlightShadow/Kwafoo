from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import logger
from utils.helpers import config
from database import db


class RAGEngine:
    def __init__(self):
        self.top_k = config.get('rag.top_k', 5)
        self.use_fts = config.get('rag.use_fts', True)

    def search(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            logger.info(f"开始RAG搜索: {query}")
            
            if self.use_fts:
                news_list = db.search_news(query, limit=self.top_k * 2)
            else:
                news_list = self._search_by_keywords(query)
            
            if category:
                news_list = self._filter_by_category(news_list, category)
            
            news_list = news_list[:self.top_k]
            
            logger.info(f"RAG搜索完成: 找到 {len(news_list)} 条相关新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"RAG搜索失败: {e}")
            return []

    def _search_by_keywords(self, query: str) -> List[Dict[str, Any]]:
        try:
            keywords = query.split()
            all_news = db.get_news_by_date(datetime.now().strftime('%Y-%m-%d'))
            
            scored_news = []
            for news in all_news:
                score = self._calculate_relevance_score(news, keywords)
                if score > 0:
                    scored_news.append((news, score))
            
            scored_news.sort(key=lambda x: x[1], reverse=True)
            
            return [news for news, score in scored_news]
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []

    def _calculate_relevance_score(self, news: Dict[str, Any], keywords: List[str]) -> int:
        score = 0
        
        title = news.get('title', '').lower()
        description = news.get('description', '').lower()
        ai_summary = news.get('ai_summary', '').lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            if keyword_lower in title:
                score += 10
            if keyword_lower in description:
                score += 5
            if keyword_lower in ai_summary:
                score += 5
        
        return score

    def _filter_by_category(self, news_list: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        filtered = []
        
        for news in news_list:
            news_category = news.get('category', '')
            
            if not news_category:
                continue
            
            if category in news_category.split(','):
                filtered.append(news)
        
        return filtered

    def build_context(self, query: str, category: Optional[str] = None) -> str:
        try:
            news_list = self.search(query, category)
            
            if not news_list:
                return "没有找到相关新闻。"
            
            context_parts = []
            for i, news in enumerate(news_list, 1):
                title = news.get('title', '')
                summary = news.get('ai_summary') or news.get('description', '')
                source = news.get('source', '')
                url = news.get('url', '')
                
                context_part = f"""
{i}. 标题：{title}
   摘要：{summary}
   来源：{source}
   链接：{url}
"""
                context_parts.append(context_part)
            
            return ''.join(context_parts)
            
        except Exception as e:
            logger.error(f"构建上下文失败: {e}")
            return "构建上下文失败。"


rag_engine = RAGEngine()