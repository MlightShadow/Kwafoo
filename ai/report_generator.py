"""
报告生成器 - 使用AI生成日报、周报、月报
"""
import json
import time
from litellm import completion
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from utils.logger import logger
from utils.helpers import config
from database import db


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.base_url = config.get('ai.base_url')
        self.model = config.get('ai.model')
        self.api_key = config.get('ai.api_key', '')
        self.max_tokens = config.get('ai.max_tokens', 4096)
        self.temperature = config.get('ai.temperature', 0.7)
        self.timeout = config.get('report.report_ai_timeout', 300)
        self.max_news_count = config.get('report.max_news_count', 20)
    
    def generate_report(self, report_type: str, hours: int = 24) -> Dict[str, Any]:
        """
        生成报告
        
        Args:
            report_type: 报告类型（daily/weekly/monthly）
            hours: 时间范围（小时）
            
        Returns:
            报告生成结果
        """
        start_time = time.time()
        
        try:
            logger.info(f"开始生成{report_type}报告，时间范围：{hours}小时")
            
            # 1. 计算时间范围
            end_time = datetime.now(timezone(timedelta(hours=8)))
            start_time_range = end_time - timedelta(hours=hours)
            
            start_time_str = start_time_range.strftime('%Y-%m-%d %H:%M:%S')
            end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 2. 直接查询评分最高的新闻
            news_with_score = db.get_news_by_score(start_time_str, end_time_str, self.max_news_count)
            
            if not news_with_score:
                logger.warning(f"没有已评分的新闻，无法生成报告")
                return {
                    'success': False,
                    'error': '没有找到已评分的新闻，请先对新闻进行AI处理'
                }
            
            logger.info(f"找到 {len(news_with_score)} 条已评分的新闻")
            
            # 3. 生成报告内容
            report_content = self._generate_report_content(news_with_score, report_type)
            
            if not report_content:
                logger.error("报告内容生成失败")
                return {
                    'success': False,
                    'error': '报告内容生成失败'
                }
            
            # 4. 创建报告记录
            report_title = self._generate_report_title(report_type, end_time)
            
            report_data = {
                'report_type': report_type,
                'title': report_title,
                'content': json.dumps(report_content, ensure_ascii=False),
                'time_range_start': start_time_str,
                'time_range_end': end_time_str,
                'news_count': len(news_with_score),
                'ai_model': self.model,
                'generation_time': time.time() - start_time
            }
            
            report_id = db.create_report(report_data)
            
            if report_id <= 0:
                logger.error("报告创建失败")
                return {
                    'success': False,
                    'error': '报告创建失败'
                }
            
            logger.info(f"报告生成成功: {report_title} (ID: {report_id})")
            
            return {
                'success': True,
                'report_id': report_id,
                'report_title': report_title,
                'news_count': len(news_with_score),
                'generation_time': time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"报告生成失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_report_content(self, news_list: List[Dict], report_type: str) -> Optional[Dict]:
        """
        生成报告内容
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
            
        Returns:
            报告内容（JSON格式）
        """
        try:
            # 限制新闻数量
            if len(news_list) > self.max_news_count:
                news_list = news_list[:self.max_news_count]
                logger.info(f"限制新闻数量为 {self.max_news_count}")
            
            # 准备新闻数据
            news_data = []
            for i, news in enumerate(news_list, 1):
                news_data.append({
                    'id': news['id'],
                    'title': news['title'],
                    'ai_summary': news.get('ai_summary', ''),
                    'category': news.get('category', '未分类'),
                    'publish_time': news.get('publish_time', ''),
                    'source': news.get('source', ''),
                    'url': news.get('url', '')
                })
            
            # 构建提示词
            prompt = self._build_report_prompt(news_data, report_type)
            
            # 使用 LiteLLM 调用 AI
            response = completion(
                model=f'openai/{self.model}',
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的新闻分析师，擅长对新闻进行分类和梳理。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                api_base=f"{self.base_url}/v1",
                api_key=self.api_key if self.api_key else "not-needed",
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=self.timeout
            )
            
            logger.debug(f"AI报告生成响应: {response}")
            
            # 统一获取返回内容
            result_text = response.choices[0].message.content.strip()
            
            if not result_text:
                logger.error("AI报告生成响应内容为空")
                return None
            
            # 清理AI返回的JSON格式
            cleaned_text = self._clean_json_response(result_text)
            
            # 解析AI返回的JSON
            try:
                report_content = json.loads(cleaned_text)
                
                # 验证报告内容格式
                if not self._validate_report_content(report_content):
                    logger.error("报告内容格式验证失败")
                    return None
                
                return report_content
                
            except json.JSONDecodeError as e:
                logger.error(f"解析AI返回的JSON失败: {e}")
                logger.error(f"AI返回内容: {result_text}")
                logger.error(f"清理后内容: {cleaned_text}")
                return None
            
        except Exception as e:
            logger.error(f"生成报告内容失败: {e}", exc_info=True)
            return None
    
    def _build_report_prompt(self, news_data: List[Dict], report_type: str) -> str:
        """
        构建报告提示词
        
        Args:
            news_data: 新闻数据
            report_type: 报告类型
            
        Returns:
            提示词
        """
        type_name = {
            'daily': '日报',
            'weekly': '周报',
            'monthly': '月报'
        }.get(report_type, '报告')
        
        news_text = "\n\n".join([
            f"【新闻{i}】\n"
            f"ID: {news['id']}\n"
            f"标题: {news['title']}\n"
            f"摘要: {news['ai_summary']}\n"
            f"分类: {news['category']}\n"
            f"时间: {news['publish_time']}\n"
            f"来源: {news['source']}"
            for i, news in enumerate(news_data, 1)
        ])
        
        prompt = f"""请根据以下{len(news_data)}条新闻，生成一份{type_name}。

要求：
1. 按照**相似话题**进行分组，并对每组事件进行**情况梳理**
2. 不要简单罗列新闻，而是对同一组事件进行综合梳理
3. 说明梳理的原因是因为哪些新闻（引用新闻ID或标题）
4. 每个话题组包含：
   - 话题标题（概括性标题）
   - 话题综述（综合梳理该组事件，200-300字）
   - 梳理原因（说明为什么将这些新闻归为一组）
   - 涉及的新闻列表（ID、标题、AI摘要、来源、时间）
5. 话题数量建议：3-5个
6. 添加整体综述（100-200字），概括今日/本周/本月的重要事件
7. 严格按照JSON格式返回，不要添加任何其他内容

JSON格式要求：
{{
  "summary": "整体综述...",
  "topics": [
    {{
      "topic_title": "话题标题",
      "topic_summary": "该组事件的综合梳理...",
      "reasoning": "梳理原因：涉及新闻[1, 3, 5]，这些新闻都围绕...",
      "news_items": [
        {{
          "id": 123,
          "title": "新闻标题",
          "ai_summary": "AI摘要",
          "category": "分类",
          "publish_time": "2024-01-15 10:00:00",
          "source": "来源",
          "url": "链接"
        }}
      ]
    }}
  ]
}}

新闻列表：
{news_text}
"""
        return prompt
    
    def _clean_json_response(self, text: str) -> str:
        """
        清理AI返回的JSON格式
        
        Args:
            text: AI返回的原始文本
            
        Returns:
            清理后的JSON文本
        """
        import re
        
        # 1. 修复URL格式：移除反引号和多余空格
        text = re.sub(r'"url":\s*`\s*([^`]+)\s*`\s*', r'"url": "\1"', text)
        
        # 2. 修复双冒号：将 "::" 替换为 ":"
        text = re.sub(r'::', ':', text)
        
        # 3. 修复空值：将 ":"," 替换为 ": "","
        text = re.sub(r'":\s*",\s*', '": "",', text)
        
        # 4. 修复只有冒号的情况：将 ":" 替换为 ": """
        text = re.sub(r'":\s*"', '": ""', text)
        
        # 5. 移除多余的空格和换行
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _validate_report_content(self, content: Dict) -> bool:
        """
        验证报告内容格式
        
        Args:
            content: 报告内容
            
        Returns:
            是否有效
        """
        if not isinstance(content, dict):
            return False
        
        if 'summary' not in content or not isinstance(content['summary'], str):
            return False
        
        if 'topics' not in content or not isinstance(content['topics'], list):
            return False
        
        for topic in content['topics']:
            if not isinstance(topic, dict):
                return False
            
            required_fields = ['topic_title', 'topic_summary', 'reasoning', 'news_items']
            for field in required_fields:
                if field not in topic:
                    return False
            
            if not isinstance(topic['news_items'], list):
                return False
        
        return True
    
    def _generate_report_title(self, report_type: str, end_time: datetime) -> str:
        """
        生成报告标题
        
        Args:
            report_type: 报告类型
            end_time: 结束时间
            
        Returns:
            报告标题
        """
        type_name = {
            'daily': '日报',
            'weekly': '周报',
            'monthly': '月报'
        }.get(report_type, '报告')
        
        date_str = end_time.strftime('%Y-%m-%d')
        time_str = end_time.strftime('%H:%M')
        
        return f"{date_str} {time_str} {type_name}"


report_generator = ReportGenerator()