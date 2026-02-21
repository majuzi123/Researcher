# Attack 图表说明与计算逻辑

- 输入文件: `D:\Mike\PycharmProjects\Researcher\evaluation_results_attack\attack_results_20260211_171509.jsonl`
- baseline 论文数: `100`
- attack 样本数: `2500`

## 核心派生字段
- `base_rating`: 同一 `base_paper_id` 的 baseline（`attack_type=none` 或 `original`）评分。
- `rating_delta = rating - base_rating`。
- `accept`: `paper_decision` 包含 `accept` 记为 1，包含 `reject` 记为 0。
- `decision_pair = base_decision -> decision`。
- `delta_sign`: `rating_delta>0` 为 `up`，`<0` 为 `down`，`=0` 为 `same`。

## 每张图说明
1. `attack_type_summary_table.png`: 按 `attack_type` 聚合统计表。
计算逻辑: `groupby(attack_type)` 后统计 count/mean_rating/mean_delta/median_delta/std_delta/positive_rate/negative_rate/same_rate/accept_rate。
2. `attack_position_summary_table.png`: 按 `attack_position` 聚合统计表。
计算逻辑: 与 attack_type 同理，只是分组键换成 `attack_position`。
3. `decision_transition_summary_table.png`: 决策迁移统计表。
计算逻辑: `groupby(attack_type, decision_pair).size()` 得 count，再在每个 attack_type 内归一化得 ratio。
4. `top20_papers_mean_delta_table.png`: 每篇论文平均攻击效应 Top20。
计算逻辑: `groupby(base_paper_id)` 统计 mean_delta/std_delta/max_delta/min_delta，按 mean_delta 降序取前20。
5. `top_positive_cases_barh.png`: 单样本升分最大的 20 个 case（横向条形图）。
计算逻辑: `nlargest(20, rating_delta)`，标签为 `base_paper_id | attack_type@attack_position`。
6. `top_negative_cases_barh.png`: 单样本降分最大的 20 个 case（横向条形图）。
计算逻辑: `nsmallest(20, rating_delta)`。
7. `rating_distribution_baseline_vs_attack.png`: baseline 与攻击样本评分核密度对比。
计算逻辑: 分别对 `base_rating` 与 `rating` 做 KDE。
8. `box_rating_delta_by_attack_type.png`: 各攻击类型的 `rating_delta` 箱线图。
计算逻辑: x=attack_type, y=rating_delta；红虚线 y=0 表示“无变化”。
9. `box_rating_delta_by_attack_position.png`: 各攻击位置的 `rating_delta` 箱线图。
计算逻辑: x=attack_position, y=rating_delta；红虚线 y=0。
10. `heatmap_mean_delta_type_position.png`: 类型×位置 平均升降分热力图。
计算逻辑: `pivot_table(index=attack_type, columns=attack_position, values=rating_delta, aggfunc=mean)`。
11. `heatmap_accept_rate_type_position.png`: 类型×位置 Accept 率热力图。
计算逻辑: 同上，只是 values=accept，aggfunc=mean。
11b. `heatmap_type_position_by_score_group_2x2.png`: 按 `base_rating>4` 与 `base_rating<=4` 分组后，绘制 2x2 合并热力图。
计算逻辑: 每个分组内分别计算 `type×position` 的 mean(`rating_delta`) 与 mean(`accept`)，共四个子图拼接为一张大图。
12. `stacked_delta_sign_by_attack_type.png`: 各类型 up/same/down 比例堆叠图。
计算逻辑: 按 `(attack_type, delta_sign)` 计数后行归一化。
13. `stacked_decision_transition_by_attack_type.png`: 各类型决策迁移比例堆叠图。
计算逻辑: 按 `(attack_type, decision_pair)` 计数后行归一化。
14. `bar_accept_rate_by_attack_type.png`: 各攻击类型 Accept 率柱状图。
计算逻辑: `groupby(attack_type)['accept'].mean()`。
15. `bar_accept_rate_by_attack_position.png`: 各攻击位置 Accept 率柱状图。
计算逻辑: `groupby(attack_position)['accept'].mean()`。
16. `scatter_baseline_vs_delta.png`: baseline 分数与分数变化散点图（按 attack_type 着色）。
计算逻辑: 每条攻击样本一个点，x=base_rating, y=rating_delta。
17. `hist_mean_delta_per_paper.png`: 每篇论文平均攻击效应分布直方图（按 baseline 分组着色）。
计算逻辑: 先按 `base_paper_id` 求 mean(rating_delta) 与 base_rating，再按 `base_rating<=4`(红) / `>4`(绿) 叠加直方图 + KDE。
18. `heatmap_count_type_position.png`: 类型×位置样本数热力图（检查数据平衡性）。
计算逻辑: `pivot_table(..., values=base_paper_id, aggfunc=count)`。
19. `box_rating_delta_section_found.png`（若存在）: 章节命中与未命中时的 `rating_delta` 对比。
计算逻辑: x=section_found, y=rating_delta 的箱线图。
20. `hist_top20_mean_delta.png`: Top20 敏感论文的 `mean_delta` 分布直方图。
计算逻辑: 先按 `base_paper_id` 聚合得到 `mean_delta`，取前20后绘制直方图 + KDE。

## 关于横轴文本
- 所有条形图/箱线图类图表都强制 `xticks(rotation=0)`，即横向显示标签。