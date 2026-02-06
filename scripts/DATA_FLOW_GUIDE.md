# 评估结果数据流程说明

## 数据流程总览

```
数据生成 → 批量评估 → 结果存储 → 详细分析 → 可视化报告
    ↓           ↓          ↓          ↓           ↓
generate_   batch_     evaluation_ analyze_   analysis_
variant_    evaluate_  results/    evaluation_ output/
dataset.py  papers.py              results.py
```

## 1. 评估结果数据存储位置

### 主要输出目录
```
Researcher/
└── evaluation_results/          # 评估结果主目录
    ├── evaluation_results_20260207_143052.jsonl    # 详细评估数据
    └── evaluation_summary_20260207_143052.json     # 汇总统计
```

### 详细评估数据 (JSONL 格式)
**文件**: `evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl`

**内容**: 每行一条记录，包含每篇论文每个变体的完整评估数据

**数据结构**:
```json
{
  "paper_id": "1706.03762",
  "title": "Attention Is All You Need",
  "variant_type": "no_abstract",
  "dataset_split": "train",
  "evaluation": {
    "avg_rating": 7.5,
    "paper_decision": "Accept",
    "confidence": 4,
    "strength": ["Novel architecture", "Strong empirical results"],
    "weaknesses": ["Limited theoretical analysis"],
    "meta_review": "This paper presents a significant contribution...",
    "originality": 8,
    "quality": 7,
    "clarity": 7,
    "significance": 8
  },
  "text_length": 25430,
  "evaluation_timestamp": "2026-02-07T14:30:52.123456"
}
```

### 汇总统计 (JSON 格式)
**文件**: `evaluation_results/evaluation_summary_YYYYMMDD_HHMMSS.json`

**内容**: 整体统计和按变体分组的统计

**数据结构**:
```json
{
  "total_papers": 600,
  "timestamp": "20260207_143052",
  "config": {
    "sample_size": 100,
    "train_ratio": null,
    "model_size": "8B",
    "seed": 42
  },
  "variant_distribution": {
    "original": 100,
    "no_abstract": 100,
    "no_introduction": 100,
    "no_methods": 100,
    "no_experiments": 100,
    "no_conclusion": 100
  },
  "decision_distribution": {
    "Accept": 450,
    "Reject": 120,
    "Borderline": 30
  },
  "rating_statistics": {
    "mean": 7.2,
    "median": 7.5,
    "min": 3.5,
    "max": 9.5,
    "std": 1.3
  },
  "variant_statistics": {
    "original": {
      "count": 100,
      "avg_rating": 7.8,
      "median_rating": 8.0,
      "std_rating": 1.1,
      "decision_distribution": {
        "Accept": 85,
        "Reject": 12,
        "Borderline": 3
      },
      "accept_rate": 0.85,
      "avg_originality": 7.9,
      "avg_quality": 8.0,
      "avg_clarity": 7.7,
      "avg_significance": 7.8
    },
    "no_abstract": {
      "count": 100,
      "avg_rating": 6.5,
      "accept_rate": 0.65,
      ...
    },
    ...
  }
}
```

## 2. 数据字段说明

### 论文基础信息
| 字段 | 类型 | 说明 |
|------|------|------|
| `paper_id` | string | 论文唯一标识符 |
| `title` | string | 论文标题 |
| `variant_type` | string | 变体类型 (original/no_abstract/no_introduction/no_methods/no_experiments/no_conclusion) |
| `dataset_split` | string | 数据集分组 (train/test) |
| `text_length` | integer | 论文文本长度 |
| `evaluation_timestamp` | string | 评估时间戳 (ISO 8601) |

### 评估指标
| 字段 | 类型 | 范围 | 说明 |
|------|------|------|------|
| `avg_rating` | float | 0-10 | 平均评分 |
| `paper_decision` | string | - | 论文决定 (Accept/Reject/Borderline) |
| `confidence` | integer | 1-5 | 评审信心等级 |
| `originality` | float | 0-10 | 原创性评分 |
| `quality` | float | 0-10 | 质量评分 |
| `clarity` | float | 0-10 | 清晰度评分 |
| `significance` | float | 0-10 | 重要性评分 |
| `strength` | array | - | 优点列表 |
| `weaknesses` | array | - | 缺点列表 |
| `meta_review` | string | - | 元评审总结 |

