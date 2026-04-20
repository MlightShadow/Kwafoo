from litellm import completion
from typing import Optional, Dict, Any
from utils.logger import logger
from utils.helpers import config, ConfigObserver


def contains_chinese(text: str) -> bool:
    """检测字符串是否包含中文字符"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False


def smart_truncate(text: str, max_length: int = 2000) -> str:
    """智能截取文本，保留头尾重要信息
    
    Args:
        text: 原始文本
        max_length: 最大长度，默认2000字
    
    Returns:
        截取后的文本
    """
    if len(text) <= max_length:
        return text
    
    # 尝试按段落分割（中文：。！？；英文：.!?）
    paragraphs = []
    current_para = ''
    
    for char in text:
        current_para += char
        if char in ['。', '！', '？', '；', '.', '!', '?', ';', '\n']:
            paragraphs.append(current_para.strip())
            current_para = ''
    
    if current_para.strip():
        paragraphs.append(current_para.strip())
    
    if len(paragraphs) >= 2:
        # 保留第一段和最后一段
        first_para = paragraphs[0]
        last_para = paragraphs[-1]
        
        # 如果总长度超过限制，截取每段
        if len(first_para) + len(last_para) > max_length:
            half_length = max_length // 2
            first_para = first_para[:half_length]
            last_para = last_para[:max_length - half_length]
        
        return first_para + '\n...\n' + last_para
    else:
        # 只有一段，按句子分割
        sentences = []
        current_sent = ''
        
        for char in text:
            current_sent += char
            if char in ['。', '！', '？', '.', '!', '?']:
                sentences.append(current_sent.strip())
                current_sent = ''
        
        if current_sent.strip():
            sentences.append(current_sent.strip())
        
        if len(sentences) >= 2:
            # 保留第一句和最后一句
            first_sent = sentences[0]
            last_sent = sentences[-1]
            
            # 如果总长度超过限制，截取每句
            if len(first_sent) + len(last_sent) > max_length:
                half_length = max_length // 2
                first_sent = first_sent[:half_length]
                last_sent = last_sent[:max_length - half_length]
            
            return first_sent + '...' + last_sent
        else:
            # 只有一句，直接截取
            return text[:max_length]


class AISummarizer(ConfigObserver):
    def __init__(self) -> None:
        self.base_url: str = config.get('ai.base_url', 'http://localhost:1234')
        self.model: str = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
        self.api_key: str = config.get('ai.api_key', '')
        self.max_tokens: int = config.get('ai.max_tokens', 4096)
        self.temperature: float = config.get('ai.temperature', 0.7)
        
        # 从配置中读取AI摘要阈值
        self.description_threshold: int = config.get('ai_summary_threshold', 140)
        self.max_input_length: int = config.get('ai.max_input_length', 2000)
        self.timeout: int = config.get('ai.timeout', 120)
        
        # 从配置中读取点评相关配置
        self.enable_summary_comment: bool = config.get('ai.enable_summary_comment', False)
        self.comment_stance: Dict[str, str] = config.get('ai.comment_stance', {})
        self.enable_reasoning: bool = config.get('ai.enable_summarizer_reasoning', False)
        
        # 注册为配置观察者
        config.add_observer(self)

    def on_config_changed(self, config: Dict[str, Any]):
        """
        配置更新回调
        
        Args:
            config: 更新后的配置字典
        """
        logger.info("AISummarizer配置已更新")
        ai_config = config.get('ai', {})
        self.base_url = ai_config.get('base_url', 'http://localhost:1234')
        self.model = ai_config.get('model', 'nvidia/nemotron-3-nano-4b')
        self.api_key = ai_config.get('api_key', '')
        self.max_tokens = ai_config.get('max_tokens', 4096)
        self.temperature = ai_config.get('temperature', 0.7)
        self.description_threshold = config.get('ai_summary_threshold', 140)
        self.max_input_length = ai_config.get('max_input_length', 2000)
        self.timeout = ai_config.get('timeout', 120)
        self.enable_summary_comment = config.get('ai.enable_summary_comment', False)
        self.comment_stance = config.get('ai.comment_stance', {})
        self.enable_reasoning = config.get('ai.enable_summarizer_reasoning', False)

    def generate_summary(self, content: str, description: Optional[str] = None, title: Optional[str] = None) -> Optional[Dict[str, str]]:
        """
        生成AI摘要和评价
        
        Args:
            content: 新闻正文
            description: 新闻描述
            title: 新闻标题
            
        Returns:
            包含评价和摘要的字典，格式：{'comment': str, 'summary': str}
        """
        try:
            # AI摘要始终可以执行（不受配置控制）
            # 配置只影响自动执行，不影响手动调用
            
            # 确定输入内容优先级：正文 > description > 标题
            input_content = None
            input_type = None
            
            if content and content.strip():
                input_content = content
                input_type = "正文"
            elif description and description.strip():
                input_content = description
                input_type = "描述"
            elif title and title.strip():
                input_content = title
                input_type = "标题"
            else:
                logger.warning("无内容可生成摘要")
                return None
            
            logger.debug(f"使用{input_type}进行AI摘要，长度: {len(input_content)}")
            
            # 检测是否包含中文
            has_chinese = contains_chinese(input_content)
            
            # 不论长度如何，只要不包含中文就进行AI摘要并翻译为中文
            if not has_chinese:
                logger.debug("内容不包含中文，进行AI摘要并翻译为中文")
                prompt = self._build_translate_and_summarize_prompt(input_content)
            # 包含中文，始终进行AI摘要（包括一句话评价）
            else:
                logger.debug("内容包含中文，进行AI摘要（包含一句话评价）")
                prompt = self._build_rewrite_prompt(input_content)
            
            logger.debug("开始生成AI摘要")
            
            # 根据配置决定是否启用 thinking 模式
            completion_kwargs = {
                "model": f'openai/{self.model}',
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻摘要助手，负责生成简洁准确的新闻摘要。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "api_base": f"{self.base_url}/v1",
                "api_key": self.api_key if self.api_key else "not-needed",
                "max_tokens": self.max_tokens,
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
            
            logger.debug(f"AI摘要响应: {response}")
            
            # 统一获取返回内容
            if not response or not response.choices or len(response.choices) == 0:
                logger.error(f"AI响应无效: response={response}")
                return None
            
            message = response.choices[0].message
            if not message:
                logger.error(f"AI响应消息为空: message={message}")
                return None
            
            content_text = message.content
            # 如果 content 为空，尝试从 reasoning_content 中提取
            if not content_text or not content_text.strip():
                reasoning_content = getattr(message, 'reasoning_content', None) or message.provider_specific_fields.get('reasoning_content', None)
                if reasoning_content and reasoning_content.strip():
                    logger.debug(f"AI返回的content为空，尝试从reasoning_content中提取: {reasoning_content[:200]}...")
                    # 从 reasoning_content 中提取最后一部分作为最终答案
                    # 通常最终答案在推理过程的末尾
                    lines = reasoning_content.split('\n')
                    # 查找包含评价或摘要的行
                    found_marker = False
                    extracted_content = []
                    for line in reversed(lines):
                        # 查找可能的评价标记（包含emoji表情）
                        if any(emoji in line for emoji in ['😊', '😄', '👍', '👎', '😮', '😂', '🤔', '💡', '🎯', '🔥', '⭐']):
                            found_marker = True
                        # 查找摘要标记
                        if '摘要' in line or '总结' in line or '概括' in line:
                            found_marker = True
                        if found_marker:
                            extracted_content.insert(0, line)
                    
                    if extracted_content:
                        content_text = '\n'.join(extracted_content)
                        logger.debug(f"从reasoning_content中提取的内容: {content_text[:200]}...")
                    else:
                        # 如果没有找到标记，使用最后几行
                        content_text = '\n'.join(lines[-10:]) if len(lines) > 10 else reasoning_content
                        logger.debug(f"使用reasoning_content的最后部分: {content_text[:200]}...")
                else:
                    logger.error(f"AI返回内容为空且reasoning_content也为空: content={content_text}, message={message}")
                    return None
            
            logger.debug(f"AI摘要返回内容: {content_text[:200]}...")
            
            if content_text:
                # 解析评价和摘要
                result = self._parse_comment_and_summary(content_text)
                logger.info(f"AI摘要生成成功，评价长度: {len(result['comment'])}, 摘要长度: {len(result['summary'])}")
                logger.debug(f"AI评价: {result['comment'][:100]}")
                logger.debug(f"AI摘要: {result['summary'][:200]}")
                return result
            else:
                logger.warning("AI摘要返回空结果")
                return None
            
        except Exception as e:
            logger.error(f"AI摘要生成失败: {e}")
            return None

    def _parse_comment_and_summary(self, content: str) -> Dict[str, str]:
        """
        解析AI返回的内容，分离评价和摘要
        
        Args:
            content: AI返回的完整内容
            
        Returns:
            包含评价和摘要的字典
        """
        # 尝试按换行符分割
        lines = content.strip().split('\n')
        
        if len(lines) >= 2:
            # 第一行是评价，剩余是摘要
            comment = lines[0].strip()
            summary = '\n'.join(lines[1:]).strip()
        else:
            # 只有一行，尝试按句号分割
            sentences = content.split('。')
            if len(sentences) >= 2:
                comment = sentences[0].strip() + '。'
                summary = '。'.join(sentences[1:]).strip()
            else:
                # 无法分割，全部作为摘要
                comment = ''
                summary = content.strip()
        
        # 如果评价为空，生成默认评价
        if not comment:
            comment = '📰 这是一篇值得关注的新闻'
        
        # 如果摘要为空，使用评价作为摘要
        if not summary:
            summary = comment
        
        return {
            'comment': comment,
            'summary': summary
        }

    def _build_summary_prompt(self, content: str) -> str:
        truncated_content = smart_truncate(content, self.max_input_length)
        if self.enable_summary_comment:
            personality = self._build_personality_description()
            return f"""请根据以下人格设定，先给出一句简短的点评（包含emoji表情），然后生成新闻摘要：

