import requests
from typing import List, Optional, Dict, Any
from utils.logger import logger
from utils.helpers import config


class AIClassifier:
    def __init__(self):
        self.base_url = config.get('ai.base_url', 'http://localhost:1234')
        self.model = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
        self.max_tokens = config.get('ai.max_tokens', 4096)
        self.temperature = config.get('ai.temperature', 0.7)
        
        self.categories = config.get('categories', {})
        self.default_category = config.get('default_category', '未分类')
        
        self.max_input_length = 800  # 限制输入长度
        self.timeout = 60  # 增加超时时间

    def classify(self, title: str, description: str, 
                 source_category: str = None) -> Optional[List[str]]:
        try:
            # AI分类始终可以执行（不受配置控制）
            # 配置只影响自动执行，不影响手动调用
            
            # 限制输入长度
            truncated_title = title[:200] if title else ''
            truncated_description = description[:self.max_input_length] if description else ''
            
            prompt = self._build_classify_prompt(truncated_title, truncated_description)
            
            logger.debug("开始AI分类")
            
            payload = {
                "model": self.model,
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
                "max_tokens": 256,  # 减少输出token数
                "temperature": self.temperature
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            logger.debug(f"AI分类响应状态: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"AI分类API调用失败: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            logger.debug(f"AI分类响应数据: {data}")
            
            if 'choices' not in data or len(data['choices']) == 0:
                logger.error("AI分类响应格式错误: 缺少choices字段")
                return None
            
            result = data['choices'][0]['message']['content'].strip()
            
            # 如果content为空，尝试从reasoning_content中提取
            if not result:
                reasoning_content = data['choices'][0]['message'].get('reasoning_content', '')
                if reasoning_content:
                    # 从推理内容中提取分类结果
                    # 查找AI明确推荐的分类（通常在推理的最后部分）
                    lines = reasoning_content.split('\n')
                    
                    # 从最后几行中查找，优先查找包含"所以"、"因此"、"最终"、"结论"等词的行
                    conclusion_keywords = ['所以', '因此', '最终', '结论', '应该', '属于']
                    
                    for line in reversed(lines[-15:]):  # 只看最后15行
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 检查是否包含结论关键词
                        has_conclusion = any(keyword in line for keyword in conclusion_keywords)
                        
                        # 检查是否包含有效的分类
                        potential_cats = []
                        for cat in self.categories.keys():
                            if cat in line:
                                potential_cats.append(cat)
                        
                        if self.default_category in line:
                            potential_cats.append(self.default_category)
                        
                        # 如果找到分类，且包含结论关键词，且这一行不太长（可能是最终结果）
                        if potential_cats and has_conclusion and len(line) < 100:
                            result = ','.join(sorted(potential_cats))
                            break
            
            logger.debug(f"AI分类原始结果: '{result}'")
            logger.debug(f"AI分类结果长度: {len(result)}")
            
            categories = self._parse_result(result)
            
            if categories:
                logger.info(f"AI分类完成: {categories}")
                return categories
            else:
                logger.warning("AI分类返回空结果")
                return None
            
        except Exception as e:
            logger.error(f"AI分类失败: {e}")
            return None

    def _build_classify_prompt(self, title: str, description: str) -> str:
        categories_list = list(self.categories.keys())
        categories_str = '、'.join(categories_list)
        
        # 从配置中读取分类描述
        category_descriptions = []
        for cat, info in self.categories.items():
            description = info.get('description', '')
            keywords = info.get('keywords', [])
            keywords_str = '、'.join(keywords[:3]) if keywords else ''
            
            if description:
                category_descriptions.append(f"- {cat}：{description}")
            elif keywords:
                category_descriptions.append(f"- {cat}：{keywords_str}")
        
        category_desc_str = '\n'.join(category_descriptions)
        
        # 从配置中读取提示词模板
        prompt_template = config.get('ai_category_prompt', '')
        
        if prompt_template:
            # 使用配置的提示词模板
            return prompt_template.format(
                categories=categories_str,
                category_descriptions=category_desc_str,
                title=title,
                description=description[:500]
            )
        else:
            # 使用默认提示词
            return f"""请根据以下新闻的标题和描述，判断它属于哪个分类。

可用分类：
{categories_str}

分类说明：
{category_desc_str}

标题：{title}

描述：{description[:500]}

要求：
1. 仔细分析新闻的核心内容，选择最相关的1-2个分类
2. 如果新闻主要涉及一个分类，只返回一个分类
3. 如果新闻确实涉及多个分类，最多返回2个分类，用逗号分隔
4. 不要为了保险而选择多个分类，只选择真正相关的
5. 如果新闻不属于任何分类，返回"其他"
6. 只返回分类名称，不要添加任何解释或额外内容

示例：
- 科技新闻：返回"科技"
- 财经新闻：返回"财经"
- 科技+财经：返回"科技,财经"或"财经,科技"
- 社会新闻：返回"其他"
"""

    def _parse_result(self, result: str) -> Optional[List[str]]:
        try:
            result = result.strip()
            
            if not result:
                return None
            
            logger.debug(f"AI分类原始返回: {result}")
            
            categories = [cat.strip() for cat in result.split(',')]
            logger.debug(f"AI分类解析后: {categories}")
            logger.debug(f"可用分类: {list(self.categories.keys())}")
            
            valid_categories = []
            
            for cat in categories:
                if cat in self.categories:
                    valid_categories.append(cat)
                    logger.debug(f"分类 '{cat}' 有效")
                elif cat == self.default_category:
                    valid_categories.append(cat)
                    logger.debug(f"分类 '{cat}' 是默认分类")
                else:
                    logger.debug(f"分类 '{cat}' 无效，跳过")
            
            logger.debug(f"AI分类最终结果: {valid_categories}")
            
            if valid_categories:
                return valid_categories
            
            return None
            
        except Exception as e:
            logger.error(f"分类结果解析失败: {e}")
            return None


ai_classifier = AIClassifier()