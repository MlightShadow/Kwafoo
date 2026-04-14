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
            max_retries = 3
            timeout_errors = (requests.Timeout, requests.exceptions.Timeout)
            http_errors = (requests.HTTPError, requests.exceptions.HTTPError)
            
            for attempt in range(max_retries):
                try:
                    session = requests.Session()
                    
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
                    
                    response = session.get(image_url, timeout=10, stream=True)
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
                    
                    # 读取图片数据
                    image_data = response.content
                    
                    # 压缩图片
                    compressed_data = self._compress_image(image_data)
                    
                    if compressed_data:
                        # 根据存储模式处理
                        if self.storage_mode == 'filesystem':
                            # 保存到文件系统
                            self.save_to_filesystem(compressed_data, image_url)
                            return (self.get_image_url(image_url), None)
                        else:
                            # 返回压缩后的数据（用于数据库存储）
                            logger.info(f"图片处理成功: {image_url} -> {len(compressed_data)} bytes")
                            return (image_url, compressed_data)
                
                except timeout_errors as e:
                    # 超时错误，进行重试
                    if attempt < max_retries - 1:
                        retry_delay = 2 ** attempt  # 指数退避：2秒、4秒
                        logger.warning(f"图片下载超时，第{attempt + 1}次重试，{retry_delay}秒后重试: {image_url}")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"图片下载超时，已达最大重试次数: {image_url}")
                        return (image_url, None)
                
                except http_errors as e:
                    # HTTP错误（400、500等），不重试
                    status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'unknown'
                    logger.warning(f"图片下载HTTP错误，不重试: {image_url} - 状态码: {status_code}")
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
        压缩图片到指定尺寸
        
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
            
            # 调整大小（保持宽高比）
            width = self.thumbnail_size['width']
            height = self.thumbnail_size['height']
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            
            # 创建新的白色背景图像
            background = Image.new('RGB', (width, height), (255,255,255))
            
            # 将图片居中粘贴到背景上
            x = (width - img.width) // 2
            y = (height - img.height) // 2
            background.paste(img, (x, y))
            
            # 保存为JPEG格式
            output = io.BytesIO()
            background.save(output, format='JPEG', quality=85, optimize=True)
            compressed_data = output.getvalue()
            
            logger.debug(f"图片压缩: {len(image_data)} -> {len(compressed_data)} bytes")
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