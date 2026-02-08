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

## 图表详细分析
每张图下方有详细解读，说明其用途、观察方法和结论建议。

---

### anomaly_count_by_variant.png
【图片内容深度解读】
本图展示每种变体类型下出现异常值的数量。异常值定义为删章节后分数高于原始分数。可以看到no_methods和no_experiments变体的异常值数量远高于其他变体，说明这些章节的删除更容易导致评分异常。original始终为0，作为基准。部分变体如no_introduction、no_conclusion也有一定数量的异常值，说明删这些章节偶尔会让评分反常提升。建议关注异常值数量较高的变体，分析其背后原因。

### anomaly_ratio_by_variant.png
【图片内容深度解读】
本图展示每种变体类型下异常值比例。no_methods和no_experiments变体异常值比例高达40%以上，说明删这些章节后评分异常提升的概率很大。original为0。部分变体如no_abstract、no_introduction异常值比例较低，说明删这些章节影响较小。建议结合异常值数量和比例综合分析变体影响。

### bar_decision_consistency_variant_type.png
【图片内容深度解读】
本图展示各变体与original决策一致性的比例。no_methods和no_experiments变体一致性最低，说明删这些章节更容易导致决策变化。no_abstract、no_introduction一致性较高，说明删这些章节对决策影响较小。建议关注一致性低的变体，分析决策变化的具体原因。

### bar_decision_ratio_variant_type.png
【图片内容深度解读】
本图展示各变体的Accept/Reject比例。original Accept比例最高，no_methods和no_experiments变体Accept比例显著下降，说明删这些章节后论文更容易被拒绝。no_abstract、no_introduction变体Accept比例与original接近，说明影响较小。建议关注Accept比例下降明显的变体，分析其评分和决策变化。

### bar_mean_std_score_diff_variant_type.png
【图片内容深度解读】
本图展示各变体评分变化（变体-原始）的均值和标准差。original为0，no_methods和no_experiments变体均值为负且标准差高，说明删这些章节后评分整体下降且波动大。部分变体如no_abstract、no_introduction均值接近0，说明影响较小。建议关注均值和标准差都较大的变体，分析其评分变化的具体分布。

### bar_mean_std_variant_type.png
【图片内容深度解读】
本图展示各变体评分均值和标准差。original均值最高，no_methods和no_experiments变体均值最低且标准差高，说明删这些章节后评分整体下降且不稳定。no_abstract、no_introduction变体均值接近original，说明影响较小。建议关注均值和标准差都较大的变体，分析其评分分布和异常值。

### boxplot_by_decision.png
【图片内容深度解读】
本图按决策类型分组展示评分分布。Accept组评分中位数高，分布集中，异常值较少。Reject组评分中位数低，分布更广，异常值较多。说明评分高的论文更容易被接受，评分低的论文更容易被拒绝。建议结合评分和决策分布分析论文质量与决策关系。

### boxplot_score_diff_variant_type.png
【图片内容深度解读】
本图展示各变体评分变化（变体-原始）分布。original为0，no_methods和no_experiments变体箱体整体低于0，异常值点分布在正区间，说明删这些章节后评分整体下降但偶尔会异常提升。建议关注箱体低于0且异常值较多的变体，分析其评分变化的具体原因。

### boxplot_variant_type.png
【图片内容深度解读】
本图展示各变体评分分布。original箱体最左且最高，no_methods和no_experiments变体箱体普遍低于original，异常值点分布在高分区间，说明删这些章节后评分整体下降但偶尔会异常提升。建议关注箱体低于original且异常值较多的变体，分析其评分分布和异常值。

### case_hml_decision_line.png
【图片内容深度解读】
本图展示高分、中分、低分论文的决策变化。original为基准，低分论文变体更容易被Reject，高分论文决策更稳定。部分变体如no_methods、no_experiments对低分论文影响最大。建议关注决策变化明显的变体和论文，分析其评分和决策关系。