## 3. 分析脚本输出

运行 `analyze_evaluation_results.py` 后，会在以下目录生成分析结果：

```
Researcher/
└── analysis_output/
    └── YYYYMMDD_HHMMSS/                    # 时间戳目录
        ├── overall_statistics.json         # 整体统计
        ├── variant_statistics.csv          # 变体对比统计表
        ├── rating_range_statistics.json    # 评分范围统计
        ├── processed_data.csv              # 处理后的完整数据
        ├── detailed_report.md              # 详细分析报告
        └── visualizations/                 # 可视化图表
            ├── rating_distribution.png     # 评分分布图
            ├── variant_comparison.png      # 变体对比图
            ├── rating_by_variant.png       # 各变体评分箱线图
            ├── decision_distribution.png   # 决定分布图
            ├── aspect_ratings_heatmap.png  # 各维度评分热力图
            └── correlation_matrix.png      # 指标相关性矩阵
```

### 3.1 整体统计 (`overall_statistics.json`)
```json
{
  "total_papers": 600,
  "rating_statistics": {
    "mean": 7.2,
    "median": 7.5,
    "std": 1.3,
    "min": 3.5,
    "max": 9.5,
    "q25": 6.5,
    "q75": 8.2
  },
  "aspect_ratings": {
    "originality": 7.3,
    "quality": 7.4,
    "clarity": 7.0,
    "significance": 7.2
  },
  "decision_distribution": {
    "Accept": 450,
    "Reject": 120,
    "Borderline": 30
  },
  "variant_distribution": {
    "original": 100,
    "no_abstract": 100,
    ...
  },
  "confidence_mean": 3.8
}
```

### 3.2 变体统计表 (`variant_statistics.csv`)
```csv
variant_type,count,avg_rating_mean,avg_rating_std,originality,quality,clarity,significance,accept_rate,reject_rate
original,100,7.80,1.10,7.90,8.00,7.70,7.80,85.0,12.0
no_conclusion,100,7.20,1.25,7.10,7.30,7.00,7.15,75.0,20.0
no_experiments,100,6.90,1.35,6.80,6.95,6.85,6.90,68.0,25.0
no_methods,100,6.75,1.40,6.70,6.80,6.75,6.72,65.0,28.0
no_introduction,100,6.50,1.45,6.50,6.60,6.45,6.55,62.0,30.0
no_abstract,100,6.30,1.50,6.35,6.45,6.30,6.40,58.0,35.0
```

### 3.3 详细分析报告 (`detailed_report.md`)
包含：
- 数据概览
- 变体对比详情
- 统计检验结果（t-test）
- 关键发现和洞察
- 建议和结论

## 4. 使用流程

### 步骤 1: 运行评估
```bash
cd /Users/maying/PycharmProjects/pythonProject/Researcher
python scripts/batch_evaluate_papers.py
```

**输出**:
- `evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl`
- `evaluation_results/evaluation_summary_YYYYMMDD_HHMMSS.json`

### 步骤 2: 分析结果
```bash
python scripts/analyze_evaluation_results.py
```

**输出**:
- `analysis_output/YYYYMMDD_HHMMSS/` 目录下的所有分析文件和图表

### 步骤 3: 查看结果

#### 查看汇总统计
```bash
cat evaluation_results/evaluation_summary_*.json | python -m json.tool
```

#### 查看变体对比
```bash
cat analysis_output/*/variant_statistics.csv
```

#### 查看详细报告
```bash
cat analysis_output/*/detailed_report.md
```

#### 查看可视化图表
在文件管理器中打开 `analysis_output/YYYYMMDD_HHMMSS/visualizations/` 目录

## 5. 数据查询示例

### 使用 Python 加载和查询数据

