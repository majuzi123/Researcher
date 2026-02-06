# batch_evaluate_papers.py 逻辑验证报告

## ✅ 代码逻辑分析

### 1️⃣ 核心逻辑流程

```
加载数据 → 按paper_id分组 → 采样基础论文 → 获取所有变体 → 评估 → 保存结果
```

**详细步骤**:

1. **加载数据** (load_dataset)
   - 从 `train_with_variants.jsonl` 和 `test_with_variants.jsonl` 加载
   - 每行一个 JSON 对象

2. **分组** (group_papers_by_id)
   - 按 `paper_id` 分组
   - 每个 `paper_id` 包含多个变体（original, no_abstract, no_introduction, no_methods, no_experiments, no_conclusion）

3. **采样** (sample_papers)
   - 采样 N 个**基础论文 ID**（默认 100）
   - 自动计算 train/test 比例（或使用指定比例）
   - 为每个采样的 paper_id，收集**所有变体**

4. **评估** (evaluate_papers)
   - 使用 CycleReviewer 逐一评估
   - 记录评分、决定、各维度评分等

5. **保存** (save_results)
   - JSONL 格式保存详细结果
   - JSON 格式保存汇总统计

---

## 📊 与文档对照检查

### ✅ 配置参数对照

| 文档声称 | 代码实际 | 是否一致 | 备注 |
|---------|---------|---------|------|
| `SAMPLE_SIZE = 100` | ✅ `SAMPLE_SIZE = 100` | ✅ 一致 | 基础论文数量 |
| `TRAIN_RATIO = 0.8` | ❌ `TRAIN_RATIO = None` | ⚠️ **不一致** | 代码实际是自动计算 |
| `MODEL_SIZE = "8B"` | ✅ `MODEL_SIZE = "8B"` | ✅ 一致 | |
| `SEED = 42` | ✅ `SEED = 42` | ✅ 一致 | |

**发现问题 #1**: 文档说 `TRAIN_RATIO = 0.8`，但代码实际是 `None`（自动计算）

---

### ✅ 采样逻辑对照

**文档声称**:
> Samples 100 base papers (each with all variants)

**代码实际**:
```python
# 1. 按 paper_id 分组
train_grouped = group_papers_by_id(train_papers)  
test_grouped = group_papers_by_id(test_papers)

# 2. 采样 N 个 paper_id
sampled_train_ids = random.sample(train_paper_ids, train_sample_size)
sampled_test_ids = random.sample(test_paper_ids, test_sample_size)

# 3. 收集所有变体
for paper_id in sampled_train_ids:
    for paper in train_grouped[paper_id]:  # 所有变体
        all_sampled.append(paper)
```

**结论**: ✅ **完全一致** - 确实是采样基础论文然后获取所有变体

---

### ✅ 输出数据格式对照

#### 详细评估数据 (JSONL)

**文档声称的格式**:
```json
{
  "paper_id": "论文ID",
  "title": "论文标题",
  "variant_type": "变体类型",
  "dataset_split": "数据集",
  "evaluation": {
    "avg_rating": 7.5,
    "paper_decision": "Accept",
    "confidence": 4,
    "originality": 8,
    "quality": 7,
    "clarity": 7,
    "significance": 8,
    "strength": ["优点1", "优点2"],
    "weaknesses": ["缺点1", "缺点2"],
    "meta_review": "总结..."
  },
  "text_length": 25430,
  "evaluation_timestamp": "2026-02-07T14:30:52"
}
```

**代码实际生成**:
```python
result = {
    'paper_id': paper.get('paper_id', f'paper_{i}'),
    'title': paper.get('title', 'Unknown'),
    'variant_type': paper.get('variant_type', 'unknown'),
    'dataset_split': paper.get('dataset_split', 'unknown'),
    'evaluation': {
        'avg_rating': review.get('avg_rating', 0),
        'paper_decision': review.get('paper_decision', 'Unknown'),
        'confidence': review.get('confidence', 0),
        'strength': review.get('strength', []),
        'weaknesses': review.get('weaknesses', []),
        'meta_review': review.get('meta_review', ''),
        'originality': review.get('originality', 0),
        'quality': review.get('quality', 0),
        'clarity': review.get('clarity', 0),
        'significance': review.get('significance', 0),
    },
    'text_length': len(paper_text),
    'evaluation_timestamp': datetime.now().isoformat()
}
```

**结论**: ✅ **完全一致** - 字段名称、结构、类型都匹配

