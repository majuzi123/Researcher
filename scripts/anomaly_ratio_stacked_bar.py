import os
import json
import re
import textwrap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    if isinstance(r.get('evaluation'), dict):
        rating = r['evaluation'].get('avg_rating')
    rows.append({
        'base_paper_id': base_id,
        'variant_type': variant,
        'rating': rating
    })
df = pd.DataFrame(rows)
df = df[df['rating'].notnull()]

# 保证 original 在所有图表中最左边
variant_order = sorted(df['variant_type'].unique(), key=lambda x: (x != 'original', x))
# 报告展示顺序（由轻到重）
severity_order = ['no_conclusion', 'no_abstract', 'no_introduction', 'no_experiments', 'no_methods']

# 计算每个变体的异常、未修改、正常反应比例
anomaly_counts = {v: 0 for v in variant_order if v != 'original'}
normal_counts = {v: 0 for v in variant_order if v != 'original'}
unmod_counts = {v: 0 for v in variant_order if v != 'original'}
total_counts = {v: 0 for v in variant_order if v != 'original'}

for base_id, group in df.groupby('base_paper_id'):
    orig = group[group['variant_type']=='original']
    if orig.empty:
        continue
    orig_score = orig.iloc[0]['rating']
    for _, row in group.iterrows():
        vt = row['variant_type']
        if vt == 'original':
            continue
        total_counts[vt] += 1
        if row['rating'] > orig_score:
            anomaly_counts[vt] += 1
        elif row['rating'] == orig_score:
            unmod_counts[vt] += 1
        else:
            normal_counts[vt] += 1

# 计算比例（先按变体名保存，再按报告顺序取出）
ratio_by_variant = {}
for vt in variant_order:
    if vt == 'original':
        continue
    total = total_counts[vt]
    if total == 0:
        ratio_by_variant[vt] = {'anomaly': 0, 'unmod': 0, 'normal': 0}
    else:
        ratio_by_variant[vt] = {
            'anomaly': anomaly_counts[vt]/total,
            'unmod': unmod_counts[vt]/total,
            'normal': normal_counts[vt]/total
        }

# 绘制堆叠柱状图
import matplotlib
matplotlib.use('Agg')
non_original_variants = [vt for vt in variant_order if vt != 'original']
labels = [vt for vt in severity_order if vt in non_original_variants] + \
         [vt for vt in non_original_variants if vt not in severity_order]
anomaly_ratio = [ratio_by_variant[vt]['anomaly'] for vt in labels]
unmod_ratio = [ratio_by_variant[vt]['unmod'] for vt in labels]
normal_ratio = [ratio_by_variant[vt]['normal'] for vt in labels]
bar_width = 0.6
fig, ax = plt.subplots(figsize=(10,6))
# 交通灯式顺序：绿（正常）在底，橙（轻异常/不变）在中，红（异常）在顶
ax.bar(labels, normal_ratio, bar_width, label='Down (Normal Reaction)', color='green')
ax.bar(labels, unmod_ratio, bar_width, bottom=normal_ratio, label='Same (Un-modified)', color='orange')
ax.bar(labels, anomaly_ratio, bar_width, bottom=np.array(normal_ratio)+np.array(unmod_ratio), label='Up (Anomaly)', color='red')
ax.set_ylabel('Ratio')
ax.set_ylim(0,1)
ax.set_title('Stacked Anomaly/Normal/Un-modified Ratio by Variant Type')
ax.legend()
plt.tight_layout()
plt.savefig(f'{outdir}/anomaly_ratio_by_variant_stacked.png')
plt.close()
print(f"Saved stacked bar plot to {outdir}/anomaly_ratio_by_variant_stacked.png")

# ========== 新增：极端异常与异常 Accept 统计与绘图 ==========
# 先尝试读取 decision 字段
# 重新读取数据，包含 decision 字段
rows = []
with open(jsonl_path, 'r', encoding='utf-8') as f:
    for line in f:
        r = json.loads(line)
        base_id = r.get('base_paper_id')
        variant = r.get('variant_type')
        title = r.get('title')
        rating = None
        decision = None
        meta_review = None
        strengths = None
        weaknesses = None
        if isinstance(r.get('evaluation'), dict):
            rating = r['evaluation'].get('avg_rating')
            decision = r['evaluation'].get('paper_decision')
            meta_review = r['evaluation'].get('meta_review')
            strengths = r['evaluation'].get('strength')
            weaknesses = r['evaluation'].get('weaknesses')
        rows.append({
            'base_paper_id': base_id,
            'variant_type': variant,
            'rating': rating,
            'decision': decision,
            'title': title,
            'meta_review': meta_review,
            'strengths': strengths,
            'weaknesses': weaknesses
        })
df_dec = pd.DataFrame(rows)
df_dec = df_dec[df_dec['rating'].notnull()]

