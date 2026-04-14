import requests
from typing import Optional, Dict, Any
from utils.logger import logger
from utils.helpers import config


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


class AISummarizer:
    def __init__(self):
        self.base_url = config.get('ai.base_url', 'http://localhost:1234')
        self.model = config.get('ai.model', 'nvidia/nemotron-3-nano-4b')
        self.max_tokens = config.get('ai.max_tokens', 4096)
        self.temperature = config.get('ai.temperature', 0.7)
        
        # 从配置中读取AI摘要阈值
        self.description_threshold = config.get('ai_summary_threshold', 140)
        self.max_input_length = 2000  # 智能截取后不超过2000字
        self.timeout = 120  # 增加超时时间到120秒

    def generate_summary(self, content: str, description: Optional[str] = None) -> Optional[str]:
        try:
            # AI摘要始终可以执行（不受配置控制）
            # 配置只影响自动执行，不影响手动调用
            
            if description:
                # 如果描述为空，不做AI摘要
                if not description or not description.strip():
                    logger.debug("描述为空，不做AI摘要")
                    return None
                
                # 检测是否包含中文
                has_chinese = contains_chinese(description)
                
                # 不论长度如何，只要不包含中文就进行AI摘要并翻译为中文
                if not has_chinese:
                    logger.debug("描述不包含中文，进行AI摘要并翻译为中文")
                    prompt = self._build_translate_and_summarize_prompt(description)
                # 包含中文且长度超过阈值，进行AI摘要
                elif len(description) > self.description_threshold:
                    logger.debug("描述包含中文且长度超过阈值，进行AI摘要")
                    prompt = self._build_rewrite_prompt(description)
                # 包含中文且长度未超过阈值，不做AI摘要
                else:
                    logger.debug("描述包含中文且长度正常，无需AI摘要")
                    return None
            else:
                if not content:
                    logger.warning("无内容可生成摘要")
                    return None
                
                prompt = self._build_summary_prompt(content)
            
            logger.debug("开始生成AI摘要")
            
            payload = {
                "model": self.model,
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
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            logger.debug(f"AI摘要请求: {self.base_url}/v1/chat/completions")
            logger.debug(f"AI摘要超时设置: {self.timeout}秒")
            
            try:
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.timeout
                )
            except requests.Timeout:
                logger.error(f"AI摘要请求超时（{self.timeout}秒）")
                return None
            except requests.ConnectionError as e:
                logger.error(f"AI摘要连接失败: {e}")
                return None
            except requests.RequestException as e:
                logger.error(f"AI摘要请求异常: {e}")
                return None
            
            logger.debug(f"AI摘要响应状态: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"AI摘要API调用失败: {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            if 'choices' not in data or len(data['choices']) == 0:
                logger.error("AI摘要响应格式错误: 缺少choices字段")
                return None
            
            summary = data['choices'][0]['message']['content'].strip()
            logger.info(f"AI摘要生成成功，长度: {len(summary)}")
            return summary
            
        except Exception as e:
            logger.error(f"AI摘要生成失败: {e}")
            return None

    def _build_summary_prompt(self, content: str) -> str:
        truncated_content = smart_truncate(content, self.max_input_length)
        return f"""请将以下新闻内容改写为简洁摘要（不超过140字）：

{truncated_content}

要求：
1. 准确概括核心内容，简洁明了，不超过140字
2. 必须使用中文书写，不能使用全英文
3. 必要的英文术语或专有名词可以保留，但整体必须是中文"""

    def _build_rewrite_prompt(self, description: str) -> str:
        truncated_description = smart_truncate(description, self.max_input_length)
        return f"""请将以下新闻描述改写为简洁摘要（不超过140字）：

{truncated_description}

要求：
1. 准确概括核心内容，简洁明了，不超过140字
2. 必须使用中文书写，不能使用全英文
3. 必要的英文术语或专有名词可以保留，但整体必须是中文"""

    def _build_translate_and_summarize_prompt(self, description: str) -> str:
        """翻译并摘要非中文内容"""
        truncated_description = smart_truncate(description, self.max_input_length)
        return f"""请将以下新闻内容翻译为中文，并改写为简洁摘要（不超过140字）：

{truncated_description}

要求：
1. 首先翻译为中文
2. 然后改写为简洁摘要
3. 准确概括核心内容，简洁明了，不超过140字
4. 必须使用中文书写，不能使用全英文
5. 必要的英文术语或专有名词可以保留，但整体必须是中文
6. 只输出中文摘要，不要包含原文或翻译过程"""


ai_summarizer = AISummarizer()