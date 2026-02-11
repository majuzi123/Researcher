import argparse
import json
from collections import Counter
from pathlib import Path


def dedup_attack_results(input_path: Path, output_path: Path) -> dict:
    seen = set()
    kept = []
    duplicate_counts = Counter()
    total = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            total += 1
            record = json.loads(line)
            combo = (
                str(record.get("base_paper_id", "")),
                str(record.get("attack_type", "")),
                str(record.get("attack_position", "")),
            )
            if combo in seen:
                duplicate_counts[combo] += 1
                continue
            seen.add(combo)
            kept.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in kept:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "total_records": total,
        "unique_records": len(kept),
        "removed_duplicates": total - len(kept),
        "duplicate_combo_count": len(duplicate_counts),
        "duplicate_counts": duplicate_counts,
    }


def build_output_path(input_path: Path, output_arg: Path | None) -> Path:
    if output_arg:
        return output_arg
    if input_path.suffix == ".jsonl":
        return input_path.with_name(input_path.stem + "_deduped.jsonl")
    return input_path.with_name(input_path.name + "_deduped")


def main():
    parser = argparse.ArgumentParser(description="Deduplicate attack results JSONL by (base_paper_id, attack_type, attack_position).")
    parser.add_argument("--input", type=Path, required=True, help="Input attack results JSONL")
    parser.add_argument("--output", type=Path, default=None, help="Output deduplicated JSONL")
    parser.add_argument("--report", type=Path, default=None, help="Optional text report path")
    args = parser.parse_args()

    input_path = args.input
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path = build_output_path(input_path, args.output)
    stats = dedup_attack_results(input_path, output_path)

    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    print(f"Total records: {stats['total_records']}")
    print(f"Unique records: {stats['unique_records']}")
    print(f"Removed duplicates: {stats['removed_duplicates']}")
    print(f"Duplicate combos: {stats['duplicate_combo_count']}")

    if args.report:
        report_path = args.report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"Input: {input_path}\n")
            f.write(f"Output: {output_path}\n")
            f.write(f"Total records: {stats['total_records']}\n")
            f.write(f"Unique records: {stats['unique_records']}\n")
            f.write(f"Removed duplicates: {stats['removed_duplicates']}\n")
            f.write(f"Duplicate combos: {stats['duplicate_combo_count']}\n\n")
            f.write("Duplicate combo details:\n")
            for combo, count in stats["duplicate_counts"].most_common():
                f.write(f"{combo}: removed {count}\n")
        print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
