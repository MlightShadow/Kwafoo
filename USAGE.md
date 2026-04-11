# Kwafoo 项目使用指南

## 快速开始

### 1. 一键启动
双击运行 `start.bat`，脚本会自动：
- 检查Python环境
- 检查并安装依赖
- 启动HTTP服务器（端口8000）
- 启动WebSocket服务器（端口8001）

### 2. 快速测试
双击运行 `test.bat`，脚本会自动测试：
- 健康检查
- 新闻统计
- 新闻列表
- 配置获取
- 搜索功能
- 分类查询
- 手动抓取
- 进度查询
- 配置更新

## 手动操作

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务器
```bash
python main.py
```

### 运行快速测试
```bash
python test_quick.py
```

### 运行完整测试（包含等待新闻抓取）
```bash
python test_auto.py
```

## 访问地址

- **Web界面**: http://localhost:8000
- **API接口**: http://localhost:8000/api
- **WebSocket**: ws://localhost:8001

## 主要API接口

### 基础接口
- `GET /api/health` - 健康检查
- `GET /api/progress` - 获取任务进度

### 新闻接口
- `GET /api/news` - 获取新闻列表
- `GET /api/news/stats` - 获取新闻统计
- `GET /api/news/search?q=关键词&limit=10` - 搜索新闻
- `GET /api/news/category?category=tech` - 按分类获取新闻
- `POST /api/news/clear` - 清空新闻

### 配置接口
- `GET /api/config` - 获取配置
- `POST /api/config` - 更新配置

### 任务接口
- `POST /api/fetch` - 手动触发新闻抓取

## 功能特性

### ✅ 已完成的功能
- WebSocket实时通信
- 前端Composables
- 配置验证器
- 全局错误处理
- 图片存储优化
- Vue + TypeScript前端
- 统一启动入口
- 打包发布方案

### 🔄 部分完成的功能
- 依赖版本管理（缺少Poetry）
- 测试覆盖（有基础测试）
- 日志增强（有基础日志）

### ❌ 待完成的功能
- API文档生成
- 性能监控
- 部署自动化

## 配置文件

主配置文件：`config.toml`

### 主要配置项
- `[server]` - 服务器配置（端口、地址）
- `[database]` - 数据库配置
- `[news_sources]` - 新闻源配置
- `[categories]` - 分类配置
- `[scheduler]` - 调度器配置
- `[ai]` - AI配置
- `[image]` - 图片配置

## 故障排除

### 服务器无法启动
1. 检查端口8000和8001是否被占用
2. 检查Python版本（需要3.10+）
3. 检查依赖是否完整安装

### 新闻抓取失败
1. 检查网络连接
2. 检查新闻源URL是否有效
3. 查看日志文件：`data/logs/kwafoo.log`

### 测试失败
1. 确保服务器正在运行
2. 检查防火墙设置
3. 查看测试脚本的错误信息

## 项目结构

```
Kwafoo/
├── main.py              # 主启动文件
├── config.toml          # 配置文件
├── requirements.txt      # Python依赖
├── start.bat           # 一键启动脚本
├── test.bat            # 快速测试脚本
├── test_quick.py       # 快速测试脚本
├── test_auto.py       # 完整测试脚本
├── database/          # 数据库模块
├── web/              # Web服务器
│   ├── api/          # API接口
│   ├── frontend/     # 前端代码
│   ├── server.py     # HTTP服务器
│   └── websocket.py  # WebSocket服务器
├── utils/            # 工具模块
├── fetcher/          # 新闻抓取
├── ai/              # AI处理
├── scheduler/        # 任务调度
└── data/            # 数据目录
    ├── kwafoo.db    # 数据库
    ├── images/      # 图片缓存
    └── logs/        # 日志文件
```

## 开发说明

### 添加新的API接口
1. 在 `web/api/` 下创建新的API文件
2. 在 `web/server.py` 中注册路由
3. 更新测试脚本

### 添加新的新闻源
1. 在 `config.toml` 的 `[news_sources]` 部分添加配置
2. 支持RSS、API和网页爬虫三种类型

### 修改前端
1. 前端代码在 `web/frontend/src/`
2. 使用Vue 3 + TypeScript
3. 组件化开发，使用Composables

## 技术栈

### 后端
- Python 3.10+
- SQLite
- websockets
- requests
- beautifulsoup4
- feedparser

### 前端
- Vue 3
- TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router

## 许可证

MIT License

## 联系方式

如有问题，请查看日志文件或提交Issue。