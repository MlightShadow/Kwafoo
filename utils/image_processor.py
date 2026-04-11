import requests
import io
from PIL import Image
from typing import Optional, Tuple
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
    
    def fetch_and_process_image(self, image_url: str) -> Optional[Tuple[str, bytes]]:
        """
        下载并处理图片
        
        Args:
            image_url: 图片URL
            
        Returns:
            (image_url, image_data) 或 None
        """
        if not self.enable_fetch or not image_url:
            return None
        
        try:
            # 下载图片（根据配置决定是否使用代理）
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
                return None
            
            # 检查图片格式
            content_type = response.headers.get('content-type', '')
            if not self._is_supported_format(content_type):
                logger.warning(f"不支持的图片格式: {content_type}")
                return None
            
            # 读取图片数据
            image_data = response.content
            
            # 压缩图片
            compressed_data = self._compress_image(image_data)
            
            if compressed_data:
                logger.info(f"图片处理成功: {image_url} -> {len(compressed_data)} bytes")
                return (image_url, compressed_data)
            
        except requests.RequestException as e:
            logger.error(f"下载图片失败: {image_url} - {e}")
        except Exception as e:
            logger.error(f"处理图片失败: {image_url} - {e}")
        
        return None
    
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
            background = Image.new('RGB', (width, height), (255, 255, 255))
            
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


# 创建全局实例
image_processor = ImageProcessor()