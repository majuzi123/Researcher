# 图表计算逻辑说明

本文件介绍 `anomaly_ratio_stacked_bar.py` 生成的主要统计图表的计算范围、计算逻辑，并举例说明。

---

## 1. 异常比例堆叠柱状图（anomaly_ratio_by_variant_stacked.png）
- **计算范围**：所有论文、所有变体类型（不含 original）。
- **计算逻辑**：
  - 对每篇论文，遍历所有变体（如 no_methods、no_experiments 等），与原始评分（original）比较：
    - 变体评分 > 原始评分：计为“异常”（红色）
    - 变体评分 = 原始评分：计为“未修改”（橙色）
    - 变体评分 < 原始评分：计为“正常反应”（绿色）
  - 对每种变体类型，统计三类数量，分别除以该变体总数，得到比例。
- **举例**：
  - 某论文 original 评分 4.5，no_methods 评分 4.7（异常），no_experiments 评分 4.5（未修改），no_introduction 评分 4.2（正常反应）。

## 2. 极端异常/异常 Accept 分组柱状图（extreme_abnormal_accept_ratio_by_variant.png）
- **计算范围**：所有论文、所有变体类型（不含 original）。
- **计算逻辑**：
  - 对每篇论文，若 original 决策为 Reject，统计该论文各变体中决策变为 Accept 的数量（极端异常，紫色），分母为该变体下 original 决策为 Reject的论文数。
  - 若 original 决策为 Accept，统计该论文各变体中决策仍为 Accept 的数量（异常 Accept，蓝色），分母为该变体下 original 决策为 Accept 的论文数。
- **举例**：
  - 某论文 original 决策为 Reject，no_abstract 变体决策为 Accept，no_methods 变体决策为 Reject，则 no_abstract 计入极端异常。
  - 某论文 original 决策为 Accept，no_methods 变体决策为 Accept，no_experiments 变体决策为 Reject，则 no_methods 计入异常 Accept。

## 3. 合并大图（combined_variant_analysis.png）
- **计算范围**：所有论文、所有变体类型（不含 original）。
- **代码计算逻辑详解**：
  - 该图由两个子图组成，均在 anomaly_ratio_stacked_bar.py 脚本中生成：
    
  **左侧：异常比例堆叠柱状图**
  1. 遍历所有论文（按 base_paper_id 分组），对每个变体（如 no_methods、no_experiments 等，排除 original）：
     - 取该论文 original 评分 orig_score。
     - 取该论文该变体评分 rating。
     - 若 rating > orig_score，anomaly_counts[变体] += 1。
     - 若 rating == orig_score，unmod_counts[变体] += 1。
     - 若 rating < orig_score，normal_counts[变体] += 1。
     - total_counts[变体] += 1。
  2. 计算每种变体的三类比例：
     - anomaly_ratio = anomaly_counts[变体] / total_counts[变体]
     - unmod_ratio = unmod_counts[变体] / total_counts[变体]
     - normal_ratio = normal_counts[变体] / total_counts[变体]
  3. 用 matplotlib 画柱状图，
     - 橙色（unmod_ratio）为底，绿色（normal_ratio）堆叠在橙色上，红色（anomaly_ratio）堆叠在前两者之上。
     - x 轴为变体类型，y 轴为比例。

  **右侧：极端异常/异常 Accept 分组柱状图**
  1. 遍历所有论文（按 base_paper_id 分组），对每个变体：
     - 若 original 决策为 Reject，total_reject[变体] += 1。
       - 若该变体决策为 Accept，extreme_abnormal_counts[变体] += 1。
     - 若 original 决策为 Accept，total_accept[变体] += 1。
       - 若该变体决策为 Accept，abnormal_accept_counts[变体] += 1。
  2. 计算每种变体的两类比例：
     - extreme_abnormal_ratio = extreme_abnormal_counts[变体] / total_reject[变体]
     - abnormal_accept_ratio = abnormal_accept_counts[变体] / total_accept[变体]
  3. 用 matplotlib 画分组柱状图，
     - 紫色为极端异常（Reject→Accept），蓝色为异常 Accept（Accept→Accept）。
     - x 轴为变体类型，y 轴为比例。

- **颜色说明**：
  - 橙色：未修改（分数不变）
  - 绿色：正常反应（分数下降）
  - 红色：异常（分数升高）
  - 紫色：Reject→Accept 极端异常
  - 蓝色：Accept→Accept 异常 Accept

