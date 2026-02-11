# Attack 高级可视化详细指南（advanced_attack_analysis_and_plot.py）

本文档对应脚本：`scripts/advanced_attack_analysis_and_plot.py`。  
本文档不仅说明“每个图怎么画”，还给出“每个图在当前这批数据上的结论”。

## 数据上下文

本轮分析参考数据：
- 输入：`evaluation_results_attack/attack_results_20260208_000302_incremental.jsonl`
- 图表输出目录：`analysis_output/attack_visual_only_test`
- baseline 论文数：100
- attack 样本数：2500（5 种 attack_type × 5 个 attack_position × 100 篇）

全局统计（用于理解后续所有图）：
- baseline 平均分：4.5025
- attack 后平均分：5.0615
- 全局平均增量 `rating_delta`：+0.5590

说明：如果你更换输入文件，下面“结论”数值会变化，但“计算逻辑”不变。

## 核心字段与公式

1. baseline 记录
- 规则：同一 `base_paper_id` 下，满足 `attack_type=none` 或 `variant_type=original` 的记录。
- 字段：`base_rating`, `base_decision`。

2. 评分增量
- 公式：`rating_delta = rating - base_rating`。
- 解释：攻击样本相对 baseline 的净变化。

3. 接收率映射
- 规则：`paper_decision` 包含 `accept` 映射为 1；包含 `reject` 映射为 0。
- 字段：`accept`。

4. 决策迁移
- 公式：`decision_pair = base_decision + " -> " + decision`。
- 示例：`Reject -> Accept`, `Accept -> Reject`。

5. 增减分分类
- 规则：
  - `rating_delta > 0` => `up`
  - `rating_delta = 0` => `same`
  - `rating_delta < 0` => `down`

## 图表逐项说明（计算逻辑 + 读图要点 + 当前结论）

### 1) `analysis_output/attack_visual_only_test/attack_type_summary_table.png`
计算逻辑：
- `groupby(attack_type)` 聚合以下统计：
  - `count`
  - `mean_rating`
  - `mean_delta`
  - `median_delta`
  - `std_delta`
  - `positive_rate`（`delta_sign=up` 比例）
  - `negative_rate`（`delta_sign=down` 比例）
  - `same_rate`
  - `accept_rate`

读图要点：
- 优先看 `mean_delta` 和 `accept_rate` 的排序，再看 `std_delta` 判断稳定性。

当前结论：
- 有效性排序：`direct > hidden > instruction > polite > persuasive`。
- `direct`: `mean_delta=+0.7536`, `accept_rate=0.332`（最强）。
- `persuasive`: `mean_delta=+0.3994`, `accept_rate=0.244`（最弱之一）。

### 2) `analysis_output/attack_visual_only_test/attack_position_summary_table.png`
计算逻辑：
- `groupby(attack_position)`，聚合指标与上图一致。

读图要点：
- 重点比较不同位置对 `mean_delta` 与 `accept_rate` 的影响。

当前结论：
- 位置效果排序：`conclusion > introduction > abstract > experiments > methods`。
- `conclusion`: `mean_delta=+0.7148`, `accept_rate=0.346`（最优）。
- `methods`: `mean_delta=+0.4477`, `accept_rate=0.228`（最弱）。

### 3) `analysis_output/attack_visual_only_test/decision_transition_summary_table.png`
计算逻辑：
- 先 `groupby(attack_type, decision_pair).size()` 得 `count`。
- 再在每个 `attack_type` 内归一化：`ratio = count / sum(count)`。

读图要点：
- 看 `Reject -> Accept` 是攻击成功关键指标。
- 看 `Accept -> Reject` 是副作用指标。

当前结论：
- `Reject -> Accept`：`direct=0.280` 最高；`polite=0.190` 最低。
- `Accept -> Reject` 非零（约 0.046~0.074），说明攻击有副作用，不是单向增益。

