"""
Analysis Script for Paper Evaluation Results
Performs comprehensive statistical analysis and visualization of evaluation results
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
import scipy.stats as stats


# ========== Configuration ==========
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation_results"
OUTPUT_DIR = PROJECT_ROOT / "analysis_output"
RATING_BINS = [0, 3, 5, 7, 10]  # Rating ranges: Poor, Fair, Good, Excellent
RATING_LABELS = ['Poor (0-3)', 'Fair (3-5)', 'Good (5-7)', 'Excellent (7-10)']


def load_latest_results(results_dir: Path) -> pd.DataFrame:
    """Load the most recent evaluation results"""
    results_path = Path(results_dir)

    # Find latest results file
    result_files = list(results_path.glob('evaluation_results_*.jsonl'))
    if not result_files:
        raise FileNotFoundError(f"No evaluation results found in {results_dir}")

    latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
    print(f"[INFO] Loading results from: {latest_file}")

    # Load data
    data = []
    with open(latest_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                # Flatten evaluation dict for easier analysis
                flat_record = {
                    'paper_id': record['paper_id'],
                    'title': record['title'],
                    'variant_type': record['variant_type'],
                    'dataset_split': record['dataset_split'],
                    'text_length': record['text_length'],
                    'avg_rating': record['evaluation']['avg_rating'],
                    'paper_decision': record['evaluation']['paper_decision'],
                    'confidence': record['evaluation']['confidence'],
                    'originality': record['evaluation']['originality'],
                    'quality': record['evaluation']['quality'],
                    'clarity': record['evaluation']['clarity'],
                    'significance': record['evaluation']['significance'],
                    'num_strengths': len(record['evaluation']['strength']),
                    'num_weaknesses': len(record['evaluation']['weaknesses']),
                    'meta_review_length': len(record['evaluation']['meta_review'])
                }
                data.append(flat_record)

    df = pd.DataFrame(data)
    print(f"[INFO] Loaded {len(df)} evaluation records")

    return df


def create_output_dir(output_dir: Path) -> Path:
    """Create output directory with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = Path(output_dir) / timestamp
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def fix_confidence_column(df):
    """Fix confidence column to ensure it's a float and robust to bad data"""
    def to_float(x):
        if isinstance(x, list):
            # 只处理全为数字的 list
            numeric = []
            for i in x:
                if isinstance(i, (int, float)):
                    numeric.append(float(i))
                elif isinstance(i, str):
                    try:
                        numeric.append(float(i))
                    except Exception:
                        continue
            return float(np.mean(numeric)) if numeric else np.nan
        if isinstance(x, (int, float)):
            return float(x)
        if isinstance(x, str):
            try:
                return float(x)
            except Exception:
                return np.nan
        return np.nan
    df['confidence'] = df['confidence'].apply(to_float)
    return df


def analyze_overall_statistics(df: pd.DataFrame, output_path: Path):
    """Generate overall statistics"""
    print("\n" + "="*70)
    print("OVERALL STATISTICS")
    print("="*70)

    df = fix_confidence_column(df)

    stats_dict = {
        'total_papers': len(df),
        'rating_statistics': {
            'mean': df['avg_rating'].mean(),
            'median': df['avg_rating'].median(),
            'std': df['avg_rating'].std(),
            'min': df['avg_rating'].min(),
            'max': df['avg_rating'].max(),
            'q25': df['avg_rating'].quantile(0.25),
            'q75': df['avg_rating'].quantile(0.75)
        },
        # 移除aspect_ratings
        'decision_distribution': df['paper_decision'].value_counts().to_dict(),
        'variant_distribution': df['variant_type'].value_counts().to_dict(),
        'confidence_mean': df['confidence'].mean()
    }

    # Print statistics
    print(f"\nTotal Papers: {stats_dict['total_papers']}")
    print(f"\nRating Statistics:")
    for key, value in stats_dict['rating_statistics'].items():
        print(f"  {key.capitalize()}: {value:.2f}")

    # 移除Aspect Ratings (Average)

    print(f"\nDecision Distribution:")
    for decision, count in stats_dict['decision_distribution'].items():
        pct = (count / stats_dict['total_papers']) * 100
        print(f"  {decision}: {count} ({pct:.1f}%)")

    # Save to JSON
    stats_file = output_path / 'overall_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats_dict, f, indent=2, ensure_ascii=False)
    print(f"\n[INFO] Saved statistics to {stats_file}")

    return stats_dict


