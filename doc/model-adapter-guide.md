# 模型适配器系统使用指南

## 概述

模型适配器系统为不同的AI模型提供统一的接口和响应解析能力，使系统能够适配多种不同的AI模型。

## 架构设计

### 核心组件

1. **模型适配器基类** (`ModelAdapter`)
   - 定义了所有适配器必须实现的接口
   - 提供通用的响应解析方法

2. **标准模型适配器** (`StandardModelAdapter`)
   - 适用于直接返回结果的模型
   - 如：NVIDIA Nemotron、LLaMA-3、Mistral等

3. **推理模型适配器** (`ReasoningModelAdapter`)
   - 适用于支持推理模式的模型
   - 能够从混合的推理过程中提取最终结果
   - 如：Gemma-4、DeepSeek、Qwen、GPT-4o等

4. **模型适配器工厂** (`ModelAdapterFactory`)
   - 根据模型名称自动创建合适的适配器
   - 支持动态注册新模型

5. **模型配置** (`model_config.py`)
   - 集中管理所有模型的特性
   - 定义推理标记、响应格式等

## 使用方法

### 基本使用

系统会自动根据配置的模型名称选择合适的适配器：

```python
from ai.model_adapter import ModelAdapterFactory

# 自动创建适配器
adapter = ModelAdapterFactory.create_adapter('google/gemma-4-e4b')

# 提取分类结果
categories = adapter.extract_classification(
    response_data, 
    available_categories=['科技', '财经', '体育'],
    default_category='未分类'
)

# 提取摘要结果
summary = adapter.extract_summary(response_data)
```

### 在分类器中使用

```python
from ai.classifier import AIClassifier

classifier = AIClassifier()
# 系统会自动创建合适的模型适配器
categories = classifier.classify(title, description)
```

### 在摘要生成器中使用

```python
from ai.summarizer import AISummarizer

summarizer = AISummarizer()
# 系统会自动创建合适的模型适配器
summary = summarizer.generate_summary(content)
```

## 支持的模型

### 推理模型

这些模型支持推理模式，返回的内容可能包含推理过程：

- `google/gemma` 系列
- `deepseek` 系列
- `qwen` 系列
- `llama-3.1` 系列
- `mistral-large` 系列
- `claude-3.5` 系列
- `gpt-4o` 系列
- `gpt-4-turbo` 系列
- `yi` 系列
- `baichuan2` 系列
- `internlm` 系列

### 标准模型

这些模型直接返回结果，不包含推理过程：

- `nvidia/nemotron` 系列
- `llama-3` 系列
- `llama-2` 系列
- `mistral` 系列
- `gpt-3.5` 系列
- `gpt-4` 系列
- `qwen-7b` 系列
- `qwen-14b` 系列
- `chatglm` 系列
- `baichuan` 系列
- `falcon` 系列
- `mpt` 系列

## 注册新模型

### 注册推理模型

```python
from ai.model_adapter import ModelAdapterFactory

# 注册新的推理模型
ModelAdapterFactory.register_reasoning_model('new-reasoning-model')
```

### 注册标准模型

```python
from ai.model_adapter import ModelAdapterFactory

# 注册新的标准模型
ModelAdapterFactory.register_standard_model('new-standard-model')
```

### 在配置文件中注册

编辑 `ai/model_config.py`：

```python
# 添加到推理模型列表
REASONING_MODELS.append('your-model-name')

# 添加模型特性
MODEL_FEATURES['your-model-name'] = {
    'supports_reasoning': True,
    'response_format': 'mixed',
    'max_context': 8192,
    'preferred_temperature': 0.7,
    'reasoning_markers': ['分析', '评估', '比对', '确定', '选择'],
}
```

## 模型特性配置

每个模型可以配置以下特性：

```python
{
    'supports_reasoning': bool,      # 是否支持推理模式
    'response_format': str,          # 响应格式: 'standard', 'mixed', 'reasoning_only'
    'max_context': int,              # 最大上下文长度
    'preferred_temperature': float,    # 推荐温度参数
    'reasoning_markers': list,       # 推理标记列表
}
```

## 响应格式类型

