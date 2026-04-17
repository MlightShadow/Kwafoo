"""
正文抓取器：从网页中提取新闻正文并压缩
支持三种提取算法：文本密度法、DOM评分法、混合模式
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List, Any
from urllib.parse import urljoin
import re
from datetime import datetime
from utils.logger import logger
from utils.helpers import config
from utils.hybrid_compressor import HybridCompressor


class ContentFetcher:
    """
    正文抓取器：支持多种提取算法
    """
    
    def __init__(self):
        # 配置参数
        self.enable_content_fetch = config.get('content_fetch.enable_content_fetch', True)
        self.algorithm = config.get('content_fetch.algorithm', 'hybrid')
        self.min_content_length = config.get('content_fetch.min_content_length', 200)
        self.max_content_length = config.get('content_fetch.max_content_length', 10000)
        self.timeout = config.get('content_fetch.timeout', 30)
        self.use_proxy = config.get('content_fetch.use_proxy', True)
        self.enable_cache = config.get('content_fetch.enable_cache', True)
        
        # 初始化压缩器
        self.compressor = HybridCompressor()
        
        # 初始化HTTP会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 配置代理
        self._configure_proxy()
        
        # 缓存（如果启用）
        self.cache = {} if self.enable_cache else None
        
        logger.info(f"正文抓取器初始化完成，算法: {self.algorithm}")
    
    def _configure_proxy(self):
        """配置代理"""
        if self.use_proxy:
            enable_proxy = config.get('network.enable_proxy', False)
            proxy_url = config.get('network.proxy_url', '')
            
            if enable_proxy and proxy_url:
                self.session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logger.info(f"正文抓取器使用代理: {proxy_url}")
    
    def fetch_content(self, url: str) -> Dict[str, Any]:
        """
        获取并处理新闻正文
        
        Args:
            url: 新闻链接
            
        Returns:
            包含content、compressed_content等字段的字典
        """
        result = {
            'content': None,
            'compressed_content': None,
            'success': False,
            'error': None
        }
        
        # 检查缓存
        if self.enable_cache and url in self.cache:
            logger.debug(f"使用缓存: {url}")
            return self.cache[url]
        
        try:
            # 1. 获取网页内容
            soup = self._fetch_page(url)
            if not soup:
                raise Exception("网页获取失败")
            
            # 2. 提取正文
            content = self._extract_content(soup)
            
            if content and len(content) >= self.min_content_length:
                result['content'] = content
                result['success'] = True
                
                # 3. 压缩正文
                if len(content) > self.max_content_length:
                    result['compressed_content'] = self.compressor.compress(content)
                    logger.debug(f"正文已压缩: {len(content)} -> {len(result['compressed_content'])}")
                else:
                    result['compressed_content'] = content
            else:
                logger.debug(f"正文长度不足: {len(content) if content else 0} < {self.min_content_length}")
                raise Exception("正文长度不足")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"正文抓取失败: {url} - {e}")
        
        # 缓存结果
        if self.enable_cache:
            self.cache[url] = result
        
        return result
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """获取网页内容"""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 自动检测编码
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.debug(f"网页获取成功: {url}")
            return soup
            
        except requests.RequestException as e:
            logger.error(f"网页请求失败: {url} - {e}")
            return None
        except Exception as e:
            logger.error(f"网页解析失败: {url} - {e}")
            return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """提取正文（根据配置的算法）"""
        if self.algorithm == 'density':
            return self._extract_by_density(soup)
        elif self.algorithm == 'dom':
            return self._extract_by_dom(soup)
        else:  # hybrid
            return self._extract_hybrid(soup)
    
    def _extract_by_density(self, soup: BeautifulSoup) -> Optional[str]:
        """文本密度法提取正文"""
        # 预处理：移除噪声标签
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'footer', 'nav', 'header', 'aside', 'form', 'button', 'input', 'select', 'textarea']):
            tag.decompose()
        
        # 移除隐藏元素
        for tag in soup.find_all(style=re.compile(r'display:\s*none|visibility:\s*hidden', re.I)):
            tag.decompose()
        
        # 移除常见的广告和无关元素
        for tag in soup.find_all(class_=re.compile(r'(ad|advertisement|banner|sidebar|comment|related|recommend|share|social)', re.I)):
            tag.decompose()
        
        # 移除id包含广告相关词汇的元素
        for tag in soup.find_all(id=re.compile(r'(ad|advertisement|banner|sidebar|comment|related|recommend|share|social)', re.I)):
            tag.decompose()
        
        # 计算每个候选节点的文本密度
        candidates = []
        for tag in soup.find_all(['div', 'article', 'section', 'main', 'td']):
            text = tag.get_text(strip=True)
            if len(text) < self.min_content_length:
                continue
            
            # 计算特征
            text_length = len(text)
            tag_count = len(tag.find_all())
            link_count = len(tag.find_all('a'))
            punctuation_count = len(re.findall(r'[，。！？；：""''（）【】]', text))
            
            # 计算密度
            tag_density = tag_count / text_length if text_length > 0 else 0
            link_density = link_count / text_length if text_length > 0 else 0
            punctuation_density = punctuation_count / text_length if text_length > 0 else 0
            
            # 更严格的噪声过滤
            if tag_density > 0.3 or link_density > 0.3:
                continue
            
            # 计算得分 - 提高标点符号的权重
            score = text_length * (punctuation_density * 2 + 1)
            candidates.append((tag, score))
        
        # 选择得分最高的节点
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_tag = candidates[0][0]
        
        # 清理并返回文本
        return self._clean_text(best_tag.get_text(separator='\n', strip=True))
    
    def _extract_by_dom(self, soup: BeautifulSoup) -> Optional[str]:
        """DOM评分法提取正文"""
        # 定义标签权重
        tag_weights = {
            'article': 50,
            'main': 40,
            '[role="main"]': 35,
            'div.content': 30,
            'div.post': 25,
            'div.entry': 20,
            'div.article': 20,
            'div.article-content': 25,
            'div.post-content': 25,
            'div.entry-content': 25,
            'div.main-content': 25,
            'section.content': 30,
            'div.sidebar': -40,
            'nav': -50,
            'footer': -60,
            'aside': -40,
            'div.comments': -50,
            'div.related': -40,
            'div.recommend': -40,
            'div.share': -40,
            'div.social': -40,
            'div.advertisement': -60,
            'div.ad': -60
        }
        
        # 预处理：移除噪声标签
        for tag in soup(['script', 'style', 'noscript', 'iframe', 'svg', 'footer', 'nav', 'header', 'aside', 'form', 'button', 'input', 'select', 'textarea']):
            tag.decompose()
        
        # 移除常见的广告和无关元素
        for tag in soup.find_all(class_=re.compile(r'(ad|advertisement|banner|sidebar|comment|related|recommend|share|social)', re.I)):
            tag.decompose()
        
        # 移除id包含广告相关词汇的元素
        for tag in soup.find_all(id=re.compile(r'(ad|advertisement|banner|sidebar|comment|related|recommend|share|social)', re.I)):
            tag.decompose()
        
        candidates = []
        
        for tag in soup.find_all(['div', 'article', 'section', 'main', 'nav', 'footer', 'aside']):
            # 计算语义分
            semantic_score = 0
            tag_name = tag.name.lower()
            tag_class = ' '.join(tag.get('class', []))
            tag_id = tag.get('id', '')
            
            # 检查标签权重
            for pattern, weight in tag_weights.items():
                if pattern.startswith('['):
                    # 属性选择器
                    if tag.get(pattern[1:-1].split('=')[0]) == pattern.split('=')[1].strip('"'):
                        semantic_score += weight
                elif '.' in pattern:
                    # 类选择器
                    if pattern.split('.')[1] in tag_class:
                        semantic_score += weight
                elif '#' in pattern:
                    # ID选择器
                    if pattern.split('#')[1] == tag_id:
                        semantic_score += weight
                else:
                    # 标签选择器
                    if tag_name == pattern:
                        semantic_score += weight
            
            # 计算文本量分
            text = tag.get_text(strip=True)
            text_length = len(text)
            if text_length < self.min_content_length:
                continue
            
            text_score = min(text_length / 1000, 10)  # 归一化到0-10
            
            # 计算密度分
            tag_count = len(tag.find_all())
            link_count = len(tag.find_all('a'))
            density_score = max(0, 10 - (link_count * 15 / text_length)) if text_length > 0 else 0
            
            # 计算连续分
            p_count = len(tag.find_all('p'))
            continuous_score = min(p_count / 5, 10)  # 归一化到0-10
            
            # 计算位置分
            position_score = 5  # 默认中间位置
            
            # 计算中文比例分
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            chinese_ratio = chinese_chars / text_length if text_length > 0 else 0
            chinese_score = chinese_ratio * 10  # 中文比例越高，分数越高
            
            # 计算总分
            total_score = (
                semantic_score * 0.25 +
                text_score * 0.20 +
                density_score * 0.20 +
                continuous_score * 0.15 +
                position_score * 0.05 +
                chinese_score * 0.15
            )
            
            candidates.append((tag, total_score))
        
        # 选择得分最高的节点
        if not candidates:
            return None
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_tag = candidates[0][0]
        
        return self._clean_text(best_tag.get_text(separator='\n', strip=True))
    
    def _extract_hybrid(self, soup: BeautifulSoup) -> Optional[str]:
        """混合模式提取正文"""
        # 第一步：用文本密度法快速筛选
        density_result = self._extract_by_density(soup)
        
        if not density_result or len(density_result) < self.min_content_length:
            # 如果密度法失败，使用DOM评分法
            return self._extract_by_dom(soup)
        
        # 第二步：验证结果质量
        # 检查是否包含足够的中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', density_result))
        if chinese_chars < len(density_result) * 0.3:
            # 中文比例过低，可能提取错误，使用DOM评分法
            logger.debug("中文比例过低，切换到DOM评分法")
            return self._extract_by_dom(soup)
        
        return density_result
    
    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白，但保留换行符
        text = re.sub(r'[ \t]+', ' ', text)  # 空格和制表符
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 多个空行合并为一个
        
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 移除常见的广告和无关文本模式
        patterns_to_remove = [
            r'点击查看更多',
            r'点击阅读原文',
            r'点击关注',
            r'扫码关注',
            r'关注我们',
            r'分享到',
            r'转载请注明',
            r'本文来源',
            r'原文链接',
            r'更多精彩内容',
            r'推荐阅读',
            r'相关推荐',
            r'热门文章',
            r'最新文章',
            r'上一篇.*?下一篇',
            r'【.*?】.*?【.*?】',  # 移除类似【上一篇】【下一篇】的内容
            r'本文版权归.*?所有',
            r'未经授权.*?转载',
            r'广告',
            r'赞助',
            r'合作',
            r'商务合作',
            r'联系我们',
            r'联系电话',
            r'邮箱',
            r'Email.*?:',
            r'微信公众号',
            r'微博',
            r'抖音',
            r'快手',
            r'知乎',
            r'B站',
            r'哔哩哔哩',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 移除URL链接
        text = re.sub(r'https?://[^\s]+', '', text)
        
        # 移除邮箱地址
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # 移除电话号码
        text = re.sub(r'\b\d{3,4}[-.]?\d{7,8}\b', '', text)
        text = re.sub(r'\b1[3-9]\d{9}\b', '', text)
        
        # 移除多余的空行
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        
        return text.strip()


# 全局实例
content_fetcher = ContentFetcher()