### case_hml_line.png
【图片内容深度解读】
本图展示高分、中分、低分论文的评分变化。original为基准横线，低分论文变体下降幅度最大，高分论文变体评分变化较小。部分变体如no_methods、no_experiments对低分论文影响最大。建议关注评分变化明显的变体和论文，分析其分布和异常值。

### decision_bar_no_abstract.png
【图片内容深度解读】
本图展示no_abstract变体下决策分布。Accept比例略低于original，说明删abstract对决策有一定负面影响。部分论文决策发生变化，建议关注决策变化的具体论文。

### decision_bar_no_conclusion.png
【图片内容深度解读】
本图展示no_conclusion变体下决策分布。Accept比例下降明显，说明删conclusion对决策影响较大。部分论文决策发生变化，建议关注决策变化的具体论文。

### decision_bar_no_experiments.png
【图片内容深度解读】
本图展示no_experiments变体下决策分布。Accept比例显著下降，说明删experiments对决策影响最大。部分论文决策发生变化，建议关注决策变化的具体论文。

### decision_bar_no_introduction.png
【图片内容深度解读】
本图展示no_introduction变体下决策分布。Accept比例略低于original，影响较小。部分论文决策发生变化，建议关注决策变化的具体论文。

### decision_bar_no_methods.png
【图片内容深度解读】
本图展示no_methods变体下决策分布。Accept比例大幅下降，说明删methods对决策影响极大。部分论文决策发生变化，建议关注决策变化的具体论文。

### decision_consistency_pie.png
【图片内容深度解读】
本图展示决策一致/变化比例。大部分变体决策与original一致，部分变体如no_methods决策变化比例较高。建议关注决策变化比例高的变体，分析其评分和决策关系。

### density_score_diff_variant_type.png
【图片内容深度解读】
本图展示各变体评分变化密度分布。original为0，no_methods和no_experiments变体曲线整体左移，说明评分下降。部分变体曲线右侧有异常值峰，说明偶尔会出现评分异常提升。建议关注曲线左移且异常值峰明显的变体。

### density_variant_type.png
【图片内容深度解读】
本图展示各变体评分密度分布。original曲线最右，no_methods和no_experiments变体曲线整体左移，说明评分下降。曲线形态可见分布集中或分散，建议关注曲线左移且分布分散的变体。

### extreme_score_scatter_no_abstract.png
【图片内容深度解读】
本图展示no_abstract变体下评分变化极端值。点分布在高分区间，说明部分论文删abstract后评分异常提升。建议关注极端值点对应的论文，分析其评分变化原因。

### extreme_score_scatter_no_conclusion.png
【图片内容深度解读】
本图展示no_conclusion变体下评分变化极端值。点分布在高分区间，说明部分论文删conclusion后评分异常提升。建议关注极端值点对应的论文，分析其评分变化原因。

### extreme_score_scatter_no_experiments.png
【图片内容深度解读】
本图展示no_experiments变体下评分变化极端值。点分布在高分区间，说明部分论文删experiments后评分异常提升。建议关注极端值点对应的论文，分析其评分变化原因。

### extreme_score_scatter_no_introduction.png
【图片内容深度解读】
本图展示no_introduction变体下评分变化极端值。点分布在高分区间，说明部分论文删introduction后评分异常提升。建议关注极端值点对应的论文，分析其评分变化原因。

### extreme_score_scatter_no_methods.png
【图片内容深度解读】
本图展示no_methods变体下评分变化极端值。点分布在高分区间，说明部分论文删methods后评分异常提升。建议关注极端值点对应的论文，分析其评分变化原因。

### line_mean_score_variant_type.png
【图片内容深度解读】
本图展示original与各变体评分均值折线。original为基准，no_methods和no_experiments变体均值最低，部分变体均值接近original。建议关注均值下降明显的变体，分析其评分变化趋势。

### score_change_heatmap.png
【图片内容深度解读】
本图展示每篇论文各变体评分变化热力图。颜色越深变化越大，no_methods和no_experiments变体颜色最深，说明影响最大。建议关注颜色深的论文和变体，分析其评分变化原因。

### score_diff_box_no_abstract.png
【图片内容深度解读】
本图展示no_abstract变体下评分变化箱线图。箱体低于0，异常值点分布在正区间，说明部分论文评分异常提升。建议关注异常值点对应的论文。

