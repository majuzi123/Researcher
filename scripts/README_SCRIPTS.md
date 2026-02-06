# 评估脚本文档索引

## 📚 文档导航

### 快速开始
- 🚀 **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - 快速参考指南（推荐从这里开始）
  - 快速命令
  - 数据位置速查
  - 常见任务示例

### 详细文档
- 📘 **[BATCH_EVALUATION_FIX.md](./BATCH_EVALUATION_FIX.md)** - 批量评估脚本修复说明
  - 问题描述和解决方案
  - 采样逻辑说明
  - 使用方法

- 📗 **[DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md)** - 数据流程完整指南
  - 数据存储位置
  - 数据字段详细说明
  - 查询和分析示例
  - 统计指标说明

## 🔧 主要脚本

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `batch_evaluate_papers.py` | 批量评估论文变体 | train/test_with_variants.jsonl | evaluation_results/*.jsonl |
| `analyze_evaluation_results.py` | 分析评估结果 | evaluation_results/*.jsonl | analysis_output/*/ |
| `generate_variant_dataset.py` | 生成变体数据集 | train.jsonl, test.jsonl | *_with_variants.jsonl |

## 📊 数据流程图

```
原始数据集 (train.jsonl, test.jsonl)
    ↓
generate_variant_dataset.py
    ↓
变体数据集 (*_with_variants.jsonl)
    每篇论文 × 6个变体
    ↓
batch_evaluate_papers.py
    采样100篇论文（每篇包含所有变体）
    ↓
评估结果 (evaluation_results/)
    ├── evaluation_results_*.jsonl    ← 所有评分数据
    └── evaluation_summary_*.json     ← 汇总统计
    ↓
analyze_evaluation_results.py
    ↓
分析报告 (analysis_output/YYYYMMDD_HHMMSS/)
    ├── variant_statistics.csv        ← Excel可打开
    ├── detailed_report.md            ← 详细报告
    ├── processed_data.csv            ← 完整数据
    └── visualizations/               ← 图表
        ├── variant_comparison.png
        ├── rating_distribution.png
        └── ...
```

## 🎯 快速任务指南

### 我想... 那么...

| 任务 | 文档/命令 |
|------|----------|
| **快速了解整个系统** | 阅读 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) |
| **运行评估** | `python scripts/batch_evaluate_papers.py` |
| **查看评估结果** | `cat evaluation_results/evaluation_summary_*.json \| python -m json.tool` |
| **分析结果** | `python scripts/analyze_evaluation_results.py` |
| **查看变体对比** | `open analysis_output/*/variant_statistics.csv` |
| **查看可视化图表** | `open analysis_output/*/visualizations/` |
| **了解数据格式** | 阅读 [DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md) 第2节 |
| **查询特定数据** | 参考 [DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md) 第5节 |
| **了解统计指标** | 阅读 [DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md) 第6节 |
| **排查问题** | 参考 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) 问题排查部分 |

## 📁 重要目录

```
Researcher/
├── scripts/                              # 脚本目录
│   ├── batch_evaluate_papers.py          # 批量评估
│   ├── analyze_evaluation_results.py     # 分析结果
│   ├── generate_variant_dataset.py       # 生成数据集
│   ├── QUICK_REFERENCE.md               # 快速参考 ⭐
│   ├── BATCH_EVALUATION_FIX.md          # 修复说明
│   ├── DATA_FLOW_GUIDE.md               # 数据流程指南
│   └── README_SCRIPTS.md                # 本文件
│
├── evaluation_results/                   # 评估结果 ⭐
│   ├── evaluation_results_*.jsonl        # 详细数据
│   └── evaluation_summary_*.json         # 汇总统计
│
├── analysis_output/                      # 分析输出 ⭐
│   └── YYYYMMDD_HHMMSS/
│       ├── variant_statistics.csv
│       ├── detailed_report.md
│       └── visualizations/
│
└── util/                                 # 数据集
    ├── train_with_variants.jsonl
    └── test_with_variants.jsonl
```

## ❓ 常见问题

### Q1: 评估数据保存在哪里？
**A**: `evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl`

每行一条 JSON 记录，包含每篇论文每个变体的完整评估数据（评分、决定、各维度评分等）。

### Q2: 如何查看变体对比？
**A**: 有多种方式：
1. 终端查看：`cat evaluation_results/evaluation_summary_*.json | python -m json.tool`
2. Excel 查看：`open analysis_output/*/variant_statistics.csv`
3. 图表查看：`open analysis_output/*/visualizations/variant_comparison.png`

### Q3: 每个变体有多少篇论文？
**A**: 脚本确保每个变体有相同数量的论文（默认100篇）。
- 采样100篇基础论文
- 每篇论文有6个变体
- 总共 100 × 6 = 600 条评估记录

### Q4: 分析脚本做了什么？
**A**: `analyze_evaluation_results.py` 自动执行：
1. 加载最新的评估结果
2. 计算整体统计（均值、中位数、标准差等）
3. 按变体分组对比
4. 生成可视化图表（分布图、箱线图、热力图等）
5. 进行统计检验（t-test）
6. 生成详细的 Markdown 报告
7. 导出 CSV 格式数据

### Q5: 如何自定义采样数量？
**A**: 编辑 `batch_evaluate_papers.py` 中的配置：
```python
SAMPLE_SIZE = 100  # 改为你想要的数量
```

## 🔗 相关文档

- [评估指南](../docs/EVALUATION_GUIDE_CN.md)
- [数据集格式](../docs/DATASET_FORMAT.md)
- [项目结构](../docs/PROJECT_STRUCTURE.md)

## 📝 更新日志

- **2026-02-07**: 修复采样逻辑，确保每个变体数量相同
- **2026-02-07**: 添加详细的数据流程文档
- **2026-02-07**: 创建快速参考指南

---

**维护者**: AI Research Team  
**最后更新**: 2026-02-07

