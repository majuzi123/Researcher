import json
from collections import defaultdict

RESULTS_PATH1 = '../evaluation_results/evaluation_results_20260206_224300_incremental.jsonl'
RESULTS_PATH2 = '../evaluation_results/evaluation_results_20260207_115647.jsonl'
OUTPUT_PATH = 'output.txt'
MERGED_PATH = '../evaluation_results/evaluation_results_20260207_115647_merged.jsonl'

# Step 1: 获取仅在文件1存在的组合
only_in_1 = set()
with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    start = False
    for line in lines:
        if '==== 仅在文件1存在的组合 ====' in line:
            start = True
            continue
        if '====' in line and start:
            break
        if start and line.strip():
            combo = line.strip().strip('()').split(',')
            if len(combo) == 2:
                base_id = combo[0].strip().strip("'")
                variant = combo[1].strip().strip("'")
                only_in_1.add((base_id, variant))

# Step 2: 从文件1提取这些组合的唯一记录（去重）
unique_records_dict = {}
with open(RESULTS_PATH1, 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line)
        combo = (record.get('base_paper_id'), record.get('variant_type'))
        if combo in only_in_1 and combo not in unique_records_dict:
            unique_records_dict[combo] = record
unique_records = list(unique_records_dict.values())

# Step 3: 检查文件2中是否已存在这些组合
combos_in_file2 = set()
with open(RESULTS_PATH2, 'r', encoding='utf-8') as f:
    for line in f:
        record = json.loads(line)
        combo = (record.get('base_paper_id'), record.get('variant_type'))
        combos_in_file2.add(combo)

# Step 4: 只追加文件2中没有的记录
final_records = [r for r in unique_records if (r.get('base_paper_id'), r.get('variant_type')) not in combos_in_file2]

# Step 5: 生成新的合并文件
with open(RESULTS_PATH2, 'r', encoding='utf-8') as f_in, open(MERGED_PATH, 'w', encoding='utf-8') as f_out:
    for line in f_in:
        f_out.write(line)
    for record in final_records:
        f_out.write(json.dumps(record, ensure_ascii=False) + '\n')

print(f'已将文件1独有的 {len(final_records)} 条唯一记录追加到文件2，生成新文件: {MERGED_PATH}')
