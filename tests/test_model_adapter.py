"""
模型适配器测试脚本

用于测试和验证模型适配器系统的功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.model_adapter import ModelAdapterFactory, StandardModelAdapter, ReasoningModelAdapter
from ai.model_config import get_model_features, is_reasoning_model, REASONING_MODELS, STANDARD_MODELS


def test_adapter_factory():
    """测试适配器工厂"""
    print("=" * 60)
    print("测试适配器工厂")
    print("=" * 60)
    
    # 测试推理模型
    reasoning_models = [
        'google/gemma-4-e4b',
        'deepseek-r1',
        'qwen-max',
        'llama-3.1-70b',
        'gpt-4o',
    ]
    
    print("\n推理模型测试:")
    for model in reasoning_models:
        adapter = ModelAdapterFactory.create_adapter(model)
        adapter_type = "推理模型适配器" if isinstance(adapter, ReasoningModelAdapter) else "标准模型适配器"
        print(f"  {model:30} -> {adapter_type}")
        assert isinstance(adapter, ReasoningModelAdapter), f"{model} 应该使用推理模型适配器"
    
    # 测试标准模型
    standard_models = [
        'nvidia/nemotron-3-nano-4b',
        'llama-3-8b',
        'mistral-7b',
        'gpt-3.5-turbo',
    ]
    
    print("\n标准模型测试:")
    for model in standard_models:
        adapter = ModelAdapterFactory.create_adapter(model)
        adapter_type = "推理模型适配器" if isinstance(adapter, ReasoningModelAdapter) else "标准模型适配器"
        print(f"  {model:30} -> {adapter_type}")
        assert isinstance(adapter, StandardModelAdapter), f"{model} 应该使用标准模型适配器"
    
    print("\n✅ 适配器工厂测试通过")


def test_model_config():
    """测试模型配置"""
    print("\n" + "=" * 60)
    print("测试模型配置")
    print("=" * 60)
    
    test_models = [
        'google/gemma-4-e4b',
        'nvidia/nemotron-3-nano-4b',
        'deepseek-r1',
        'gpt-4o',
    ]
    
    print("\n模型特性测试:")
    for model in test_models:
        features = get_model_features(model)
        is_reasoning = is_reasoning_model(model)
        print(f"\n  模型: {model}")
        print(f"    是否推理模型: {is_reasoning}")
        print(f"    响应格式: {features.get('response_format')}")
        print(f"    最大上下文: {features.get('max_context')}")
        print(f"    推荐温度: {features.get('preferred_temperature')}")
    
    print("\n✅ 模型配置测试通过")


def test_classification_extraction():
    """测试分类提取"""
    print("\n" + "=" * 60)
    print("测试分类提取")
    print("=" * 60)
    
    # 创建标准模型适配器
    standard_adapter = ModelAdapterFactory.create_adapter('nvidia/nemotron-3-nano-4b')
    
    # 标准响应
    standard_response = {
        'choices': [
            {
                'message': {
                    'content': '科技'
                }
            }
        ]
    }
    
    categories = standard_adapter.extract_classification(
        standard_response,
        ['科技', '财经', '体育', '娱乐', '国际'],
        '未分类'
    )
    print(f"\n标准模型分类提取: {categories}")
    assert categories == ['科技'], f"期望 ['科技'], 得到 {categories}"
    
    # 创建推理模型适配器
    reasoning_adapter = ModelAdapterFactory.create_adapter('google/gemma-4-e4b')
    
    # 推理响应
    reasoning_response = {
        'choices': [
            {
                'message': {
                    'content': '''分析新闻内容...
评估可用分类...
确定主分类：科技'''
                }
            }
        ]
    }
    
    categories = reasoning_adapter.extract_classification(
        reasoning_response,
        ['科技', '财经', '体育', '娱乐', '国际'],
        '未分类'
    )
    print(f"推理模型分类提取: {categories}")
    assert '科技' in categories, f"期望包含 '科技', 得到 {categories}"
    
    print("\n✅ 分类提取测试通过")


def test_summary_extraction():
    """测试摘要提取"""
    print("\n" + "=" * 60)
    print("测试摘要提取")
    print("=" * 60)
    
    # 创建标准模型适配器
    standard_adapter = ModelAdapterFactory.create_adapter('nvidia/nemotron-3-nano-4b')
    
    # 标准响应
    standard_response = {
        'choices': [
            {
                'message': {
                    'content': '这是一条新闻的摘要内容，简洁明了。'
                }
            }
        ]
    }
    
    summary = standard_adapter.extract_summary(standard_response)
    print(f"\n标准模型摘要提取: {summary}")
    assert '新闻的摘要内容' in summary, f"期望包含摘要内容"
    
    # 创建推理模型适配器
    reasoning_adapter = ModelAdapterFactory.create_adapter('google/gemma-4-e4b')
    
    # 推理响应
    reasoning_response = {
        'choices': [
            {
                'message': {
                    'content': '''分析新闻内容...
评估关键信息...
确定摘要要点：
这是一条新闻的摘要内容，简洁明了。'''
                }
            }
        ]
    }
    
    summary = reasoning_adapter.extract_summary(reasoning_response)
    print(f"推理模型摘要提取: {summary}")
    assert '新闻的摘要内容' in summary, f"期望包含摘要内容"
    
    print("\n✅ 摘要提取测试通过")


def test_model_registration():
    """测试模型注册"""
    print("\n" + "=" * 60)
    print("测试模型注册")
    print("=" * 60)
    
    # 注册新模型
    ModelAdapterFactory.register_reasoning_model('test-reasoning-model')
    ModelAdapterFactory.register_standard_model('test-standard-model')
    
    # 测试新注册的模型
    reasoning_adapter = ModelAdapterFactory.create_adapter('test-reasoning-model-v1')
    standard_adapter = ModelAdapterFactory.create_adapter('test-standard-model-v1')
    
    assert isinstance(reasoning_adapter, ReasoningModelAdapter), "新注册的推理模型应该使用推理适配器"
    assert isinstance(standard_adapter, StandardModelAdapter), "新注册的标准模型应该使用标准适配器"
    
    print(f"\n推理模型数量: {len(REASONING_MODELS)}")
    print(f"标准模型数量: {len(STANDARD_MODELS)}")
    
    print("\n✅ 模型注册测试通过")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("模型适配器系统测试")
    print("=" * 60)
    
    try:
        test_adapter_factory()
        test_model_config()
        test_classification_extraction()
        test_summary_extraction()
        test_model_registration()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())