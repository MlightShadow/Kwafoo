import feedparser
import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from utils.logger import logger
from utils.image_processor import image_processor
from utils.helpers import config
from fetcher.content_fetcher import content_fetcher


class RSSFetcher:
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

    def fetch(self, rss_url: str, source_name: str, 
              fetch_days: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            logger.info(f"开始抓取RSS: {source_name} - {rss_url}")
            
            if fetch_days is not None:
                logger.info(f"抓取天数限制: {fetch_days} 天")
            
            response = self.session.get(rss_url, timeout=30)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            news_list = []
            for entry in feed.entries:
                news_data = self._parse_entry(entry, source_name, fetch_days)
                if news_data:
                    news_list.append(news_data)
            
            logger.info(f"RSS抓取完成: {source_name} - 获取 {len(news_list)} 条新闻")
            return news_list
            
        except requests.RequestException as e:
            logger.error(f"RSS请求失败: {rss_url} - {e}")
            return []
        except Exception as e:
            logger.error(f"RSS解析失败: {rss_url} - {e}")
            return []

    def _clean_html(self, text: str) -> str:
        if not text:
            return ''
        
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

    def _parse_entry(self, entry: Any, source_name: str, 
                    fetch_days: Optional[int] = None) -> Dict[str, Any]:
        try:
            title = entry.get('title', '').strip()
            if not title:
                return None
            
            raw_description = entry.get('description', '')
            if not raw_description:
                raw_description = entry.get('summary', '')
            
            # 提取图片URL（使用原始HTML）
            image_url = self._extract_image_url(entry, raw_description)
            
            # 清理HTML标签
            description = self._clean_html(raw_description)
            
            link = entry.get('link', '')
            if not link:
                return None
            
            publish_time = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                publish_time = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                publish_time = datetime(*entry.updated_parsed[:6])
            
            if publish_time is None:
                logger.warning(f"新闻缺少发布时间，跳过: {title}")
                return None
            
            if fetch_days is not None:
                time_threshold = datetime.now() - timedelta(days=fetch_days)
                if publish_time < time_threshold:
                    logger.debug(f"新闻发布时间超过 {fetch_days} 天，跳过: {title} ({publish_time})")
                    return None
            
            # 初始化结果
            result = {
                'title': title,
                'description': description,  # RSS描述就是摘要
                'content': None,
                'compressed_content': None,
                'url': link,
                'source': source_name,
                'category': None,
                'publish_time': publish_time,
                'is_visible': 1,
                'image_url': image_url
            }
            
            # 如果启用正文抓取
            if config.get('content_fetch.enable_content_fetch', False):
                try:
                    content_result = content_fetcher.fetch_content(link)
                    
                    # 更新结果
                    result['content'] = content_result.get('content')
                    result['compressed_content'] = content_result.get('compressed_content')
                    
                    logger.debug(f"正文抓取成功: {title}")
                    
                except Exception as e:
                    logger.warning(f"正文抓取失败: {title} - {e}")
                    # 不影响RSS抓取流程，description就是摘要
            
            return result
            
        except Exception as e:
            logger.error(f"RSS条目解析失败: {e}")
            return None
    
    def _extract_image_url(self, entry: Any, description: str) -> Optional[str]:
        """
        从RSS条目中提取图片URL
        
        优先级：
        1. media:content 标签
        2. enclosure 标签
        3. description 中的 img 标签
        """
        # 1. 检查 media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    return media.get('url')
        
        # 2. 检查 enclosure
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    return enclosure.get('href')
        
        # 3. 从 description 中提取
        if description:
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', description, re.IGNORECASE)
            if img_match:
                return img_match.group(1)
        
        return None


rss_fetcher = RSSFetcher()