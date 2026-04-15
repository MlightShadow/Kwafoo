import requests
from typing import List, Optional, Dict, Any
from utils.logger import logger
from utils.helpers import config, get_category_names, get_default_category, ConfigObserver


class AIClassifier(ConfigObserver):
    def __init__(self) -> None:
        self.base_url: str = config.get('ai.base_url', 'http://localhost:1234')
        self.model: str = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
        self.max_tokens: int = config.get('ai.max_tokens', 4096)
        self.temperature: float = config.get('ai.temperature', 0.7)
        self.enable_reasoning: bool = config.get('ai.enable_classifier_reasoning', False)
        
        self.categories: List[str] = get_category_names()
        self.categories_config: List[Dict[str, Any]] = config.get('categories', [])
        self.default_category: str = get_default_category()
        
        self.max_input_length: int = config.get('ai.max_input_length', 800)
        self.timeout: int = config.get('ai.timeout', 120)
        
        # 注册为配置观察者
        config.add_observer(self)

    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置更新回调
        
        Args:
            config: 更新后的配置字典
        """
        logger.info("AIClassifier配置已更新")
        ai_config = config.get('ai', {})
        self.base_url = ai_config.get('base_url', 'http://localhost:1234')
        self.model = ai_config.get('model', 'nvidia/nemotron-3-nano-4b')
        self.max_tokens = ai_config.get('max_tokens', 4096)
        self.temperature = ai_config.get('temperature', 0.7)
        self.enable_reasoning = ai_config.get('enable_classifier_reasoning', False)
        self.max_input_length = ai_config.get('max_input_length', 800)
        self.timeout = ai_config.get('timeout', 120)
        
        # 更新分类信息
        self.categories = get_category_names()
        self.categories_config = config.get('categories', [])
        self.default_category = get_default_category()

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
                "max_tokens": 256,
                "temperature": self.temperature
            }
            
            if self.enable_reasoning:
                payload["reasoning_effort"] = "medium"
                logger.debug(f"AI分类已启用深度思考功能")
            else:
                logger.debug(f"AI分类未启用深度思考功能")
            
            logger.debug(f"AI分类请求: {self.base_url}/v1/chat/completions")
            logger.debug(f"AI分类超时设置: {self.timeout}秒")
            
            try:
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )
            except requests.Timeout:
                logger.error(f"AI分类请求超时（{self.timeout}秒）")
                return None
            except requests.ConnectionError as e:
                logger.error(f"AI分类连接失败: {e}")
                return None
            except requests.RequestException as e:
                logger.error(f"AI分类请求异常: {e}")
                return None
            
            logger.debug(f"AI分类响应状态: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"AI分类API调用失败: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            logger.debug(f"AI分类响应数据: {data}")
            
            # 记录完整的响应以便诊断
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0]['message']
                logger.debug(f"AI分类message keys: {list(message.keys())}")
                if 'content' in message:
                    logger.debug(f"AI分类content长度: {len(message['content'])}")
                if 'reasoning_content' in message:
                    logger.debug(f"AI分类reasoning_content长度: {len(message['reasoning_content'])}")
            
            if 'choices' not in data or len(data['choices']) == 0:
                logger.error("AI分类响应格式错误: 缺少choices字段")
                return None
            
            result = data['choices'][0]['message']['content'].strip()
            
            logger.debug(f"AI分类原始返回内容: '{result}'")
            logger.debug(f"AI分类返回长度: {len(result)}")
            
            # 如果content为空，尝试从reasoning_content中提取
            if not result:
                reasoning_content = data['choices'][0]['message'].get('reasoning_content', '')
                logger.warning(f"AI分类content为空，尝试从reasoning_content提取")
                logger.debug(f"reasoning_content长度: {len(reasoning_content)}")
                
                if reasoning_content:
                    # 从推理内容中提取分类结果
                    # 查找AI明确推荐的分类（通常在推理的最后部分）
                    lines = reasoning_content.split('\n')
                    
                    # 从最后20行中查找，放宽查找范围
                    for line in reversed(lines[-20:]):
                        line = line.strip()
                        if not line:
                            continue
                        
                        # 检查是否包含有效的分类
                        potential_cats = []
                        for cat in self.categories:
                            if cat in line:
                                potential_cats.append(cat)
                        
                        if self.default_category in line:
                            potential_cats.append(self.default_category)
                        
                        # 如果找到分类，且这一行不太长（可能是最终结果）
                        # 放宽条件：只要有分类且行不太长就认为是结果
                        if potential_cats and len(line) < 150:
                            result = ','.join(sorted(potential_cats))
                            logger.debug(f"从reasoning_content提取到分类: {result}")
                            logger.debug(f"提取的行: {line}")
                            break
            
            logger.debug(f"AI分类处理后结果: '{result}'")
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
        categories_str = '、'.join(self.categories)
        
        # 从配置中读取分类描述
        category_descriptions = []
        for cat_config in self.categories_config:
            name = cat_config.get('name', '')
            cat_description = cat_config.get('description', '')
            keywords = cat_config.get('keywords', [])
            keywords_str = '、'.join(keywords[:3]) if keywords else ''
            
            if cat_description:
                category_descriptions.append(f"- {name}：{cat_description}")
            elif keywords:
                category_descriptions.append(f"- {name}：{keywords_str}")
        
        category_desc_str = '\n'.join(category_descriptions)
        
        # 从配置中读取提示词模板
        prompt_template = config.get('ai_category_prompt', '')
        
        # 处理description为空的情况
        desc_text = description[:500] if description else '（无描述）'
        
        if prompt_template:
            # 使用配置的提示词模板
            return prompt_template.format(
                categories=categories_str,
                category_descriptions=category_desc_str,
                title=title,
                description=desc_text
            )
        else:
            # 使用默认提示词
            return f"""请根据以下新闻的标题和描述，判断它属于哪个分类。

