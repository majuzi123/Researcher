# batch_evaluate_papers.py 逻辑说明

## 🎯 核心逻辑（简洁版）

```
输入数据集 → 按paper_id分组 → 采样N个paper_id → 获取所有变体 → 逐一评估 → 保存结果
```

## 📋 执行流程

### 1. 加载数据
```python
train_papers = load_dataset("util/train_with_variants.jsonl")
test_papers = load_dataset("util/test_with_variants.jsonl")
```

### 2. 按paper_id分组
```python
# 每个paper_id有6个变体
train_grouped = {
    "1706.03762": [
        {variant_type: "original", ...},
        {variant_type: "no_abstract", ...},
        {variant_type: "no_introduction", ...},
        {variant_type: "no_methods", ...},
        {variant_type: "no_experiments", ...},
        {variant_type: "no_conclusion", ...}
    ],
    ...
}
```

### 3. 采样
```python
# 配置: SAMPLE_SIZE = 100
# 自动计算比例 (例如: train有1234个ID, test有456个ID)
# 比例 = 1234/(1234+456) = 73%

# 采样:
sampled_train_ids = random.sample(train_paper_ids, 73)  # 73个paper_id
sampled_test_ids = random.sample(test_paper_ids, 27)    # 27个paper_id
```

### 4. 获取所有变体
```python
all_sampled = []
for paper_id in sampled_train_ids + sampled_test_ids:
    # 获取该paper_id的所有6个变体
    for variant in grouped[paper_id]:
        all_sampled.append(variant)

# 结果: 100个paper_id × 6个变体 = 600篇论文
```

### 5. 评估
```python
for paper in all_sampled:  # 600篇
    review = reviewer.evaluate(paper['text'])
    result = {
        'paper_id': paper['paper_id'],
        'variant_type': paper['variant_type'],
        'evaluation': {
            'avg_rating': review['avg_rating'],
            'paper_decision': review['paper_decision'],
            'originality': review['originality'],
            'quality': review['quality'],
            'clarity': review['clarity'],
            'significance': review['significance'],
            ...
        }
    }
    results.append(result)
```

### 6. 保存结果
```python
# 详细数据 (JSONL格式，每行一条记录)
evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl

# 汇总统计 (JSON格式)
evaluation_results/evaluation_summary_YYYYMMDD_HHMMSS.json
```

## ✅ 关键保证

1. **每个变体数量相同**: 每个变体恰好100篇（因为采样100个paper_id，每个有6个变体）
2. **数据完整**: 每条记录包含所有评分和决定
3. **可复现**: 使用固定随机种子（SEED=42）
4. **自动比例**: 根据数据集自动计算train/test比例

## 📊 输出数据示例

### 详细数据 (evaluation_results_*.jsonl)
```json
{"paper_id": "1706.03762", "variant_type": "original", "evaluation": {"avg_rating": 7.8, ...}}
{"paper_id": "1706.03762", "variant_type": "no_abstract", "evaluation": {"avg_rating": 6.5, ...}}
{"paper_id": "1706.03762", "variant_type": "no_introduction", "evaluation": {"avg_rating": 6.2, ...}}
...
{"paper_id": "another_paper", "variant_type": "original", "evaluation": {...}}
...
```

### 汇总统计 (evaluation_summary_*.json)
```json
{
  "total_papers": 600,
  "variant_distribution": {
    "original": 100,
    "no_abstract": 100,
    "no_introduction": 100,
    "no_methods": 100,
    "no_experiments": 100,
    "no_conclusion": 100
  },
  "variant_statistics": {
    "original": {
      "count": 100,
      "avg_rating": 7.80,
      "accept_rate": 0.85,
      "avg_originality": 7.90,
      "avg_quality": 8.00,
      "avg_clarity": 7.70,
      "avg_significance": 7.80
    },
    "no_abstract": {
      "count": 100,
      "avg_rating": 6.30,
      "accept_rate": 0.58,
      ...
    },
    ...
  }
}
```

## 🔍 与文档对照结论

### ✅ 完全符合文档的部分
- ✅ 采样逻辑: 100个基础论文，每个包含所有变体
- ✅ 数据格式: JSONL详细数据 + JSON汇总统计
- ✅ 字段内容: 所有文档声称的字段都生成
- ✅ 输出位置: evaluation_results/ 目录
- ✅ 统计计算: 正确计算各变体的统计数据

### ⚠️ 与文档不一致的部分
- ⚠️ `TRAIN_RATIO`: 文档说0.8，代码是None（自动计算）
  - **影响**: 实际比例取决于数据集，而非固定80/20
  - **已修正**: 已更新文档说明

## 💡 使用建议

### 如果想要固定比例（如 80/20）
```python
# 在 batch_evaluate_papers.py 中修改:
TRAIN_RATIO = 0.8  # 固定80% train, 20% test
```

### 如果想要更多样本
```python
SAMPLE_SIZE = 200  # 200个基础论文 × 6变体 = 1200次评估
```

### 如果想查看特定论文的所有变体
```python
python scripts/example_query_results.py
# 会展示如何查询和分析结果
```

## 📚 相关文档
- [LOGIC_VERIFICATION.md](./LOGIC_VERIFICATION.md) - 详细验证报告
- [DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md) - 完整数据流程
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 快速参考

---
**最后更新**: 2026-02-07  
**验证状态**: ✅ 逻辑严格按文档实现，仅配置说明有小差异（已修正）

