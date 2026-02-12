import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# 输出目录
outdir = f'../analysis_output/evaluted_results'
os.makedirs(outdir, exist_ok=True)

# 读取数据
jsonl_path = '../evaluation_results/evaluation_results_20260212_054243.jsonl'
records = []
with open(jsonl_path, 'r', encoding='utf-8') as f:
    for line in f:
        records.append(json.loads(line))

# 转为DataFrame
rows = []
for r in records:
    base_id = r.get('base_paper_id')
    variant = r.get('variant_type')
    rating = None
    decision = None
    if isinstance(r.get('evaluation'), dict):
        rating = r['evaluation'].get('avg_rating')
        decision = r['evaluation'].get('paper_decision')
    rows.append({
        'base_paper_id': base_id,
        'variant_type': variant,
        'rating': rating,
        'decision': decision
    })
df = pd.DataFrame(rows)

# 只保留有评分的
df = df[df['rating'].notnull()]

# 保证 original 在所有图表中最左边
variant_order = sorted(df['variant_type'].unique(), key=lambda x: (x != 'original', x))

# 生成 score_diff_df（必须在用到它之前）
score_diff_long = []
for base_id, group in df.groupby('base_paper_id'):
    orig = group[group['variant_type']=='original']
    if orig.empty:
        continue
    orig_score = orig.iloc[0]['rating']
    for _, row in group.iterrows():
        if row['variant_type'] != 'original':
            score_diff_long.append({'variant_type': row['variant_type'], 'score_diff': row['rating']-orig_score})
score_diff_df = pd.DataFrame(score_diff_long)

# 1. 各变体评分箱线图（original最左，基准线）
plt.figure(figsize=(10,6))
sns.boxplot(x='variant_type', y='rating', data=df, order=variant_order, showfliers=True)
orig_mean = df[df['variant_type']=='original']['rating'].mean()
plt.axhline(orig_mean, color='red', linestyle='--', label=f'Original Mean: {orig_mean:.2f}')
plt.title('Score Distribution by Variant Type')
plt.legend()
plt.savefig(f'{outdir}/boxplot_variant_type.png')
plt.close()

# 3. 个案折线图（高/中/低分各一篇）和决策变化合并到一张图
med = df[df['variant_type']=='original']['rating'].median()
high = df[df['variant_type']=='original']['rating'].max()
low = df[df['variant_type']=='original']['rating'].min()

cases = []
for score in [high, med, low]:
    case = df[(df['variant_type']=='original') & (df['rating']==score)]
    if not case.empty:
        cases.append(case.iloc[0]['base_paper_id'])

plt.figure(figsize=(10,6))
for case_id, color, label in zip(cases, ['red','green','blue'], ['High','Median','Low']):
    sub = df[df['base_paper_id']==case_id].sort_values('variant_type')
    plt.plot(sub['variant_type'], sub['rating'], marker='o', label=f'{label} ({case_id})')
plt.axhline(orig_mean, color='gray', linestyle='--', label=f'Original Mean: {orig_mean:.2f}')
plt.title('Score Change for High/Median/Low Cases')
plt.ylabel('Score')
plt.xlabel('Variant Type')
plt.legend()
plt.savefig(f'{outdir}/case_hml_line.png')
plt.close()

# 个案决策变化合并到一张图
plt.figure(figsize=(10,6))
for case_id, color, label in zip(cases, ['red','green','blue'], ['High','Median','Low']):
    sub = df[df['base_paper_id']==case_id].sort_values('variant_type')
    dec_map = sub['decision'].map({'Accept':1,'Reject':0})
    plt.plot(sub['variant_type'], dec_map, marker='o', label=f'{label} ({case_id})')
plt.title('Decision Change for High/Median/Low Cases')
plt.ylabel('Decision (1=Accept, 0=Reject)')
plt.xlabel('Variant Type')
plt.yticks([0,1],['Reject','Accept'])
plt.legend()
plt.savefig(f'{outdir}/case_hml_decision_line.png')
plt.close()

# 2. 标注异常值（删章节后分数上升）并统计比例
anomalies = []
total_variants = 0
for base_id, group in df.groupby('base_paper_id'):
    orig = group[group['variant_type']=='original']
    if orig.empty:
        continue
    orig_score = orig.iloc[0]['rating']
    for _, row in group.iterrows():
        if row['variant_type'] != 'original':
            total_variants += 1
            if row['rating'] > orig_score:
                anomalies.append({
                    'base_paper_id': base_id,
                    'variant_type': row['variant_type'],
                    'orig_score': orig_score,
                    'variant_score': row['rating']
                })
