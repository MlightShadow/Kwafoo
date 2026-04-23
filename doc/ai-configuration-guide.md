# AI配置必填项指南

## 概述

Kwafoo新闻聚合系统使用AI进行新闻分类、摘要生成和评论生成。为了正常使用这些功能，用户必须正确配置AI相关的参数。

## 必填配置项

在 `config.toml` 文件的 `[ai]` 配置节中，以下两个参数是**必填项**：

### 1. AI服务地址 (base_url)

**配置项：** `ai.base_url`  
**必填：** 是  
**默认值：** 无（必须由用户填写）

**说明：**
- AI服务的访问地址
- 支持本地AI服务（如Ollama、LM Studio等）
- 支持云端AI服务（如OpenAI、Anthropic等）

**示例：**
```toml
[ai]
base_url = "http://localhost:1234"  # 本地AI服务
# 或者
base_url = "https://api.openai.com/v1"  # OpenAI服务
# 或者
base_url = "https://api.anthropic.com"  # Anthropic服务
```

**注意事项：**
- 地址必须以 `http://` 或 `https://` 开头
- 本地服务通常运行在 `localhost` 或 `127.0.0.1`
- 确保AI服务正在运行并可访问
- 如果使用代理，请确保代理配置正确

### 2. AI模型名称 (model)

**配置项：** `ai.model`  
**必填：** 是  
**默认值：** 无（必须由用户填写）

**说明：**
- 要使用的AI模型名称
- 模型名称必须与AI服务支持的模型匹配
- 不同AI服务支持的模型不同

**示例：**
```toml
[ai]
# Google Gemma模型
model = "google/gemma-4-e4b"

# NVIDIA Nemotron模型
model = "nvidia/nemotron-3-nano-4b"

# OpenAI模型
model = "gpt-4"
model = "gpt-3.5-turbo"

# Anthropic模型
model = "claude-3-opus-20240229"

# Meta LLaMA模型
model = "llama-3-8b"

# Mistral模型
model = "mistral-7b"
```

**注意事项：**
- 模型名称必须准确，区分大小写
- 确保AI服务已下载或支持该模型
- 不同模型有不同的性能和成本特点
- 建议根据硬件配置选择合适的模型

## 可选配置项

以下配置项有默认值，用户可以根据需要调整：

### API密钥 (api_key)

```toml
api_key = ""  # API密钥（某些服务需要）
```

**说明：**
- 某些云端AI服务需要API密钥
- 本地AI服务通常不需要API密钥
- 请妥善保管API密钥，不要泄露

### 最大Token数 (max_tokens)

```toml
max_tokens = 4096  # 最大输出token数
```

**说明：**
- 控制AI输出的最大长度
- 默认值为4096
- 增加此值可以获得更长的输出，但会增加成本和延迟

### 温度参数 (temperature)

```toml
temperature = 0.7  # 温度参数（0-1，越高越随机）
```

**说明：**
- 控制AI输出的随机性
- 范围：0.0-2.0
- 较低的值（0.1-0.3）：输出更确定、一致
- 较高的值（0.7-1.0）：输出更有创意、多样
- 默认值为0.7

### 超时时间 (timeout)

```toml
timeout = 120  # 超时时间（秒）
```

**说明：**
- AI调用的超时时间
- 默认值为120秒
- 如果AI响应较慢，可以适当增加此值

## 配置验证

系统会在启动时检查AI配置，如果缺少必填项，会显示错误信息并退出：

### 错误示例1：缺少AI服务地址

```
2026-04-23 10:00:00 - kwafoo - ERROR - AI服务地址未配置！请在config.toml中设置ai.base_url
```

**解决方法：**
在 `config.toml` 中添加：
```toml
[ai]
base_url = "http://localhost:1234"
```

### 错误示例2：缺少AI模型

```
2026-04-23 10:00:00 - kwafoo - ERROR - AI模型未配置！请在config.toml中设置ai.model
2026-04-23 10:00:00 - kwafoo - ERROR - 例如：model = "google/gemma-4-e4b" 或 model = "nvidia/nemotron-3-nano-4b"
```

**解决方法：**
在 `config.toml` 中添加：
```toml
[ai]
model = "google/gemma-4-e4b"
```

### 配置检查通过

如果配置正确，会显示：
```
2026-04-23 10:00:00 - kwafoo - INFO - 检查AI配置...
2026-04-23 10:00:00 - kwafoo - INFO - AI配置检查通过：base_url=http://localhost:1234, model=google/gemma-4-e4b
```

## 常见AI服务配置

### 1. Ollama（本地）

