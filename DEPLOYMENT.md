# Kwafoo 新闻聚合系统 - 打包部署说明

## 打包说明

### 前置要求
- Python 3.8+
- 网络连接（用于下载依赖）

### 打包步骤

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **运行打包脚本**
   ```bash
   # Windows
   build.bat
   
   # Linux/Mac
   chmod +x build.sh
   ./build.sh
   ```

3. **打包结果**
   - 可执行文件位于 `dist/kwafoo/kwafoo.exe` (Windows)
   - 包含所有必要的依赖和资源文件

## 部署说明

### 部署步骤

1. **复制整个文件夹**
   - 将 `dist/kwafoo` 整个文件夹复制到目标位置
   - 确保文件夹结构完整

2. **启动程序**
   ```bash
   # Windows
   kwafoo.exe
   
   # Linux/Mac
   ./kwafoo
   ```

3. **访问Web界面**
   - 打开浏览器访问: `http://localhost:8000`
   - 如果修改了端口，使用相应的地址

### 文件结构

```
kwafoo/
├── kwafoo.exe              # 主程序
├── config.toml             # 配置文件（可修改）
├── config.toml.example     # 配置示例
└── data/                   # 数据目录（运行时生成）
    ├── kwafoo.db            # 数据库文件
    └── logs/               # 日志文件
        └── kwafoo.log
```

## 配置说明

### 通过文件修改配置

直接编辑 `config.toml` 文件：

```toml
[server]
host = "0.0.0.0"
port = 8000

[scheduler]
fetch_interval = 1800  # 新闻抓取间隔（秒）
auto_fetch = false     # 自动抓取

[ai]
base_url = "http://localhost:1234"
model = "nvidia/nemotron-3-nano-4b"
enable_summary = true
```

### 通过Web界面修改配置

1. 访问系统设置页面
2. 修改配置项
3. 保存更改（会自动更新到config.toml）

## 常见问题

### 1. 端口被占用
- 修改 `config.toml` 中的 `server.port` 值
- 重启程序

### 2. 数据库错误
- 删除 `data/kwafoo.db` 文件
- 重启程序（会自动创建新数据库）

### 3. 日志文件过大
- 修改 `config.toml` 中的 `logging.max_size` 值
- 或手动删除 `data/logs/` 下的旧日志文件

### 4. 程序无法启动
- 检查是否有防火墙阻止
- 查看日志文件 `data/logs/kwafoo.log`
- 确保端口未被占用

## 更新升级

### 方法1：替换程序
1. 停止当前运行的程序
2. 备份 `config.toml` 和 `data/` 目录
3. 用新版本的 `kwafoo.exe` 替换旧版本
4. 恢复备份的配置和数据
5. 启动新版本程序

### 方法2：重新打包
1. 更新源代码
2. 重新运行打包脚本
3. 部署新版本

## 系统要求

### 最低配置
- CPU: 双核处理器
- 内存: 2GB RAM
- 磁盘: 500MB 可用空间
- 网络: 宽带连接

### 推荐配置
- CPU: 四核处理器
- 内存: 4GB RAM
- 磁盘: 2GB 可用空间
- 网络: 稳定的宽带连接

## 技术支持

如遇到问题，请查看：
1. 日志文件: `data/logs/kwafoo.log`
2. 配置文件: `config.toml`
3. 系统文档: `doc/` 目录

## 许可证

请参考项目根目录的 LICENSE 文件。