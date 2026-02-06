# 论文评估与分析流程使用指南

## 📋 概述

这个评估流程包含三个主要脚本：

1. **测试脚本** (`test_evaluation_pipeline.py`) - 验证环境配置
2. **批量评估** (`batch_evaluate_papers.py`) - 评估100篇论文样本
3. **结果分析** (`analyze_evaluation_results.py`) - 生成统计分析和可视化

## 🚀 快速开始

### 第一步：环境测试

运行测试脚本确认一切就绪：

```bash
cd D:\Mike\PycharmProjects\Researcher
python scripts/test_evaluation_pipeline.py
```

如果所有测试通过，继续下一步。

### 第二步：批量评估

评估100篇论文（80篇训练集 + 20篇测试集）：

```bash
python scripts/batch_evaluate_papers.py
```

**预计耗时**: 15-30分钟（取决于机器性能）

**输出文件**:
- `evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl`
- `evaluation_results/evaluation_summary_YYYYMMDD_HHMMSS.json`

### 第三步：结果分析

分析评估结果并生成图表：

```bash
python scripts/analyze_evaluation_results.py
```

**输出目录**: `analysis_output/YYYYMMDD_HHMMSS/`

包含：
- 8个可视化图表（PNG）
- 5个统计文件（JSON/CSV）
- 1个详细报告（TXT）

## 📊 生成的分析内容

### 1. 整体统计
- 平均分、中位数、标准差
- 各维度评分（原创性、质量、清晰度、重要性）
- 决策分布（接受/拒绝比例）

### 2. 按变体分析
每种变体的：
- 平均评分和标准差
- 接受率和拒绝率
- 各维度得分

包括的变体：
- `original` - 原始论文
- `no_abstract` - 删除摘要
- `no_introduction` - 删除引言
- `no_conclusion` - 删除结论
- `no_experiments` - 删除实验
- `no_methods` - 删除方法

### 3. 按评分区间分析
- 差 (0-3分)
- 一般 (3-5分)
- 良好 (5-7分)
- 优秀 (7-10分)

每个区间的论文数量、变体分布、特征分析。

### 4. 原始论文 vs 变体对比
- 统计检验（t-test）
- 接受率对比
- 各维度得分对比

### 5. 可视化图表

| 图表 | 说明 |
|------|------|
| `rating_distribution.png` | 评分分布直方图 |
| `ratings_by_variant_boxplot.png` | 各变体评分箱线图 |
| `ratings_by_variant_violin.png` | 各变体评分小提琴图 |
| `decision_distribution.png` | 决策分布饼图 |
| `aspect_ratings.png` | 各维度平均分柱状图 |
| `variant_decision_heatmap.png` | 变体-决策热力图 |
| `correlation_heatmap.png` | 评分维度相关性矩阵 |
| `text_length_vs_rating.png` | 文本长度与评分散点图 |

## 🔧 配置选项

### 修改样本大小

编辑 `batch_evaluate_papers.py`:

```python
SAMPLE_SIZE = 200  # 增加到200篇
TRAIN_RATIO = 0.75  # 调整训练/测试比例
```

### 修改评分区间

编辑 `analyze_evaluation_results.py`:

```python
RATING_BINS = [0, 2, 4, 6, 8, 10]  # 更细粒度的区间
RATING_LABELS = ['很差', '差', '一般', '好', '很好']
```

### 修改模型大小

编辑 `batch_evaluate_papers.py`:

```python
MODEL_SIZE = "4B"  # 使用更小的模型（更快但可能不够准确）
# 或
MODEL_SIZE = "70B"  # 使用更大的模型（更准确但更慢）
```

## 📈 典型使用场景

### 场景1：快速预览

使用5篇论文快速测试：

```python
# 修改 batch_evaluate_papers.py
SAMPLE_SIZE = 5
```

### 场景2：完整评估

评估全部100篇：

```bash
python scripts/batch_evaluate_papers.py
python scripts/analyze_evaluation_results.py
```

### 场景3：深度分析

评估200篇并生成详细报告：

```python
# 修改 SAMPLE_SIZE = 200
python scripts/batch_evaluate_papers.py
python scripts/analyze_evaluation_results.py
```

## 📁 输出文件说明

### evaluation_results/ 目录

```
evaluation_results_20260207_143022.jsonl  - 详细评估结果
evaluation_summary_20260207_143022.json   - 评估摘要
```

### analysis_output/YYYYMMDD_HHMMSS/ 目录

```
overall_statistics.json           - 总体统计
variant_statistics.csv            - 变体统计
rating_range_statistics.json      - 评分区间统计
original_vs_variants.json         - 对比分析
processed_data.csv                - 完整处理数据
analysis_report.txt               - 详细文本报告
*.png (8个图表)                   - 可视化图表
```

## 🔍 数据格式

### 评估结果 (JSONL格式)

```json
{
  "paper_id": "paper_123",
  "title": "论文标题",
  "variant_type": "no_abstract",
  "dataset_split": "train",
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
    "meta_review": "综合评审意见..."
  },
  "text_length": 15234,
  "evaluation_timestamp": "2026-02-07T14:30:22"
}
```

## ❓ 常见问题

### Q: 评估太慢怎么办？
A: 
- 减少 `SAMPLE_SIZE`
- 使用更小的 `MODEL_SIZE`
- 使用GPU加速

### Q: 内存不足？
A: 
- 减少 `SAMPLE_SIZE`
- 分批处理
- 关闭其他程序

### Q: 找不到评估结果？
A: 
- 确认先运行了 `batch_evaluate_papers.py`
- 检查 `evaluation_results/` 目录

### Q: 图表不清晰？
A: 
编辑 `analyze_evaluation_results.py`，修改DPI:
```python
plt.savefig(output_path / 'xxx.png', dpi=600)  # 提高到600
```

## 🎯 最佳实践

1. **先测试**: 运行 `test_evaluation_pipeline.py` 确认环境
2. **小样本**: 先用5-10篇测试流程
3. **完整运行**: 再用100篇完整评估
4. **保存结果**: 及时备份 `evaluation_results/` 和 `analysis_output/`
5. **分析对比**: 多次运行可以对比不同配置的效果

## 📝 注意事项

- 评估需要联网（调用LLM API）
- 结果文件使用时间戳，不会覆盖
- 所有文本使用UTF-8编码
- 建议在运行前检查磁盘空间

## 🆘 获取帮助

如果遇到问题：
1. 查看 `scripts/README_EVALUATION.md` 详细文档
2. 运行测试脚本诊断问题
3. 检查错误日志输出

---



