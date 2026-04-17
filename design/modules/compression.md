# 文本压缩模块设计

## 模块概述

文本压缩模块提供多种文本压缩算法，用于生成新闻摘要、提取关键信息等。模块支持多种压缩级别和模式，可以根据需求选择最合适的压缩算法。

## 压缩算法

### 1. 默认压缩器（DefaultTextCompressor）

**技术选型：**
- 融合基础算法和高级算法
- 基于TF-IDF和句子评分
- 支持多种评分维度

**核心功能：**
- 句子分割和清洗
- TF-IDF计算
- 多维度句子评分
- 智能句子选择
- 支持多种压缩级别和模式

**评分维度：**
- **语义得分**：基于关键词匹配
- **主题得分**：基于主题相关性
- **情感得分**：基于情感分析
- **结构得分**：基于句子位置和长度

**压缩级别：**
- `conservative`：保守压缩，保留更多信息
- `balanced`：平衡压缩，默认级别
- `aggressive`：激进压缩，更简洁

**压缩模式：**
- `summary`：摘要模式，生成连贯的摘要
- `keypoints`：要点模式，提取关键点
- `qa`：问答模式，生成问答对

**配置参数：**
```toml
[compression]
target_tokens = 2000
compression_level = 'balanced'
mode = 'summary'
```

**代码引用：**
[utils/default_compressor.py](../../utils/default_compressor.py) - 默认压缩器实现

### 2. TextRank压缩器（TextRankCompressor）

**技术选型：**
- 基于textrank4zh库
- 使用TextRank算法
- 专门针对中文文本优化

**核心功能：**
- 基于TextRank的句子重要性排序
- 高质量的中文文本压缩
- 支持多种压缩级别
- 自动降级到默认压缩器

**TextRank算法：**
- 将句子作为图的节点
- 句子相似度作为边的权重
- 使用PageRank算法计算句子重要性
- 选择最重要的句子组成摘要

**优势：**
- 比TF-IDF更准确
- 考虑句子间的语义关系
- 生成更连贯的摘要
- 专门针对中文优化

**依赖：**
```bash
pip install textrank4zh
```

**配置参数：**
```toml
[compression]
target_tokens = 2000
compression_level = 'balanced'
```

**代码引用：**
[utils/textrank_compressor.py](../../utils/textrank_compressor.py) - TextRank压缩器实现

### 3. 混合压缩器（HybridCompressor）

**技术选型：**
- 智能选择最佳压缩算法
- 支持自动选择和手动指定
- 提供最佳的性能和质量平衡

**核心功能：**
- 自动检测textrank4zh可用性
- 根据配置选择算法
- 支持多种算法选择策略
- 统一的接口

**算法选择策略：**
- `auto`：自动选择（优先使用textrank4zh）
- `default`：使用默认压缩器
- `textrank`：使用textrank4zh压缩器

**选择逻辑：**
1. 如果配置为`textrank`：
   - 检查textrank4zh是否可用
   - 可用则使用textrank4zh
   - 不可用则降级到默认压缩器
2. 如果配置为`default`：
   - 始终使用默认压缩器
3. 如果配置为`auto`：
   - 优先使用textrank4zh
   - 不可用时使用默认压缩器

**配置参数：**
```toml
[compression]
target_tokens = 2000
compression_level = 'balanced'
mode = 'summary'
algorithm = 'auto'  # 'auto', 'default', 'textrank'
```

**代码引用：**
[utils/hybrid_compressor.py](../../utils/hybrid_compressor.py) - 混合压缩器实现

## 压缩流程

### 通用流程

```
输入文本 → 句子分割 → 句子评分 → 句子选择 → 摘要生成 → 输出结果
```

### 默认压缩器流程

1. **预处理**：
   - 清洗文本（去除HTML标签、特殊字符）
   - 句子分割（基于标点符号）
   - 去除空句子和过短句子