### 标准格式 (standard)
- 直接返回最终结果
- 不包含推理过程
- 示例：`"科技"`

### 混合格式 (mixed)
- 包含推理过程和最终结果
- 需要从混合内容中提取结果
- 示例：
  ```
  分析新闻内容...
  确定分类：科技
  ```

### 仅推理格式 (reasoning_only)
- 只返回推理过程
- 最终结果需要从推理中推断
- 较少见

## 自定义适配器

如果需要创建自定义适配器：

```python
from ai.model_adapter import ModelAdapter

class CustomModelAdapter(ModelAdapter):
    def extract_classification(self, response_data, available_categories, default_category):
        # 实现自定义分类提取逻辑
        pass
    
    def extract_summary(self, response_data):
        # 实现自定义摘要提取逻辑
        pass
    
    def supports_reasoning(self):
        # 返回是否支持推理模式
        return True/False
```

## 配置示例

### .env 配置

```env
# 使用推理模型
AI_MODEL=google/gemma-4-e4b

# 使用标准模型
# AI_MODEL=nvidia/nemotron-3-nano-4b

# 启用推理模式（仅对支持推理的模型有效）
AI_ENABLE_CLASSIFIER_REASONING=false
AI_ENABLE_SUMMARIZER_REASONING=false
```

### config.toml 配置

```toml
[ai]
model = "google/gemma-4-e4b"
base_url = "http://localhost:1234"
max_tokens = 4096
temperature = 0.7

[ai]
enable_classifier_reasoning = false
enable_summarizer_reasoning = false
```

## 故障排除

### 模型识别错误

如果系统错误识别了模型类型：

1. 检查模型名称是否正确
2. 在 `model_config.py` 中注册模型
3. 使用 `ModelAdapterFactory.register_*_model()` 动态注册

### 分类/摘要提取失败

如果提取失败：

1. 检查日志中的原始响应
2. 确认模型的响应格式
3. 调整 `reasoning_markers` 配置
4. 考虑创建自定义适配器

### 性能问题

如果性能不佳：

1. 检查 `max_context` 设置
2. 调整 `temperature` 参数
3. 考虑使用更简单的适配器

## 最佳实践

1. **模型选择**
   - 根据任务复杂度选择合适的模型
   - 简单任务使用标准模型
   - 复杂任务使用推理模型

2. **配置优化**
   - 根据模型特性调整参数
   - 测试不同的温度设置
   - 监控响应质量

3. **错误处理**
   - 实现适当的错误处理
   - 记录详细的日志
   - 提供降级方案

4. **性能监控**
   - 监控响应时间
   - 跟踪成功率
   - 定期评估模型性能

## 技术细节

### 适配器选择逻辑

```
1. 检查模型名称
2. 在配置中查找匹配的模式
3. 根据模型特性创建适配器
4. 如果未找到，使用推理模型适配器（更安全）
```

### 响应解析流程

```
1. 获取原始响应数据
2. 检查响应格式
3. 应用相应的解析策略
4. 验证提取结果
5. 返回处理后的结果
```

## 扩展性

系统设计具有良好的扩展性：

- **水平扩展**：可以轻松添加新的适配器
- **垂直扩展**：可以增强现有适配器的功能
- **配置扩展**：可以添加新的模型特性
- **动态扩展**：支持运行时注册新模型

## 维护指南

### 添加新模型支持

1. 在 `model_config.py` 中添加模型特性
2. 测试适配器选择是否正确
3. 验证响应解析是否正常
4. 更新文档

### 更新现有模型

1. 修改模型特性配置
2. 测试兼容性
3. 更新相关文档
4. 通知用户变更

### 调试适配器

1. 启用详细日志
2. 检查原始响应
3. 验证解析逻辑
4. 修复问题

## 相关文件

- `ai/model_adapter.py` - 适配器实现
- `ai/model_config.py` - 模型配置
- `ai/classifier.py` - 分类器（使用适配器）
- `ai/summarizer.py` - 摘要生成器（使用适配器）
- `main.py` - 主程序（初始化适配器）

## 联系与支持

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发起 Pull Request
- 参与讨论