```python
import json
import pandas as pd

# 加载详细评估数据
data = []
with open('evaluation_results/evaluation_results_20260207_143052.jsonl', 'r') as f:
    for line in f:
        data.append(json.loads(line))

df = pd.DataFrame(data)

# 查询特定论文的所有变体
paper_variants = df[df['paper_id'] == '1706.03762']
print(paper_variants[['variant_type', 'evaluation.avg_rating', 'evaluation.paper_decision']])

# 比较各变体的平均评分
variant_ratings = df.groupby('variant_type')['evaluation.avg_rating'].agg(['mean', 'std', 'count'])
print(variant_ratings)

# 查找评分最高的论文
top_papers = df.nlargest(10, 'evaluation.avg_rating')
print(top_papers[['paper_id', 'title', 'variant_type', 'evaluation.avg_rating']])

# 统计每个变体的接受率
for variant in df['variant_type'].unique():
    variant_df = df[df['variant_type'] == variant]
    accept_rate = variant_df['evaluation.paper_decision'].str.contains('Accept').sum() / len(variant_df)
    print(f"{variant}: {accept_rate:.1%}")
```

### 使用 jq 查询 JSONL 数据

```bash
# 查询所有 original 变体的平均评分
cat evaluation_results/evaluation_results_*.jsonl | \
  jq -s 'map(select(.variant_type == "original")) | map(.evaluation.avg_rating) | add/length'

# 查询评分最高的10篇论文
cat evaluation_results/evaluation_results_*.jsonl | \
  jq -s 'sort_by(.evaluation.avg_rating) | reverse | .[0:10] | .[] | {title, variant_type, rating: .evaluation.avg_rating}'

# 统计各决定的数量
cat evaluation_results/evaluation_results_*.jsonl | \
  jq -s 'group_by(.evaluation.paper_decision) | map({decision: .[0].evaluation.paper_decision, count: length})'
```

## 6. 关键分析指标

### 6.1 变体影响分析
- **评分下降幅度**: 相比 original 的评分变化百分比
- **接受率差异**: 各变体的 Accept 决定比例
- **评分方差**: 评分的稳定性

### 6.2 维度对比
- **原创性 (Originality)**: 缺少哪个部分影响最大
- **质量 (Quality)**: 整体质量受影响程度
- **清晰度 (Clarity)**: 结构完整性的重要性
- **重要性 (Significance)**: 贡献声明的影响

### 6.3 统计检验
- **t-test**: original vs 各变体的显著性差异
- **ANOVA**: 所有变体之间的整体差异
- **相关性分析**: 各评分维度之间的相关性

## 7. 常见问题

### Q1: 如何找到最新的评估结果？
```bash
ls -lt evaluation_results/evaluation_results_*.jsonl | head -1
```

### Q2: 如何合并多次评估的结果？
```python
import json
import glob

all_data = []
for file in glob.glob('evaluation_results/evaluation_results_*.jsonl'):
    with open(file, 'r') as f:
        for line in f:
            all_data.append(json.loads(line))

# 去重（基于 paper_id + variant_type + evaluation_timestamp）
# 保存合并后的数据
```

### Q3: 数据太大怎么办？
使用流式处理或采样：
```python
# 只分析前 N 条记录
import itertools
with open('evaluation_results/evaluation_results_*.jsonl', 'r') as f:
    for line in itertools.islice(f, N):
        data = json.loads(line)
        # 处理...
```

## 8. 数据备份建议

```bash
# 创建备份
tar -czf evaluation_backup_$(date +%Y%m%d).tar.gz evaluation_results/ analysis_output/

# 恢复备份
tar -xzf evaluation_backup_20260207.tar.gz
```

## 总结

评估系统完整记录了：
1. ✅ **每篇论文**的每个**变体**的评估数据
2. ✅ **详细的评分和决定**（avg_rating, paper_decision, 各维度评分）
3. ✅ **时间戳和元数据**（便于追溯）
4. ✅ **结构化存储**（JSONL + JSON，易于查询和分析）
5. ✅ **自动化分析**（统计、可视化、报告生成）

所有数据都保存在：
- `evaluation_results/` - 原始评估数据
- `analysis_output/` - 分析结果和可视化

