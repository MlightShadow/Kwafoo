## 1. 最推荐：基于抽取式摘要的压缩

### 方案 A: `sumy` + `jieba`（中文友好）

```python
# pip install sumy jieba networkx

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer as SumyTokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words
import jieba

class SumyCompressor:
    """基于sumy的文本压缩器，支持中英文"""
    
    def __init__(self, language="chinese", sentences_count=10):
        self.language = "english" if language != "chinese" else "english"
        self.sentences_count = sentences_count
        self.stemmer = Stemmer(self.language)
        
    def compress(self, text: str, ratio: float = 0.3) -> str:
        """
        ratio: 保留比例，0.3表示保留30%的句子
        """
        # 估算句子数
        sentences = text.replace('。', '.').replace('！', '!').replace('？', '?')
        est_sentences = len([s for s in sentences.split('.') if len(s.strip()) > 10])
        target_sentences = max(3, int(est_sentences * ratio))
        
        try:
            parser = PlaintextParser.from_string(text, SumyTokenizer(self.language))
            summarizer = TextRankSummarizer(self.stemmer)
            summarizer.stop_words = get_stop_words(self.language)
            
            summary = summarizer(parser.document, target_sentences)
            return ' '.join([str(s) for s in summary])
        except:
            # 失败时返回原文前N字符
            return text[:2000]

# 使用
compressor = SumyCompressor(language="chinese", sentences_count=5)
text = "你的长文本..."
compressed = compressor.compress(text, ratio=0.3)
```

### 方案 B: `bert-extractive-summarizer`（基于BERT，更准确）

```python
# pip install bert-extractive-summarizer transformers torch

from summarizer import Summarizer

class BERTCompressor:
    """基于BERT的抽取式摘要，质量高但稍慢"""
    
    def __init__(self):
        self.model = Summarizer()
        
    def compress(self, text: str, ratio: float = 0.2) -> str:
        """
        ratio: 保留字符比例
        """
        target_chars = int(len(text) * ratio)
        # num_sentences 或 ratio 都可以
        result = self.model(text, num_sentences=5)
        return result

# 使用
compressor = BERTCompressor()
compressed = compressor.compress(long_text, ratio=0.3)
```

---

## 2. 轻量级：基于TextRank的纯Python实现

### 方案 C: `textrank4zh`（专为中文优化）

```python
# pip install textrank4zh jieba

from textrank4zh import TextRank4Sentence

class TextRankCompressor:
    """专为中文设计的TextRank压缩"""
    
    def __init__(self):
        self.tr4s = TextRank4Sentence()
        
    def compress(self, text: str, num_sentences: int = 5) -> str:
        self.tr4s.analyze(text=text, lower=True, source='all_filters')
        
        # 获取最重要的句子
        key_sentences = self.tr4s.get_key_sentences(num=num_sentences)
        
        # 按原文顺序排列
        key_sentences = sorted(key_sentences, key=lambda x: x.index)
        
        return '。'.join([s.sentence for s in key_sentences])

# 使用
compressor = TextRankCompressor()
text = """
自然语言处理是人工智能领域的重要方向。它研究如何实现人与计算机之间用自然语言进行有效通信。
近年来，深度学习技术在NLP领域取得了突破性进展。
Transformer架构的提出彻底改变了这一领域。
BERT、GPT等预训练模型大幅提升了各项任务的性能。
未来，多模态融合将成为新的研究热点。
"""
compressed = compressor.compress(text, num_sentences=3)
print(compressed)
```

---

## 3. 快速近似：基于词频的压缩

### 方案 D: 纯Python实现（无依赖，最快）