### score_diff_box_no_conclusion.png
【图片内容深度解读】
本图展示no_conclusion变体下评分变化箱线图。箱体低于0，异常值点分布在正区间，说明部分论文评分异常提升。建议关注异常值点对应的论文。

### score_diff_box_no_experiments.png
【图片内容深度解读】
本图展示no_experiments变体下评分变化箱线图。箱体低于0，异常值点分布在正区间，说明部分论文评分异常提升。建议关注异常值点对应的论文。

### score_diff_box_no_introduction.png
【图片内容深度解读】
本图展示no_introduction变体下评分变化箱线图。箱体低于0，异常值点分布在正区间，说明部分论文评分异常提升。建议关注异常值点对应的论文。

### score_diff_box_no_methods.png
【图片内容深度解读】
本图展示no_methods变体下评分变化箱线图。箱体低于0，异常值点分布在正区间，说明部分论文评分异常提升。建议关注异常值点对应的论文。

### score_hist.png
【图片内容深度解读】
本图展示整体评分分布直方图。original分布最右，no_methods和no_experiments变体分布左移，说明评分整体下降。部分变体分布接近original，说明影响较小。建议关注分布左移明显的变体。

### score_hist_no_abstract.png
【图片内容深度解读】
本图展示no_abstract变体下评分分布直方图。分布左移，红线为original均值，说明评分下降。部分论文评分接近original，说明影响有限。

### score_hist_no_conclusion.png
【图片内容深度解读】
本图展示no_conclusion变体下评分分布直方图。分布左移，红线为original均值，说明评分下降。部分论文评分接近original，说明影响有限。

### score_hist_no_experiments.png
【图片内容深度解读】
本图展示no_experiments变体下评分分布直方图。分布左移，红线为original均值，说明评分下降。部分论文评分接近original，说明影响有限。

### score_hist_no_introduction.png
【图片内容深度解读】
本图展示no_introduction变体下评分分布直方图。分布左移，红线为original均值，说明评分下降。部分论文评分接近original，说明影响有限。

### score_hist_no_methods.png
【图片内容深度解读】
本图展示no_methods变体下评分分布直方图。分布左移，红线为original均值，说明评分下降。部分论文评分接近original，说明影响有限。

### score_std_per_paper.png
【图片内容深度解读】
本图展示每篇论文变体评分标准差分布。标准差高的论文说明变体影响大，标准差低的论文说明变体影响小。部分论文标准差极高，建议关注这些论文，分析其变体影响原因。

---

## 图表内容解析
每张图均包含：
- 横轴：变体类型或base_paper_id或评分区间
- 纵轴：评分、评分变化、决策比例、异常值数量/比例等
- 红线：original均值或无变化基准
- 箱体：分布范围，异常值以点标出
- 柱状图：比例或均值/标准差
- 散点图：极端值分布
- 热力图：变化幅度
- 饼图：决策一致性

主要观察方法：
- original始终在最左，红线为基准
- 变体箱体整体低于original说明评分下降
- 柱状图比例低于original说明决策影响
- 异常值以点标出，极端值散点图定位影响最大论文
- 热力图可定位影响集中区域
- 个案折线图可观察特定论文变化趋势

异常值分析：
- 异常值定义为删章节后分数高于原始分数
- 全局异常值比例: 32.09%
- anomaly_count_by_variant.png: 各变体类型异常值数量分布
- anomaly_ratio_by_variant.png: 各变体类型异常值比例分布
- boxplot_variant_type.png, boxplot_score_diff_variant_type.png: 图标题已标注异常值比例
- case_hml_line.png, case_hml_decision_line.png: 高/中/低分个案评分与决策变化合并展示

## 主要结论与解读
请结合箱线图、均值图、密度图、决策比例图、热力图等，综合分析各变体对评分和决策的影响。异常值和极端变化需重点关注。
数据缺失已自动处理，所有统计均基于实际有效数据。
如需进一步分析或定制图表，请联系开发者。
