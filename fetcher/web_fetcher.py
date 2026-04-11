import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from utils.logger import logger
from utils.helpers import config


class WebFetcher:
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

    def fetch(self, url: str, selectors: Dict[str, str], source_name: str,
              fetch_days: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            logger.info(f"开始抓取网页: {source_name} - {url}")
            
            if fetch_days is not None:
                logger.info(f"抓取天数限制: {fetch_days} 天")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            container = soup.select_one(selectors.get('container', 'body'))
            if not container:
                logger.warning(f"未找到容器元素: {selectors.get('container')}")
                return []
            
            news_list = []
            items = container.select(selectors.get('item', 'div'))
            
            for item in items:
                news_data = self._parse_item(item, selectors, source_name, fetch_days, url)
                if news_data:
                    news_list.append(news_data)
            
            logger.info(f"网页抓取完成: {source_name} - 获取 {len(news_list)} 条新闻")
            return news_list
            
        except requests.RequestException as e:
            logger.error(f"网页请求失败: {url} - {e}")
            return []
        except Exception as e:
            logger.error(f"网页解析失败: {url} - {e}")
            return []

    def _parse_item(self, item: BeautifulSoup, selectors: Dict[str, str],
                   source_name: str, fetch_days: Optional[int] = None, base_url: str = '') -> Optional[Dict[str, Any]]:
        try:
            title_elem = item.select_one(selectors.get('title', 'h1, h2, h3'))
            if not title_elem:
                return None
            
            title = title_elem.get_text(strip=True)
            if not title:
                return None
            
            description = self._get_text(item, selectors.get('content', 'p'))
            
            link_elem = item.select_one(selectors.get('link', 'a'))
            link = link_elem.get('href', '') if link_elem else ''
            
            if link and not link.startswith('http'):
                link = requests.compat.urljoin(base_url, link)
            
            if not link:
                return None
            
            publish_time = self._parse_time(item, selectors.get('time', 'time'))
            
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
            logger.error(f"网页条目解析失败: {e}")
            return None

    def _get_text(self, element: BeautifulSoup, selector: str) -> Optional[str]:
        if not selector:
            return None
        
        elem = element.select_one(selector)
        if elem:
            return elem.get_text(strip=True)
        return None

    def _parse_time(self, item: BeautifulSoup, selector: str) -> Optional[datetime]:
        if not selector:
            return None
        
        time_elem = item.select_one(selector)
        if not time_elem:
            return None
        
        time_text = time_elem.get_text(strip=True)
        if not time_text:
            return None
        
        datetime_attr = time_elem.get('datetime')
        if datetime_attr:
            try:
                return datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
            except (ValueError, TypeError) as e:
                logger.debug(f"datetime属性解析失败: {datetime_attr}, 错误: {e}")
        
        try:
            return datetime.fromisoformat(time_text)
        except (ValueError, TypeError) as e:
            logger.debug(f"时间文本解析失败: {time_text}, 错误: {e}")
            return None


web_fetcher = WebFetcher()