# 统计每种变体的决策变化构成（re2re/ac2re/ac2ac/re2ac）
variant_order = sorted(df_dec['variant_type'].unique(), key=lambda x: (x != 'original', x))
decision_change_counts = {
    v: {'re2re': 0, 'ac2re': 0, 'ac2ac': 0, 're2ac': 0, 'total': 0}
    for v in variant_order if v != 'original'
}
extreme_abnormal_cases = []
abnormal_accept_cases = []

for base_id, group in df_dec.groupby('base_paper_id'):
    orig = group[group['variant_type']=='original']
    if orig.empty:
        continue
    orig_dec = orig.iloc[0]['decision']
    for _, row in group.iterrows():
        vt = row['variant_type']
        if vt == 'original':
            continue
        var_dec = row['decision']
        if orig_dec == 'Reject' and var_dec == 'Reject':
            decision_change_counts[vt]['re2re'] += 1
        elif orig_dec == 'Accept' and var_dec == 'Reject':
            decision_change_counts[vt]['ac2re'] += 1
        elif orig_dec == 'Accept' and var_dec == 'Accept':
            decision_change_counts[vt]['ac2ac'] += 1
            abnormal_accept_cases.append({
                'base_paper_id': base_id,
                'variant_type': vt,
                'orig_decision': orig_dec,
                'variant_decision': var_dec,
                'rating': row['rating']
            })
        elif orig_dec == 'Reject' and var_dec == 'Accept':
            decision_change_counts[vt]['re2ac'] += 1
            extreme_abnormal_cases.append({
                'base_paper_id': base_id,
                'variant_type': vt,
                'orig_decision': orig_dec,
                'variant_decision': var_dec,
                'rating': row['rating']
            })
        else:
            continue
        decision_change_counts[vt]['total'] += 1

# 计算比例（分母为该变体下全部有效样本）
non_original_variants = [vt for vt in variant_order if vt != 'original']
labels = [vt for vt in severity_order if vt in non_original_variants] + \
         [vt for vt in non_original_variants if vt not in severity_order]
re2re_ratio = []
ac2re_ratio = []
ac2ac_ratio = []
re2ac_ratio = []
for vt in labels:
    total = decision_change_counts[vt]['total']
    if total == 0:
        re2re_ratio.append(0)
        ac2re_ratio.append(0)
        ac2ac_ratio.append(0)
        re2ac_ratio.append(0)
    else:
        re2re_ratio.append(decision_change_counts[vt]['re2re']/total)
        ac2re_ratio.append(decision_change_counts[vt]['ac2re']/total)
        ac2ac_ratio.append(decision_change_counts[vt]['ac2ac']/total)
        re2ac_ratio.append(decision_change_counts[vt]['re2ac']/total)

# 兼容后续组合图中原变量名
extreme_abnormal_ratio = re2ac_ratio
abnormal_accept_ratio = ac2ac_ratio

# 绘图
bar_width = 0.6
fig, ax = plt.subplots(figsize=(10,6))
ax.bar(labels, re2re_ratio, bar_width, label='Reject→Reject', color='#1b5e20')  # dark green
ax.bar(labels, ac2re_ratio, bar_width, bottom=re2re_ratio, label='Accept→Reject', color='#8bc34a')  # light green
ax.bar(labels, ac2ac_ratio, bar_width, bottom=np.array(re2re_ratio)+np.array(ac2re_ratio), label='Accept→Accept (Abnormal)', color='#ff9800')  # orange
ax.bar(labels, re2ac_ratio, bar_width, bottom=np.array(re2re_ratio)+np.array(ac2re_ratio)+np.array(ac2ac_ratio), label='Reject→Accept (Extreme Abnormal)', color='#d32f2f')  # red
ax.set_ylabel('Ratio')
ax.set_ylim(0,1)
ax.set_title('Decision Change Composition by Variant Type')
ax.legend()
plt.tight_layout()
plt.savefig(f'{outdir}/extreme_abnormal_accept_ratio_by_variant.png')
plt.close()

# 导出案例
pd.DataFrame(extreme_abnormal_cases).to_csv(f'{outdir}/extreme_abnormal_cases.csv', index=False)
pd.DataFrame(abnormal_accept_cases).to_csv(f'{outdir}/abnormal_accept_cases.csv', index=False)
print(f"Saved plot and case csvs to {outdir}")