```python
import re
import heapq
from collections import Counter, defaultdict
import math

class FastCompressor:
    """快速文本压缩，零依赖，适合大批量处理"""
    
    # 中文停用词
    CN_STOPWORDS = set('的 了 和 是 在 有 我 他 她 它 们 这 那 之 与 及 等 或 但 而 因 于 被 把 给 让 向 往 从 自 到 为 着 过 说 要 就 都 你 会 对 能 上 下 来 去 能 可 会 能 很 会 会 可 很 也 但 并 而 且 或 因为 所以 因此 如果 即使 虽然 尽管 然而 但是 于是 从而 而且 并且 或者 还是 要么 假如 假定 譬如 例如 比如 像是 像 似的 似乎 好像 一样 一般 通常 常常 经常 往往 一直 一向 从来 始终 毕竟 究竟 到底 终究 终于 结果 后果 成果 然后 而后 之后 后来 随即 随手 随手 随手 随手'.split())
    
    # 英文停用词
    EN_STOPWORDS = set('the a an is are was were be been being have has had do does did will would could should may might must shall can need dare ought used to about above across after against along among around at before behind below beneath beside between beyond by down during except for from in inside into like near of off on onto out outside over past since through throughout till to toward under underneath until up upon with within without'.split())
    
    def __init__(self, target_ratio: float = 0.3):
        self.target_ratio = target_ratio
        
    def compress(self, text: str, max_sentences: int = None) -> str:
        sentences = self._split_sentences(text)
        if len(sentences) <= 3:
            return text
            
        if max_sentences is None:
            max_sentences = max(3, int(len(sentences) * self.target_ratio))
        
        # 计算TF-IDF分数
        scores = self._score_sentences(sentences)
        
        # 选择top N，但保持原文顺序
        top_indices = heapq.nlargest(max_sentences, range(len(scores)), key=lambda i: scores[i])
        top_indices.sort()
        
        return ' '.join([sentences[i] for i in top_indices])
    
    def _split_sentences(self, text: str) -> list:
        """分句"""
        # 中文
        text = re.sub(r'([。！？；])', r'\1|SPLIT|', text)
        # 英文
        text = re.sub(r'([.!?;])\s+', r'\1|SPLIT|', text)
        
        sentences = [s.strip() for s in text.split('|SPLIT|') if len(s.strip()) > 10]
        return sentences
    
    def _score_sentences(self, sentences: list) -> list:
        """基于TF-IDF打分"""
        # 构建词频
        word_freq = defaultdict(int)
        sent_words = []
        
        for sent in sentences:
            words = self._extract_words(sent)
            sent_words.append(words)
            for w in words:
                if w not in self.CN_STOPWORDS and w not in self.EN_STOPWORDS:
                    word_freq[w] += 1
        
        # 计算IDF
        N = len(sentences)
        idf = {w: math.log(N / (freq + 1)) + 1 for w, freq in word_freq.items()}
        
        # 计算句子得分
        scores = []
        for words in sent_words:
            if not words:
                scores.append(0)
                continue
                
            tf = Counter(words)
            score = sum((tf[w] / len(words)) * idf.get(w, 1) for w in set(words))
            
            # 位置加权：开头和结尾更重要
            idx = len(scores)
            if idx == 0 or idx == len(sentences) - 1:
                score *= 1.5
            elif idx < len(sentences) * 0.2:
                score *= 1.2
                
            scores.append(score)
        
        return scores
    
    def _extract_words(self, text: str) -> list:
        """提取词汇（中英文）"""
        # 中文单字
        cn_words = list(re.findall(r'[\u4e00-\u9fff]', text))
        # 英文单词
        en_words = re.findall(r'[a-zA-Z]+', text.lower())
        return cn_words + en_words


# 使用示例
compressor = FastCompressor(target_ratio=0.3)
text = "你的长文本内容..."
compressed = compressor.compress(text)
print(f"压缩率: {len(compressed)/len(text):.1%}")
```

---

## 4. 完整对比与推荐

| 工具 | 速度 | 中文支持 | 依赖 | 推荐场景 |
|------|------|----------|------|----------|
| **FastCompressor** | ⚡ 极快 | ⭐⭐⭐ | 无 | 大批量、实时处理 |
| **textrank4zh** | 🚀 快 | ⭐⭐⭐⭐ | jieba | 中文为主 |
| **sumy** | 🚀 快 | ⭐⭐⭐ | 轻量 | 多语言混合 |
| **BERT Summarizer** | 🐢 慢 | ⭐⭐⭐⭐⭐ | PyTorch | 精度优先 |

---

## 5. 生产环境推荐配置

```python
class SmartCompressor:
    """智能选择压缩策略"""
    
    def __init__(self, target_tokens: int = 2000):
        self.target_tokens = target_tokens
        self.fast = FastCompressor()
        
        # 尝试加载高级压缩器
        try:
            from textrank4zh import TextRank4Sentence
            self.tr = TextRankCompressor()
            self.mode = "textrank"
        except ImportError:
            self.mode = "fast"
            
    def compress(self, text: str) -> str:
        # 估算当前token数（中文约2字符/token，英文约4字符/token）
        cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        en_chars = len(re.findall(r'[a-zA-Z]', text))
        est_tokens = cn_chars / 2 + en_chars / 4
        
        if est_tokens <= self.target_tokens:
            return text
            
        # 计算压缩比例
        ratio = self.target_tokens / est_tokens
        
        if self.mode == "textrank" and cn_chars > en_chars:
            # 中文用textrank
            num_sentences = max(3, int(len(self._split_sentences(text)) * ratio))
            return self.tr.compress(text, num_sentences=num_sentences)
        else:
            # 其他用fast
            return self.fast.compress(text, ratio=ratio)
    
    def _split_sentences(self, text: str) -> list:
        return re.split(r'[。！？.!?]', text)
```

**最省心的选择**：如果只需要一个，直接用 `FastCompressor`（上面的方案D），零依赖、速度快、效果够用。如果追求更高质量，用 `textrank4zh`。