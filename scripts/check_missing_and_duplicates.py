import json
import os
from collections import Counter, defaultdict

# 文件路径
RESULTS_PATH1 = '../evaluation_results/evaluation_results_20260206_224300_incremental.jsonl'
RESULTS_PATH2 = '../evaluation_results/evaluation_results_20260212_054243.jsonl'
SUMMARY_PATH = '../evaluation_results/evaluation_summary_20260212_054243.json'

# 读取 summary 文件，获取理论 base_paper_id × variant_type
with open(SUMMARY_PATH, 'r', encoding='utf-8') as f:
    summary = json.load(f)

variant_types = list(summary['variant_distribution'].keys())
base_paper_ids = set()

# 读取第一个增量文件
actual_combos1 = Counter()
combo_records1 = defaultdict(list)
with open(RESULTS_PATH1, 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line)
        base_id = record.get('base_paper_id')
        variant = record.get('variant_type')
        combo = (base_id, variant)
        actual_combos1[combo] += 1
        combo_records1[combo].append(record)
        base_paper_ids.add(base_id)

# 读取第二个增量文件
actual_combos2 = Counter()
combo_records2 = defaultdict(list)
with open(RESULTS_PATH2, 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line)
        base_id = record.get('base_paper_id')
        variant = record.get('variant_type')
        combo = (base_id, variant)
        actual_combos2[combo] += 1
        combo_records2[combo].append(record)
        base_paper_ids.add(base_id)

# 理论所有组合
expected_combos = set()
for base_id in base_paper_ids:
    for variant in variant_types:
        expected_combos.add((base_id, variant))

# 缺失和重复统计
missing_combos1 = [combo for combo in expected_combos if actual_combos1[combo] == 0]
duplicate_combos1 = [combo for combo, count in actual_combos1.items() if count > 1]
missing_combos2 = [combo for combo in expected_combos if actual_combos2[combo] == 0]
duplicate_combos2 = [combo for combo, count in actual_combos2.items() if count > 1]

# 每种 variant_type 的实际数量
variant_actual_counts1 = Counter()
for combo in actual_combos1:
    variant_actual_counts1[combo[1]] += actual_combos1[combo]
variant_actual_counts2 = Counter()
for combo in actual_combos2:
    variant_actual_counts2[combo[1]] += actual_combos2[combo]

# 对比两个文件的组合
combos1 = set(actual_combos1.keys())
combos2 = set(actual_combos2.keys())
only_in_1 = combos1 - combos2
only_in_2 = combos2 - combos1
in_both = combos1 & combos2

diff_records = []
for combo in in_both:
    recs1 = combo_records1[combo]
    recs2 = combo_records2[combo]
    # 只比较第一条（假设无重复）
    if recs1 and recs2:
        r1 = recs1[0]
        r2 = recs2[0]
        # 比较评分和决策
        if r1.get('evaluation', {}) != r2.get('evaluation', {}):
            diff_records.append({'combo': combo, 'eval1': r1.get('evaluation', {}), 'eval2': r2.get('evaluation', {})})

with open('output.txt', 'w', encoding='utf-8') as f:
    f.write('==== 缺失组合（文件1） ====' + '\n')
    for combo in missing_combos1:
        f.write(f'{combo}\n')
    f.write(f'共缺失: {len(missing_combos1)}\n\n')
    f.write('==== 缺失组合（文件2） ====' + '\n')
    for combo in missing_combos2:
        f.write(f'{combo}\n')
    f.write(f'共缺失: {len(missing_combos2)}\n\n')
    f.write('==== 重复组合（文件1） ====' + '\n')
    for combo in duplicate_combos1:
        f.write(f'{combo}: {actual_combos1[combo]} 次\n')
    f.write(f'共重复: {len(duplicate_combos1)}\n\n')
    f.write('==== 重复组合（文件2） ====' + '\n')
    for combo in duplicate_combos2:
        f.write(f'{combo}: {actual_combos2[combo]} 次\n')
    f.write(f'共重复: {len(duplicate_combos2)}\n\n')
    f.write('==== 每种 variant_type 实际数量（文件1） ====' + '\n')
    for variant in variant_types:
        f.write(f'{variant}: {variant_actual_counts1[variant]}\n')
    f.write('==== 每种 variant_type 实际数量（文件2） ====' + '\n')
    for variant in variant_types:
        f.write(f'{variant}: {variant_actual_counts2[variant]}\n')
    f.write('\n==== 仅在文件1存在的组合 ====' + '\n')
    for combo in only_in_1:
        f.write(f'{combo}\n')
    f.write(f'共: {len(only_in_1)}\n\n')
    f.write('==== 仅在文件2存在的组合 ====' + '\n')
    for combo in only_in_2:
        f.write(f'{combo}\n')
    f.write(f'共: {len(only_in_2)}\n\n')
    f.write('==== 两文件都存在但评估不同的组合 ====' + '\n')
    for diff in diff_records:
        f.write(f'{diff["combo"]}:\n  file1: {diff["eval1"]}\n  file2: {diff["eval2"]}\n')
    f.write(f'共: {len(diff_records)}\n')

print('统计完成，详细结果见 output.txt')