# ========== 合并大图：异常比例堆叠柱状图 + 极端异常/异常 Accept 分组柱状图 ==========
fig, axes = plt.subplots(1, 2, figsize=(18, 7))
# 左侧：异常比例堆叠柱状图
axes[0].bar(labels, normal_ratio, 0.6, label='Down (Normal Reaction)', color='green')
axes[0].bar(labels, unmod_ratio, 0.6, bottom=normal_ratio, label='Same (Un-modified)', color='orange')
axes[0].bar(labels, anomaly_ratio, 0.6, bottom=np.array(normal_ratio)+np.array(unmod_ratio), label='Up (Anomaly)', color='red')
axes[0].set_ylabel('Ratio')
axes[0].set_ylim(0,1)
axes[0].set_title('Stacked Anomaly/Normal/Un-modified Ratio')
axes[0].legend()
# 右侧：决策变化构成堆叠柱状图（交通灯顺序）
axes[1].bar(labels, re2re_ratio, 0.6, label='Reject→Reject', color='#1b5e20')
axes[1].bar(labels, ac2re_ratio, 0.6, bottom=re2re_ratio, label='Accept→Reject', color='#8bc34a')
axes[1].bar(labels, ac2ac_ratio, 0.6, bottom=np.array(re2re_ratio)+np.array(ac2re_ratio), label='Accept→Accept (Abnormal)', color='#ff9800')
axes[1].bar(labels, re2ac_ratio, 0.6, bottom=np.array(re2re_ratio)+np.array(ac2re_ratio)+np.array(ac2ac_ratio), label='Reject→Accept (Extreme Abnormal)', color='#d32f2f')
axes[1].set_ylabel('Ratio')
axes[1].set_ylim(0,1)
axes[1].set_title('Decision Change Composition')
axes[1].legend()
plt.tight_layout()
plt.savefig(f'{outdir}/combined_variant_analysis.png')
plt.close()
print(f"Saved combined variant analysis plot to {outdir}/combined_variant_analysis.png")

# ========== 分数变化与决策变化关系统计与图表 ==========
score_decision_stats = {vt: {'up': {'ac2re':0, 're2ac':0, 'ac2ac':0, 're2re':0, 'total':0},
                             'down': {'ac2re':0, 're2ac':0, 'ac2ac':0, 're2re':0, 'total':0},
                             'same': {'ac2re':0, 're2ac':0, 'ac2ac':0, 're2re':0, 'total':0}}
                      for vt in variant_order if vt != 'original'}
score_decision_cases = []

for base_id, group in df_dec.groupby('base_paper_id'):
    orig = group[group['variant_type']=='original']
    if orig.empty:
        continue
    orig_score = orig.iloc[0]['rating']
    orig_dec = orig.iloc[0]['decision']
    for _, row in group.iterrows():
        vt = row['variant_type']
        if vt == 'original':
            continue
        score_diff = row['rating'] - orig_score
        # 分数变化分类
        if score_diff > 0:
            score_cat = 'up'
        elif score_diff < 0:
            score_cat = 'down'
        else:
            score_cat = 'same'
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
            dec_cat = 'other'  # 处理异常情况
        if dec_cat != 'other':
            score_decision_stats[vt][score_cat][dec_cat] += 1
            score_decision_stats[vt][score_cat]['total'] += 1
            score_decision_cases.append({
                'base_paper_id': base_id,
                'variant_type': vt,
                'score_diff': score_diff,
                'score_cat': score_cat,
                'orig_decision': orig_dec,
                'variant_decision': row['decision'],
                'dec_cat': dec_cat,
                'rating': row['rating']
            })

# 统计比例（按决策类别名存储，避免绘图阶段顺序错位）
score_decision_ratio = {vt: {'up': {}, 'down': {}, 'same': {}} for vt in score_decision_stats}
for vt in score_decision_stats:
    for score_cat in ['up','down','same']:
        total = score_decision_stats[vt][score_cat]['total']
        if total == 0:
            score_decision_ratio[vt][score_cat] = {
                'ac2re': 0,
                're2ac': 0,
                'ac2ac': 0,
                're2re': 0
            }
        else:
            score_decision_ratio[vt][score_cat] = {
                'ac2re': score_decision_stats[vt][score_cat]['ac2re']/total,
                're2ac': score_decision_stats[vt][score_cat]['re2ac']/total,
                'ac2ac': score_decision_stats[vt][score_cat]['ac2ac']/total,
                're2re': score_decision_stats[vt][score_cat]['re2re']/total
            }

# 统计 Score Up/Down/Same 的全局占比（用于子图标题，三者和为1）
score_cat_totals = {k: 0 for k in ['up', 'down', 'same']}
for vt in score_decision_stats:
    for score_cat in ['up', 'down', 'same']:
        score_cat_totals[score_cat] += score_decision_stats[vt][score_cat]['total']
score_cat_all_total = sum(score_cat_totals.values())
if score_cat_all_total == 0:
    score_cat_share = {k: 0.0 for k in ['up', 'down', 'same']}
else:
    score_cat_share = {k: score_cat_totals[k] / score_cat_all_total for k in ['up', 'down', 'same']}

