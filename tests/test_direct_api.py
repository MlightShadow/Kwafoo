import sys
import os
import requests
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import logger
from utils.helpers import config


def test_direct_api():
    logger.info("=" * 60)
    logger.info("直接测试AI API调用")
    logger.info("=" * 60)
    
    base_url = config.get('ai.base_url', 'http://localhost:1234')
    model = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
    
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Model: {model}")
    
    logger.info("\n【测试1】检查模型列表")
    logger.info("-" * 60)
    
    try:
        response = requests.get(f"{base_url}/v1/models", timeout=10)
        logger.info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'data' in data:
                logger.info(f"可用模型数量: {len(data['data'])}")
                for m in data['data'][:5]:
                    logger.info(f"  - {m['id']}")
            else:
                logger.warning("响应中没有data字段")
        else:
            logger.error(f"请求失败: {response.text}")
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    logger.info("\n【测试2】测试简单的聊天请求")
    logger.info("-" * 60)
    
    test_prompt = "你好，请回复'测试成功'"
    
    logger.info(f"测试提示词: {test_prompt}")
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个测试助手。"
            },
            {
                "role": "user",
                "content": test_prompt
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        logger.info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'choices' in data and len(data['choices']) > 0:
                result = data['choices'][0]['message']['content'].strip()
                logger.info(f"✓ API调用成功，结果: {result}")
            else:
                logger.error("✗ 响应结构异常")
        else:
            logger.error(f"请求失败: {response.text}")
            
    except Exception as e:
        logger.error(f"✗ API调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n【测试3】测试新闻分类")
    logger.info("-" * 60)
    
    test_title = "海底捞：控股股东张勇拟增持不少于1亿港元"
    test_description = "海底捞在港交所公告，公司控股股东张勇拟增持公司股份，增持金额不少于1亿港元。"
    
    categories = config.get('categories', {})
    categories_list = list(categories.keys())
    categories_str = '、'.join(categories_list)
    
    prompt = f"""请根据以下新闻的标题和描述，判断它属于哪个分类。

可用分类：{categories_str}

标题：{test_title}

描述：{test_description[:500]}

要求：
1. 只返回分类名称，不要添加任何解释
2. 如果新闻涉及多个分类，请用逗号分隔，例如："科技,互联网"
3. 如果新闻不属于任何分类，返回"未分类"
4. 只返回分类名称，不要添加其他内容"""
    
    logger.info(f"分类提示词: {prompt}")
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个专业的新闻分类助手，负责准确识别新闻的分类。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            timeout=30
        )
        
        logger.info(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'choices' in data and len(data['choices']) > 0:
                result = data['choices'][0]['message']['content'].strip()
                logger.info(f"分类结果: {result}")
                logger.info("✓ 新闻分类成功")
            else:
                logger.error("✗ 响应结构异常")
        else:
            logger.error(f"请求失败: {response.text}")
            
    except Exception as e:
        logger.error(f"✗ 新闻分类失败: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成")
    logger.info("=" * 60)


if __name__ == '__main__':
    try:
        test_direct_api()
        print("\n✓ 测试完成！")
    except Exception as e:
        logger.error(f"测试失败: {e}")
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)