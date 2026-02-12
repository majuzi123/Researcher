# 图表说明
本目录下所有统计图表均基于 merged.jsonl 数据自动生成，涵盖评分、决策、变体影响、极端值、分布等。

## 图表列表
- anomaly_count_by_variant.png
- anomaly_ratio_by_variant.png
- bar_decision_consistency_variant_type.png
- bar_decision_ratio_variant_type.png
- bar_mean_std_score_diff_variant_type.png
- bar_mean_std_variant_type.png
- boxplot_by_decision.png
- boxplot_score_diff_variant_type.png
- boxplot_variant_type.png
- case_hml_decision_line.png
- case_hml_line.png
- decision_bar_no_abstract.png
- decision_bar_no_conclusion.png
- decision_bar_no_experiments.png
- decision_bar_no_introduction.png
- decision_bar_no_methods.png
- decision_consistency_pie.png
- density_score_diff_variant_type.png
- density_variant_type.png
- extreme_score_scatter_no_abstract.png
- extreme_score_scatter_no_conclusion.png
- extreme_score_scatter_no_experiments.png
- extreme_score_scatter_no_introduction.png
- extreme_score_scatter_no_methods.png
- line_mean_score_variant_type.png
- score_change_heatmap.png
- score_diff_box_no_abstract.png
- score_diff_box_no_conclusion.png
- score_diff_box_no_experiments.png
- score_diff_box_no_introduction.png
- score_diff_box_no_methods.png
- score_hist.png
- score_hist_no_abstract.png
- score_hist_no_conclusion.png
- score_hist_no_experiments.png
- score_hist_no_introduction.png
- score_hist_no_methods.png
- score_std_per_paper.png

## 图表说明
每张图下方有详细解读，说明其用途、观察方法和结论建议。
### boxplot_variant_type.png
各变体评分箱线图，original在最左，红线为original均值。可观察各变体分布、异常值、与原始论文的对比。
### bar_mean_std_variant_type.png
各变体评分均值/标准差柱状图，红线为original均值。可直观比较各变体均值和波动。
### density_variant_type.png
各变体评分分布密度图，红线为original均值。可观察分布形态和偏移。
### bar_decision_ratio_variant_type.png
各变体决策比例柱状图，横向x轴。可比较各变体的Accept/Reject比例。
### line_mean_score_variant_type.png
原始与变体评分均值对比折线图，红线为original均值。可观察均值变化趋势。
### bar_decision_consistency_variant_type.png
原始与变体决策一致性分布条形图。可看出各变体决策变化比例。
### boxplot_score_diff_variant_type.png
每种变体评分变化（变体-原始）分布箱线图，红线为无变化基准。
### bar_mean_std_score_diff_variant_type.png
每种变体评分变化均值/标准差柱状图，红线为无变化基准。
### density_score_diff_variant_type.png
每种变体评分变化密度图，红线为无变化基准。
### bar_decision_change_variant_type.png
每种变体决策变化比例柱状图。
### score_change_heatmap.png
按base_paper_id评分变化热力图。
### decision_change_heatmap.png
按base_paper_id决策变化热力图。
### score_std_per_paper.png
每篇论文变体评分标准差分布。
### abs_score_change_hist.png
评分变化绝对值分布。
### extreme_score_change_scatter.png
评分变化极端值（Top 5%）散点图。
### all_papers_score_line.png
所有论文评分变化折线图。
### all_papers_decision_line.png
所有论文决策变化折线图。
### score_change_scatter.png
评分变化分布散点图。
### decision_change_scatter.png
决策变化分布散点图。
### score_vs_decision_joint.png
评分变化与决策变化联合分布图。
### case_xxx_line.png
高/中/低分个案折线图。
### decision_consistency_pie.png
原始与变体决策一致性统计饼图。
### score_hist.png
分数区间分布直方图。
### score_hist_no_abstract.png
no_abstract 评分分布直方图，红线为original均值。
### decision_bar_no_abstract.png
no_abstract 决策分布柱状图。
### score_diff_box_no_abstract.png
no_abstract 评分变化箱线图。
### extreme_score_scatter_no_abstract.png
no_abstract 评分变化极端值散点图。
### score_hist_no_conclusion.png
no_conclusion 评分分布直方图，红线为original均值。
### decision_bar_no_conclusion.png
no_conclusion 决策分布柱状图。
### score_diff_box_no_conclusion.png
no_conclusion 评分变化箱线图。
### extreme_score_scatter_no_conclusion.png
no_conclusion 评分变化极端值散点图。
### score_hist_no_experiments.png
no_experiments 评分分布直方图，红线为original均值。
### decision_bar_no_experiments.png
no_experiments 决策分布柱状图。
### score_diff_box_no_experiments.png
no_experiments 评分变化箱线图。
### extreme_score_scatter_no_experiments.png
no_experiments 评分变化极端值散点图。
### score_hist_no_introduction.png
no_introduction 评分分布直方图，红线为original均值。
### decision_bar_no_introduction.png
no_introduction 决策分布柱状图。
### score_diff_box_no_introduction.png
no_introduction 评分变化箱线图。
### extreme_score_scatter_no_introduction.png
no_introduction 评分变化极端值散点图。
### score_hist_no_methods.png
no_methods 评分分布直方图，红线为original均值。
### decision_bar_no_methods.png
no_methods 决策分布柱状图。
### score_diff_box_no_methods.png
no_methods 评分变化箱线图。
### extreme_score_scatter_no_methods.png
no_methods 评分变化极端值散点图。

## 主要结论与解读
请结合箱线图、均值图、密度图、决策比例图、热力图等，综合分析各变体对评分和决策的影响。异常值和极端变化需重点关注。
数据缺失已自动处理，所有统计均基于实际有效数据。
如需进一步分析或定制图表，请联系开发者。

### 异常值分析
异常值定义为删章节后分数高于原始分数。
全局异常值比例: 32.60%
anomaly_count_by_variant.png: 各变体类型异常值数量分布。
anomaly_ratio_by_variant.png: 各变体类型异常值比例分布。
boxplot_variant_type.png, boxplot_score_diff_variant_type.png: 图标题已标注异常值比例。
case_hml_line.png, case_hml_decision_line.png: 高/中/低分个案评分与决策变化合并展示。