- **举例**：
  - 假设有 100 篇论文，no_methods 变体下有 60 篇分数下降（绿色），30 篇分数不变（橙色），10 篇分数升高（红色），则三类比例分别为 0.6、0.3、0.1。
  - 其中有 20 篇论文 original 决策为 Reject，no_methods 变体下有 2 篇变为 Accept（紫色，比例 0.1）；有 50 篇 original 决策为 Accept，no_methods 变体下有 40 篇仍为 Accept（蓝色，比例 0.8）。


## 4. 分数变化与决策变化堆叠柱状图（score_decision_change_stacked.png）
- **计算范围**：所有论文、所有变体类型（不含 original）。
- **计算逻辑**：
  - 对每篇论文每个变体，计算分数变化（变体评分-原始评分）：升高（up）、降低（down）、不变（same）。
  - 同时统计决策变化：
    - Accept→Reject（ac2re）
    - Reject→Accept（re2ac）
    - Accept→Accept（ac2ac，决策不变）
    - Reject→Reject（re2re，决策不变）
  - 只统计和展示上述四类决策变化，不再统计 nochange。
  - 对每种变体类型，统计分数升高/降低/不变时，各类决策变化的比例。
- **举例**：
  - 某论文 original 决策 Accept，no_experiments 变体分数降低且决策变为 Reject，属于“分数降低+Accept→Reject”。
  - 某论文 original 决策 Reject，no_methods 变体分数升高且决策变为 Accept，属于“分数升高+Reject→Accept”。
  - 某论文 original 决策 Accept，no_methods 变体分数升高且决策仍为 Accept，属于“分数升高+Accept→Accept”。
  - 某论文 original 决策 Reject，no_experiments 变体分数不变且决策仍为 Reject，属于“分数不变+Reject→Reject”。

- **代码片段参考**：
```python
# 决策变化分类
if orig_dec == 'Accept' and row['decision'] == 'Reject':
    dec_cat = 'ac2re'
elif orig_dec == 'Reject' and row['decision'] == 'Accept':
    dec_cat = 're2ac'
elif orig_dec == 'Accept' and row['decision'] == 'Accept':
    dec_cat = 'ac2ac'
elif orig_dec == 'Reject' and row['decision'] == 'Reject':
    dec_cat = 're2re'
else:
    dec_cat = 'other'  # 只统计上述四类
```
- **图表说明**：
  - 每个变体类型下，分数升高/降低/不变时，决策变化的比例以堆叠柱状图展示。
  - 只展示 ac2re、re2ac、ac2ac、re2re 四类决策变化。

## 5. 全正常论文比例饼图（all_normal_papers_pie.png）
- **计算范围**：所有论文。
- **计算逻辑**：
  - 检查每篇论文所有变体分数变化（变体评分-原始评分）是否都≤0。
  - 若全部≤0，计为“全正常论文”；否则为“含异常论文”。
  - 统计全正常论文数量及比例。
- **举例**：
  - 某论文所有变体分数都低于原始分数，则为“全正常论文”。

## 6. 评分变化热力图（score_change_heatmap_all_papers.png）
- **计算范围**：所有论文、所有变体类型（不含 original）。
- **计算逻辑**：
  - 构建矩阵，行是论文，列是变体类型，值为变体评分-原始评分。
  - 用热力图展示，蓝色为分数下降，红色为分数上升。
  - y 轴为论文索引，不显示编号。
- **举例**：
  - 一行全蓝，说明该论文所有变体分数均下降。

## 7. 合理降分论文比例饼图（reasonable_score_change_pie.png）
- **计算范围**：所有论文，且关键变体（no_abstract、no_experiments、no_introduction、no_methods、no_conclusion）均有分数。
- **计算逻辑**：
  - 检查每篇论文在上述关键变体下：no_abstract、no_experiments、no_introduction、no_methods 分数均小于原始分数，no_conclusion 分数小于等于原始分数。
  - 满足条件计为“合理降分论文”，否则为“其他”。
  - 统计数量及比例。
- **举例**：
  - 某论文在 no_abstract、no_experiments、no_introduction、no_methods 变体分数均小于原始分数，no_conclusion 变体分数等于原始分数，则为“合理降分论文”。

## 8. 典型案例折线图（typical_cases_line.png）
- **计算范围**：所有论文。
- **计算逻辑**：
  - 筛选 Reject→Accept 且分数升高的极端异常案例（原始决策为 Reject，某变体决策为 Accept 且分数升高）。
  - 筛选 Accept 高分论文删除 methods/experiments 后仍为 Accept 且分数高的异常案例（原始分数高，变体分数不降且决策为 Accept）。
  - 展示原始与变体分数对比，并在图中标注原始和变体的决策（Accept/Reject），使分数变化和决策变化一目了然。
