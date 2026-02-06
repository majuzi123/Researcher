"""
Dataset Visualization and Analysis Script
Analyzes the generated paper variant dataset and creates various visualizations
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from collections import Counter, defaultdict
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

# File paths (relative to project root)
PROJECT_ROOT = Path(__file__).parent.parent
TRAIN_FILE = PROJECT_ROOT / "util/train_with_variants.jsonl"
TEST_FILE = PROJECT_ROOT / "util/test_with_variants.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "analysis_output"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_dataset(file_path: Path):
    """Load dataset from JSONL file"""
    data = []
    if not file_path.exists():
        print(f"[WARN] File does not exist: {file_path}")
        return data

    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to parse line: {e}")

    return data


def plot_variant_distribution(data, output_path):
    """Plot variant type distribution"""
    variant_counts = Counter(item["variant_type"] for item in data)

    plt.figure(figsize=(10, 6))
    plt.bar(variant_counts.keys(), variant_counts.values(), color='skyblue', edgecolor='black')
    plt.xlabel('Variant Type', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.title('Variant Type Distribution', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path / 'variant_distribution.png', dpi=300)
    plt.close()
    print(f"[INFO] Saved: variant_distribution.png")


def plot_text_length_comparison(data, output_path):
    """Plot text length comparison across variants"""
    df_data = []
    for item in data:
        df_data.append({
            'variant_type': item['variant_type'],
            'text_length': len(item['text'])
        })

    df = pd.DataFrame(df_data)

    plt.figure(figsize=(14, 6))
    sns.boxplot(data=df, x='variant_type', y='text_length', palette='Set2')
    plt.xlabel('Variant Type', fontsize=12)
    plt.ylabel('Text Length (characters)', fontsize=12)
    plt.title('Text Length Distribution by Variant Type', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path / 'text_length_distribution.png', dpi=300)
    plt.close()
    print(f"[INFO] Saved: text_length_distribution.png")


def plot_text_reduction(data, output_path):
    """Plot text reduction percentage by variant"""
    # Group by original paper
    papers = defaultdict(dict)
    for item in data:
        original_id = item.get('original_id') or item.get('original_path')
        papers[original_id][item['variant_type']] = len(item['text'])

    # Calculate reduction
    reductions = defaultdict(list)
    for paper_id, variants in papers.items():
        original_len = variants.get('original', 1)
        if original_len == 0:
            continue
        for variant_type, length in variants.items():
            if variant_type != 'original':
                reduction_pct = (1 - length / original_len) * 100
                reductions[variant_type].append(reduction_pct)

    # Plot
    avg_reductions = {k: sum(v) / len(v) for k, v in reductions.items()}

    plt.figure(figsize=(10, 6))
    variant_types = sorted(avg_reductions.keys())
    values = [avg_reductions[k] for k in variant_types]

    bars = plt.bar(variant_types, values, color='coral', edgecolor='black')
    plt.xlabel('Variant Type', fontsize=12)
    plt.ylabel('Average Text Reduction (%)', fontsize=12)
    plt.title('Average Text Reduction by Variant Type', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)

    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path / 'text_reduction.png', dpi=300)
    plt.close()
    print(f"[INFO] Saved: text_reduction.png")


def plot_decision_distribution(data, output_path):
    """Plot decision distribution by variant type"""
    df_data = []
    for item in data:
        decision = item.get('decision', 'unknown')
        df_data.append({
            'variant_type': item['variant_type'],
            'decision': decision if decision else 'unknown'
        })

    df = pd.DataFrame(df_data)

    # Create pivot table
    pivot = df.pivot_table(index='decision', columns='variant_type', aggfunc='size', fill_value=0)

    plt.figure(figsize=(14, 6))
    sns.heatmap(pivot, annot=True, fmt='d', cmap='YlOrRd', cbar_kws={'label': 'Count'})
    plt.xlabel('Variant Type', fontsize=12)
    plt.ylabel('Decision', fontsize=12)
    plt.title('Decision vs Variant Type Heatmap', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path / 'decision_variant_heatmap.png', dpi=300)
    plt.close()
    print(f"[INFO] Saved: decision_variant_heatmap.png")


def plot_rating_distribution(data, output_path):
    """Plot rating score distribution"""
    ratings = []
    for item in data:
        if item.get('rates'):
            ratings.extend(item['rates'])

    if not ratings:
        print("[WARN] No rating data available")
        return

    plt.figure(figsize=(10, 6))
    plt.hist(ratings, bins=range(1, 12), color='lightgreen', edgecolor='black', alpha=0.7)
    plt.xlabel('Rating Score', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.title('Rating Score Distribution', fontsize=14, fontweight='bold')
    plt.xticks(range(1, 11))
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path / 'rating_distribution.png', dpi=300)
    plt.close()
    print(f"[INFO] Saved: rating_distribution.png")


def generate_statistics_report(data, output_path):
    """Generate detailed statistics report"""
    report = []
    report.append("=" * 60)
    report.append("DATASET STATISTICS REPORT")
    report.append("=" * 60)
    report.append("")

    # Basic statistics
    report.append(f"Total records: {len(data)}")

    # Unique papers
    unique_papers = set(item.get('original_id') or item.get('original_path') for item in data)
    report.append(f"Unique papers: {len(unique_papers)}")

    # Variant counts
    variant_counts = Counter(item['variant_type'] for item in data)
    report.append(f"\nVariant type counts:")
    for variant, count in sorted(variant_counts.items()):
        report.append(f"  - {variant}: {count}")

    # Decision counts
    decision_counts = Counter(item.get('decision', 'unknown') for item in data)
    report.append(f"\nDecision counts:")
    for decision, count in sorted(decision_counts.items()):
        report.append(f"  - {decision}: {count}")

    # Text length statistics
    text_lengths = [len(item['text']) for item in data]
    report.append(f"\nText length statistics:")
    report.append(f"  - Mean: {sum(text_lengths) / len(text_lengths):.2f} chars")
    report.append(f"  - Min: {min(text_lengths)} chars")
    report.append(f"  - Max: {max(text_lengths)} chars")

    # Rating statistics
    all_ratings = []
    for item in data:
        if item.get('rates'):
            all_ratings.extend(item['rates'])

    if all_ratings:
        report.append(f"\nRating statistics:")
        report.append(f"  - Total ratings: {len(all_ratings)}")
        report.append(f"  - Mean rating: {sum(all_ratings) / len(all_ratings):.2f}")
        report.append(f"  - Min rating: {min(all_ratings)}")
        report.append(f"  - Max rating: {max(all_ratings)}")

    # Check data completeness
    report.append(f"\nData completeness check:")
    papers_variants = defaultdict(set)
    for item in data:
        original_id = item.get('original_id') or item.get('original_path')
        papers_variants[original_id].add(item['variant_type'])

    expected_variants = {
        'original', 'no_abstract', 'no_conclusion', 'no_introduction',
        'no_references', 'no_experiments', 'no_methods', 'no_formulas', 'no_figures'
    }

    complete_papers = sum(1 for variants in papers_variants.values() if variants == expected_variants)
    report.append(f"  - Complete papers (all 9 variants): {complete_papers}/{len(papers_variants)}")

    incomplete = [(pid, expected_variants - variants)
                  for pid, variants in papers_variants.items()
                  if variants != expected_variants]

    if incomplete:
        report.append(f"  - Incomplete papers: {len(incomplete)}")
        for pid, missing in incomplete[:5]:
            report.append(f"    * {pid}: missing {missing}")

    report.append("")
    report.append("=" * 60)

    # Save report
    report_text = "\n".join(report)
    with open(output_path / 'statistics_report.txt', 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(report_text)
    print(f"\n[INFO] Saved: statistics_report.txt")


def main():
    """Main analysis function"""
    print("[INFO] Starting dataset analysis...")

    # Load data
    print("\n[INFO] Loading datasets...")
    train_data = load_dataset(TRAIN_FILE)
    test_data = load_dataset(TEST_FILE)

    if not train_data and not test_data:
        print("[ERROR] No data loaded. Please check file paths.")
        return

    # Analyze train set
    if train_data:
        print(f"\n[INFO] Analyzing training set ({len(train_data)} records)...")
        train_output = OUTPUT_DIR / "train"
        train_output.mkdir(exist_ok=True)

        plot_variant_distribution(train_data, train_output)
        plot_text_length_comparison(train_data, train_output)
        plot_text_reduction(train_data, train_output)
        plot_decision_distribution(train_data, train_output)
        plot_rating_distribution(train_data, train_output)
        generate_statistics_report(train_data, train_output)

    # Analyze test set
    if test_data:
        print(f"\n[INFO] Analyzing test set ({len(test_data)} records)...")
        test_output = OUTPUT_DIR / "test"
        test_output.mkdir(exist_ok=True)

        plot_variant_distribution(test_data, test_output)
        plot_text_length_comparison(test_data, test_output)
        plot_text_reduction(test_data, test_output)
        plot_decision_distribution(test_data, test_output)
        plot_rating_distribution(test_data, test_output)
        generate_statistics_report(test_data, test_output)

    print(f"\n[INFO] Analysis complete! Results saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