### 4) `analysis_output/attack_visual_only_test/top20_papers_mean_delta_table.png`
计算逻辑：
- `groupby(base_paper_id)` 计算 `mean_delta/std_delta/max_delta/min_delta`。
- 按 `mean_delta` 降序取 Top20。

读图要点：
- 定位“高敏感论文”（多攻击下普遍被抬分）。

当前结论：
- 存在一批对攻击高度敏感的论文，建议后续单独做鲁棒性 case study。

### 5) `analysis_output/attack_visual_only_test/top_positive_cases_barh.png`
计算逻辑：
- 选 `nlargest(20, rating_delta)`。
- 横轴 `rating_delta`，纵轴为 `base_paper_id | attack_type@attack_position`。

读图要点：
- 看极端正向增量是否伴随 `Reject -> Accept`。

当前结论：
- 最极端样本达到 `+5.0`。
- 多个高增益样本伴随决策翻转到 Accept，代表高风险漏洞点。

### 6) `analysis_output/attack_visual_only_test/top_negative_cases_barh.png`
计算逻辑：
- 选 `nsmallest(20, rating_delta)`，其余同上。

读图要点：
- 判断攻击是否在某些样本上“反噬”。

当前结论：
- 最低样本约 `-3.0`，说明攻击不是总能提分。

### 7) `analysis_output/attack_visual_only_test/rating_distribution_baseline_vs_attack.png`
计算逻辑：
- 对 `base_rating` 和 `rating` 分别做 KDE。

读图要点：
- 比较分布中心是否右移。
- 比较是否仍有较大重叠（稳定性问题）。

当前结论：
- 攻击分布整体右移（均值上升）。
- 仍有重叠，说明有效但非“压倒性稳定”。

### 8) `analysis_output/attack_visual_only_test/box_rating_delta_by_attack_type.png`
计算逻辑：
- 箱线图：`x=attack_type`, `y=rating_delta`。
- 红虚线 `y=0` 作为无变化基准。

读图要点：
- 中位数是否 > 0。
- 下须是否穿过 0 以下（风险）。
- 箱体高度反映波动性。

当前结论：
- 所有类型中位数均为正。
- `direct`/`hidden` 中位增量约 0.5，提升最明显。
- 同时存在负尾，代表不稳定性。

### 9) `analysis_output/attack_visual_only_test/box_rating_delta_by_attack_position.png`
计算逻辑：
- 箱线图：`x=attack_position`, `y=rating_delta`。

读图要点：
- 看位置维度的中位增量与负尾深度。

当前结论：
- `conclusion` 箱体整体更高，提升更稳定。
- `methods` 负尾更明显，风险更大。

### 10) `analysis_output/attack_visual_only_test/heatmap_mean_delta_type_position.png`
计算逻辑：
- `pivot_table(index=attack_type, columns=attack_position, values=rating_delta, aggfunc=mean)`。

读图要点：
- 找“最强组合”和“最弱组合”。

当前结论（关键组合）：
- 强组合：`direct@conclusion +0.930`，`hidden@conclusion +0.958`。
- 弱组合：`persuasive@methods +0.221`。

### 11) `analysis_output/attack_visual_only_test/heatmap_accept_rate_type_position.png`
计算逻辑：
- `pivot_table(index=attack_type, columns=attack_position, values=accept, aggfunc=mean)`。

读图要点：
- 看哪些组合最容易把样本推到 Accept。

当前结论：
- 最高：`direct@conclusion=0.45`，`hidden@conclusion=0.45`。
- 最低：`persuasive@methods=0.17`。

### 12) `analysis_output/attack_visual_only_test/stacked_delta_sign_by_attack_type.png`
计算逻辑：
- 按 `(attack_type, delta_sign)` 计数。
- 对每个 `attack_type` 行归一化后堆叠展示。

读图要点：
- 看 `up` 比例是否显著高于 `down`。

当前结论：
- 全部类型 `up` 比例 > 0.55。
- `direct` 最高（0.676），`polite/persuasive` 相对较低（约 0.55）。

