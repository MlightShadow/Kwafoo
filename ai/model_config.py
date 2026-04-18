"""
模型适配器配置文件

定义不同模型的适配规则和特性
"""

# 推理模型列表
# 这些模型通常支持推理模式，返回的内容可能包含推理过程
REASONING_MODELS = [
    'google/gemma',
    'deepseek',
    'qwen',
    'llama-3.1',
    'mistral-large',
    'claude-3.5',
    'gpt-4o',
    'gpt-4-turbo',
    'yi',
    'baichuan2',
    'internlm',
]

# 标准模型列表
# 这些模型通常直接返回结果，不包含推理过程
STANDARD_MODELS = [
    'nvidia/nemotron',
    'llama-3',
    'llama-2',
    'mistral',
    'gpt-3.5',
    'gpt-4',
    'qwen-7b',
    'qwen-14b',
    'chatglm',
    'baichuan',
    'falcon',
    'mpt',
]

# 模型特性映射
# 定义不同模型的特殊处理需求
MODEL_FEATURES = {
    # NVIDIA 模型特性
    'nvidia': {
        'supports_reasoning': False,
        'response_format': 'standard',
        'max_context': 4096,
        'preferred_temperature': 0.7,
    },
    
    # Gemma 模型特性
    'gemma': {
        'supports_reasoning': True,
        'response_format': 'mixed',
        'max_context': 8192,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    },
    
    # DeepSeek 模型特性
    'deepseek': {
        'supports_reasoning': True,
        'response_format': 'mixed',
        'max_context': 16384,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    },
    
    # Qwen 模型特性
    'qwen': {
        'supports_reasoning': True,
        'response_format': 'mixed',
        'max_context': 32768,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    },
    
    # GPT 模型特性
    'gpt-3.5': {
        'supports_reasoning': False,
        'response_format': 'standard',
        'max_context': 16384,
        'preferred_temperature': 0.7,
    },
    
    'gpt-4': {
        'supports_reasoning': False,
        'response_format': 'standard',
        'max_context': 8192,
        'preferred_temperature': 0.7,
    },
    
    'gpt-4o': {
        'supports_reasoning': True,
        'response_format': 'mixed',
        'max_context': 128000,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    },
    
    # Claude 模型特性
    'claude-3.5': {
        'supports_reasoning': True,
        'response_format': 'mixed',
        'max_context': 200000,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    },
    
    # LLaMA 模型特性
    'llama-3': {
        'supports_reasoning': False,
        'response_format': 'standard',
        'max_context': 8192,
        'preferred_temperature': 0.7,
    },
    
    'llama-3.1': {
        'supports_reasoning': True,
        'response_format': 'mixed',
        'max_context': 128000,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    },
    
    # Mistral 模型特性
    'mistral': {
        'supports_reasoning': False,
        'response_format': 'standard',
        'max_context': 8192,
        'preferred_temperature': 0.7,
    },
    
    'mistral-large': {
        'supports_reasoning': True,
        'response_format': 'mixed',
        'max_context': 32768,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    },
}

# 响应格式类型
RESPONSE_FORMATS = {
    'standard': '标准格式，直接返回结果',
    'mixed': '混合格式，可能包含推理过程',
    'reasoning_only': '仅推理格式',
}

# 获取模型特性
def get_model_features(model_name: str) -> dict:
    """
    获取指定模型的特性
    
    Args:
        model_name: 模型名称
        
    Returns:
        模型特性字典，如果模型未定义返回默认特性
    """
    model_name_lower = model_name.lower()
    
    # 查找匹配的模型
    for pattern, features in MODEL_FEATURES.items():
        if pattern in model_name_lower:
            return features
    
    # 默认特性
    return {
        'supports_reasoning': True,  # 默认假设支持推理
        'response_format': 'mixed',
        'max_context': 8192,
        'preferred_temperature': 0.7,
        'reasoning_markers': ['分析', '评估', '比对', '确定', '选择', '执行', '自我检查', '步骤', '考虑', '计划'],
    }

# 检查是否是推理模型
def is_reasoning_model(model_name: str) -> bool:
    """
    检查指定模型是否是推理模型
    
    Args:
        model_name: 模型名称
        
    Returns:
        是否是推理模型
    """
    model_name_lower = model_name.lower()
    
    # 检查推理模型列表
    for reasoning_model in REASONING_MODELS:
        if reasoning_model in model_name_lower:
            return True
    
    # 检查模型特性
    features = get_model_features(model_name)
    return features.get('supports_reasoning', False)

# 注册新模型
def register_model(model_pattern: str, features: dict, model_type: str = 'reasoning'):
    """
    注册新模型及其特性
    
    Args:
        model_pattern: 模型名称模式（支持部分匹配）
        features: 模型特性字典
        model_type: 模型类型 ('reasoning' 或 'standard')
    """
    MODEL_FEATURES[model_pattern] = features
    
    if model_type == 'reasoning' and model_pattern not in REASONING_MODELS:
        REASONING_MODELS.append(model_pattern)
    elif model_type == 'standard' and model_pattern not in STANDARD_MODELS:
        STANDARD_MODELS.append(model_pattern)