可用分类：
{categories_str}

分类说明：
{category_desc_str}

标题：{title}

描述：{desc_text}

要求：
1. 仔细分析新闻的核心内容，选择最相关的1-2个分类
2. 如果新闻主要涉及一个分类，只返回一个分类
3. 如果新闻确实涉及多个分类，最多返回2个分类，用逗号分隔
4. 不要为了保险而选择多个分类，只选择真正相关的
5. **重要：必须从以下分类中选择一个：{categories_str}**
6. **不要返回"未分类"，即使新闻看起来不相关，也要选择最接近的分类**
7. **重要：只返回分类的中文名称（如科技、财经等），不要返回其他内容**

示例：
- 科技新闻：返回"科技"
- 财经新闻：返回"财经"
- 科技+财经：返回"科技,财经"或"财经,科技"
"""

    def _parse_result(self, result: str) -> Optional[List[str]]:
        try:
            result = result.strip()
            
            if not result:
                return None
            
            logger.debug(f"AI分类原始返回: {result}")
            
            categories = [cat.strip() for cat in result.split(',')]
            logger.debug(f"AI分类解析后: {categories}")
            logger.debug(f"可用分类: {self.categories}")
            
            valid_categories = []
            
            for cat in categories:
                # 排除"未分类"，强制选择一个实际分类
                if cat == '未分类':
                    logger.warning(f"AI返回了'未分类'，已忽略")
                    continue
                    
                if cat in self.categories:
                    valid_categories.append(cat)
                    logger.debug(f"分类 '{cat}' 有效")
                elif cat == self.default_category and cat != '未分类':
                    valid_categories.append(cat)
                    logger.debug(f"分类 '{cat}' 是默认分类")
                else:
                    logger.debug(f"分类 '{cat}' 无效，跳过")
            
            # 如果没有有效分类，返回None，让调用者处理
            if not valid_categories:
                logger.warning(f"AI分类没有返回有效分类，原始结果: {result}")
                return None
            
            # 限制最多返回2个分类
            if len(valid_categories) > 2:
                valid_categories = valid_categories[:2]
                logger.debug(f"分类数量超过2个，已限制为: {valid_categories}")
            
            logger.debug(f"AI分类最终结果: {valid_categories}")
            
            return valid_categories
            
        except Exception as e:
            logger.error(f"分类结果解析失败: {e}")
            return None


ai_classifier = AIClassifier()