import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def find_latest_file(directory: Path, pattern: str) -> Path | None:
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def find_latest_two_result_files(directory: Path) -> tuple[Path | None, Path | None]:
    files = sorted(
        directory.glob("attack_results_*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if len(files) < 2:
        return None, None
    return files[1], files[0]


def load_summary(summary_path: Path) -> tuple[list[str], list[str]]:
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    attack_analysis = summary.get("attack_analysis", {})
    by_attack_type = attack_analysis.get("by_attack_type", {})
    by_attack_position = attack_analysis.get("by_attack_position", {})

    attack_types = list(by_attack_type.keys())
    attack_positions = list(by_attack_position.keys())

    return attack_types, attack_positions


def load_records(path: Path) -> tuple[Counter, defaultdict, set]:
    combo_counter: Counter = Counter()
    combo_records = defaultdict(list)
    base_paper_ids = set()

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            base_id = str(record.get("base_paper_id", ""))
            attack_type = str(record.get("attack_type", ""))
            attack_position = str(record.get("attack_position", ""))

            combo = (base_id, attack_type, attack_position)
            combo_counter[combo] += 1
            combo_records[combo].append(record)
            if base_id:
                base_paper_ids.add(base_id)

    return combo_counter, combo_records, base_paper_ids


def build_expected_combos(base_ids: set, attack_types: list[str], attack_positions: list[str]) -> set:
    expected = set()

    normal_types = [t for t in attack_types if t != "none"]
    normal_positions = [p for p in attack_positions if p != "none"]

    for base_id in base_ids:
        expected.add((base_id, "none", "none"))
        for attack_type in normal_types:
            for attack_pos in normal_positions:
                expected.add((base_id, attack_type, attack_pos))

    return expected


def count_by_dimension(combo_counter: Counter) -> tuple[Counter, Counter]:
    type_counts = Counter()
    position_counts = Counter()
    for (_, attack_type, attack_pos), count in combo_counter.items():
        type_counts[attack_type] += count
        position_counts[attack_pos] += count
    return type_counts, position_counts


def compare_evaluations(records1: defaultdict, records2: defaultdict, common_combos: set) -> list[dict]:
    diffs = []
    for combo in common_combos:
        recs1 = records1.get(combo, [])
        recs2 = records2.get(combo, [])
        if not recs1 or not recs2:
            continue
        eval1 = recs1[0].get("evaluation", {})
        eval2 = recs2[0].get("evaluation", {})
        if eval1 != eval2:
            diffs.append({"combo": combo, "eval1": eval1, "eval2": eval2})
    return diffs


def write_report(
    output_path: Path,
    missing1: list,
    missing2: list,
    dup1: list,
    dup2: list,
    counter1: Counter,
    counter2: Counter,
    attack_types: list[str],
    attack_positions: list[str],
    only_in_1: set,
    only_in_2: set,
    diff_records: list[dict],
):
    type_counts1, pos_counts1 = count_by_dimension(counter1)
    type_counts2, pos_counts2 = count_by_dimension(counter2)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("==== 缺失组合（文件1） ====\n")
        for combo in missing1:
            f.write(f"{combo}\n")
        f.write(f"共缺失: {len(missing1)}\n\n")

        f.write("==== 缺失组合（文件2） ====\n")
        for combo in missing2:
            f.write(f"{combo}\n")
        f.write(f"共缺失: {len(missing2)}\n\n")

        f.write("==== 重复组合（文件1） ====\n")
        for combo in dup1:
            f.write(f"{combo}: {counter1[combo]} 次\n")
        f.write(f"共重复: {len(dup1)}\n\n")

        f.write("==== 重复组合（文件2） ====\n")
        for combo in dup2:
            f.write(f"{combo}: {counter2[combo]} 次\n")
        f.write(f"共重复: {len(dup2)}\n\n")

        f.write("==== 每种 attack_type 实际数量（文件1） ====\n")
        for attack_type in attack_types:
            f.write(f"{attack_type}: {type_counts1[attack_type]}\n")
        f.write("==== 每种 attack_type 实际数量（文件2） ====\n")
        for attack_type in attack_types:
            f.write(f"{attack_type}: {type_counts2[attack_type]}\n")

        f.write("\n==== 每种 attack_position 实际数量（文件1） ====\n")
        for attack_pos in attack_positions:
            f.write(f"{attack_pos}: {pos_counts1[attack_pos]}\n")
        f.write("==== 每种 attack_position 实际数量（文件2） ====\n")
        for attack_pos in attack_positions:
            f.write(f"{attack_pos}: {pos_counts2[attack_pos]}\n")

        f.write("\n==== 仅在文件1存在的组合 ====\n")
        for combo in sorted(only_in_1):
            f.write(f"{combo}\n")
        f.write(f"共: {len(only_in_1)}\n\n")

        f.write("==== 仅在文件2存在的组合 ====\n")
        for combo in sorted(only_in_2):
            f.write(f"{combo}\n")
        f.write(f"共: {len(only_in_2)}\n\n")

        f.write("==== 两文件都存在但评估不同的组合 ====\n")
        for diff in diff_records:
            f.write(f"{diff['combo']}:\n  file1: {diff['eval1']}\n  file2: {diff['eval2']}\n")
        f.write(f"共: {len(diff_records)}\n")


def main():
    project_root = Path(__file__).resolve().parent.parent
    attack_dir = project_root / "evaluation_results_attack"

    parser = argparse.ArgumentParser(description="Check missing/duplicate attack evaluation combos.")
    parser.add_argument("--file1", type=Path, default=None, help="First attack results JSONL file")
    parser.add_argument("--file2", type=Path, default=None, help="Second attack results JSONL file")
    parser.add_argument("--summary", type=Path, default=None, help="Attack summary JSON file")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output_attack_check.txt"),
        help="Output report path",
    )
    args = parser.parse_args()

    file1 = args.file1
    file2 = args.file2
    summary = args.summary

    if summary is None:
        summary = find_latest_file(attack_dir, "attack_summary_*.json")
    if file1 is None or file2 is None:
        auto_file1, auto_file2 = find_latest_two_result_files(attack_dir)
        file1 = file1 or auto_file1
        file2 = file2 or auto_file2

    if not summary or not summary.exists():
        raise FileNotFoundError("Summary file not found. Pass --summary explicitly.")
    if not file1 or not file1.exists() or not file2 or not file2.exists():
        raise FileNotFoundError("Need two attack result files. Pass --file1 and --file2 explicitly.")

    attack_types, attack_positions = load_summary(summary)
    counter1, records1, base_ids1 = load_records(file1)
    counter2, records2, base_ids2 = load_records(file2)

    base_ids = base_ids1 | base_ids2
    expected = build_expected_combos(base_ids, attack_types, attack_positions)

    missing1 = [combo for combo in expected if counter1[combo] == 0]
    missing2 = [combo for combo in expected if counter2[combo] == 0]
    dup1 = [combo for combo, count in counter1.items() if count > 1]
    dup2 = [combo for combo, count in counter2.items() if count > 1]

    combos1 = set(counter1.keys())
    combos2 = set(counter2.keys())
    only_in_1 = combos1 - combos2
    only_in_2 = combos2 - combos1
    in_both = combos1 & combos2
    diffs = compare_evaluations(records1, records2, in_both)

    output_path = args.output if args.output.is_absolute() else Path.cwd() / args.output
    write_report(
        output_path=output_path,
        missing1=missing1,
        missing2=missing2,
        dup1=dup1,
        dup2=dup2,
        counter1=counter1,
        counter2=counter2,
        attack_types=attack_types,
        attack_positions=attack_positions,
        only_in_1=only_in_1,
        only_in_2=only_in_2,
        diff_records=diffs,
    )

    print("统计完成，详细结果见", output_path)
    print("文件1:", file1)
    print("文件2:", file2)
    print("summary:", summary)


if __name__ == "__main__":
    main()