anomaly_ratio = len(anomalies) / total_variants if total_variants else 0
if anomalies:
    adf = pd.DataFrame(anomalies)
    adf.to_csv(f'{outdir}/anomaly_score_up.csv', index=False)

# 在箱线图和评分变化箱线图上标注异常值比例
plt.figure(figsize=(10,6))
sns.boxplot(x='variant_type', y='rating', data=df, order=variant_order, showfliers=True)
plt.axhline(orig_mean, color='red', linestyle='--', label=f'Original Mean: {orig_mean:.2f}')
plt.title(f'Score Distribution by Variant Type\n(Anomaly Ratio: {anomaly_ratio:.2%})')
plt.legend()
plt.savefig(f'{outdir}/boxplot_variant_type.png')
plt.close()

plt.figure(figsize=(10,6))
sns.boxplot(x='variant_type', y='score_diff', data=score_diff_df, order=[v for v in variant_order if v != 'original'])
plt.axhline(0, color='red', linestyle='--', label='No Change (Original)')
plt.title(f'Score Change (Variant - Original) by Variant Type\n(Anomaly Ratio: {anomaly_ratio:.2%})')
plt.legend()
plt.savefig(f'{outdir}/boxplot_score_diff_variant_type.png')
plt.close()

# 异常值分布分析图（按变体类型）
anom_df = pd.DataFrame(anomalies)
if not anom_df.empty:
    plt.figure(figsize=(10,6))
    sns.countplot(x='variant_type', data=anom_df, order=[v for v in variant_order if v != 'original'])
    plt.title('Anomaly Count (Score Up) by Variant Type')
    plt.ylabel('Count (Anomaly)')
    plt.savefig(f'{outdir}/anomaly_count_by_variant.png')
    plt.close()
    # 异常值比例图
    total_by_variant = score_diff_df.groupby('variant_type').size()
    anomaly_by_variant = anom_df.groupby('variant_type').size()
    ratio_by_variant = (anomaly_by_variant / total_by_variant).reindex([v for v in variant_order if v != 'original'])
    plt.figure(figsize=(10,6))
    ratio_by_variant.plot(kind='bar')
    plt.title('Anomaly Ratio (Score Up) by Variant Type')
    plt.ylabel('Anomaly Ratio')
    plt.ylim(0,1)
    plt.savefig(f'{outdir}/anomaly_ratio_by_variant.png')
    plt.close()

# 4. 分数区间分布直方图
plt.figure(figsize=(8,5))
sns.histplot(df['rating'], bins=20, kde=True)
plt.title('Score Distribution (All Variants)')
plt.savefig(f'{outdir}/score_hist.png')
plt.close()

# 5. 按决策分类的箱线图
plt.figure(figsize=(8,5))
sns.boxplot(x='decision', y='rating', data=df)
plt.title('Score Distribution by Decision')
plt.savefig(f'{outdir}/boxplot_by_decision.png')
plt.close()

# 6. 原始与变体决策一致性统计
consistency = []
for base_id, group in df.groupby('base_paper_id'):
    orig_dec = group[group['variant_type']=='original']['decision'].values
    if len(orig_dec)==0:
        continue
    orig_dec = orig_dec[0]
    for _, row in group.iterrows():
        if row['variant_type'] != 'original':
            consistency.append({
                'base_paper_id': base_id,
                'variant_type': row['variant_type'],
                'original_decision': orig_dec,
                'variant_decision': row['decision'],
                'changed': orig_dec != row['decision']
            })
cons_df = pd.DataFrame(consistency)
cons_df.to_csv(f'{outdir}/decision_consistency.csv', index=False)

# 决策变化统计饼图
plt.figure(figsize=(6,6))
changed = cons_df['changed'].sum()
not_changed = len(cons_df) - changed
plt.pie([not_changed, changed], labels=['Unchanged','Changed'], autopct='%1.1f%%', colors=['#66b3ff','#ff9999'])
plt.title('Decision Consistency (Original vs Variant)')
plt.savefig(f'{outdir}/decision_consistency_pie.png')
plt.close()