---

#### 汇总统计数据 (JSON)

**文档声称的格式**:
```json
{
  "total_papers": 600,
  "timestamp": "20260207_143052",
  "config": {...},
  "variant_distribution": {...},
  "decision_distribution": {...},
  "rating_statistics": {...},
  "variant_statistics": {
    "original": {
      "count": 100,
      "avg_rating": 7.8,
      "median_rating": 8.0,
      "std_rating": 1.1,
      "decision_distribution": {...},
      "accept_rate": 0.85,
      "avg_originality": 7.9,
      "avg_quality": 8.0,
      "avg_clarity": 7.7,
      "avg_significance": 7.8
    },
    ...
  }
}
```

**代码实际生成**:
```python
summary = {
    'total_papers': len(results),
    'timestamp': timestamp,
    'config': {
        'sample_size': SAMPLE_SIZE,
        'train_ratio': TRAIN_RATIO,
        'model_size': MODEL_SIZE,
        'seed': SEED
    },
    'variant_distribution': dict(variant_counts),
    'decision_distribution': dict(decision_counts),
    'rating_statistics': {
        'mean': statistics.mean(ratings),
        'median': statistics.median(ratings),
        'min': min(ratings),
        'max': max(ratings),
        'std': statistics.stdev(ratings)
    },
    'variant_statistics': {
        variant: {
            'count': len(variant_results),
            'avg_rating': statistics.mean(variant_ratings),
            'median_rating': statistics.median(variant_ratings),
            'std_rating': statistics.stdev(variant_ratings),
            'decision_distribution': dict(variant_decisions),
            'accept_rate': ...,
            'avg_originality': ...,
            'avg_quality': ...,
            'avg_clarity': ...,
            'avg_significance': ...
        }
    }
}
```

**结论**: ✅ **完全一致** - 所有字段都按文档生成

---

### ✅ 输出文件位置对照

| 文档声称 | 代码实际 | 是否一致 |
|---------|---------|---------|
| `evaluation_results/evaluation_results_*.jsonl` | ✅ `evaluation_results/evaluation_results_{timestamp}.jsonl` | ✅ 一致 |
| `evaluation_results/evaluation_summary_*.json` | ✅ `evaluation_results/evaluation_summary_{timestamp}.json` | ✅ 一致 |

---

## 🔍 关键逻辑验证

### ✅ 验证点 1: 每个变体数量相同

**代码逻辑**:
```python
# 采样 100 个 paper_id
sampled_train_ids = random.sample(train_paper_ids, 73)  # 假设 73%
sampled_test_ids = random.sample(test_paper_ids, 27)    # 假设 27%

# 为每个 paper_id 获取所有变体
for paper_id in sampled_train_ids:
    for paper in train_grouped[paper_id]:  # 6个变体
        all_sampled.append(paper)
```

**结果**:
- 100 个 paper_id × 6 个变体 = 600 篇论文
- 每个变体恰好 100 篇

**结论**: ✅ **逻辑正确** - 确保每个变体数量相同

---

### ✅ 验证点 2: 数据完整性

**代码检查**:
```python
# 评估时记录所有字段
result = {
    'paper_id': ...,
    'title': ...,
    'variant_type': ...,
    'dataset_split': ...,
    'evaluation': {
        'avg_rating': ...,           # ✅
        'paper_decision': ...,        # ✅
        'confidence': ...,            # ✅
        'strength': ...,              # ✅
        'weaknesses': ...,            # ✅
        'meta_review': ...,           # ✅
        'originality': ...,           # ✅
        'quality': ...,               # ✅
        'clarity': ...,               # ✅
        'significance': ...,          # ✅
    },
    'text_length': ...,               # ✅
    'evaluation_timestamp': ...       # ✅
}
```

**结论**: ✅ **数据完整** - 所有文档声称的字段都被记录

---

### ✅ 验证点 3: 统计计算正确性

**代码检查**:
```python
# 按变体分组统计
for variant in variants:
    variant_results = [r for r in results if r['variant_type'] == variant]
    variant_ratings = [r['evaluation']['avg_rating'] for r in variant_results]
    
    summary['variant_statistics'][variant] = {
        'count': len(variant_results),                    # ✅ 计数
        'avg_rating': statistics.mean(variant_ratings),   # ✅ 平均值
        'median_rating': statistics.median(variant_ratings), # ✅ 中位数
        'std_rating': statistics.stdev(variant_ratings),  # ✅ 标准差
        'accept_rate': ...,                               # ✅ 接受率
        'avg_originality': ...,                           # ✅ 各维度平均值
        ...
    }
```