```toml
[ai]
base_url = "http://localhost:11434"
model = "llama-3-8b"
```

**说明：**
- Ollama默认端口：11434
- 支持多种开源模型
- 下载模型：`ollama pull llama-3-8b`

### 2. LM Studio（本地）

```toml
[ai]
base_url = "http://localhost:1234"
model = "google/gemma-4-e4b"
```

**说明：**
- LM Studio默认端口：1234
- 支持多种模型格式
- 需要在LM Studio中下载并启动模型

### 3. OpenAI（云端）

```toml
[ai]
base_url = "https://api.openai.com/v1"
model = "gpt-4"
api_key = "sk-..."  # 从OpenAI官网获取
```

**说明：**
- 需要OpenAI API密钥
- 按使用量计费
- 支持多种GPT模型

### 4. Anthropic（云端）

```toml
[ai]
base_url = "https://api.anthropic.com"
model = "claude-3-opus-20240229"
api_key = "sk-ant-..."  # 从Anthropic官网获取
```

**说明：**
- 需要Anthropic API密钥
- 按使用量计费
- Claude系列模型性能优秀

### 5. NVIDIA NIM（云端）

```toml
[ai]
base_url = "https://integrate.api.nvidia.com/v1"
model = "nvidia/nemotron-3-nano-4b"
api_key = "nvapi-..."  # 从NVIDIA官网获取
```

**说明：**
- 需要NVIDIA API密钥
- NVIDIA提供免费额度
- Nemotron模型性能优秀

## 模型选择建议

### 根据硬件配置选择

**低端配置（4GB显存）：**
- `google/gemma-4-e4b`（4B参数）
- `nvidia/nemotron-3-nano-4b`（4B参数）
- `llama-3-8b`（8B参数，量化版）

**中端配置（8GB显存）：**
- `llama-3-8b`（8B参数）
- `mistral-7b`（7B参数）
- `phi-3-mini`（3.8B参数）

**高端配置（16GB+显存）：**
- `llama-3-70b`（70B参数，量化版）
- `claude-3-opus-20240229`（云端API）
- `gpt-4`（云端API）

### 根据用途选择

**新闻分类：**
- 需要理解能力
- 推荐模型：`llama-3-8b`、`gemma-4-e4b`

**摘要生成：**
- 需要总结能力
- 推荐模型：`mistral-7b`、`phi-3-mini`

**评论生成：**
- 需要创造能力
- 推荐模型：`gpt-4`、`claude-3-opus-20240229`

## 故障排除

### 问题1：启动时报错"AI服务地址未配置"

**原因：** `config.toml` 中缺少 `ai.base_url` 配置

**解决：**
```toml
[ai]
base_url = "http://localhost:1234"
```

### 问题2：启动时报错"AI模型未配置"

**原因：** `config.toml` 中缺少 `ai.model` 配置

**解决：**
```toml
[ai]
model = "google/gemma-4-e4b"
```

### 问题3：AI调用失败

**可能原因：**
1. AI服务未启动
2. 地址配置错误
3. 模型未下载
4. 网络连接问题

**解决方法：**
1. 确认AI服务正在运行
2. 检查地址和端口是否正确
3. 下载或安装对应的模型
4. 检查网络连接和代理设置

### 问题4：AI响应很慢

**可能原因：**
1. 模型太大
2. 硬件性能不足
3. 网络延迟

**解决方法：**
1. 使用更小的模型
2. 升级硬件配置
3. 使用本地服务减少网络延迟

## 配置更新

修改配置后需要重启服务器：

```bash
# 停止服务器
# 在服务器终端按 Ctrl+C

# 重新启动服务器
python main.py
```

系统会在启动时检查AI配置，确保配置正确。

## 安全建议

1. **API密钥安全**
   - 不要将API密钥提交到版本控制系统
   - 定期更换API密钥
   - 监控API使用情况

2. **本地服务安全**
   - 不要将本地AI服务暴露到公网
   - 使用防火墙限制访问
   - 定期更新AI服务

3. **配置文件安全**
   - 设置合适的文件权限
   - 不要分享包含敏感信息的配置文件
   - 定期检查配置文件

## 总结

正确配置AI参数是使用Kwafoo新闻聚合系统的前提。请确保：

1. ✅ 配置了 `ai.base_url`（AI服务地址）
2. ✅ 配置了 `ai.model`（AI模型名称）
3. ✅ AI服务正在运行并可访问
4. ✅ 模型已下载或安装
5. ✅ 网络连接正常（如使用云端服务）

完成以上配置后，系统即可正常使用AI功能进行新闻分类、摘要生成和评论生成。