### 13) `analysis_output/attack_visual_only_test/stacked_decision_transition_by_attack_type.png`
计算逻辑：
- 按 `(attack_type, decision_pair)` 计数并归一化堆叠。

读图要点：
- `Reject -> Accept` 占比越高，攻击越有效。
- `Accept -> Reject` 占比越高，副作用越强。

当前结论：
- 主体仍是 `Reject -> Reject`（模型有一定鲁棒性）。
- `Reject -> Accept` 在 `direct` 中最突出。

### 14) `analysis_output/attack_visual_only_test/bar_accept_rate_by_attack_type.png`
计算逻辑：
- `groupby(attack_type)['accept'].mean()`。

读图要点：
- 直接比较类型级攻击成功率。

当前结论：
- `direct`、`hidden` 显著优于其余类型。

### 15) `analysis_output/attack_visual_only_test/bar_accept_rate_by_attack_position.png`
计算逻辑：
- `groupby(attack_position)['accept'].mean()`。

读图要点：
- 直接比较位置级攻击成功率。

当前结论：
- `conclusion` 明显最高，`methods` 最低，与均值增量图结论一致。

### 16) `analysis_output/attack_visual_only_test/scatter_baseline_vs_delta.png`
计算逻辑：
- 散点：`x=base_rating`, `y=rating_delta`, hue=`attack_type`。

读图要点：
- 看 baseline 分数与增量关系（是否存在“越低越好攻”）。

当前结论：
- 低 baseline 样本更容易出现大正增量。
- 高 baseline 区域出现更多负增量点。

### 17) `analysis_output/attack_visual_only_test/hist_mean_delta_per_paper.png`
计算逻辑：
- 先对每个 `base_paper_id` 求 `mean(rating_delta)`。
- 再绘制直方图 + KDE。

读图要点：
- 看论文级“平均受攻击程度”分布。

当前结论：
- 分布右偏，整体均值为正。
- 统计上：67 篇论文平均增量 > 0，33 篇 <= 0。

### 18) `analysis_output/attack_visual_only_test/heatmap_count_type_position.png`
计算逻辑：
- `pivot_table(index=attack_type, columns=attack_position, values=base_paper_id, aggfunc=count)`。

读图要点：
- 检查设计是否平衡，防止样本数偏差影响比较。

当前结论：
- 各格基本都是 100，实验设计平衡，跨类型/位置比较可信。

### 19) `analysis_output/attack_visual_only_test/box_rating_delta_section_found.png`（可选）
计算逻辑：
- 当 `section_found` 同时有 True/False 时，画 `x=section_found`, `y=rating_delta` 箱线图。

读图要点：
- 比较“精准插入”与“估算插入”在攻击效果上的差异。

当前结论：
- 本次输出目录无该图，说明 `section_found` 可能单值或不足以形成对比组。

## 总结（基于当前数据）

1. 攻击整体有效：平均提分 +0.559。  
2. 类型层面：`direct` 最强，`persuasive/polite` 较弱。  
3. 位置层面：`conclusion` 最强，`methods` 最弱。  
4. 关键风险：存在大量 `Reject -> Accept` 翻转，且极端样本增量可到 +5。  
5. 同时存在副作用：`Accept -> Reject` 与强负增量样本并存，说明攻击并非单向。  
6. 数据平衡性良好：`type×position` 计数均衡，结论不太可能是样本数偏差造成。

## 运行命令

默认读取 `evaluation_results_attack` 最新结果：

```bash
python scripts/advanced_attack_analysis_and_plot.py
```

指定输入文件：

```bash
python scripts/advanced_attack_analysis_and_plot.py --input evaluation_results_attack/attack_results_20260208_000302_incremental.jsonl
```

指定输出目录：

```bash
python scripts/advanced_attack_analysis_and_plot.py --output-dir analysis_output/attack_visual_only_test
```