# 7. 评分标准差分布（每篇论文的变体评分波动）
stds = df.groupby('base_paper_id')['rating'].std().dropna()
plt.figure(figsize=(8,5))
sns.histplot(stds, bins=20, kde=True)
plt.title('Std of Scores Across Variants (per paper)')
plt.xlabel('Std of Scores')
plt.savefig(f'{outdir}/score_std_per_paper.png')
plt.close()

# 8. 变体类型与评分变化热力图
pivot = df.pivot_table(index='base_paper_id', columns='variant_type', values='rating')
score_diff = pivot.subtract(pivot['original'], axis=0)
score_diff = score_diff.drop(columns=['original'])
plt.figure(figsize=(12,6))
sns.heatmap(score_diff, cmap='coolwarm', center=0)
plt.title('Score Change (Variant - Original)')
plt.savefig(f'{outdir}/score_change_heatmap.png')
plt.close()

# 9. 各变体评分均值/标准差柱状图（横向x轴，original基准线）
mean_std = df.groupby('variant_type')['rating'].agg(['mean','std']).reindex(variant_order).reset_index()
plt.figure(figsize=(10,6))
plt.bar(mean_std['variant_type'], mean_std['mean'], yerr=mean_std['std'], capsize=5)
plt.axhline(orig_mean, color='red', linestyle='--', label=f'Original Mean: {orig_mean:.2f}')
plt.title('Mean & Std of Scores by Variant Type')
plt.ylabel('Score')
plt.xticks(rotation=0)
plt.legend()
plt.savefig(f'{outdir}/bar_mean_std_variant_type.png')
plt.close()

# 10. 各变体评分分布密度图（original基准线）
plt.figure(figsize=(10,6))
for vt in variant_order:
    sns.kdeplot(df[df['variant_type']==vt]['rating'], label=vt)
plt.axvline(orig_mean, color='red', linestyle='--', label=f'Original Mean: {orig_mean:.2f}')
plt.title('Score Density by Variant Type')
plt.legend()
plt.savefig(f'{outdir}/density_variant_type.png')
plt.close()

# 11. 各变体决策比例柱状图（横向x轴）
dec_ratio = df.groupby(['variant_type','decision']).size().unstack(fill_value=0).reindex(variant_order)
dec_ratio = dec_ratio.div(dec_ratio.sum(axis=1), axis=0)
dec_ratio.plot(kind='bar', stacked=True, figsize=(10,6))
plt.title('Decision Ratio by Variant Type')
plt.ylabel('Ratio')
plt.xticks(rotation=0)
plt.savefig(f'{outdir}/bar_decision_ratio_variant_type.png')
plt.close()

# 12. 原始与变体评分均值对比折线图（original最左，基准线）
mean_scores = df.groupby(['variant_type'])['rating'].mean().reindex(variant_order).reset_index()
plt.figure(figsize=(10,6))
plt.plot(mean_scores['variant_type'], mean_scores['rating'], marker='o')
plt.axhline(orig_mean, color='red', linestyle='--', label=f'Original Mean: {orig_mean:.2f}')
plt.title('Mean Score by Variant Type')
plt.ylabel('Mean Score')
plt.xticks(rotation=0)
plt.legend()
plt.savefig(f'{outdir}/line_mean_score_variant_type.png')
plt.close()

# 13. 原始与变体决策一致性分布条形图（横向x轴）
cons_bar = cons_df.groupby(['variant_type','changed']).size().unstack(fill_value=0).reindex(variant_order)
cons_bar = cons_bar.div(cons_bar.sum(axis=1), axis=0)
cons_bar.plot(kind='bar', stacked=True, figsize=(10,6))
plt.title('Decision Consistency Ratio by Variant Type')
plt.ylabel('Ratio')
plt.xticks(rotation=0)
plt.savefig(f'{outdir}/bar_decision_consistency_variant_type.png')
plt.close()

# 14. 每种变体评分变化（变体-原始）分布箱线图（original最左，基准线）
plt.figure(figsize=(10,6))
sns.boxplot(x='variant_type', y='score_diff', data=score_diff_df, order=[v for v in variant_order if v != 'original'])
plt.axhline(0, color='red', linestyle='--', label='No Change (Original)')
plt.title(f'Score Change (Variant - Original) by Variant Type\n(Anomaly Ratio: {anomaly_ratio:.2%})')
plt.legend()
plt.savefig(f'{outdir}/boxplot_score_diff_variant_type.png')
plt.close()