- **可视化**：
  - 用折线图（而非条形图）展示每个典型案例的 original/variant 分数。
  - 在每个点上用不同颜色/符号标注决策（如红色为Accept，蓝色为Reject）。
  - Reject→Accept和Accept高分两类案例分别画在一张图的左右两侧。
- **举例**：
  - x轴为案例编号（论文ID+变体），y轴为分数，点上标注决策。
- **代码片段**：
```python
fig, axes = plt.subplots(1, 2, figsize=(14,6))
# Reject→Accept
if reject_accept_cases_sorted:
    ...
    axes[0].plot(x, orig_scores1, marker='o', label='Original Score', color='gray', linestyle='--')
    axes[0].plot(x, variant_scores1, marker='o', label='Variant Score', color='red')
    for i, (xo, vo, od, vd) in enumerate(zip(orig_scores1, variant_scores1, orig_decisions1, variant_decisions1)):
        axes[0].text(i, orig_scores1[i], od, color='black', fontsize=10, ha='center', va='bottom')
        axes[0].text(i, variant_scores1[i], vd, color='red' if vd=='Accept' else 'blue', fontsize=10, ha='center', va='top')
    ...
# Accept高分
if accept_high_cases_sorted:
    ...
    axes[1].plot(x2, orig_scores2, marker='o', label='Original Score', color='gray', linestyle='--')
    axes[1].plot(x2, variant_scores2, marker='o', label='Variant Score', color='blue')
    for i, (xo, vo, od, vd) in enumerate(zip(orig_scores2, variant_scores2, orig_decisions2, variant_decisions2)):
        axes[1].text(i, orig_scores2[i], od, color='black', fontsize=10, ha='center', va='bottom')
        axes[1].text(i, variant_scores2[i], vd, color='red' if vd=='Accept' else 'blue', fontsize=10, ha='center', va='top')
    ...
plt.tight_layout()
plt.savefig(f'{outdir}/typical_cases_line.png')
plt.close()
```

## 9. 按原始决策分组热力图与决策变化柱状图（decision_change_bar_papers.png 等）
- **计算范围**：所有论文，按 original 决策分为 Accept、Reject 两组。
- **修正后计算逻辑**：
  - Accept组：只统计 original 决策为 Accept 且该变体有评分/决策的论文，分母为这两类之和。
    - 只统计 ac2ac（Accept→Accept）和 ac2re（Accept→Reject），比例之和为1。
  - Reject组：同理，只统计 re2ac（Reject→Accept）和 re2re（Reject→Reject），比例之和为1。
  - 缺失数据（无评分/决策）不计入分母。
- **修正后代码片段**：
```python
for dec_cat in ['Accept','Reject']:
    paper_ids = df_dec[df_dec['variant_type']=='original']
    paper_ids = paper_ids[paper_ids['decision']==dec_cat]['base_paper_id'].unique()
    group_dec = df_dec[df_dec['base_paper_id'].isin(paper_ids)]
    dec_change_stats = {vt: {'ac2re':0, 're2ac':0, 'ac2ac':0, 're2re':0, 'total':0} for vt in variant_order if vt != 'original'}
    for vt in variant_order:
        if vt == 'original':
            continue
        for base_id in paper_ids:
            orig = group_dec[(group_dec['base_paper_id']==base_id) & (group_dec['variant_type']=='original')]
            var = group_dec[(group_dec['base_paper_id']==base_id) & (group_dec['variant_type']==vt)]
            if orig.empty or var.empty or pd.isnull(var.iloc[0]['decision']):
                continue
            orig_dec = orig.iloc[0]['decision']
            var_dec = var.iloc[0]['decision']
            if dec_cat == 'Accept':
                if var_dec == 'Accept':
                    dec_change_stats[vt]['ac2ac'] += 1
                elif var_dec == 'Reject':
                    dec_change_stats[vt]['ac2re'] += 1
                dec_change_stats[vt]['total'] += 1
            elif dec_cat == 'Reject':
                if var_dec == 'Accept':
                    dec_change_stats[vt]['re2ac'] += 1
                elif var_dec == 'Reject':
                    dec_change_stats[vt]['re2re'] += 1
                dec_change_stats[vt]['total'] += 1
# 绘图时Accept组只画ac2ac和ac2re，Reject组只画re2ac和re2re，比例之和为1。
```
- **举例**：
  - Accept 组决策变化柱状图只展示 ac2re、ac2ac 两类比例，且每列之和为1。
  - Reject 组只展示 re2ac、re2re 两类比例，且每列之和为1。

---

如需进一步细化某个图表的逻辑或数据处理细节，请随时补充需求。
