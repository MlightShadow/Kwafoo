from litellm import completion
from typing import List, Optional, Dict, Any
from utils.logger import logger
from utils.helpers import config, get_category_names, get_default_category, ConfigObserver


class AIClassifier(ConfigObserver):
    def __init__(self) -> None:
        self.base_url: str = config.get('ai.base_url', 'http://localhost:1234')
        self.model: str = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
        self.api_key: str = config.get('ai.api_key', '')
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
        self.api_key = ai_config.get('api_key', '')
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
                 source_category: str = None) -> Optional[Dict[str, Any]]:
        try:
            # AI分类始终可以执行（不受配置控制）
            # 配置只影响自动执行，不影响手动调用
            
            # 限制输入长度
            truncated_title = title[:200] if title else ''
            truncated_description = description[:self.max_input_length] if description else ''
            
            logger.debug(f"AI分类输入: title={truncated_title[:50]}..., description_length={len(truncated_description)}")
            
            prompt = self._build_classify_prompt(truncated_title, truncated_description)
            
            logger.debug("开始AI分类")
            
            # 根据配置决定是否启用 thinking 模式
            completion_kwargs = {
                "model": f'openai/{self.model}',
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻分类助手，负责准确识别新闻的分类和提取关键字。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "api_base": f"{self.base_url}/v1",
                "api_key": self.api_key if self.api_key else "not-needed",
                "max_tokens": 2048,
                "temperature": self.temperature,
                "timeout": self.timeout
            }
            
            # 只有在配置启用时才添加 reasoning_effort 参数
            if self.enable_reasoning:
                completion_kwargs["extra_body"] = {"reasoning_effort": "low"}
                logger.debug("启用 thinking 模式")
            else:
                logger.debug("关闭 thinking 模式")
            
            # 使用 LiteLLM 调用 AI
            response = completion(**completion_kwargs)
            
            logger.debug(f"AI分类响应: {response}")
            
            # 统一获取返回内容
            if not response or not response.choices or len(response.choices) == 0:
                logger.error(f"AI响应无效: response={response}")
                return None
            
            message = response.choices[0].message
            if not message:
                logger.error(f"AI响应消息为空: message={message}")
                return None
            
            content = message.content
            # 如果 content 为空，尝试从 reasoning_content 中提取
            if not content or not content.strip():
                reasoning_content = getattr(message, 'reasoning_content', None) or message.provider_specific_fields.get('reasoning_content', None)
                if reasoning_content and reasoning_content.strip():
                    logger.debug(f"AI返回的content为空，尝试从reasoning_content中提取: {reasoning_content[:200]}...")
                    # 从 reasoning_content 中提取最后一部分作为最终答案
                    # 通常最终答案在推理过程的末尾
                    lines = reasoning_content.split('\n')
                    # 查找包含"分类："或"关键字："的行
                    found_marker = False
                    extracted_content = []
                    for line in reversed(lines):
                        if '分类：' in line or '分类:' in line or '关键字：' in line or '关键字:' in line:
                            found_marker = True
                        if found_marker:
                            extracted_content.insert(0, line)
                    
                    if extracted_content:
                        content = '\n'.join(extracted_content)
                        logger.debug(f"从reasoning_content中提取的内容: {content[:200]}...")
                    else:
                        # 如果没有找到标记，使用最后几行
                        content = '\n'.join(lines[-5:]) if len(lines) > 5 else reasoning_content
                        logger.debug(f"使用reasoning_content的最后部分: {content[:200]}...")
                else:
                    logger.error(f"AI返回内容为空且reasoning_content也为空: content={content}, message={message}")
                    return None
            
            if not content or not content.strip():
                logger.error(f"AI返回内容为空: content={content}, message={message}")
                return None
            
            logger.debug(f"AI分类返回内容: {content[:200]}...")
            
            # 解析分类和关键字
            result = self._parse_result(content)
            
            if result:
                categories = result.get('categories', [])
                keywords = result.get('keywords', [])
                
                # 如果AI没有返回分类，则根据关键字命中情况选取1-2个标签
                if not categories and keywords:
                    categories = self._classify_by_keywords(keywords)
                    logger.info(f"AI未返回分类，根据关键字命中情况选取分类: {categories}")
                
                logger.info(f"AI分类完成: {categories}, 关键字: {keywords}")
                return {
                    'categories': categories,
                    'keywords': keywords
                }
            else:
                logger.warning("AI分类返回空结果")
                return None
            
        except Exception as e:
            logger.error(f"AI分类失败: {e}")
            return None

    def _classify_by_keywords(self, keywords: List[str]) -> List[str]:
        """
        根据关键字命中情况选取1-2个分类
        
        Args:
            keywords: AI提取的关键字列表
            
        Returns:
            分类列表
        """
        if not keywords:
            logger.warning("关键字列表为空，返回默认分类")
            return [self.default_category]
        
        logger.debug(f"根据关键字分类: keywords={keywords}")
        
        # 统计每个分类的关键字命中次数
        category_scores = {}
        
        for cat_config in self.categories_config:
            category_name = cat_config.get('name', '')
            category_keywords = cat_config.get('keywords', [])
            
            if not category_keywords:
                continue
            
            score = 0
            for keyword in keywords:
                for cat_keyword in category_keywords:
                    if keyword.lower() in cat_keyword.lower() or cat_keyword.lower() in keyword.lower():
                        score += 1
                        break
            
            if score > 0:
                category_scores[category_name] = score
                logger.debug(f"分类 {category_name} 命中 {score} 次")
        
        # 按命中次数排序
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 选取前1-2个分类
        if sorted_categories:
            result = [sorted_categories[0][0]]
            if len(sorted_categories) > 1 and sorted_categories[1][1] > 0:
                result.append(sorted_categories[1][0])
            logger.info(f"根据关键字命中情况选取分类: {result}, 命中次数: {sorted_categories[:2]}")
            return result
        
        # 如果没有命中任何分类，返回默认分类
        logger.warning("没有命中任何分类，返回默认分类")
        return [self.default_category]

    def _parse_result(self, content: str) -> Optional[Dict[str, Any]]:
        """
        解析AI返回的分类结果和关键字
        
        Args:
            content: AI返回的完整内容
            
        Returns:
            包含分类和关键字的字典
        """
        try:
            # 记录原始内容用于调试
            logger.debug(f"开始解析AI返回内容，原始内容长度: {len(content)}, 内容: {content[:500]}")
            
            # 检查内容是否为空
            if not content or not content.strip():
                logger.warning("AI返回内容为空")
                return None
            
            categories = None
            keywords = None
            
            # 检查是否包含"分类："和"关键字："标记
            if '分类：' in content or '分类:' in content:
                logger.debug("发现分类标记，尝试提取分类")
                categories = self._extract_classification_from_content(content)
                logger.debug(f"提取分类结果: {categories}")
            
            if '关键字：' in content or '关键字:' in content:
                logger.debug("发现关键字标记，尝试提取关键字")
                keywords = self._extract_keywords_from_content(content)
                logger.debug(f"提取关键字结果: {keywords}")
            
            # 如果没有找到标记，尝试简单解析
            if not categories:
                logger.debug("未发现分类标记，尝试简单解析")
                categories = self._parse_simple_classification(content)
                logger.debug(f"简单解析分类结果: {categories}")
            
            if not keywords:
                logger.debug("未发现关键字标记，尝试简单提取关键字")
                keywords = self._extract_keywords_simple(content)
                logger.debug(f"简单提取关键字结果: {keywords}")
            
            # 检查解析结果
            if categories or keywords:
                logger.info(f"解析成功: categories={categories}, keywords={keywords}")
                return {
                    'categories': categories or [],
                    'keywords': keywords or []
                }
            
            # 如果所有解析都失败，记录详细信息
            logger.warning(f"所有解析方法都失败，原始内容: {content}")
            return None
            
        except Exception as e:
            logger.error(f"解析AI返回结果失败: {e}, 原始内容: {content}")
            return None

    def _extract_classification_from_content(self, content: str) -> Optional[List[str]]:
        """
        从内容中提取分类（查找"分类："标记）
        """
        try:
            # 查找"分类："或"分类:"标记
            for marker in ['分类：', '分类:']:
                if marker in content:
                    # 提取标记后的内容
                    parts = content.split(marker)
                    if len(parts) > 1:
                        classification_part = parts[1].strip()
                        
                        # 提取到下一行或"关键字："之前的内容
                        lines = classification_part.split('\n')
                        if lines:
                            classification_line = lines[0].strip()
                            
                            # 尝试多种分隔符
                            categories = []
                            for separator in [',', '，', '、']:
                                if separator in classification_line:
                                    parts = classification_line.split(separator)
                                    for part in parts:
                                        part = part.strip()
                                        # 过滤掉无效的分类名称
                                        if not part or part == '未分类' or part == 'categories' or part == '分类':
                                            continue
                                        if part in self.categories:
                                            categories.append(part)
                                        elif part == self.default_category:
                                            categories.append(part)
                                    if categories:
                                        break
                            
                            if categories:
                                categories = list(set(categories))
                                if len(categories) > 2:
                                    categories = categories[:2]
                                logger.debug(f"提取分类结果: {categories}")
                                return categories
            
            return None
            
        except Exception as e:
            logger.error(f"从内容中提取分类失败: {e}")
            return None

    def _extract_keywords_from_content(self, content: str) -> Optional[List[str]]:
        """
        从内容中提取关键字（查找"关键字："标记）
        """
        try:
            # 查找"关键字："或"关键字:"标记
            for marker in ['关键字：', '关键字:']:
                if marker in content:
                    # 提取标记后的内容
                    parts = content.split(marker)
                    if len(parts) > 1:
                        keywords_part = parts[1].strip()
                        
                        # 提取到下一行或结束的内容
                        lines = keywords_part.split('\n')
                        if lines:
                            keywords_line = lines[0].strip()
                            
                            # 尝试多种分隔符
                            keywords = []
                            for separator in [',', '，', '、']:
                                if separator in keywords_line:
                                    parts = keywords_line.split(separator)
                                    for part in parts:
                                        part = part.strip()
                                        if part:
                                            keywords.append(part)
                                    if keywords:
                                        break
                            
                            if keywords:
                                # 限制为10个关键字
                                keywords = keywords[:10]
                                return keywords
            
            return None
            
        except Exception as e:
            logger.error(f"从内容中提取关键字失败: {e}")
            return None

    def _parse_simple_classification(self, content: str) -> Optional[List[str]]:
        """
        解析简单的分类结果
        """
        try:
            content = content.strip()
            
            if not content:
                return None
            
            # 尝试多种分隔符
            categories = []
            for separator in [',', '，', '、']:
                if separator in content:
                    parts = content.split(separator)
                    for part in parts:
                        part = part.strip()
                        # 过滤掉无效的分类名称
                        if not part or part == '未分类' or part == 'categories' or part == '分类':
                            continue
                        if part in self.categories:
                            categories.append(part)
                        elif part == self.default_category:
                            categories.append(part)
                    if categories:
                        break
            
            # 如果没有找到，尝试直接匹配
            if not categories:
                for cat in self.categories:
                    if cat in content and len(content) < 100:
                        categories.append(cat)
                if self.default_category in content and len(content) < 100:
                    categories.append(self.default_category)
            
            if categories:
                categories = list(set(categories))
                if len(categories) > 2:
                    categories = categories[:2]
                logger.debug(f"简单解析分类结果: {categories}")
                return categories
            
            return None
            
        except Exception as e:
            logger.error(f"解析简单分类失败: {e}")
            return None

    def _extract_keywords_simple(self, content: str) -> Optional[List[str]]:
        """
        简单提取关键字（如果没有标记）
        """
        try:
            # 尝试从内容中提取可能的关键字
            # 移除标点符号
            import re
            cleaned_content = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', content)
            
            # 分词
            words = cleaned_content.split()
            
            # 过滤掉短词和常见词
            stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
            filtered_words = [word for word in words if len(word) > 1 and word not in stop_words]
            
            # 统计词频
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按词频排序
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # 提取前10个关键字
            keywords = [word for word, freq in sorted_words[:10]]
            
            return keywords
            
        except Exception as e:
            logger.error(f"简单提取关键字失败: {e}")
            return None

    def _build_classify_prompt(self, title: str, description: str) -> str:
        categories_str = '、'.join(self.categories)
        
        # 从配置中读取分类描述（不包含关键字）
        category_descriptions = []
        for cat_config in self.categories_config:
            name = cat_config.get('name', '')
            cat_description = cat_config.get('description', '')
            
            if cat_description:
                category_descriptions.append(f"- {name}：{cat_description}")
        
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
            return f"""请根据以下新闻的标题和描述，判断它属于哪个分类，并提取10个关键字。

可用分类：
{categories_str}

分类说明（请仔细阅读以下每个分类的详细描述）：
{category_desc_str}

标题：{title}

描述：{desc_text}

要求：
1. **首先仔细阅读上述"分类说明"中每个分类的详细描述，理解每个分类的适用范围**
2. 根据新闻的核心内容，选择最相关的1-2个分类
3. 如果新闻主要涉及一个分类，只返回一个分类
4. 如果新闻确实涉及多个分类，最多返回2个分类，用逗号分隔
5. 不要为了保险而选择多个分类，只选择真正相关的
6. **重要：必须从以下分类中选择一个：{categories_str}**
7. **不要返回"未分类"，即使新闻看起来不相关，也要选择最接近的分类**
8. **提取新闻中的10个关键字，关键字应该能够代表新闻的核心内容**
9. **关键字应该是新闻中出现的词汇，而不是分类名称**
10. **格式要求：按照以下格式返回结果**
    - 分类：分类名称（如"科技"或"科技,财经"）
    - 关键字：关键字1,关键字2,关键字3,关键字4,关键字5,关键字6,关键字7,关键字8,关键字9,关键字10

示例：
- 科技新闻：
  分类：科技
  关键字：人工智能,机器学习,深度学习,神经网络,算法,数据,模型,训练,预测,应用
- 财经新闻：
  分类：财经
  关键字：股票,市场,投资,经济,金融,企业,财报,利润,增长,股价
- 科技+财经：
  分类：科技,财经
  关键字：人工智能,投资,融资,创业,科技,市场,经济,创新,企业,发展
"""



ai_classifier = AIClassifier()