def analyze_by_variant(df: pd.DataFrame, output_path: Path):
    """Analyze results grouped by variant type"""
    print("\n" + "="*70)
    print("ANALYSIS BY VARIANT TYPE")
    print("="*70)

    variant_stats = []

    for variant in df['variant_type'].unique():
        variant_df = df[df['variant_type'] == variant]

        stats = {
            'variant_type': variant,
            'count': len(variant_df),
            'avg_rating_mean': variant_df['avg_rating'].mean(),
            'avg_rating_std': variant_df['avg_rating'].std(),
            # 移除originality, quality, clarity, significance
            'accept_rate': (variant_df['paper_decision'].str.contains('Accept', case=False).sum() / len(variant_df) * 100),
            'reject_rate': (variant_df['paper_decision'].str.contains('Reject', case=False).sum() / len(variant_df) * 100)
        }

        variant_stats.append(stats)

        print(f"\n{variant}:")
        print(f"  Count: {stats['count']}")
        print(f"  Avg Rating: {stats['avg_rating_mean']:.2f} ± {stats['avg_rating_std']:.2f}")
        print(f"  Accept Rate: {stats['accept_rate']:.1f}%")

    # Create DataFrame and save
    variant_df_stats = pd.DataFrame(variant_stats)
    variant_df_stats = variant_df_stats.sort_values('avg_rating_mean', ascending=False)

    csv_file = output_path / 'variant_statistics.csv'
    variant_df_stats.to_csv(csv_file, index=False)
    print(f"\n[INFO] Saved variant statistics to {csv_file}")

    return variant_df_stats


def analyze_by_rating_range(df: pd.DataFrame, output_path: Path):
    """Analyze papers grouped by rating ranges"""
    print("\n" + "="*70)
    print("ANALYSIS BY RATING RANGE")
    print("="*70)

    # Create rating bins
    df['rating_bin'] = pd.cut(df['avg_rating'], bins=RATING_BINS, labels=RATING_LABELS, include_lowest=True)

    rating_stats = []

    for rating_label in RATING_LABELS:
        rating_df = df[df['rating_bin'] == rating_label]

        if len(rating_df) == 0:
            continue

        # Count variants in this rating range
        variant_dist = rating_df['variant_type'].value_counts().to_dict()

        stats = {
            'rating_range': rating_label,
            'count': len(rating_df),
            'percentage': (len(rating_df) / len(df)) * 100,
            # 移除avg_originality, avg_quality, avg_clarity, avg_significance
            'top_variant': max(variant_dist.items(), key=lambda x: x[1])[0] if variant_dist else 'N/A',
            'variant_distribution': variant_dist
        }

        rating_stats.append(stats)

        print(f"\n{rating_label}:")
        print(f"  Count: {stats['count']} ({stats['percentage']:.1f}%)")
        print(f"  Top Variant: {stats['top_variant']}")

    # Save
    stats_file = output_path / 'rating_range_statistics.json'
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(rating_stats, f, indent=2, ensure_ascii=False)
    print(f"\n[INFO] Saved rating range statistics to {stats_file}")

    return rating_stats