# 15. 每种变体评分变化均值/标准差柱状图（横向x轴）
mean_std_diff = score_diff_df.groupby('variant_type')['score_diff'].agg(['mean','std']).reindex([v for v in variant_order if v != 'original']).reset_index()
plt.figure(figsize=(10,6))
plt.bar(mean_std_diff['variant_type'], mean_std_diff['mean'], yerr=mean_std_diff['std'], capsize=5)
plt.axhline(0, color='red', linestyle='--', label='No Change (Original)')
plt.title('Mean & Std of Score Change by Variant Type')
plt.ylabel('Score Change')
plt.xticks(rotation=0)
plt.legend()
plt.savefig(f'{outdir}/bar_mean_std_score_diff_variant_type.png')
plt.close()

# 16. 每种变体评分变化密度图（original基准线）
plt.figure(figsize=(10,6))
for vt in [v for v in variant_order if v != 'original']:
    sns.kdeplot(score_diff_df[score_diff_df['variant_type']==vt]['score_diff'], label=vt)
plt.axvline(0, color='red', linestyle='--', label='No Change (Original)')
plt.title('Score Change Density by Variant Type')
plt.legend()
plt.savefig(f'{outdir}/density_score_diff_variant_type.png')
plt.close()

# 针对每一类变体生成分析图（评分分布、决策分布、评分变化箱线图、异常值散点图）
for vt in [v for v in variant_order if v != 'original']:
    sub = df[df['variant_type']==vt]
    plt.figure(figsize=(8,5))
    sns.histplot(sub['rating'], bins=15, kde=True)
    plt.axvline(orig_mean, color='red', linestyle='--', label=f'Original Mean: {orig_mean:.2f}')
    plt.title(f'Score Distribution for {vt}')
    plt.legend()
    plt.savefig(f'{outdir}/score_hist_{vt}.png')
    plt.close()
    # 决策分布
    plt.figure(figsize=(6,4))
    sub['decision'].value_counts().plot(kind='bar')
    plt.title(f'Decision Distribution for {vt}')
    plt.ylabel('Count')
    plt.xticks(rotation=0)
    plt.savefig(f'{outdir}/decision_bar_{vt}.png')
    plt.close()
    # 评分变化箱线图
    diff = score_diff_df[score_diff_df['variant_type']==vt]
    plt.figure(figsize=(6,4))
    sns.boxplot(y=diff['score_diff'])
    plt.axhline(0, color='red', linestyle='--', label='No Change (Original)')
    plt.title(f'Score Change (Variant - Original) for {vt}')
    plt.legend()
    plt.savefig(f'{outdir}/score_diff_box_{vt}.png')
    plt.close()
    # 异常值散点图
    extreme = diff[diff['score_diff'] > diff['score_diff'].quantile(0.95)]
    if not extreme.empty:
        plt.figure(figsize=(6,4))
        plt.scatter([vt]*len(extreme), extreme['score_diff'], color='orange', label='Extreme (Top 5%)')
        plt.axhline(0, color='red', linestyle='--')
        plt.title(f'Extreme Score Change for {vt}')
        plt.legend()
        plt.savefig(f'{outdir}/extreme_score_scatter_{vt}.png')
        plt.close()

