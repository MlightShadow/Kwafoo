import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from utils.logger import logger
from utils.helpers import config


class APIFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 根据配置设置代理
        self._configure_proxy()

    def _configure_proxy(self):
        """根据配置设置代理"""
        enable_proxy = config.get('network.enable_proxy', False)
        proxy_url = config.get('network.proxy_url', '')
        
        if enable_proxy:
            if proxy_url:
                # 使用配置的自定义代理
                self.session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logger.info(f"使用自定义代理: {proxy_url}")
            else:
                # 使用系统环境变量中的代理
                logger.info("使用系统环境变量代理")
        else:
            # 不启用代理，跟随系统网络设置
            logger.info("跟随系统网络设置")

    def fetch(self, api_url: str, api_key: str, source_name: str,
              fetch_days: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            logger.info(f"开始抓取API: {source_name} - {api_url}")
            
            if fetch_days is not None:
                logger.info(f"抓取天数限制: {fetch_days} 天")
            
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'
            
            response = self.session.get(api_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            news_list = []
            if isinstance(data, dict):
                articles = data.get('articles', data.get('data', data.get('news', [])))
            else:
                articles = data
            
            for article in articles:
                news_data = self._parse_article(article, source_name, fetch_days)
                if news_data:
                    news_list.append(news_data)
            
            logger.info(f"API抓取完成: {source_name} - 获取 {len(news_list)} 条新闻")
            return news_list
            
        except requests.RequestException as e:
            logger.error(f"API请求失败: {api_url} - {e}")
            return []
        except Exception as e:
            logger.error(f"API解析失败: {api_url} - {e}")
            return []

    def _parse_article(self, article: Dict[str, Any], source_name: str,
                       fetch_days: Optional[int] = None) -> Optional[Dict[str, Any]]:
        try:
            title = self._get_field(article, ['title', 'headline', 'name'])
            if not title:
                return None
            
            description = self._get_field(article, [
                'description', 'summary', 'content', 'excerpt', 'body'
            ])
            
            link = self._get_field(article, ['url', 'link', 'permalink', 'webUrl'])
            if not link:
                return None
            
            publish_time = self._parse_time(article)
            
            if publish_time is None:
                logger.warning(f"新闻缺少发布时间，跳过: {title}")
                return None
            
            if fetch_days is not None:
                time_threshold = datetime.now() - timedelta(days=fetch_days)
                if publish_time < time_threshold:
                    logger.debug(f"新闻发布时间超过 {fetch_days} 天，跳过: {title} ({publish_time})")
                    return None
            
            return {
                'title': title,
                'description': description,
                'content': None,
                'url': link,
                'source': source_name,
                'category': None,
                'publish_time': publish_time,
                'is_visible': 1
            }
            
        except Exception as e:
            logger.error(f"API文章解析失败: {e}")
            return None

    def _get_field(self, article: Dict[str, Any], field_names: List[str]) -> Optional[str]:
        for field_name in field_names:
            value = article.get(field_name)
            if value:
                return str(value).strip()
        return None

    def _parse_time(self, article: Dict[str, Any]) -> Optional[datetime]:
        time_fields = ['publishedAt', 'published', 'pubDate', 'date', 'timestamp']
        
        for field_name in time_fields:
            value = article.get(field_name)
            if value:
                try:
                    if isinstance(value, (int, float)):
                        return datetime.fromtimestamp(value)
                    elif isinstance(value, str):
                        return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    continue
        
        return None


api_fetcher = APIFetcher()