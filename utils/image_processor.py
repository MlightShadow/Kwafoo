import requests
import io
import os
import hashlib
from PIL import Image
from typing import Optional, Tuple
from datetime import datetime
from utils.logger import logger
from utils.helpers import config


class ImageProcessor:
    """图片处理类：下载、压缩、存储图片"""
    
    def __init__(self):
        self.enable_fetch = config.get('image.enable_fetch', True)
        self.thumbnail_size = config.get('image.thumbnail_size', {'width': 256, 'height': 256})
        self.default_image = config.get('image.default_image', '')
        self.supported_formats = config.get('image.supported_formats', ['jpg', 'jpeg', 'png', 'webp', 'gif'])
        self.max_image_size = config.get('image.max_image_size', 5242880)  # 5MB
        
        # 代理配置
        self.enable_proxy = config.get('network.enable_proxy', False)
        self.proxy_url = config.get('network.proxy_url', '')
        
        # 文件存储配置
        self.storage_mode = config.get('image.storage_mode', 'filesystem')  # 'filesystem' or 'database'
        self.storage_path = config.get('image.storage_path', 'data/images')
        self.ensure_storage_directory()
    
    def ensure_storage_directory(self):
        """确保图片存储目录存在"""
        if self.storage_mode == 'filesystem':
            os.makedirs(self.storage_path, exist_ok=True)
            logger.info(f"图片存储目录: {self.storage_path}")
    
    def generate_filename(self, image_url: str) -> str:
        """根据URL生成唯一的文件名"""
        # 使用URL的哈希值作为文件名
        url_hash = hashlib.md5(image_url.encode('utf-8')).hexdigest()
        return f"{url_hash}.jpg"
    
    def get_image_path(self, image_url: str) -> str:
        """获取图片的存储路径"""
        filename = self.generate_filename(image_url)
        return os.path.join(self.storage_path, filename)
    
    def get_image_url(self, image_url: str) -> str:
        """获取图片的访问URL"""
        if self.storage_mode == 'filesystem':
            filename = self.generate_filename(image_url)
            return f"/api/images/{filename}"
        else:
            # 数据库模式，返回原始URL或base64
            return image_url
    
    def save_to_filesystem(self, image_data: bytes, image_url: str) -> str:
        """
        保存图片到文件系统
        
        Args:
            image_data: 图片数据
            image_url: 原始URL
            
        Returns:
            保存后的文件路径
        """
        try:
            filepath = self.get_image_path(image_url)
            
            # 如果文件已存在，直接返回
            if os.path.exists(filepath):
                logger.debug(f"图片已存在: {filepath}")
                return filepath
            
            # 保存图片
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"图片保存成功: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存图片失败: {e}")
            raise
    
    def load_from_filesystem(self, filename: str) -> Optional[bytes]:
        """
        从文件系统加载图片
        
        Args:
            filename: 文件名
            
        Returns:
            图片数据
        """
        try:
            filepath = os.path.join(self.storage_path, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"图片文件不存在: {filepath}")
                return None
            
            with open(filepath, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"加载图片失败: {e}")
            return None
    
    def fetch_and_process_image(self, image_url: str) -> Optional[Tuple[str, Optional[bytes]]]:
        """
        下载并处理图片（带重试机制）
        
        Args:
            image_url: 图片URL
            
        Returns:
            (image_url, image_data) 或 (image_url, None)
        """
        if not self.enable_fetch or not image_url:
            return (image_url, None)
        
        try:
            # 检查是否已存在
            if self.storage_mode == 'filesystem':
                filepath = self.get_image_path(image_url)
                if os.path.exists(filepath):
                    logger.debug(f"图片已缓存: {image_url}")
                    return (self.get_image_url(image_url), None)
            
            # 下载图片（根据配置决定是否使用代理）
            max_retries = 5  # 增加重试次数
            timeout_errors = (requests.Timeout, requests.exceptions.Timeout)
            http_errors = (requests.HTTPError, requests.exceptions.HTTPError)
            
            # 解析图片URL，获取域名用于设置Referer
            from urllib.parse import urlparse
            parsed_url = urlparse(image_url)
            referer_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 准备多个Referer策略
            referer_strategies = [
                referer_domain,  # 使用图片来源域名
                f"{parsed_url.scheme}://{parsed_url.netloc}/",  # 带尾部斜杠
                'https://www.google.com/',  # 使用Google作为Referer
                'https://www.bing.com/',  # 使用Bing作为Referer
                'https://www.baidu.com/'  # 使用百度作为Referer
            ]
            
            # 随机User-Agent，避免被识别为机器人
            import random
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]
            
            for attempt in range(max_retries):
                try:
                    session = requests.Session()
                    
                    # 每次重试使用不同的Referer策略
                    current_referer = referer_strategies[attempt % len(referer_strategies)]
                    
                    # 准备请求头，模拟真实浏览器
                    headers = {
                        'User-Agent': random.choice(user_agents),
                        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Referer': current_referer,  # 使用当前策略的Referer
                        'DNT': '1',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1',
                        'Sec-Fetch-Dest': 'image',
                        'Sec-Fetch-Mode': 'no-cors',
                        'Sec-Fetch-Site': 'same-origin',
                        'Cache-Control': 'max-age=0',
                        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"'
                    }
                    
                    session.headers.update(headers)
                    
                    # 配置重定向
                    session.max_redirects = 5
                    
                    if self.enable_proxy:
                        if self.proxy_url:
                            # 使用配置的自定义代理
                            session.proxies = {
                                'http': self.proxy_url,
                                'https': self.proxy_url
                            }
                            logger.debug(f"使用代理下载图片: {self.proxy_url}")
                        else:
                            # 使用系统环境变量中的代理
                            logger.debug("使用系统环境变量代理下载图片")
                    else:
                        # 不启用代理，跟随系统网络设置
                        logger.debug("跟随系统网络设置下载图片")
                    
                    # 增加超时时间到30秒
                    response = session.get(image_url, timeout=30, stream=True, allow_redirects=True)
                    response.raise_for_status()
                    
                    # 检查图片大小
                    content_length = response.headers.get('content-length', 0)
                    if content_length and int(content_length) > self.max_image_size:
                        logger.warning(f"图片过大，跳过: {image_url} ({content_length} bytes)")
                        return (image_url, None)
                    
                    # 检查图片格式
                    content_type = response.headers.get('content-type', '')
                    if not self._is_supported_format(content_type):
                        logger.warning(f"不支持的图片格式: {content_type}")
                        return (image_url, None)
                    
                    # 读取图片数据（流式读取，避免内存溢出）
                    image_data = b''
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            image_data += chunk
                    
                    # 验证图片数据完整性
                    if len(image_data) == 0:
                        logger.warning(f"图片数据为空: {image_url}")
                        if attempt < max_retries - 1:
                            continue
                        return (image_url, None)
                    
                    if len(image_data) < 1024:  # 小于1KB，可能是错误页面
                        logger.warning(f"图片数据过小，可能无效: {image_url} ({len(image_data)} bytes)")
                        if attempt < max_retries - 1:
                            continue
                        return (image_url, None)
                    
                    # 验证是否为有效图片
                    try:
                        from io import BytesIO
                        from PIL import Image
                        img = Image.open(BytesIO(image_data))
                        img.verify()  # 验证图片完整性
                        # 重新打开，因为verify()会关闭文件
                        img = Image.open(BytesIO(image_data))
                        width, height = img.size
                        if width < 10 or height < 10:
                            logger.warning(f"图片尺寸过小: {image_url} ({width}x{height})")
                            if attempt < max_retries - 1:
                                continue
                            return (image_url, None)
                    except Exception as e:
                        logger.warning(f"图片验证失败: {image_url} - {e}")
                        if attempt < max_retries - 1:
                            continue
                        return (image_url, None)
                    
                    # 压缩图片
                    compressed_data = self._compress_image(image_data)
                    
                    if compressed_data:
                        # 根据存储模式处理
                        if self.storage_mode == 'filesystem':
                            # 保存到文件系统
                            self.save_to_filesystem(compressed_data, image_url)
                            # 返回本地URL和压缩数据（用于前端判断是否已下载）
                            logger.info(f"图片下载成功: {image_url} -> {len(compressed_data)} bytes")
                            return (self.get_image_url(image_url), compressed_data)
                        else:
                            # 返回压缩后的数据（用于数据库存储）
                            logger.info(f"图片处理成功: {image_url} -> {len(compressed_data)} bytes")
                            return (image_url, compressed_data)
                
                except timeout_errors as e:
                    # 超时错误，进行重试
                    if attempt < max_retries - 1:
                        retry_delay = 2 ** attempt  # 指数退避：2秒、4秒、8秒、16秒
                        logger.warning(f"图片下载超时，第{attempt + 1}次重试，{retry_delay}秒后重试: {image_url}")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"图片下载超时，已达最大重试次数: {image_url}")
                        return (image_url, None)
                
                except http_errors as e:
                    # HTTP错误处理
                    status_code = 'unknown'
                    error_detail = str(e)
                    
                    if hasattr(e, 'response') and e.response is not None:
                        status_code = e.response.status_code
                        error_detail = f"HTTP {status_code}"
                    elif hasattr(e, 'request') and e.request is not None:
                        error_detail = "连接失败"
                    
                    # 对于某些错误可以重试（如429 Too Many Requests, 403 Forbidden）
                    retryable_codes = [403, 429, 500, 502, 503, 504]
                    if status_code in retryable_codes and attempt < max_retries - 1:
                        retry_delay = 2 ** attempt
                        logger.warning(f"图片下载HTTP错误（可重试），第{attempt + 1}次重试，{retry_delay}秒后重试: {image_url} - {error_detail}")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.warning(f"图片下载HTTP错误，不重试: {image_url} - {error_detail}")
                        return (image_url, None)
                
                except requests.ConnectionError as e:
                    # 连接错误，可以重试
                    if attempt < max_retries - 1:
                        retry_delay = 2 ** attempt
                        logger.warning(f"图片下载连接错误，第{attempt + 1}次重试，{retry_delay}秒后重试: {image_url} - {e}")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"图片下载连接错误，已达最大重试次数: {image_url} - {e}")
                        return (image_url, None)
                
                except requests.SSLError as e:
                    # SSL错误，尝试不验证SSL
                    if attempt < max_retries - 1:
                        logger.warning(f"SSL错误，第{attempt + 1}次重试: {image_url} - {e}")
                        import time
                        time.sleep(2 ** attempt)
                        # 下次重试时禁用SSL验证
                        try:
                            response = requests.get(image_url, timeout=30, stream=True, verify=False, headers=headers)
                            response.raise_for_status()
                            # 继续处理...
                        except Exception:
                            continue
                    else:
                        logger.error(f"SSL错误，已达最大重试次数: {image_url}")
                        return (image_url, None)
                
                except requests.RequestException as e:
                    # 其他请求错误
                    if attempt < max_retries - 1:
                        retry_delay = 2 ** attempt
                        logger.warning(f"图片下载失败，第{attempt + 1}次重试，{retry_delay}秒后重试: {image_url} - {e}")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"图片下载失败，已达最大重试次数: {image_url} - {e}")
                        return (image_url, None)
            
            return (image_url, None)
            
        except Exception as e:
            logger.error(f"处理图片失败: {image_url} - {e}")
            return (image_url, None)
    
    def _is_supported_format(self, content_type: str) -> bool:
        """检查图片格式是否支持"""
        format_map = {
            'image/jpeg': 'jpg',
            'image/jpg': 'jpg',
            'image/png': 'png',
            'image/webp': 'webp',
            'image/gif': 'gif'
        }
        
        file_format = format_map.get(content_type.lower())
        return file_format in self.supported_formats
    
    def _compress_image(self, image_data: bytes) -> Optional[bytes]:
        """
        压缩图片到指定尺寸（2:1比例）
        
        Args:
            image_data: 原始图片数据
            
        Returns:
            压缩后的图片数据
        """
        try:
            # 打开图片
            img = Image.open(io.BytesIO(image_data))
            
            # 转换为RGB模式（如果需要）
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 获取原始尺寸
            original_width, original_height = img.size
            
            # 按照2:1比例计算目标尺寸
            target_width = self.thumbnail_size['width']
            target_height = target_width // 2  # 2:1比例
            
            # 先按照2:1比例裁剪原始图片
            if original_width > original_height:
                # 宽图：保持高度不变，计算需要的宽度
                cropped_width = original_height * 2
                # 居中裁剪
                left = (original_width - cropped_width) // 2
                top = 0
                right = left + cropped_width
                bottom = original_height
            else:
                # 长图：保持宽度不变，计算需要的高度
                # 确保宽度是偶数，这样除以2才是整数
                if original_width % 2 != 0:
                    # 奇数宽度，减1变成偶数
                    cropped_width = original_width - 1
                    left = 1  # 从第1列开始裁剪
                    right = left + cropped_width
                else:
                    cropped_width = original_width
                    left = 0
                    right = original_width
                cropped_height = cropped_width // 2
                # 从顶部裁剪
                top = 0
                bottom = cropped_height
            
            # 验证裁剪区域是否有效
            if left < 0 or top < 0 or right > original_width or bottom > original_height or bottom <= top:
                logger.warning(f"裁剪区域无效: ({left}, {top}, {right}, {bottom}), 原始尺寸: {original_width}x{original_height}")
                # 如果裁剪区域无效，直接缩放整个图片
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            else:
                # 裁剪图片
                img = img.crop((left, top, right, bottom))
                
                # 缩放到目标尺寸
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            # 保存为JPEG格式（不添加白色背景）
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            compressed_data = output.getvalue()
            
            logger.debug(f"图片压缩: {len(image_data)} -> {len(compressed_data)} bytes, 尺寸: {original_width}x{original_height} -> {target_width}x{target_height}")
            return compressed_data
            
        except Exception as e:
            logger.error(f"图片压缩失败: {e}")
            return None
    
    def get_default_image(self) -> str:
        """获取默认图片URL"""
        return self.default_image
    
    def cleanup_old_images(self, max_age_days: int = 30):
        """
        清理旧的图片文件
        
        Args:
            max_age_days: 最大保留天数
        """
        if self.storage_mode != 'filesystem':
            return
        
        try:
            current_time = datetime.now()
            deleted_count = 0
            
            for filename in os.listdir(self.storage_path):
                filepath = os.path.join(self.storage_path, filename)
                
                # 获取文件修改时间
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                age_days = (current_time - file_mtime).days
                
                if age_days > max_age_days:
                    os.remove(filepath)
                    deleted_count += 1
                    logger.debug(f"删除旧图片: {filename} ({age_days}天)")
            
            if deleted_count > 0:
                logger.info(f"清理完成，删除了 {deleted_count} 个旧图片文件")
                
        except Exception as e:
            logger.error(f"清理旧图片失败: {e}")


# 创建全局实例
image_processor = ImageProcessor()