# 绘制堆叠柱状图：每种变体类型，分数升高/降低/不变时决策变化比例
score_cats = ['up','down','same']
score_cat_labels = {'up':'Score Up','down':'Score Down','same':'Score Same'}
# 交通灯顺序（由下到上）：深绿 -> 浅绿 -> 橙 -> 红
decision_labels = ['re2re','ac2re','ac2ac','re2ac']
decision_colors = {
    're2re': '#1b5e20',   # dark green
    'ac2re': '#8bc34a',   # light green
    'ac2ac': '#ff9800',   # orange
    're2ac': '#d32f2f'    # red
}
fig, axes = plt.subplots(1, 3, figsize=(22,7))
for i, score_cat in enumerate(score_cats):
    bottoms = np.zeros(len(labels))
    for dec_cat in decision_labels:
        values = [score_decision_ratio[vt][score_cat][dec_cat] for vt in labels]
        axes[i].bar(labels, values, bar_width, bottom=bottoms, label=dec_cat, color=decision_colors[dec_cat])
        bottoms += np.array(values)
    axes[i].set_ylim(0,1)
    axes[i].set_title(f"{score_cat_labels[score_cat]} ({score_cat_share[score_cat]:.1%}): Decision Change Ratio")
    axes[i].set_ylabel('Ratio')
    axes[i].legend()
plt.tight_layout()
plt.savefig(f'{outdir}/score_decision_change_stacked.png')
plt.close()
print(f"Saved score-decision change stacked plot to {outdir}/score_decision_change_stacked.png")
# 导出案例
pd.DataFrame(score_decision_cases).to_csv(f'{outdir}/score_decision_change_cases.csv', index=False)

# ========== 评分变化热力图正常论文统计（严格标准） ==========
# 构建评分变化矩阵（与热力图一致）
pivot = df_dec.pivot_table(index='base_paper_id', columns='variant_type', values='rating')
score_diff = pivot.subtract(pivot['original'], axis=0)
score_diff = score_diff.drop(columns=['original'])
# 严格标准：
# no_experiment(s)/no_methods/no_introduction 必须 < 0
# no_abstract/no_conclusion 必须 <= 0
experiment_col = 'no_experiments' if 'no_experiments' in score_diff.columns else (
    'no_experiment' if 'no_experiment' in score_diff.columns else None
)
strict_columns = {
    'no_abstract': 'le',
    'no_introduction': 'lt',
    'no_methods': 'lt',
    'no_conclusion': 'le'
}
if experiment_col is not None:
    strict_columns[experiment_col] = 'lt'
missing_variants = [v for v in ['no_abstract', 'no_introduction', 'no_methods', 'no_conclusion'] if v not in score_diff.columns]
if experiment_col is None:
    missing_variants.append('no_experiment(s)')
if missing_variants:
    print(f"Warning: strict criterion skipped missing variants: {missing_variants}")

strict_actual_variants = [v for v in strict_columns if v in score_diff.columns]
score_diff_strict = score_diff[strict_actual_variants].dropna()
all_normal_mask = pd.Series(True, index=score_diff_strict.index)
for col, op in strict_columns.items():
    if col not in score_diff_strict.columns:
        continue
    if op == 'lt':
        all_normal_mask = all_normal_mask & (score_diff_strict[col] < 0)
    else:
        all_normal_mask = all_normal_mask & (score_diff_strict[col] <= 0)
all_normal_papers = score_diff_strict[all_normal_mask]
num_all_normal = all_normal_papers.shape[0]
total_papers = score_diff_strict.shape[0]
percent_all_normal = num_all_normal / total_papers if total_papers else 0
# 导出全正常论文base_paper_id及分数变化
all_normal_papers.to_csv(f'{outdir}/all_normal_papers_score_diff.csv')
# 输出统计结果
with open(f'{outdir}/all_normal_papers_stats.txt', 'w', encoding='utf-8') as f:
    exp_label = experiment_col if experiment_col is not None else 'no_experiment(s)'
    f.write(f'统计标准: {exp_label}/no_methods/no_introduction < 0; no_abstract/no_conclusion <= 0\n')
    f.write(f'全正常论文数量: {num_all_normal}\n')
    f.write(f'总论文数量: {total_papers}\n')
    f.write(f'全正常论文比例: {percent_all_normal:.2%}\n')
print(f"全正常论文数量: {num_all_normal}, 总论文数量: {total_papers}, 比例: {percent_all_normal:.2%}")

# ========== 全正常论文比例可视化 ==========
fig, ax = plt.subplots(figsize=(6,6))
labels_pie = ['All Normal Papers', 'Papers with Anomaly']
sizes = [num_all_normal, total_papers-num_all_normal]
colors_pie = ['#99ff99','#ff9999']
ax.pie(sizes, labels=labels_pie, autopct='%1.1f%%', colors=colors_pie, startangle=90)
ax.set_title('Proportion of Papers Satisfying Strict Criterion')
plt.tight_layout()
plt.savefig(f'{outdir}/all_normal_papers_pie.png')
plt.close()
print(f"Saved all normal papers pie chart to {outdir}/all_normal_papers_pie.png")

