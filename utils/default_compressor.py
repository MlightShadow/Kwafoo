"""
默认文本压缩器：融合基础算法和高级算法的所有功能
提供完整的文本压缩解决方案
"""

import re
import math
import heapq
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Set
from utils.helpers import config
from utils.logger import logger


@dataclass
class DefaultSentenceScore:
    """默认的句子评分数据结构"""
    index: int
    text: str
    score: float
    tokens: int
    semantic_score: float = 0.0      # 语义得分
    topic_score: float = 0.0         # 主题得分
    sentiment_score: float = 0.0     # 情感得分
    structure_score: float = 0.0     # 结构得分


class DefaultTextCompressor:
    """
    默认文本压缩器：融合基础算法和高级算法的所有功能
    """
    
    def __init__(self, target_tokens: int = None, compression_level: str = None,
                 compression_mode: str = None):
        """初始化默认压缩器"""
        # 从配置读取参数，如果没有提供则使用默认值
        self.target_tokens = target_tokens or config.get('compression.target_tokens', 2000)
        self.compression_level = compression_level or config.get('compression.compression_level', 'balanced')
        self.compression_mode = compression_mode or config.get('compression.mode', 'summary')
        
        # 平均字符每token（中文约2-3字符/token）
        self.avg_chars_per_token = 2.5
        self.target_chars = int(self.target_tokens * self.avg_chars_per_token)
        
        # 根据压缩级别调整参数
        self._set_compression_level()
        
        # 根据压缩模式调整参数
        self._set_compression_mode()
        
        # 默认的停用词表（融合基础和高级的停用词）
        self.stopwords = self._create_default_stopwords()
        
        # 同义词简化表
        self.synonyms = self._create_synonyms_table()
        
        logger.debug(f"默认压缩器初始化完成，模式: {self.compression_mode}, 级别: {self.compression_level}")
    
    def _create_default_stopwords(self) -> Set[str]:
        """创建默认的停用词表"""
        # 基础停用词
        base_stopwords = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', 
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would'
        }
        
        # 高级停用词（冗余词）
        advanced_stopwords = {
            '然后', '接着', '接下来', '随后', '之后', '以后', '后来',
            '首先', '其次', '再次', '最后', '总之', '综上所述',
            '例如', '比如', '比如说', '譬如', '比方说',
            '实际上', '事实上', '其实', '说白了',
            'then', 'next', 'after', 'later', 'finally',
            'first', 'second', 'third', 'lastly',
            'for example', 'for instance', 'such as',
            'actually', 'in fact', 'basically'
        }
        
        return base_stopwords | advanced_stopwords
    
    def _create_synonyms_table(self) -> Dict[str, str]:
        """创建同义词简化表"""
        return {
            # 中文同义词简化
            '非常': '很', '特别': '很', '十分': '很', '极其': '很', '相当': '很',
            '换句话说': '即', '也就是说': '即', '总而言之': '总之', '综上所述': '综上',
            '与此同时': '同时', '尽管如此': '但', '然而': '但', '但是': '但',
            '因为': '因', '所以': '故', '因此': '故', '于是': '故',
            
            # 英文同义词简化
            'very': '', 'extremely': '', 'particularly': '', 'quite': '',
            'in other words': 'i.e.', 'that is to say': 'i.e.',
            'in conclusion': 'conclusion', 'to sum up': 'summary',
            'at the same time': 'simultaneously', 'nevertheless': 'but',
            'however': 'but', 'because': 'since', 'therefore': 'so'
        }
    
    def _set_compression_level(self):
        """根据压缩级别设置参数"""
        if self.compression_level == 'aggressive':
            # 激进压缩：最大压缩比
            self.min_sentence_length = 30
            self.position_weight_strong = 1.8
            self.position_weight_weak = 1.2
            self.tfidf_weight = 0.4
            self.position_weight = 0.6
            # 高级评分权重
            self.semantic_weight = 0.2
            self.topic_weight = 0.2
            self.sentiment_weight = 0.1
            self.structure_weight = 0.1
        elif self.compression_level == 'conservative':
            # 保守压缩：最小压缩比
            self.min_sentence_length = 10
            self.position_weight_strong = 1.3
            self.position_weight_weak = 1.1
            self.tfidf_weight = 0.7
            self.position_weight = 0.3
            # 高级评分权重
            self.semantic_weight = 0.3
            self.topic_weight = 0.3
            self.sentiment_weight = 0.2
            self.structure_weight = 0.2
        else:  # balanced
            # 平衡压缩：默认设置
            self.min_sentence_length = 20
            self.position_weight_strong = 1.5
            self.position_weight_weak = 1.2
            self.tfidf_weight = 0.6
            self.position_weight = 0.4
            # 高级评分权重
            self.semantic_weight = 0.25
            self.topic_weight = 0.25
            self.sentiment_weight = 0.2
            self.structure_weight = 0.3
    
    def _set_compression_mode(self):
        """根据压缩模式调整参数"""
        if self.compression_mode == 'keypoints':
            # 要点模式：更注重关键信息提取
            self.semantic_weight = 0.4
            self.topic_weight = 0.3
            self.sentiment_weight = 0.1
            self.structure_weight = 0.2
        elif self.compression_mode == 'qa':
            # 问答模式：注重问题和答案的提取
            self.semantic_weight = 0.3
            self.topic_weight = 0.2
            self.sentiment_weight = 0.1
            self.structure_weight = 0.4
        else:  # summary模式
            # 摘要模式：平衡各种因素
            self.semantic_weight = 0.25
            self.topic_weight = 0.25
            self.sentiment_weight = 0.2
            self.structure_weight = 0.3
    
    def compress(self, text: str, preserve_structure: bool = True) -> str:
        """
        默认压缩函数：融合基础和高级算法的所有功能
        """
        start_time = time.time()
        
        # 处理空白文本
        if not text or not text.strip():
            return ""
        
        # 清理文本
        cleaned_text = text.strip()
        
        # 检查文本长度是否需要进行压缩
        if len(cleaned_text) <= self.target_chars:
            logger.debug("文本长度在目标范围内，无需压缩")
            return cleaned_text
        
        logger.debug(f"开始默认压缩文本，原始长度: {len(cleaned_text)} 字符，目标: {self.target_chars} 字符")
        
        # 1. 智能分句（基础算法功能）
        sentences = self._split_sentences(cleaned_text)
        
        # 如果分句失败但文本很长，强制进行压缩
        if len(sentences) <= 3 and len(cleaned_text) > self.target_chars * 2:
            logger.debug("分句失败但文本很长，强制进行压缩")
            chunk_size = max(self.min_sentence_length * 3, 200)
            sentences = []
            for i in range(0, len(cleaned_text), chunk_size):
                chunk = cleaned_text[i:i+chunk_size].strip()
                if chunk:
                    sentences.append(chunk)
        
        if len(sentences) <= 3:
            logger.debug("句子数量太少，无需压缩")
            return cleaned_text
        
        logger.debug(f"分句完成，共 {len(sentences)} 个句子")
        
        # 2. 默认评分：融合基础和高级评分（核心融合）
        scored_sentences = self._default_score_sentences(sentences)
        
        # 3. 选择关键句
        selected = self._select_sentences(scored_sentences, preserve_structure)
        
        # 4. 智能表达精简（融合基础和高级的精简功能）
        compressed = self._default_refine_text(selected)
        
        # 5. 根据压缩模式进行格式化
        compressed = self._format_by_mode(compressed)
        
        # 6. 最终截断（如果还是太长）
        if len(compressed) > self.target_chars:
            compressed = self._smart_truncate(compressed)
        
        compression_ratio = len(compressed) / len(text)
        processing_time = time.time() - start_time
        
        logger.debug(f"默认压缩完成，压缩比: {compression_ratio:.2%}，最终长度: {len(compressed)} 字符，耗时: {processing_time:.2f}秒")
        
        return compressed
    
    def _split_sentences(self, text: str) -> List[str]:
        """智能分句（基础算法功能）"""
        # 基础算法的智能分句逻辑
        paragraphs = re.split(r'\n\s*\n', text.strip())
        
        sentences = []
        for para in paragraphs:
            if not para.strip():
                continue
            
            # 检测语言类型
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', para))
            total_chars = len(para)
            
            if chinese_chars / total_chars > 0.3:
                # 中文为主：使用多种分句策略
                chinese_punctuations = r'[。！？]'
                parts = re.split(f'({chinese_punctuations})', para)
                for i in range(0, len(parts)-1, 2):
                    sent = (parts[i] + (parts[i+1] if i+1 < len(parts) else '')).strip()
                    if sent and len(sent) > self.min_sentence_length:
                        sentences.append(sent)
                
                # 如果没有找到句子，尝试按分号分割
                if not sentences:
                    parts = re.split(r'([；])', para)
                    for i in range(0, len(parts)-1, 2):
                        sent = (parts[i] + (parts[i+1] if i+1 < len(parts) else '')).strip()
                        if sent and len(sent) > self.min_sentence_length:
                            sentences.append(sent)
                
                # 如果还是没有句子，尝试按换行符分割
                if not sentences:
                    lines = para.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > self.min_sentence_length:
                            sentences.append(line)
                
                # 如果还是没有句子，尝试按固定长度分割
                if not sentences and len(para) > self.min_sentence_length * 2:
                    chunk_size = max(self.min_sentence_length * 2, 100)
                    for i in range(0, len(para), chunk_size):
                        chunk = para[i:i+chunk_size].strip()
                        if chunk:
                            sentences.append(chunk)
            else:
                # 英文为主：使用英文标点分句
                english_punctuations = r'[.!?]'
                parts = re.split(f'({english_punctuations})', para)
                for i in range(0, len(parts)-1, 2):
                    sent = (parts[i] + (parts[i+1] if i+1 < len(parts) else '')).strip()
                    if sent and len(sent) > self.min_sentence_length:
                        sentences.append(sent)
                
                # 如果没有找到句子，尝试按分号分割
                if not sentences:
                    parts = re.split(r'([;])', para)
                    for i in range(0, len(parts)-1, 2):
                        sent = (parts[i] + (parts[i+1] if i+1 < len(parts) else '')).strip()
                        if sent and len(sent) > self.min_sentence_length:
                            sentences.append(sent)
                
                # 如果还是没有句子，尝试按换行符分割
                if not sentences:
                    lines = para.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > self.min_sentence_length:
                            sentences.append(line)
        
        # 如果还是没有句子，将整个文本作为一个句子
        if not sentences:
            sentences = [text.strip()]
        
        return sentences
    
    def _default_score_sentences(self, sentences: List[str]) -> List[DefaultSentenceScore]:
        """
        默认评分：融合基础和高级算法的评分机制
        """
        # 1. 基础TF-IDF评分
        word_freq = defaultdict(int)
        sentence_words = []
        
        for sent in sentences:
            words = self._extract_words(sent)
            sentence_words.append(words)
            for w in words:
                if w not in self.stopwords:
                    word_freq[w] += 1
        
        # 计算IDF
        total_docs = len(sentences)
        idf = {}
        for word, freq in word_freq.items():
            doc_count = sum(1 for words in sentence_words if word in words)
            idf[word] = math.log(total_docs / (doc_count + 1)) + 1
        
        # 2. 默认评分
        scores = []
        for idx, (sent, words) in enumerate(zip(sentences, sentence_words)):
            # 基础TF-IDF得分
            tfidf_score = 0
            word_counts = Counter(words)
            for word, count in word_counts.items():
                if word not in self.stopwords:
                    tf = count / len(words) if words else 0
                    tfidf_score += tf * idf.get(word, 1)
            
            # 位置权重（基础算法功能）
            position_weight = 1.0
            if idx == 0:  # 首句
                position_weight = self.position_weight_strong
            elif idx == len(sentences) - 1:  # 末句
                position_weight = self.position_weight_strong
            elif idx < len(sentences) * 0.1:  # 前10%
                position_weight = self.position_weight_weak
            elif idx > len(sentences) * 0.9:  # 后10%
                position_weight = self.position_weight_weak
            
            # 长度惩罚（基础算法功能）
            length_score = min(len(sent) / 100, 1.0)
            
            # 高级评分维度
            semantic_score = self._calculate_semantic_score(sent)
            topic_score = self._calculate_topic_score(sent, sentences)
            sentiment_score = self._calculate_sentiment_score(sent)
            structure_score = self._calculate_structure_score(sent, idx, len(sentences))
            
            # 综合得分（核心融合）
            base_score = (tfidf_score * self.tfidf_weight + position_weight * self.position_weight) * length_score
            advanced_score = (semantic_score * self.semantic_weight +
                             topic_score * self.topic_weight +
                             sentiment_score * self.sentiment_weight +
                             structure_score * self.structure_weight)
            
            final_score = base_score * 0.6 + advanced_score * 0.4  # 基础算法占60%，高级算法占40%
            
            # 估算token数
            est_tokens = len(sent) / self.avg_chars_per_token
            
            scores.append(DefaultSentenceScore(
                index=idx,
                text=sent,
                score=final_score,
                tokens=int(est_tokens),
                semantic_score=semantic_score,
                topic_score=topic_score,
                sentiment_score=sentiment_score,
                structure_score=structure_score
            ))
        
        return scores
    
    # 以下为高级算法的评分函数（直接复用）
    def _calculate_semantic_score(self, sentence: str) -> float:
        """计算语义得分"""
        words = self._extract_words(sentence)
        unique_words = set(words)
        
        lexical_richness = len(unique_words) / len(words) if words else 0
        length_score = 1.0 - abs(len(sentence) - 80) / 200
        length_score = max(0, min(1, length_score))
        
        return (lexical_richness + length_score) / 2
    
    def _calculate_topic_score(self, sentence: str, all_sentences: List[str]) -> float:
        """计算主题得分"""
        all_text = ' '.join(all_sentences)
        all_words = self._extract_words(all_text)
        
        word_freq = Counter(all_words)
        total_words = len(all_words)
        if total_words == 0:
            return 0.0
        
        threshold = total_words * 0.1
        topic_words = {word for word, freq in word_freq.items() if freq > threshold}
        
        sentence_words = set(self._extract_words(sentence))
        if not sentence_words:
            return 0.0
        
        topic_word_count = len(sentence_words & topic_words)
        return topic_word_count / len(sentence_words)
    
    def _calculate_sentiment_score(self, sentence: str) -> float:
        """计算情感得分"""
        positive_words = {'好', '优秀', '完美', '成功', '胜利', '快乐', '幸福', '满意'}
        negative_words = {'坏', '糟糕', '失败', '错误', '痛苦', '悲伤', '不满'}
        
        words = set(self._extract_words(sentence))
        
        positive_count = len(words & positive_words)
        negative_count = len(words & negative_words)
        
        if positive_count > negative_count:
            return min(1.0, positive_count * 0.2)
        elif negative_count > positive_count:
            return min(1.0, negative_count * 0.2)
        else:
            return 0.0
    
    def _calculate_structure_score(self, sentence: str, index: int, total_sentences: int) -> float:
        """计算结构得分"""
        score = 0.0
        
        if index == 0 or index == total_sentences - 1:
            score += 0.3
        elif index < total_sentences * 0.1 or index > total_sentences * 0.9:
            score += 0.1
        
        if re.search(r'\d+', sentence):
            score += 0.1
        
        if '"' in sentence or '\'' in sentence:
            score += 0.1
        
        if '?' in sentence or '？' in sentence:
            score += 0.1
        
        return min(1.0, score)
    
    def _extract_words(self, text: str) -> List[str]:
        """提取词汇"""
        chinese_words = re.findall(r'[\u4e00-\u9fff]', text)
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        return chinese_words + english_words
    
    def _select_sentences(self, scored_sentences: List[DefaultSentenceScore], 
                         preserve_structure: bool) -> List[str]:
        """选择关键句"""
        scored_sentences.sort(key=lambda x: x.score, reverse=True)
        
        total_tokens = sum(s.tokens for s in scored_sentences)
        
        if total_tokens <= self.target_tokens:
            return [s.text for s in sorted(scored_sentences, key=lambda x: x.index)]
        
        # 动态规划选择
        selected = []
        current_tokens = 0
        
        for sentence in scored_sentences:
            if current_tokens + sentence.tokens <= self.target_tokens:
                selected.append(sentence)
                current_tokens += sentence.tokens
            else:
                remaining_tokens = self.target_tokens - current_tokens
                if remaining_tokens > sentence.tokens * 0.3:
                    selected.append(sentence)
                    current_tokens += sentence.tokens
                break
        
        selected.sort(key=lambda x: x.index)
        return [s.text for s in selected]
    
    def _default_refine_text(self, sentences: List[str]) -> str:
        """默认表达精简"""
        if not sentences:
            return ""
        
        refined_sentences = []
        for sent in sentences:
            # 基础精简：去除冗余词
            refined = self._simplify_expression(sent)
            refined_sentences.append(refined)
        
        return ' '.join(refined_sentences)
    
    def _simplify_expression(self, text: str) -> str:
        """简化表达"""
        simplified = text
        
        # 去除冗余词
        for word in self.stopwords:
            if len(word) > 1:  # 只处理多字词
                simplified = simplified.replace(word, '')
        
        # 同义词简化
        for old, new in self.synonyms.items():
            simplified = simplified.replace(old, new)
        
        # 去除多余空格
        simplified = re.sub(r'\s+', ' ', simplified).strip()
        
        return simplified
    
    def _format_by_mode(self, text: str) -> str:
        """根据压缩模式格式化输出"""
        if self.compression_mode == 'keypoints':
            # 要点模式：提取关键句
            sentences = self._split_sentences(text)
            keypoints = []
            for sent in sentences[:10]:  # 最多10个要点
                if len(sent.strip()) > 10:
                    keypoints.append(f"• {sent.strip()}")
            return '\n'.join(keypoints) if keypoints else text
        
        elif self.compression_mode == 'qa':
            # 问答模式：提取问答对
            sentences = self._split_sentences(text)
            qa_pairs = []
            for sent in sentences:
                if self._is_question(sent):
                    qa_pairs.append(f"Q: {sent.strip()}")
                elif len(qa_pairs) > 0 and not qa_pairs[-1].startswith("A:"):
                    qa_pairs.append(f"A: {sent.strip()}")
            return '\n'.join(qa_pairs) if qa_pairs else text
        
        else:  # summary模式
            # 摘要模式：保持原文结构
            return text
    
    def _is_question(self, text: str) -> bool:
        """判断是否为问句"""
        question_indicators = ['什么', '如何', '为什么', '怎样', '哪里', '谁', '哪个',
                            'what', 'how', 'why', 'where', 'who', 'which', '?', '？']
        return any(indicator in text.lower() for indicator in question_indicators)
    
    def _smart_truncate(self, text: str) -> str:
        """智能截断"""
        if len(text) <= self.target_chars:
            return text
        
        # 尝试在句子边界截断
        sentences = self._split_sentences(text)
        result = []
        current_length = 0
        
        for sent in sentences:
            if current_length + len(sent) <= self.target_chars:
                result.append(sent)
                current_length += len(sent)
            else:
                break
        
        truncated = ' '.join(result)
        
        # 如果还是太长，直接截断
        if len(truncated) > self.target_chars:
            truncated = truncated[:self.target_chars-3] + '...'
        
        return truncated


def compress_text_default(text: str, target_tokens: int = None, 
                         compression_level: str = None, compression_mode: str = None) -> str:
    """
    便捷函数：使用默认压缩器压缩文本
    
    Args:
        text: 要压缩的文本
        target_tokens: 目标token数
        compression_level: 压缩级别（balanced/aggressive/conservative）
        compression_mode: 压缩模式（summary/keypoints/qa）
    
    Returns:
        压缩后的文本
    """
    compressor = DefaultTextCompressor(target_tokens, compression_level, compression_mode)
    return compressor.compress(text)


def get_default_compression_info() -> Dict[str, any]:
    """获取默认压缩器信息"""
    return {
        'name': '默认文本压缩器',
        'description': '融合基础和高级算法的完整压缩解决方案',
        'features': [
            '多维度评分（TF-IDF + 语义/主题/情感/结构）',
            '三种压缩模式（摘要/要点/问答）',
            '智能表达精简',
            '多语言支持',
            '可配置的压缩级别'
        ],
        'modes': {
            'summary': '摘要模式：生成连贯的摘要文本',
            'keypoints': '要点模式：提取关键要点列表',
            'qa': '问答模式：将文本转换为问答形式'
        }
    }