**结论**: ✅ **统计正确** - 使用 Python statistics 模块正确计算

---

## ⚠️ 发现的不一致

### 问题 1: TRAIN_RATIO 配置

**文档说**:
```markdown
**Configuration** (in `batch_evaluate_papers.py`):
- `TRAIN_RATIO = 0.8` - Ratio of train vs test papers
```

**代码实际**:
```python
TRAIN_RATIO = None  # Auto-calculate based on actual dataset ratio
```

**影响**:
- 文档说是固定 80% train / 20% test
- 实际是根据数据集自动计算比例
- 如果 train 有 1234 篇，test 有 456 篇，则比例是 73% / 27%

**建议**: ⚠️ **需要更新文档**

---

### 问题 2: 文档路径

**文档中的路径**:
```bash
cd D:\Mike\PycharmProjects\Researcher  # Windows 路径
```

**实际环境**:
```
/Users/maying/PycharmProjects/pythonProject/Researcher  # macOS 路径
```

**建议**: ⚠️ **文档应使用通用路径表示**

---

## ✅ 总体结论

### 核心逻辑: ✅ **完全符合文档**
1. ✅ 采样 100 篇基础论文
2. ✅ 每篇论文包含所有 6 个变体
3. ✅ 总共 600 篇论文评估
4. ✅ 每个变体恰好 100 篇

### 数据格式: ✅ **完全符合文档**
1. ✅ JSONL 格式详细数据
2. ✅ JSON 格式汇总统计
3. ✅ 所有字段都按文档生成
4. ✅ 文件命名和位置正确

### 统计计算: ✅ **正确且完整**
1. ✅ 整体统计（均值、中位数、标准差）
2. ✅ 按变体分组统计
3. ✅ 接受率、各维度评分
4. ✅ 终端打印变体对比

### 需要修正的文档问题:
1. ⚠️ `TRAIN_RATIO` 实际是 `None`（自动计算），而非固定 `0.8`
2. ⚠️ 路径应使用通用表示
3. ⚠️ 文档应说明"自动计算比例"的行为

---

## 📝 推荐的文档更新

### README_EVALUATION.md 应该改为:

```markdown
**Configuration** (in `batch_evaluate_papers.py`):
- `SAMPLE_SIZE = 100` - Number of BASE papers to sample
- `TRAIN_RATIO = None` - Auto-calculate ratio from dataset (or set to float like 0.8 for fixed ratio)
- `MODEL_SIZE = "8B"` - CycleReviewer model size
- `SEED = 42` - Random seed for reproducibility

**Note**: When `TRAIN_RATIO = None`, the script automatically calculates the ratio 
based on the number of unique papers in train vs test sets. For example, if train 
has 1234 papers and test has 456 papers, it will sample 73 from train and 27 from test.
```

---

## 🎯 代码行为总结

当运行 `batch_evaluate_papers.py` 时:

1. **输入**: 
   - `util/train_with_variants.jsonl` (例如: 7404篇，1234个唯一paper_id × 6变体)
   - `util/test_with_variants.jsonl` (例如: 2736篇，456个唯一paper_id × 6变体)

2. **处理**:
   - 按 paper_id 分组
   - 自动计算比例: 1234/(1234+456) = 73%
   - 采样 73 个 train paper_id + 27 个 test paper_id
   - 获取这 100 个 paper_id 的所有 6 个变体 = 600 篇论文

3. **输出**:
   - `evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl` (600行)
   - `evaluation_results/evaluation_summary_YYYYMMDD_HHMMSS.json` (含变体统计)

4. **终端输出**:
   ```
   [INFO] Sampled papers by variant type:
     no_abstract: 100
     no_conclusion: 100
     no_experiments: 100
     no_introduction: 100
     no_methods: 100
     original: 100
   
   VARIANT COMPARISON
   ======================================================================
   no_abstract:
     Count: 100
     Avg Rating: 6.30
     Accept Rate: 58.0%
     ...
   original:
     Count: 100
     Avg Rating: 7.80
     Accept Rate: 85.0%
     ...
   ```

---

**验证日期**: 2026-02-07  
**验证人**: AI Assistant  
**结论**: ✅ 代码逻辑**严格按照设计文档**实现，仅有配置参数文档需要更新

