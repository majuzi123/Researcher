# 评估系统快速参考

## 快速开始

### 1. 运行评估（生成数据）
```bash
cd /Users/maying/PycharmProjects/pythonProject/Researcher
python scripts/batch_evaluate_papers.py
```

**输出位置**: 
- `evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl` ← **所有评分数据在这里**
- `evaluation_results/evaluation_summary_YYYYMMDD_HHMMSS.json` ← **汇总统计在这里**

**包含数据**: 
- ✅ 100篇论文 × 6个变体 = 600条评估记录
- ✅ 每条记录包含：评分、决定、原创性、质量、清晰度、重要性

---

### 2. 分析结果（生成报告）
```bash
python scripts/analyze_evaluation_results.py
```

**输出位置**: 
- `analysis_output/YYYYMMDD_HHMMSS/` ← **所有分析结果在这里**

**包含内容**:
- ✅ `variant_statistics.csv` - Excel可打开的变体对比表
- ✅ `detailed_report.md` - 详细分析报告
- ✅ `visualizations/` - 各种图表

---

## 数据位置速查

| 数据类型 | 文件路径 | 格式 | 说明 |
|---------|---------|------|------|
| **原始评估数据** | `evaluation_results/evaluation_results_*.jsonl` | JSONL | 每行一条评估记录 |
| **汇总统计** | `evaluation_results/evaluation_summary_*.json` | JSON | 按变体分组的统计 |
| **变体对比表** | `analysis_output/*/variant_statistics.csv` | CSV | Excel可打开 |
| **详细报告** | `analysis_output/*/detailed_report.md` | Markdown | 完整分析报告 |
| **可视化图表** | `analysis_output/*/visualizations/*.png` | PNG | 各种统计图表 |

---

## 评估数据字段

每条评估记录包含：

```json
{
  "paper_id": "论文ID",
  "title": "论文标题",
  "variant_type": "变体类型 (original/no_abstract/no_introduction/no_methods/no_experiments/no_conclusion)",
  "dataset_split": "数据集 (train/test)",
  "evaluation": {
    "avg_rating": 7.5,              // 平均评分 (0-10)
    "paper_decision": "Accept",      // 决定 (Accept/Reject/Borderline)
    "confidence": 4,                 // 信心 (1-5)
    "originality": 8,                // 原创性 (0-10)
    "quality": 7,                    // 质量 (0-10)
    "clarity": 7,                    // 清晰度 (0-10)
    "significance": 8,               // 重要性 (0-10)
    "strength": ["优点1", "优点2"],
    "weaknesses": ["缺点1", "缺点2"],
    "meta_review": "总结..."
  },
  "text_length": 25430,
  "evaluation_timestamp": "2026-02-07T14:30:52"
}
```

---

## 快速查询命令

### 查看最新评估文件
```bash
ls -lt evaluation_results/evaluation_results_*.jsonl | head -1
```

### 查看变体统计（终端）
```bash
cat evaluation_results/evaluation_summary_*.json | python -m json.tool | grep -A 10 "variant_statistics"
```

### 查看变体对比表（Excel）
```bash
open analysis_output/*/variant_statistics.csv
```

### 查看所有图表
```bash
open analysis_output/*/visualizations/
```

### 统计每个变体的平均评分（命令行）
```bash
cat evaluation_results/evaluation_results_*.jsonl | \
  jq -s 'group_by(.variant_type) | 
         map({variant: .[0].variant_type, 
              avg_rating: (map(.evaluation.avg_rating) | add / length)}) | 
         sort_by(.avg_rating) | reverse'
```

---

## Python 快速查询

### 加载和查看数据
```python
import json
import pandas as pd

# 方法1: 加载 JSONL 数据
data = []
with open('evaluation_results/evaluation_results_20260207_143052.jsonl') as f:
    for line in f:
        data.append(json.loads(line))

# 方法2: 直接用 pandas 读取 CSV（如果已经运行了分析脚本）
df = pd.read_csv('analysis_output/20260207_143052/processed_data.csv')

# 查看基本信息
print(df.info())
print(df.describe())
```

