"""
Resume Evaluation Script
Resumes evaluation from an interrupted incremental save file
"""

import json
from pathlib import Path
from collections import Counter

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation_results"


def find_latest_incremental_file():
    """Find the most recent incremental save file"""
    incremental_files = list(RESULTS_DIR.glob("evaluation_results_*_incremental.jsonl"))

    if not incremental_files:
        print("❌ No incremental save files found")
        return None

    latest = max(incremental_files, key=lambda p: p.stat().st_mtime)
    return latest


def analyze_incremental_results(file_path: Path):
    """Analyze what's in the incremental file"""
    print(f"\n{'='*70}")
    print(f"Analyzing: {file_path.name}")
    print(f"{'='*70}\n")

    results = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    if not results:
        print("❌ File is empty")
        return None

    # Basic stats
    print(f"Total evaluations completed: {len(results)}")

    # Variant distribution
    variant_counts = Counter(r['variant_type'] for r in results)
    print(f"\nVariant distribution:")
    for variant, count in sorted(variant_counts.items()):
        print(f"  {variant}: {count}")

    # Base paper count
    base_paper_ids = set(r.get('base_paper_id', r.get('paper_id')) for r in results)
    print(f"\nUnique base papers evaluated: {len(base_paper_ids)}")

    # Time span
    timestamps = [r['evaluation_timestamp'] for r in results]
    print(f"\nFirst evaluation: {timestamps[0]}")
    print(f"Last evaluation: {timestamps[-1]}")

    # Rating stats
    ratings = [r['evaluation']['avg_rating'] for r in results]
    print(f"\nRating statistics:")
    print(f"  Mean: {sum(ratings)/len(ratings):.2f}")
    print(f"  Min: {min(ratings):.2f}")
    print(f"  Max: {max(ratings):.2f}")

    # Decision distribution
    decision_counts = Counter(r['evaluation']['paper_decision'] for r in results)
    print(f"\nDecision distribution:")
    for decision, count in decision_counts.items():
        print(f"  {decision}: {count}")

    return results


def convert_to_final_format(incremental_file: Path):
    """Convert incremental file to final format"""
    results = []
    with open(incremental_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    if not results:
        print("❌ No results to convert")
        return

    # Generate final file name
    timestamp = incremental_file.stem.replace('evaluation_results_', '').replace('_incremental', '')
    final_file = incremental_file.parent / f'evaluation_results_{timestamp}.jsonl'

    print(f"\n{'='*70}")
    print(f"Converting to final format...")
    print(f"{'='*70}\n")
    print(f"Output: {final_file}")

    # Save as final format (same as incremental, just without _incremental suffix)
    with open(final_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(f"\n✓ Converted {len(results)} results to: {final_file}")

    # Create summary
    create_summary(results, final_file.parent, timestamp)


def create_summary(results, output_dir, timestamp):
    """Create summary file"""
    from collections import Counter
    import statistics

    summary = {
        'total_papers': len(results),
        'timestamp': timestamp,
        'variant_distribution': dict(Counter(r['variant_type'] for r in results)),
        'decision_distribution': dict(Counter(r['evaluation']['paper_decision'] for r in results)),
        'rating_statistics': {}
    }

    ratings = [r['evaluation']['avg_rating'] for r in results]
    if ratings:
        summary['rating_statistics'] = {
            'mean': statistics.mean(ratings),
            'median': statistics.median(ratings),
            'min': min(ratings),
            'max': max(ratings),
            'std': statistics.stdev(ratings) if len(ratings) > 1 else 0
        }

    summary_file = output_dir / f'evaluation_summary_{timestamp}.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"✓ Created summary: {summary_file}")


def main():
    print("="*70)
    print("RESUME/ANALYZE EVALUATION RESULTS")
    print("="*70)

    # Find latest incremental file
    incremental_file = find_latest_incremental_file()

    if not incremental_file:
        print("\n❌ No incremental files found in evaluation_results/")
        print("   Make sure evaluation has started and created at least one result.")
        return

    # Analyze results
    results = analyze_incremental_results(incremental_file)

    if not results:
        return

    # Ask user what to do
    print(f"\n{'='*70}")
    print("What would you like to do?")
    print("="*70)
    print("1. Just view the analysis (default)")
    print("2. Convert to final format (creates final .jsonl and summary)")
    print("3. Both (analyze + convert)")

    choice = input("\nChoice [1/2/3]: ").strip()

    if choice == "2" or choice == "3":
        convert_to_final_format(incremental_file)
        print(f"\n✓ Done! You can now run analyze_evaluation_results.py")
    else:
        print(f"\n✓ Analysis complete. Incremental file preserved at:")
        print(f"  {incremental_file}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Completed evaluations: {len(results)}")
    print(f"Incremental file: {incremental_file.name}")
    print("="*70)


if __name__ == "__main__":
    main()