{personality}

{truncated_content}

要求：
1. 第一句话：简短点评，包含emoji表情，表达阅读后的感受（不超过30字）
2. 第二部分：准确概括核心内容，简洁明了（接近140字，120-160字之间）
3. 必须使用中文书写，不能使用全英文
4. 必要的英文术语或专有名词可以保留，但整体必须是中文
5. 摘要部分要详细一些，确保接近140字"""
        else:
            return f"""请将以下新闻内容改写为简洁摘要：

{truncated_content}

要求：
1. 准确概括核心内容，简洁明了（接近140字，120-160字之间）
2. 必须使用中文书写，不能使用全英文
3. 必要的英文术语或专有名词可以保留，但整体必须是中文
4. 摘要要详细一些，确保接近140字"""

    def _build_rewrite_prompt(self, description: str) -> str:
        truncated_description = smart_truncate(description, self.max_input_length)
        if self.enable_summary_comment:
            personality = self._build_personality_description()
            return f"""请根据以下人格设定，先给出一句简短的点评（包含emoji表情），然后改写新闻描述为摘要：

{personality}

{truncated_description}

要求：
1. 第一句话：简短点评，包含emoji表情，表达阅读后的感受（不超过30字）
2. 第二部分：准确概括核心内容，简洁明了（接近140字，120-160字之间）
3. 必须使用中文书写，不能使用全英文
4. 必要的英文术语或专有名词可以保留，但整体必须是中文
5. 摘要部分要详细一些，确保接近140字"""
        else:
            return f"""请将以下新闻描述改写为简洁摘要：