# 自动生成更详细的配套说明文档
with open(f'{outdir}/README.md', 'w', encoding='utf-8') as f:
    f.write('# 图表说明\n')
    f.write('本目录下所有统计图表均基于 merged.jsonl 数据自动生成，涵盖评分、决策、变体影响、极端值、分布等。\n\n')
    f.write('## 图表列表\n')
    for img in sorted(os.listdir(outdir)):
        if img.endswith('.png'):
            f.write(f'- {img}\n')
    f.write('\n## 图表说明\n')
    f.write('每张图下方有详细解读，说明其用途、观察方法和结论建议。\n')
    f.write('### boxplot_variant_type.png\n')
    f.write('各变体评分箱线图，original在最左，红线为original均值。可观察各变体分布、异常值、与原始论文的对比。\n')
    f.write('### bar_mean_std_variant_type.png\n')
    f.write('各变体评分均值/标准差柱状图，红线为original均值。可直观比较各变体均值和波动。\n')
    f.write('### density_variant_type.png\n')
    f.write('各变体评分分布密度图，红线为original均值。可观察分布形态和偏移。\n')
    f.write('### bar_decision_ratio_variant_type.png\n')
    f.write('各变体决策比例柱状图，横向x轴。可比较各变体的Accept/Reject比例。\n')
    f.write('### line_mean_score_variant_type.png\n')
    f.write('原始与变体评分均值对比折线图，红线为original均值。可观察均值变化趋势。\n')
    f.write('### bar_decision_consistency_variant_type.png\n')
    f.write('原始与变体决策一致性分布条形图。可看出各变体决策变化比例。\n')
    f.write('### boxplot_score_diff_variant_type.png\n')
    f.write('每种变体评分变化（变体-原始）分布箱线图，红线为无变化基准。\n')
    f.write('### bar_mean_std_score_diff_variant_type.png\n')
    f.write('每种变体评分变化均值/标准差柱状图，红线为无变化基准。\n')
    f.write('### density_score_diff_variant_type.png\n')
    f.write('每种变体评分变化密度图，红线为无变化基准。\n')
    f.write('### bar_decision_change_variant_type.png\n')
    f.write('每种变体决策变化比例柱状图。\n')
    f.write('### score_change_heatmap.png\n')
    f.write('按base_paper_id评分变化热力图。\n')
    f.write('### decision_change_heatmap.png\n')
    f.write('按base_paper_id决策变化热力图。\n')
    f.write('### score_std_per_paper.png\n')
    f.write('每篇论文变体评分标准差分布。\n')
    f.write('### abs_score_change_hist.png\n')
    f.write('评分变化绝对值分布。\n')
    f.write('### extreme_score_change_scatter.png\n')
    f.write('评分变化极端值（Top 5%）散点图。\n')
    f.write('### all_papers_score_line.png\n')
    f.write('所有论文评分变化折线图。\n')
    f.write('### all_papers_decision_line.png\n')
    f.write('所有论文决策变化折线图。\n')
    f.write('### score_change_scatter.png\n')
    f.write('评分变化分布散点图。\n')
    f.write('### decision_change_scatter.png\n')
    f.write('决策变化分布散点图。\n')
    f.write('### score_vs_decision_joint.png\n')
    f.write('评分变化与决策变化联合分布图。\n')
    f.write('### case_xxx_line.png\n')
    f.write('高/中/低分个案折线图。\n')
    f.write('### decision_consistency_pie.png\n')
    f.write('原始与变体决策一致性统计饼图。\n')
    f.write('### score_hist.png\n')
    f.write('分数区间分布直方图。\n')
    for vt in [v for v in variant_order if v != 'original']:
        f.write(f'### score_hist_{vt}.png\n{vt} 评分分布直方图，红线为original均值。\n')
        f.write(f'### decision_bar_{vt}.png\n{vt} 决策分布柱状图。\n')
        f.write(f'### score_diff_box_{vt}.png\n{vt} 评分变化箱线图。\n')
        f.write(f'### extreme_score_scatter_{vt}.png\n{vt} 评分变化极端值散点图。\n')
    f.write('\n## 主要结论与解读\n')
    f.write('请结合箱线图、均值图、密度图、决策比例图、热力图等，综合分析各变体对评分和决策的影响。异常值和极端变化需重点关注。\n')
    f.write('数据缺失已自动处理，所有统计均基于实际有效数据。\n')
    f.write('如需进一步分析或定制图表，请联系开发者。\n')
    f.write(f'\n### 异常值分析\n')
    f.write(f'异常值定义为删章节后分数高于原始分数。\n')
    f.write(f'全局异常值比例: {anomaly_ratio:.2%}\n')
    f.write(f'anomaly_count_by_variant.png: 各变体类型异常值数量分布。\n')
    f.write(f'anomaly_ratio_by_variant.png: 各变体类型异常值比例分布。\n')
    f.write(f'boxplot_variant_type.png, boxplot_score_diff_variant_type.png: 图标题已标注异常值比例。\n')
    f.write(f'case_hml_line.png, case_hml_decision_line.png: 高/中/低分个案评分与决策变化合并展示。\n')

print(f'分析完成，所有统计图和详细说明文档已保存到: {outdir}')