### 常用查询
```python
# 各变体平均评分
print(df.groupby('variant_type')['avg_rating'].mean().sort_values(ascending=False))

# 各变体接受率
print(df.groupby('variant_type')['paper_decision'].apply(
    lambda x: (x.str.contains('Accept').sum() / len(x) * 100)
))

# 找出评分最高的10篇论文
print(df.nlargest(10, 'avg_rating')[['title', 'variant_type', 'avg_rating']])

# 比较 original vs 其他变体
original = df[df['variant_type'] == 'original']['avg_rating'].mean()
for variant in df['variant_type'].unique():
    if variant != 'original':
        var_rating = df[df['variant_type'] == variant]['avg_rating'].mean()
        diff = var_rating - original
        print(f"{variant}: {var_rating:.2f} (Δ {diff:+.2f})")
```

---

## 常见任务

### ❓ 我想知道哪个部分最重要
查看 `variant_statistics.csv`，按 `avg_rating_mean` 排序，评分下降最多的变体对应最重要的部分

### ❓ 我想看可视化对比
打开 `analysis_output/*/visualizations/variant_comparison.png`

### ❓ 我想导出到 Excel 分析
所有数据已经有 CSV 格式：
- `variant_statistics.csv` - 变体对比
- `processed_data.csv` - 完整数据

### ❓ 我想看统计检验结果
查看 `detailed_report.md`，包含 t-test 结果

### ❓ 我想合并多次评估结果
```python
import json
import glob

all_data = []
for file in glob.glob('evaluation_results/evaluation_results_*.jsonl'):
    with open(file) as f:
        for line in f:
            all_data.append(json.loads(line))

# 去重并保存
import pandas as pd
df = pd.DataFrame(all_data)
df = df.drop_duplicates(subset=['paper_id', 'variant_type'])
df.to_json('merged_results.jsonl', orient='records', lines=True)
```

---

## 预期结果示例

### 终端输出（batch_evaluate_papers.py）
```
======================================================================
Batch Paper Evaluation Script
======================================================================

[INFO] Loading datasets...
[INFO] Loaded 7404 train papers, 2736 test papers

[INFO] Sampling 100 BASE papers (each with all variants)...
[INFO] Grouping papers by paper_id...
[INFO] Found 1234 unique papers in train set
[INFO] Found 456 unique papers in test set
[INFO] Auto-calculated train_ratio: 73.02%
[INFO] Sampling 73 base papers from train, 27 from test
[INFO] Total papers with all variants: 600

[INFO] Sampled papers by variant type:
  no_abstract: 100
  no_conclusion: 100
  no_experiments: 100
  no_introduction: 100
  no_methods: 100
  original: 100

[INFO] Expected 100 papers × 6 variants = 600 total papers
[INFO] Actual sampled papers: 600

[INFO] Initializing CycleReviewer (model size: 8B)...
[INFO] Evaluating 600 papers...
Evaluating papers: 100%|████████████| 600/600 [2:15:30<00:00, 13.55s/it]

======================================================================
VARIANT COMPARISON
======================================================================

no_abstract:
  Count: 100
  Avg Rating: 6.30
  Accept Rate: 58.0%
  Originality: 6.35
  Quality: 6.45
  Clarity: 6.30
  Significance: 6.40
  
...

original:
  Count: 100
  Avg Rating: 7.80
  Accept Rate: 85.0%
  Originality: 7.90
  Quality: 8.00
  Clarity: 7.70
  Significance: 7.80

======================================================================
Evaluation Complete!
======================================================================
Total papers evaluated: 598/600
Results saved to: evaluation_results/evaluation_results_20260207_143052.jsonl
Summary saved to: evaluation_results/evaluation_summary_20260207_143052.json
======================================================================
```

---

## 问题排查

### ❌ 找不到数据文件
```bash
# 检查评估结果目录
ls -la evaluation_results/

# 如果为空，需要先运行评估
python scripts/batch_evaluate_papers.py
```

### ❌ 分析脚本报错"No results found"
```bash
# 确保有评估结果文件
ls evaluation_results/evaluation_results_*.jsonl

# 如果没有，先运行评估
python scripts/batch_evaluate_papers.py
```

### ❌ 图表无法显示
确保安装了可视化依赖：
```bash
pip install matplotlib seaborn
```

---

## 文档索引

- 📘 **[BATCH_EVALUATION_FIX.md](./BATCH_EVALUATION_FIX.md)** - 修复说明和使用方法
- 📗 **[DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md)** - 完整数据流程和字段说明
- 📕 **本文档** - 快速参考

---

**最后更新**: 2026-02-07

