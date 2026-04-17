# 图片处理模块设计

## 模块概述

图片处理模块负责新闻图片的自动下载、压缩和存储。模块支持多种存储模式（文件系统、数据库），提供完善的错误处理和重试机制，确保图片处理的稳定性和可靠性。

## 核心功能

### 1. 图片下载

**技术选型：**
- 使用`requests`库下载图片
- 支持代理配置
- 支持重试机制（指数退避）
- 支持超时控制

**下载流程：**
1. 检查图片URL是否有效
2. 检查图片是否已缓存
3. 下载图片（带重试机制）
4. 验证图片格式和大小
5. 返回图片数据

**重试策略：**
- 最大重试次数：3次
- 超时错误：指数退避（2秒、4秒）
- HTTP错误：不重试（400、500等）
- 其他错误：指数退避

**配置参数：**
```toml
[image]
enable_fetch = true
max_image_size = 5242880  # 5MB
supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'gif']

[network]
enable_proxy = false
proxy_url = "http://proxy.example.com:8080"
```

### 2. 图片压缩

**技术选型：**
- 使用`Pillow`（PIL）库处理图片
- 支持多种图片格式
- 保持宽高比
- 高质量压缩

**压缩策略：**
1. 转换为RGB模式（如果需要）
2. 调整大小到指定尺寸（保持宽高比）
3. 居中粘贴到白色背景上
4. 保存为JPEG格式（quality=85, optimize=True）

**压缩效果：**
- 原始图片：可能几MB
- 压缩后：通常几十KB
- 尺寸：默认256x256像素

**配置参数：**
```toml
[image]
thumbnail_size = {width = 256, height = 256}
```

### 3. 图片存储

**存储模式：**

**模式1：文件系统（推荐）**
- 存储路径：`data/images/`
- 文件名：URL的MD5哈希值
- 访问URL：`/api/images/{filename}`
- 优点：简单、高效、易于备份
- 缺点：需要管理文件权限

**模式2：数据库**
- 存储位置：news表的image_data字段（BLOB）
- 数据格式：Base64编码
- 访问方式：通过API返回
- 优点：数据集中管理
- 缺点：数据库体积增大、性能下降

**配置参数：**
```toml
[image]
storage_mode = 'filesystem'  # 'filesystem' or 'database'
storage_path = 'data/images'
```

**文件命名：**
```python
def generate_filename(self, image_url: str) -> str:
    """根据URL生成唯一的文件名"""
    url_hash = hashlib.md5(image_url.encode('utf-8')).hexdigest()
    return f"{url_hash}.jpg"
```

### 4. 图片清理

**清理策略：**
- 定期清理旧的图片文件
- 基于文件创建时间判断
- 可配置保留天数

**清理流程：**
1. 遍历存储目录
2. 检查文件创建时间
3. 删除超过保留天数的文件
4. 记录清理日志

**配置参数：**
```python
cleanup_old_images(max_age_days=30)
```

## 数据库集成

### news表字段

```sql
CREATE TABLE news (
    ...
    image_url TEXT,           -- 原始图片URL
    image_data BLOB,          -- 压缩后的图片数据（Base64编码）
    ...
);
```

### 存储流程

1. **抓取新闻**：获取image_url
2. **下载图片**：调用`fetch_and_process_image()`
3. **压缩图片**：调整大小和格式
4. **存储图片**：
   - 文件系统模式：保存到`data/images/`目录
   - 数据库模式：存入news表的image_data字段
5. **更新数据库**：更新image_url和image_data字段

### 访问流程

1. **前端请求**：`GET /api/images/{filename}`
2. **后端处理**：
   - 文件系统模式：从`data/images/`读取文件
   - 数据库模式：从news表查询image_data
3. **返回图片**：返回图片数据

## 错误处理

### 下载错误
- 超时错误：重试3次（指数退避）
- HTTP错误：不重试（400、500等）
- 网络错误：重试3次（指数退避）
- 格式不支持：跳过该图片

### 压缩错误
- 图片格式不支持：跳过该图片
- 图片损坏：跳过该图片
- 压缩失败：记录日志，不影响新闻存储

### 存储错误
- 磁盘空间不足：记录日志，跳过该图片
- 权限错误：记录日志，跳过该图片
- 文件已存在：直接使用缓存

## 性能优化

### 下载优化
- 使用Session复用连接
- 支持代理配置
- 超时控制（10秒）
- 流式下载（避免内存溢出）

### 压缩优化
- 使用高质量压缩算法（LANCZOS）
- 优化JPEG参数（quality=85, optimize=True）
- 限制图片尺寸（256x256）

### 存储优化
- 文件系统模式：使用哈希文件名，避免重复
- 数据库模式：使用BLOB存储，Base64编码
- 缓存机制：已下载的图片直接使用缓存

### 清理优化
- 定期清理旧图片（默认30天）
- 避免磁盘空间不足
- 保持系统性能

## 配置说明

### 图片配置
```toml
[image]
enable_fetch = true                    # 是否启用图片下载
thumbnail_size = {width = 256, height = 256}  # 缩略图尺寸
default_image = ""                      # 默认图片URL
supported_formats = ['jpg', 'jpeg', 'png', 'webp', 'gif']  # 支持的格式
max_image_size = 5242880               # 最大图片大小（5MB）
storage_mode = 'filesystem'             # 存储模式：'filesystem' or 'database'
storage_path = 'data/images'           # 文件系统存储路径
```

### 网络配置
```toml
[network]
enable_proxy = false                    # 是否启用代理
proxy_url = "http://proxy.example.com:8080"  # 代理URL
```

## API接口

### 获取图片
```
GET /api/images/{filename}
```

**响应：**
- 文件系统模式：返回图片文件
- 数据库模式：返回Base64编码的图片数据

### 清理旧图片
```
POST /api/images/cleanup
```

**请求参数：**
```json
{
  "max_age_days": 30
}
```

**响应：**
```json
{
  "success": true,
  "message": "已清理100个旧图片文件"
}
```

## 代码引用

### 图片处理器
[utils/image_processor.py](../../utils/image_processor.py) - 图片处理器实现

### 数据库管理器
[database/manager.py](../../database/manager.py) - 数据库管理器（包含图片存储）

### 图片API
[web/api/news_api.py](../../web/api/news_api.py) - 新闻API（包含图片接口）

## 依赖库

- `requests` - HTTP请求
- `Pillow` - 图片处理
- `hashlib` - 哈希计算

## 注意事项

1. **版权问题**：注意图片的版权，避免侵权
2. **存储空间**：定期清理旧图片，避免磁盘空间不足
3. **性能影响**：大量图片下载可能影响系统性能
4. **网络限制**：注意网络带宽和代理配置
5. **格式兼容**：确保支持的图片格式与实际需求匹配
6. **错误处理**：完善的错误处理，避免图片下载失败影响新闻存储
7. **缓存机制**：使用缓存避免重复下载
8. **安全性**：验证图片URL，避免恶意链接