{truncated_description}

要求：
1. 准确概括核心内容，简洁明了（接近140字，120-160字之间）
2. 必须使用中文书写，不能使用全英文
3. 必要的英文术语或专有名词可以保留，但整体必须是中文
4. 摘要要详细一些，确保接近140字"""

    def _build_translate_and_summarize_prompt(self, description: str) -> str:
        """翻译并摘要非中文内容"""
        truncated_description = smart_truncate(description, self.max_input_length)
        if self.enable_summary_comment:
            personality = self._build_personality_description()
            return f"""请根据以下人格设定，先给出一句简短的点评（包含emoji表情），然后将以下新闻内容翻译为中文，并改写为简洁摘要：

{personality}

{truncated_description}

要求：
1. 第一句话：简短点评，包含emoji表情，表达阅读后的感受（不超过30字）
2. 第二部分：首先翻译为中文，然后改写为简洁摘要（接近140字，120-160字之间）
3. 准确概括核心内容，简洁明了
4. 必须使用中文书写，不能使用全英文
5. 必要的英文术语或专有名词可以保留，但整体必须是中文
6. 只输出中文摘要，不要包含原文或翻译过程
7. 摘要部分要详细一些，确保接近140字"""
        else:
            return f"""请将以下新闻内容翻译为中文，并改写为简洁摘要：

{truncated_description}

要求：
1. 首先翻译为中文
2. 然后改写为简洁摘要（接近140字，120-160字之间）
3. 准确概括核心内容，简洁明了
4. 必须使用中文书写，不能使用全英文
5. 必要的英文术语或专有名词可以保留，但整体必须是中文
6. 只输出中文摘要，不要包含原文或翻译过程
7. 摘要要详细一些，确保接近140字"""

    def _build_personality_description(self) -> str:
        if self.comment_stance.get('custom_description', '').strip():
            return self.comment_stance['custom_description'].strip()
        
        nationality = self.comment_stance.get('nationality', '中国')
        gender = self.comment_stance.get('gender', '')
        age = self.comment_stance.get('age', '')
        family_status = self.comment_stance.get('family_status', '')
        income = self.comment_stance.get('income', '')
        health_status = self.comment_stance.get('health_status', '')
        religion = self.comment_stance.get('religion', '无')
        
        parts = []
        parts.append(f"国籍：{nationality}")
        if gender:
            parts.append(f"性别：{gender}")
        if age:
            parts.append(f"年龄：{age}岁")
        if family_status:
            parts.append(f"家庭状况：{family_status}")
        if income:
            parts.append(f"收入水平：{income}")
        if health_status:
            parts.append(f"健康状况：{health_status}")
        if religion and religion != '无':
            parts.append(f"宗教信仰：{religion}")
        
        return "，".join(parts)



ai_summarizer = AISummarizer()