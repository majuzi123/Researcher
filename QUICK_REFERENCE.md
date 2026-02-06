# 📋 Quick Reference Card

## 一键运行完整流程

```bash
python run_evaluation_pipeline.py
```

## 分步运行

```bash
# 1. 测试环境
python scripts/test_evaluation_pipeline.py

# 2. 批量评估（15-30分钟）
python scripts/batch_evaluate_papers.py

# 3. 分析结果（1-2分钟）
python scripts/analyze_evaluation_results.py
```

## 关键配置

### 修改样本数量
`scripts/batch_evaluate_papers.py` 第17行:
```python
SAMPLE_SIZE = 100  # 改为你需要的数量
```

### 修改训练/测试比例
`scripts/batch_evaluate_papers.py` 第18行:
```python
TRAIN_RATIO = 0.8  # 80% train, 20% test
```

### 修改模型大小
`scripts/batch_evaluate_papers.py` 第20行:
```python
MODEL_SIZE = "8B"  # 可选: "4B", "8B", "70B"
```

## 输出文件位置

### 评估结果
```
evaluation_results/
  ├── evaluation_results_YYYYMMDD_HHMMSS.jsonl
  └── evaluation_summary_YYYYMMDD_HHMMSS.json
```

### 分析结果
```
analysis_output/YYYYMMDD_HHMMSS/
  ├── overall_statistics.json
  ├── variant_statistics.csv
  ├── rating_range_statistics.json
  ├── original_vs_variants.json
  ├── processed_data.csv
  ├── analysis_report.txt
  └── *.png (8个可视化图表)
```

## 8个可视化图表

1. `rating_distribution.png` - 评分分布
2. `ratings_by_variant_boxplot.png` - 变体评分箱线图
3. `ratings_by_variant_violin.png` - 变体评分小提琴图
4. `decision_distribution.png` - 决策分布
5. `aspect_ratings.png` - 维度评分
6. `variant_decision_heatmap.png` - 变体-决策热力图
7. `correlation_heatmap.png` - 相关性矩阵
8. `text_length_vs_rating.png` - 文本长度vs评分

## 6种变体类型

- `original` - 原始论文
- `no_abstract` - 删除摘要
- `no_introduction` - 删除引言  
- `no_conclusion` - 删除结论
- `no_experiments` - 删除实验
- `no_methods` - 删除方法

## 评分区间

- **0-3**: 差 (Poor)
- **3-5**: 一般 (Fair)
- **5-7**: 良好 (Good)
- **7-10**: 优秀 (Excellent)

## 常见问题快速解决

| 问题 | 解决方案 |
|------|----------|
| 找不到结果文件 | 先运行 `batch_evaluate_papers.py` |
| 缺少包 | `pip install pandas numpy matplotlib seaborn scipy tqdm` |
| 评估太慢 | 减少 `SAMPLE_SIZE` 或使用更小的 `MODEL_SIZE` |
| 内存不足 | 减少 `SAMPLE_SIZE` |
| 测试失败 | 运行 `test_evaluation_pipeline.py` 查看详情 |

## 数据集统计

当前生成的数据集：
- **训练集**: 4,272 个样本 (712 篇论文 × 6 变体)
- **测试集**: 1,086 个样本 (181 篇论文 × 6 变体)
- **总计**: 5,358 个样本

评估样本（默认配置）：
- **训练集**: 80 篇
- **测试集**: 20 篇
- **总计**: 100 篇 × 6 变体 = 预计600个评估

## 时间估算

| 步骤 | 时间 |
|------|------|
| 环境测试 | < 1分钟 |
| 评估100篇 | 15-30分钟 |
| 分析结果 | 1-2分钟 |
| **总计** | **约20-35分钟** |

## 文档位置

- **英文详细文档**: `scripts/README_EVALUATION.md`
- **中文使用指南**: `docs/EVALUATION_GUIDE_CN.md`
- **流程总结**: `docs/EVALUATION_PIPELINE_SUMMARY.md`

## 获取帮助

1. 查看详细文档
2. 运行测试脚本诊断
3. 检查错误输出信息

---

**快速提示**: 首次运行建议先用 `SAMPLE_SIZE=5` 测试流程！

