# 环境变量配置故障排除指南

## 问题描述

### 症状
修改 `.env` 文件后，配置没有生效，系统仍然使用 `config.toml` 中的默认值。

### 示例场景
```bash
# 在 .env 文件中设置
AI_BASE_URL=http://192.168.101.104:1234
AI_MODEL=google/gemma-4-e4b

# 但系统仍然使用 config.toml 中的默认值
# AI_BASE_URL: http://localhost:1234
# AI_MODEL: nvidia/nemotron-3-nano-4b
```

## 根本原因

### 1. python-dotenv 包未安装
**主要原因**：虽然 `requirements.txt` 中包含 `python-dotenv>=1.0.0`，但实际环境中没有安装。

**可能原因**：
- 使用不同的 Python 环境或虚拟环境
- `pip install -r requirements.txt` 执行失败或被中断
- 手动安装依赖时遗漏了这个包
- 从其他方式克隆项目而没有正确安装依赖

### 2. 静默失败机制
**代码结构**：
```python
# utils/helpers.py
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 静默忽略错误
```

**问题**：
- 错误被静默忽略，系统仍然能正常运行
- `.env` 文件没有被加载，但没有任何错误提示
- 开发者难以发现问题

## 解决方法

### 方法一：检查并安装 python-dotenv

#### 1. 检查是否安装
```bash
pip show python-dotenv
```

**预期输出**：
```
Name: python-dotenv
Version: 1.2.2
...
```

**如果没有安装**：
```
WARNING: Package(s) not found: python-dotenv
```

#### 2. 安装 python-dotenv
```bash
# 单独安装
pip install python-dotenv

# 或重新安装所有依赖
pip install -r requirements.txt
```

#### 3. 验证安装
```bash
# 检查安装是否成功
python -c "from dotenv import load_dotenv; print('python-dotenv installed successfully')"
```

### 方法二：重新安装所有依赖

```bash
# 卸载所有依赖（可选）
pip freeze | xargs pip uninstall -y

# 重新安装
pip install -r requirements.txt
```

### 方法三：使用虚拟环境（推荐）

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动程序
python main.py
```

## 验证配置是否生效

### 方法一：使用 Python 脚本验证

```bash
python -c "from utils.helpers import config; print('AI_BASE_URL:', config.get('ai.base_url'))"
```

**预期输出**（如果 .env 配置生效）：
```
AI_BASE_URL: http://192.168.101.104:1234
```

**输出示例**（如果 .env 配置未生效）：
```
AI_BASE_URL: http://localhost:1234
```

### 方法二：检查系统日志

```bash
# 查看日志文件
tail -f data/logs/kwafoo.log
```

**正常情况**：
```
2026-04-18 21:30:21 - kwafoo - INFO - 配置文件加载成功: config.toml
```

**注意**：即使 `.env` 未加载，也不会有错误提示，这是静默失败的特点。

### 方法三：通过 API 检查

```bash
# 获取当前配置
curl http://localhost:8000/api/config
```

检查返回的配置是否与 `.env` 文件中的设置一致。

## 预防措施

### 1. 使用虚拟环境
虚拟环境可以避免依赖冲突，确保环境一致性。

### 2. 完整安装依赖
```bash
# 始终使用完整安装命令
pip install -r requirements.txt

# 检查安装结果
pip list | grep dotenv
```

### 3. 添加启动检查
在 `start.bat` 或启动脚本中添加依赖检查：

```batch
@echo off
echo 检查依赖...
python -c "from dotenv import load_dotenv" 2>nul
if errorlevel 1 (
    echo 错误: python-dotenv 未安装
    echo 正在安装 python-dotenv...
    pip install python-dotenv
)
echo 依赖检查完成
```

### 4. 改进错误处理
修改 `utils/helpers.py`，添加日志记录：

```python
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("环境变量文件 .env 加载成功")
except ImportError:
    logger.warning("python-dotenv 未安装，.env 文件将被忽略")
    logger.warning("请运行: pip install python-dotenv")
```

## 常见问题

### Q1: 为什么 requirements.txt 中有 python-dotenv 但没有安装？

**A**: 可能的原因：
- 安装过程中网络问题导致部分包未安装
- 使用了不同的 Python 环境
- 安装命令被中断
- 使用了 `--no-deps` 参数跳过依赖

### Q2: 系统为什么能正常运行？

**A**: 因为 `python-dotenv` 的导入错误被静默捕获，系统会继续使用 `config.toml` 中的默认配置。

### Q3: 如何避免这个问题？

**A**: 
1. 使用虚拟环境
2. 完整安装依赖并验证
3. 在启动脚本中添加依赖检查
4. 改进错误处理，添加日志记录

### Q4: .env 文件的优先级是什么？

**A**: 配置优先级从高到低：
1. `.env` 文件（环境变量）
2. `config.toml` 文件（默认配置）

## 相关文档

- [README.md](../README.md) - 项目主文档
- [configuration.md](configuration.md) - 配置文件详解
- [troubleshooting.md](troubleshooting.md) - 通用故障排除

## 更新日志

- 2026-04-18: 初始版本，记录环境变量配置问题