def compare_original_vs_variants(df: pd.DataFrame, output_path: Path):
    """Compare original papers vs all variants"""
    print("\n" + "="*70)
    print("ORIGINAL VS VARIANTS COMPARISON")
    print("="*70)

    original_df = df[df['variant_type'] == 'original']
    variants_df = df[df['variant_type'] != 'original']

    comparison = {
        'original': {
            'count': len(original_df),
            'avg_rating': original_df['avg_rating'].mean(),
            'rating_std': original_df['avg_rating'].std(),
            'accept_rate': (original_df['paper_decision'].str.contains('Accept', case=False).sum() / len(original_df) * 100) if len(original_df) > 0 else 0,
        },
        'variants': {
            'count': len(variants_df),
            'avg_rating': variants_df['avg_rating'].mean() if len(variants_df) > 0 else 0,
            'rating_std': variants_df['avg_rating'].std() if len(variants_df) > 0 else 0,
            'accept_rate': (variants_df['paper_decision'].str.contains('Accept', case=False).sum() / len(variants_df) * 100) if len(variants_df) > 0 else 0,
        }
    }

    # Statistical test
    if len(original_df) > 0 and len(variants_df) > 0:
        t_stat, p_value = stats.ttest_ind(original_df['avg_rating'], variants_df['avg_rating'])
        # 转换numpy.bool_为Python bool
        significant = bool(p_value < 0.05)
        comparison['statistical_test'] = {
            't_statistic': float(t_stat),
            'p_value': float(p_value),
            'significant': significant
        }

    # Print
    print(f"\nOriginal Papers (n={comparison['original']['count']}):")
    print(f"  Avg Rating: {comparison['original']['avg_rating']:.2f} ± {comparison['original']['rating_std']:.2f}")
    print(f"  Accept Rate: {comparison['original']['accept_rate']:.1f}%")

    print(f"\nVariant Papers (n={comparison['variants']['count']}):")
    print(f"  Avg Rating: {comparison['variants']['avg_rating']:.2f} ± {comparison['variants']['rating_std']:.2f}")
    print(f"  Accept Rate: {comparison['variants']['accept_rate']:.1f}%")

    if 'statistical_test' in comparison:
        print(f"\nT-test: t={comparison['statistical_test']['t_statistic']:.3f}, p={comparison['statistical_test']['p_value']:.4f}")
        print(f"Significant difference: {'Yes' if comparison['statistical_test']['significant'] else 'No'}")

    # Save
    comp_file = output_path / 'original_vs_variants.json'
    with open(comp_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    print(f"\n[INFO] Saved comparison to {comp_file}")

    return comparison


def create_visualizations(df: pd.DataFrame, output_path: Path):
    """Create visualization plots"""
    print("\n" + "="*70)
    print("GENERATING VISUALIZATIONS")
    print("="*70)

    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)

    # 1. Rating distribution histogram
    plt.figure(figsize=(10, 6))
    plt.hist(df['avg_rating'], bins=20, edgecolor='black', alpha=0.7)
    plt.xlabel('Average Rating', fontsize=12)
    plt.ylabel('Number of Papers', fontsize=12)
    plt.title('Distribution of Paper Ratings', fontsize=14, fontweight='bold')
    plt.axvline(df['avg_rating'].mean(), color='red', linestyle='--', label=f'Mean: {df["avg_rating"].mean():.2f}')
    plt.axvline(df['avg_rating'].median(), color='green', linestyle='--', label=f'Median: {df["avg_rating"].median():.2f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path / 'rating_distribution.png', dpi=300)
    print(f"[INFO] Saved rating_distribution.png")
    plt.close()

    # 2. Ratings by variant type (box plot)
    plt.figure(figsize=(14, 8))
    variant_order = df.groupby('variant_type')['avg_rating'].mean().sort_values(ascending=False).index
    sns.boxplot(data=df, x='variant_type', y='avg_rating', order=variant_order)
    plt.xlabel('Variant Type', fontsize=12)
    plt.ylabel('Average Rating', fontsize=12)
    plt.title('Rating Distribution by Variant Type', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path / 'ratings_by_variant_boxplot.png', dpi=300)
    print(f"[INFO] Saved ratings_by_variant_boxplot.png")
    plt.close()

    # 3. Decision distribution pie chart
    plt.figure(figsize=(10, 10))
    decision_counts = df['paper_decision'].value_counts()
    plt.pie(decision_counts.values, labels=decision_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Paper Decision Distribution', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path / 'decision_distribution.png', dpi=300)
    print(f"[INFO] Saved decision_distribution.png")
    plt.close()

    # 4. Aspect ratings comparison (radar chart-like)
    aspects = ['originality', 'quality', 'clarity', 'significance']
    aspect_means = [df[aspect].mean() for aspect in aspects]

    plt.figure(figsize=(10, 6))
    plt.bar(aspects, aspect_means, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
    plt.xlabel('Aspect', fontsize=12)
    plt.ylabel('Average Score', fontsize=12)
    plt.title('Average Scores by Evaluation Aspect', fontsize=14, fontweight='bold')
    plt.ylim(0, 10)
    for i, v in enumerate(aspect_means):
        plt.text(i, v + 0.2, f'{v:.2f}', ha='center', fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path / 'aspect_ratings.png', dpi=300)
    print(f"[INFO] Saved aspect_ratings.png")
    plt.close()

    # 5. Heatmap: Variant vs Decision
    variant_decision = pd.crosstab(df['variant_type'], df['paper_decision'])
    plt.figure(figsize=(12, 8))
    sns.heatmap(variant_decision, annot=True, fmt='d', cmap='YlOrRd')
    plt.title('Variant Type vs Decision Heatmap', fontsize=14, fontweight='bold')
    plt.xlabel('Decision', fontsize=12)
    plt.ylabel('Variant Type', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path / 'variant_decision_heatmap.png', dpi=300)
    print(f"[INFO] Saved variant_decision_heatmap.png")
    plt.close()

    # 6. Correlation heatmap of aspect ratings
    aspect_cols = ['avg_rating', 'originality', 'quality', 'clarity', 'significance', 'confidence']
    corr_matrix = df[aspect_cols].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('Correlation Matrix of Evaluation Aspects', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path / 'correlation_heatmap.png', dpi=300)
    print(f"[INFO] Saved correlation_heatmap.png")
    plt.close()

    # 7. Rating by variant (violin plot)
    plt.figure(figsize=(14, 8))
    sns.violinplot(data=df, x='variant_type', y='avg_rating', order=variant_order)
    plt.xlabel('Variant Type', fontsize=12)
    plt.ylabel('Average Rating', fontsize=12)
    plt.title('Rating Distribution by Variant Type (Violin Plot)', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path / 'ratings_by_variant_violin.png', dpi=300)
    print(f"[INFO] Saved ratings_by_variant_violin.png")
    plt.close()

    # 8. Text length vs rating scatter
    plt.figure(figsize=(10, 6))
    plt.scatter(df['text_length'], df['avg_rating'], alpha=0.5)
    plt.xlabel('Text Length (characters)', fontsize=12)
    plt.ylabel('Average Rating', fontsize=12)
    plt.title('Text Length vs Average Rating', fontsize=14, fontweight='bold')

    # Add trend line
    z = np.polyfit(df['text_length'], df['avg_rating'], 1)
    p = np.poly1d(z)
    plt.plot(df['text_length'], p(df['text_length']), "r--", alpha=0.8, label=f'Trend: y={z[0]:.2e}x+{z[1]:.2f}')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path / 'text_length_vs_rating.png', dpi=300)
    print(f"[INFO] Saved text_length_vs_rating.png")
    plt.close()

    print(f"\n[INFO] All visualizations saved to {output_path}")


def generate_detailed_report(df: pd.DataFrame, output_path: Path,
                            overall_stats: dict, variant_stats: pd.DataFrame):
    """Generate a detailed text report"""
    report_file = output_path / 'analysis_report.txt'

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("PAPER EVALUATION ANALYSIS REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")

        # Overall statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-"*70 + "\n")
        f.write(f"Total Papers Evaluated: {overall_stats['total_papers']}\n\n")

        f.write("Rating Statistics:\n")
        for key, value in overall_stats['rating_statistics'].items():
            f.write(f"  {key.capitalize()}: {value:.2f}\n")

        # 移除Aspect Ratings (Average)

        f.write("\nDecision Distribution:\n")
        for decision, count in overall_stats['decision_distribution'].items():
            pct = (count / overall_stats['total_papers']) * 100
            f.write(f"  {decision}: {count} ({pct:.1f}%)\n")

        # Variant analysis
        f.write("\n\n" + "="*70 + "\n")
        f.write("VARIANT TYPE ANALYSIS\n")
        f.write("="*70 + "\n\n")

        for _, row in variant_stats.iterrows():
            f.write(f"{row['variant_type']}:\n")
            f.write(f"  Count: {row['count']}\n")
            f.write(f"  Average Rating: {row['avg_rating_mean']:.2f} ± {row['avg_rating_std']:.2f}\n")
            f.write(f"  Accept Rate: {row['accept_rate']:.1f}%\n")
            f.write(f"  Reject Rate: {row['reject_rate']:.1f}%\n\n")

        # Top and bottom rated papers
        f.write("\n" + "="*70 + "\n")
        f.write("TOP 10 RATED PAPERS\n")
        f.write("="*70 + "\n\n")

        top_papers = df.nlargest(10, 'avg_rating')
        for i, (_, paper) in enumerate(top_papers.iterrows(), 1):
            f.write(f"{i}. {paper['title'][:60]}...\n")
            f.write(f"   Variant: {paper['variant_type']}, Rating: {paper['avg_rating']:.2f}\n\n")

        f.write("\n" + "="*70 + "\n")
        f.write("BOTTOM 10 RATED PAPERS\n")
        f.write("="*70 + "\n\n")

        bottom_papers = df.nsmallest(10, 'avg_rating')
        for i, (_, paper) in enumerate(bottom_papers.iterrows(), 1):
            f.write(f"{i}. {paper['title'][:60]}...\n")
            f.write(f"   Variant: {paper['variant_type']}, Rating: {paper['avg_rating']:.2f}\n\n")

    print(f"\n[INFO] Saved detailed report to {report_file}")


def main():
    print("="*70)
    print("Paper Evaluation Analysis Script")
    print("="*70)

    # Load data
    print("\n[INFO] Loading evaluation results...")
    df = load_latest_results(RESULTS_DIR)

    # Create output directory
    output_path = create_output_dir(OUTPUT_DIR)
    print(f"[INFO] Output directory: {output_path}")

    # Run analyses
    overall_stats = analyze_overall_statistics(df, output_path)
    variant_stats = analyze_by_variant(df, output_path)
    rating_stats = analyze_by_rating_range(df, output_path)
    comparison = compare_original_vs_variants(df, output_path)

    # Create visualizations
    create_visualizations(df, output_path)

    # Generate report
    generate_detailed_report(df, output_path, overall_stats, variant_stats)

    # Save processed DataFrame
    csv_output = output_path / 'processed_data.csv'
    df.to_csv(csv_output, index=False)
    print(f"\n[INFO] Saved processed data to {csv_output}")

    print("\n" + "="*70)
    print("Analysis Complete!")
    print("="*70)
    print(f"All results saved to: {output_path}")
    print("="*70)


if __name__ == "__main__":
    main()