# ========== 评分变化热力图（所有论文，y轴为序号） ==========
import seaborn as sns
score_diff_matrix = score_diff.values
fig, ax = plt.subplots(figsize=(12, max(6, score_diff_matrix.shape[0]//5)))
sns.heatmap(score_diff_matrix, cmap='coolwarm', center=0, cbar=True, ax=ax,
            xticklabels=score_diff.columns, yticklabels=False)
ax.set_xlabel('Variant Type')
ax.set_ylabel('Paper Index (not ID)')
ax.set_title('Score Change Heatmap (All Papers, Y=Index)')
plt.tight_layout()
plt.savefig(f'{outdir}/score_change_heatmap_all_papers.png')
plt.close()
print(f"Saved score change heatmap for all papers to {outdir}/score_change_heatmap_all_papers.png")

# ========== 变体合理降分论文统计（严格标准） ==========
# 严格规则：
# no_experiment(s)/no_methods/no_introduction 必须 < 0
# no_abstract/no_conclusion 必须 <= 0
experiment_col = 'no_experiments' if 'no_experiments' in score_diff.columns else (
    'no_experiment' if 'no_experiment' in score_diff.columns else None
)
strict_columns = {
    'no_abstract': 'le',
    'no_introduction': 'lt',
    'no_methods': 'lt',
    'no_conclusion': 'le'
}
if experiment_col is not None:
    strict_columns[experiment_col] = 'lt'

required_core = ['no_abstract', 'no_introduction', 'no_methods', 'no_conclusion']
missing_variants = [v for v in required_core if v not in score_diff.columns]
if experiment_col is None:
    missing_variants.append('no_experiment(s)')
if missing_variants:
    print(f"Warning: strict criterion skipped missing variants: {missing_variants}")

actual_variants = [v for v in strict_columns if v in score_diff.columns]
score_diff_req = score_diff[actual_variants].dropna()
mask = pd.Series(True, index=score_diff_req.index)
for col, op in strict_columns.items():
    if col not in score_diff_req.columns:
        continue
    if op == 'lt':
        mask = mask & (score_diff_req[col] < 0)
    else:
        mask = mask & (score_diff_req[col] <= 0)

reasonable_papers = score_diff_req[mask]
num_reasonable = reasonable_papers.shape[0]
total_req_papers = score_diff_req.shape[0]
percent_reasonable = num_reasonable / total_req_papers if total_req_papers else 0
reasonable_papers.to_csv(f'{outdir}/reasonable_score_change_papers.csv')
with open(f'{outdir}/reasonable_score_change_stats.txt', 'w', encoding='utf-8') as f:
    exp_label = experiment_col if experiment_col is not None else 'no_experiment(s)'
    f.write(f'统计标准: {exp_label}/no_methods/no_introduction < 0; no_abstract/no_conclusion <= 0\n')
    f.write(f'合理降分论文数量: {num_reasonable}\n')
    f.write(f'总论文数量: {total_req_papers}\n')
    f.write(f'合理降分论文比例: {percent_reasonable:.2%}\n')
print(f"合理降分论文数量: {num_reasonable}, 总论文数量: {total_req_papers}, 比例: {percent_reasonable:.2%}")
# 可视化
fig, ax = plt.subplots(figsize=(6,6))
labels_pie2 = ['Reasonable Score Change', 'Others']
sizes2 = [num_reasonable, total_req_papers-num_reasonable]
colors_pie2 = ['#66b3ff','#ff9999']
ax.pie(sizes2, labels=labels_pie2, autopct='%1.1f%%', colors=colors_pie2, startangle=90)
ax.set_title('Proportion of Papers with Reasonable Score Change (Key Variants)')
plt.tight_layout()
plt.savefig(f'{outdir}/reasonable_score_change_pie.png')
plt.close()
print(f"Saved reasonable score change pie chart to {outdir}/reasonable_score_change_pie.png")

# ========== 典型案例筛选与可视化 ==========
# 1. Reject→Accept且分数升高的极端异常案例
reject_accept_cases = []
for base_id, group in df_dec.groupby('base_paper_id'):
    orig = group[group['variant_type']=='original']
    if orig.empty:
        continue
    orig_score = orig.iloc[0]['rating']
    orig_dec = orig.iloc[0]['decision']
    if orig_dec != 'Reject':
        continue
    for _, row in group.iterrows():
        vt = row['variant_type']
        if vt == 'original':
            continue
        if row['decision'] == 'Accept' and row['rating'] > orig_score:
            reject_accept_cases.append({
                'base_paper_id': base_id,
                'orig_score': orig_score,
                'orig_decision': orig_dec,
                'variant_type': vt,
                'variant_score': row['rating'],
                'variant_decision': row['decision']
            })
# 挑选分数升高最多的前5个案例
reject_accept_cases_sorted = sorted(reject_accept_cases, key=lambda x: x['variant_score']-x['orig_score'], reverse=True)[:5]
pd.DataFrame(reject_accept_cases_sorted).to_csv(f'{outdir}/typical_reject_accept_cases.csv', index=False)

# 2. Accept论文删除methods/experiments后仍为Accept的异常案例
accept_high_cases = []
for base_id, group in df_dec.groupby('base_paper_id'):
    orig = group[group['variant_type']=='original']
    if orig.empty:
        continue
    orig_score = orig.iloc[0]['rating']
    orig_dec = orig.iloc[0]['decision']
    if orig_dec != 'Accept':
        continue
    for vt in ['no_methods','no_experiments']:
        variant = group[group['variant_type']==vt]
        if variant.empty:
            continue
        v_score = variant.iloc[0]['rating']
        v_dec = variant.iloc[0]['decision']
        if v_dec == 'Accept':
            accept_high_cases.append({
                'base_paper_id': base_id,
                'orig_score': orig_score,
                'orig_decision': orig_dec,
                'variant_type': vt,
                'variant_score': v_score,
                'variant_decision': v_dec
            })
# 挑选分数不降的前5个案例
accept_high_cases_sorted = sorted(accept_high_cases, key=lambda x: x['variant_score']-x['orig_score'], reverse=True)[:5]
pd.DataFrame(accept_high_cases_sorted).to_csv(f'{outdir}/typical_accept_high_cases.csv', index=False)

# 可视化：折线图展示典型案例分数变化及决策变化
fig, axes = plt.subplots(1, 2, figsize=(14,6))
# Reject→Accept
if reject_accept_cases_sorted:
    labels1 = [f"{c['base_paper_id']}\n{c['variant_type']}" for c in reject_accept_cases_sorted]
    orig_scores1 = [c['orig_score'] for c in reject_accept_cases_sorted]
    variant_scores1 = [c['variant_score'] for c in reject_accept_cases_sorted]
    orig_decisions1 = [c['orig_decision'] for c in reject_accept_cases_sorted]
    variant_decisions1 = [c['variant_decision'] for c in reject_accept_cases_sorted]
    x = np.arange(len(labels1))
    # 画分数变化折线
    axes[0].plot(x, orig_scores1, marker='o', label='Original Score', color='gray', linestyle='--')
    axes[0].plot(x, variant_scores1, marker='o', label='Variant Score', color='red')
    # 标注决策变化
    for i, (xo, vo, od, vd) in enumerate(zip(orig_scores1, variant_scores1, orig_decisions1, variant_decisions1)):
        axes[0].text(i, orig_scores1[i], od, color='black', fontsize=10, ha='center', va='bottom')
        axes[0].text(i, variant_scores1[i], vd, color='red' if vd=='Accept' else 'blue', fontsize=10, ha='center', va='top')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(labels1, rotation=30, ha='right')
    axes[0].set_title('Reject→Accept: Score & Decision Change')
    axes[0].set_ylabel('Score')
    axes[0].legend()
else:
    axes[0].set_title('No Typical Reject→Accept Cases')
# Accept高分
if accept_high_cases_sorted:
    labels2 = [f"{c['base_paper_id']}\n{c['variant_type']}" for c in accept_high_cases_sorted]
    orig_scores2 = [c['orig_score'] for c in accept_high_cases_sorted]
    variant_scores2 = [c['variant_score'] for c in accept_high_cases_sorted]
    orig_decisions2 = [c['orig_decision'] for c in accept_high_cases_sorted]
    variant_decisions2 = [c['variant_decision'] for c in accept_high_cases_sorted]
    x2 = np.arange(len(labels2))
    axes[1].plot(x2, orig_scores2, marker='o', label='Original Score', color='gray', linestyle='--')
    axes[1].plot(x2, variant_scores2, marker='o', label='Variant Score', color='blue')
    for i, (xo, vo, od, vd) in enumerate(zip(orig_scores2, variant_scores2, orig_decisions2, variant_decisions2)):
        axes[1].text(i, orig_scores2[i], od, color='black', fontsize=10, ha='center', va='bottom')
        axes[1].text(i, variant_scores2[i], vd, color='red' if vd=='Accept' else 'blue', fontsize=10, ha='center', va='top')
    axes[1].set_xticks(x2)
    axes[1].set_xticklabels(labels2, rotation=30, ha='right')
    axes[1].set_title('Accept High: Score & Decision Change')
    axes[1].set_ylabel('Score')
    axes[1].legend()
else:
    axes[1].set_title('No Typical Accept High Cases')
plt.tight_layout()
plt.savefig(f'{outdir}/typical_cases_line.png')
plt.close()
print(f"Saved typical cases line chart to {outdir}/typical_cases_line.png")

# ========== 典型案例变体全折线图 ==========
# 目标：合并图固定为 2 个 AC→AC + 2 个 RE→AC（第1个子图优先 AC→AC 且 no_methods）
def _pick_unique_case_entries(cases, top_n=2, prefer_variants=None):
    prefer_variants = prefer_variants or []
    ranked = sorted(
        cases,
        key=lambda x: (
            0 if x.get('variant_type') in prefer_variants else 1,
            -(x.get('variant_score', np.nan) - x.get('orig_score', np.nan)),
        ),
    )
    selected = []
    used_ids = set()
    for item in ranked:
        pid = item.get('base_paper_id')
        if pid in used_ids:
            continue
        selected.append(item)
        used_ids.add(pid)
        if len(selected) >= top_n:
            break
    return selected

selected_ac2ac = _pick_unique_case_entries(
    accept_high_cases,
    top_n=2,
    prefer_variants=['no_methods', 'no_experiments'],
)
selected_re2ac = _pick_unique_case_entries(
    reject_accept_cases,
    top_n=2,
    prefer_variants=['no_methods', 'no_experiments'],
)
typical_specs = (
    [{'base_paper_id': c['base_paper_id'], 'case_tag': 'AC→AC', 'focus_variant': c.get('variant_type', '')} for c in selected_ac2ac] +
    [{'base_paper_id': c['base_paper_id'], 'case_tag': 'RE→AC', 'focus_variant': c.get('variant_type', '')} for c in selected_re2ac]
)

def _clean_base_title(raw_title):
    if not isinstance(raw_title, str):
        return ''
    # 去掉标题末尾的变体后缀，例如 "[no_methods]"
    return re.sub(r'\s*\[[^\]]+\]\s*$', '', raw_title).strip()

if typical_specs:
    combined_cases = []
    for spec in typical_specs:
        paper_id = spec['base_paper_id']
        variants = df_dec[df_dec['base_paper_id'] == paper_id].copy()
        if variants.empty:
            print(f"Warning: no data for forced/typical paper_id={paper_id}")
            continue

        # 固定变体顺序：original优先，其余按全局严重度顺序
        ordered_variant_types = ['original'] + [v for v in severity_order if v in variants['variant_type'].values]
        other_variants = [v for v in variants['variant_type'].values if v not in ordered_variant_types]
        ordered_variant_types.extend(sorted(set(other_variants)))
        variants['variant_type'] = pd.Categorical(variants['variant_type'], categories=ordered_variant_types, ordered=True)
        variants = variants.sort_values('variant_type')

        variant_types = variants['variant_type'].astype(str).tolist()
        scores = variants['rating'].tolist()
        decisions = variants['decision'].tolist()
        base_title = ''
        orig_row = variants[variants['variant_type'].astype(str) == 'original']
        if not orig_row.empty:
            base_title = _clean_base_title(orig_row.iloc[0]['title'])
        if not base_title:
            base_title = _clean_base_title(variants.iloc[0]['title'])
        title_snapshot = textwrap.fill(base_title, width=78) if base_title else '(title unavailable)'
        combined_cases.append({
            'paper_id': paper_id,
            'case_tag': spec['case_tag'],
            'focus_variant': spec['focus_variant'],
            'variant_types': variant_types,
            'scores': scores,
            'decisions': decisions,
            'title_snapshot': title_snapshot
        })

        # 画折线图
        fig, ax = plt.subplots(figsize=(14, 6))
        x = np.arange(len(variant_types))
        ax.plot(x, scores, marker='o', color='blue', label='Score')
        for i, (vt, s, d) in enumerate(zip(variant_types, scores, decisions)):
            ax.text(i, s, d, color='red' if d == 'Accept' else 'black', fontsize=10, ha='center', va='bottom')
        ax.set_xticks(x)
        ax.set_xticklabels(variant_types, rotation=30, ha='right')
        ax.set_title(f'Typical Case: All Variants Score & Decision ({paper_id})\n{title_snapshot}')
        ax.set_ylabel('Score')
        ax.set_xlabel('Variant Type')
        ax.legend()
        plt.tight_layout()
        plt.savefig(f'{outdir}/typical_case_variants_line_{paper_id}.png')
        plt.close()
        print(f"Saved typical case variants line chart for {paper_id} to {outdir}/typical_case_variants_line_{paper_id}.png")

        # 导出该论文所有变体的review快照，便于人工检查“新生成review”内容
        review_snapshot = variants[['base_paper_id', 'variant_type', 'title', 'rating', 'decision', 'meta_review', 'strengths', 'weaknesses']].copy()
        review_snapshot.to_csv(f'{outdir}/typical_case_reviews_{paper_id}.csv', index=False)
        print(f"Saved typical case review snapshot for {paper_id} to {outdir}/typical_case_reviews_{paper_id}.csv")

    # 合并图：展示 2 个 AC→AC + 2 个 RE→AC，便于横向对比
    combined_cases = combined_cases[:4]
    if combined_cases:
        fig, axes = plt.subplots(2, 2, figsize=(24, 14))
        axes = axes.flatten()
        for i, case in enumerate(combined_cases):
            ax = axes[i]
            x = np.arange(len(case['variant_types']))
            ax.plot(x, case['scores'], marker='o', color='blue', linewidth=2.5, markersize=7)
            for j, (vt, s, d) in enumerate(zip(case['variant_types'], case['scores'], case['decisions'])):
                ax.text(
                    j,
                    s,
                    d,
                    color='red' if d == 'Accept' else 'black',
                    fontsize=14,
                    fontweight='bold',
                    ha='center',
                    va='bottom'
                )
                # 强调异常点：no_methods / no_experiments 下仍为 Accept
                if d == 'Accept' and vt in ['no_methods', 'no_experiments']:
                    ax.scatter(
                        j, s,
                        s=240,
                        facecolors='none',
                        edgecolors='#fb8c00',
                        linewidths=2.0,
                        zorder=6
                    )
                    ax.annotate(
                        'anomaly',
                        (j, s),
                        textcoords='offset points',
                        xytext=(0, -16),
                        ha='center',
                        va='top',
                        color='#fb8c00',
                        fontsize=10,
                        fontweight='bold'
                    )
            ax.set_xticks(x)
            ax.set_xticklabels(case['variant_types'], rotation=30, ha='right', fontsize=11)
            short_title = textwrap.shorten(case['title_snapshot'].replace('\n', ' '), width=95, placeholder='...')
            ax.set_title(f"{case['case_tag']} | {case['paper_id']}\n{short_title}", fontsize=13)
            ax.set_ylabel('Score', fontsize=12)
            ax.set_xlabel('Variant Type', fontsize=12)
            ax.tick_params(axis='y', labelsize=11)
            ax.grid(axis='y', alpha=0.2)
            ax.set_ylim(0, max(7, np.nanmax(case['scores']) + 0.5))
        for j in range(len(combined_cases), 4):
            axes[j].axis('off')
        fig.suptitle(
            'Typical Cases: 2 AC→AC + 2 RE→AC (Accept in no_methods/no_experiments highlighted)',
            fontsize=18
        )
        plt.tight_layout(rect=(0, 0, 1, 0.96))
        plt.savefig(f'{outdir}/typical_case_variants_line_combined_4papers.png')
        plt.close()
        print(f"Saved combined typical cases chart to {outdir}/typical_case_variants_line_combined_4papers.png")

# ========== 按原始决策分组分析（高分/中分/低分） ==========
grouped_stats = {}
for dec_cat in ['Accept','Reject']:
    paper_ids = df_dec[df_dec['variant_type']=='original']
    paper_ids = paper_ids[paper_ids['decision']==dec_cat]['base_paper_id'].unique()
    group_pivot = score_diff.loc[paper_ids] if len(paper_ids)>0 else None
    grouped_stats[dec_cat] = group_pivot
    # 热力图
    if group_pivot is not None and not group_pivot.empty:
        matrix = group_pivot.values
        fig, ax = plt.subplots(figsize=(12, max(6, matrix.shape[0]//5)))
        import seaborn as sns
        sns.heatmap(matrix, cmap='coolwarm', center=0, cbar=True, ax=ax,
                    xticklabels=group_pivot.columns, yticklabels=False)
        ax.set_xlabel('Variant Type')
        ax.set_ylabel(f'{dec_cat} Paper Index')
        ax.set_title(f'Score Change Heatmap ({dec_cat} Papers)')
        plt.tight_layout()
        plt.savefig(f'{outdir}/score_change_heatmap_{dec_cat.lower()}_papers.png')
        plt.close()
        print(f"Saved score change heatmap for {dec_cat} papers to {outdir}/score_change_heatmap_{dec_cat.lower()}_papers.png")
    # 决策变化统计（修正版）
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
    # 绘制决策变化统计图
    labels3 = [vt for vt in variant_order if vt != 'original']
    fig, ax = plt.subplots(figsize=(10,6))
    if dec_cat == 'Accept':
        # 只画ac2re和ac2ac
        ac2re_vals = [dec_change_stats[vt]['ac2re']/dec_change_stats[vt]['total'] if dec_change_stats[vt]['total'] else 0 for vt in labels3]
        ac2ac_vals = [dec_change_stats[vt]['ac2ac']/dec_change_stats[vt]['total'] if dec_change_stats[vt]['total'] else 0 for vt in labels3]
        ax.bar(labels3, ac2re_vals, label='ac2re', alpha=0.7, color='#ff9999')
        ax.bar(labels3, ac2ac_vals, bottom=ac2re_vals, label='ac2ac', alpha=0.7, color='#99ff99')
    else:
        # 只画re2ac和re2re
        re2ac_vals = [dec_change_stats[vt]['re2ac']/dec_change_stats[vt]['total'] if dec_change_stats[vt]['total'] else 0 for vt in labels3]
        re2re_vals = [dec_change_stats[vt]['re2re']/dec_change_stats[vt]['total'] if dec_change_stats[vt]['total'] else 0 for vt in labels3]
        ax.bar(labels3, re2ac_vals, label='re2ac', alpha=0.7, color='#66b3ff')
        ax.bar(labels3, re2re_vals, bottom=re2ac_vals, label='re2re', alpha=0.7, color='#cccccc')
    ax.set_ylabel('Ratio')
    ax.set_ylim(0,1)
    ax.set_title(f'Decision Change Ratio by Variant ({dec_cat} Papers)')
    ax.legend()
    plt.tight_layout()
    plt.savefig(f'{outdir}/decision_change_bar_{dec_cat.lower()}_papers.png')
    plt.close()
    print(f"Saved decision change bar for {dec_cat} papers to {outdir}/decision_change_bar_{dec_cat.lower()}_papers.png")