2. **评分**：
   - 计算TF-IDF
   - 计算语义得分
   - 计算主题得分
   - 计算情感得分
   - 计算结构得分

3. **选择**：
   - 根据得分排序句子
   - 选择top-k句子
   - 保持原始顺序

4. **生成**：
   - 根据压缩模式生成结果
   - 摘要模式：连贯的摘要
   - 要点模式：关键点列表
   - 问答模式：问答对

### TextRank压缩器流程

1. **预处理**：
   - 清洗文本
   - 句子分割

2. **构建图**：
   - 将句子作为节点
   - 计算句子相似度
   - 构建相似度矩阵

3. **计算重要性**：
   - 使用PageRank算法
   - 计算每个句子的重要性得分

4. **选择**：
   - 根据重要性排序
   - 选择top-k句子
   - 保持原始顺序

5. **生成**：
   - 组合选中的句子
   - 生成最终摘要

## 配置说明

### 基础配置
```toml
[compression]
target_tokens = 2000              # 目标token数量
compression_level = 'balanced'    # 压缩级别：'conservative', 'balanced', 'aggressive'
mode = 'summary'                 # 压缩模式：'summary', 'keypoints', 'qa'
algorithm = 'auto'               # 算法选择：'auto', 'default', 'textrank'
```

### 压缩级别说明

**conservative（保守）**
- 保留更多信息
- 摘要长度较长
- 适合需要详细信息的场景

**balanced（平衡）**
- 默认级别
- 平衡信息量和简洁性
- 适合大多数场景

**aggressive（激进）**
- 更简洁的摘要
- 摘要长度较短
- 适合快速浏览的场景

### 压缩模式说明

**summary（摘要）**
- 生成连贯的摘要
- 保持句子间的逻辑关系
- 适合生成新闻摘要

**keypoints（要点）**
- 提取关键点
- 列表形式展示
- 适合快速浏览

**qa（问答）**
- 生成问答对
- 适合FAQ场景
- 便于信息检索

## 使用示例

### 使用默认压缩器
```python
from utils.default_compressor import DefaultTextCompressor

compressor = DefaultTextCompressor(target_tokens=2000, compression_level='balanced')
summary = compressor.compress(text, mode='summary')
```

### 使用TextRank压缩器
```python
from utils.textrank_compressor import TextRankCompressor

compressor = TextRankCompressor(target_tokens=2000, compression_level='balanced')
summary = compressor.compress(text)
```

### 使用混合压缩器
```python
from utils.hybrid_compressor import HybridCompressor

compressor = HybridCompressor(target_tokens=2000, compression_level='balanced')
summary = compressor.compress(text, mode='summary')
```

## 性能对比

### 压缩质量
- **TextRank**：最高质量，考虑句子间语义关系
- **默认压缩器**：中等质量，基于TF-IDF
- **混合压缩器**：根据可用性选择最佳算法

### 处理速度
- **默认压缩器**：最快，纯Python实现
- **TextRank**：较慢，需要构建图和计算PageRank
- **混合压缩器**：取决于选择的算法

### 资源占用
- **默认压缩器**：最低，内存占用小
- **TextRank**：较高，需要存储相似度矩阵
- **混合压缩器**：取决于选择的算法

## 依赖库

### 必需依赖
- `re` - 正则表达式
- `math` - 数学计算
- `heapq` - 堆算法
- `collections` - 集合数据结构

### 可选依赖
- `textrank4zh` - TextRank算法（用于TextRank压缩器）

## 注意事项

1. **中文支持**：所有压缩器都支持中文文本
2. **编码问题**：确保输入文本为UTF-8编码
3. **文本长度**：过长的文本可能影响性能
4. **压缩级别**：根据需求选择合适的压缩级别
5. **压缩模式**：根据使用场景选择合适的压缩模式
6. **算法选择**：混合压缩器会自动选择最佳算法
7. **降级处理**：TextRank不可用时会自动降级到默认压缩器
8. **性能监控**：监控压缩性能，及时调整参数