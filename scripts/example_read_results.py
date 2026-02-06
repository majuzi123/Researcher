"""
Quick example: How to read and analyze evaluation results
快速示例：如何读取和分析评估结果
"""

import json
from pathlib import Path
from collections import Counter

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation_results"


def example_1_read_jsonl():
    """示例 1: 读取 JSONL 文件"""
    print("\n" + "="*70)
    print("示例 1: 读取 JSONL 评估结果")
    print("="*70)

    # 找到最新的结果文件
    result_files = list(RESULTS_DIR.glob("evaluation_results_*.jsonl"))
    if not result_files:
        print("❌ 没有找到结果文件")
        return None

    latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
    print(f"\n读取文件: {latest_file.name}")

    # 读取所有记录
    results = []
    with open(latest_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))

    print(f"总记录数: {len(results)}")

    # 显示第一条记录
    if results:
        print(f"\n第一条记录:")
        first = results[0]
        print(f"  Paper ID: {first['paper_id']}")
        print(f"  标题: {first['title'][:60]}...")
        print(f"  变体类型: {first['variant_type']}")
        print(f"  平均评分: {first['evaluation']['avg_rating']}")
        print(f"  决策: {first['evaluation']['paper_decision']}")
        print(f"  文本长度: {first['text_length']} 字符")

    return results


def example_2_statistics(results):
    """示例 2: 计算基础统计"""
    if not results:
        return

    print("\n" + "="*70)
    print("示例 2: 基础统计")
    print("="*70)

    # 变体分布
    variant_counts = Counter(r['variant_type'] for r in results)
    print(f"\n变体分布:")
    for variant, count in sorted(variant_counts.items()):
        print(f"  {variant}: {count}")

    # 决策分布
    decision_counts = Counter(r['evaluation']['paper_decision'] for r in results)
    print(f"\n决策分布:")
    for decision, count in decision_counts.items():
        pct = (count / len(results)) * 100
        print(f"  {decision}: {count} ({pct:.1f}%)")

    # 评分统计
    ratings = [r['evaluation']['avg_rating'] for r in results]
    print(f"\n评分统计:")
    print(f"  平均分: {sum(ratings)/len(ratings):.2f}")
    print(f"  最低分: {min(ratings):.2f}")
    print(f"  最高分: {max(ratings):.2f}")

    # 各维度平均分
    print(f"\n各维度平均分:")
    for dimension in ['originality', 'quality', 'clarity', 'significance']:
        scores = [r['evaluation'][dimension] for r in results]
        avg = sum(scores) / len(scores)
        print(f"  {dimension.capitalize()}: {avg:.2f}")


def example_3_variant_comparison(results):
    """示例 3: 比较不同变体的表现"""
    if not results:
        return

    print("\n" + "="*70)
    print("示例 3: 变体对比分析")
    print("="*70)

    # 按变体分组
    variants = {}
    for r in results:
        vtype = r['variant_type']
        if vtype not in variants:
            variants[vtype] = []
        variants[vtype].append(r)

    # 对比每个变体
    print(f"\n{'变体':<20} {'数量':<8} {'平均分':<10} {'接受率':<10}")
    print("-" * 60)

    for vtype in sorted(variants.keys()):
        records = variants[vtype]
        avg_rating = sum(r['evaluation']['avg_rating'] for r in records) / len(records)
        accept_count = sum(1 for r in records if 'accept' in r['evaluation']['paper_decision'].lower())
        accept_rate = (accept_count / len(records)) * 100

        print(f"{vtype:<20} {len(records):<8} {avg_rating:<10.2f} {accept_rate:<10.1f}%")


def example_4_top_papers(results):
    """示例 4: 找出评分最高和最低的论文"""
    if not results:
        return

    print("\n" + "="*70)
    print("示例 4: 极端案例分析")
    print("="*70)

    # 按评分排序
    sorted_results = sorted(results, key=lambda r: r['evaluation']['avg_rating'], reverse=True)

    # 最高分
    print(f"\n评分最高的 5 篇论文:")
    for i, r in enumerate(sorted_results[:5], 1):
        print(f"\n{i}. {r['title'][:60]}...")
        print(f"   变体: {r['variant_type']}")
        print(f"   评分: {r['evaluation']['avg_rating']:.2f}")
        print(f"   决策: {r['evaluation']['paper_decision']}")

    # 最低分
    print(f"\n评分最低的 5 篇论文:")
    for i, r in enumerate(sorted_results[-5:], 1):
        print(f"\n{i}. {r['title'][:60]}...")
        print(f"   变体: {r['variant_type']}")
        print(f"   评分: {r['evaluation']['avg_rating']:.2f}")
        print(f"   决策: {r['evaluation']['paper_decision']}")


def example_5_original_vs_variants(results):
    """示例 5: 原始论文 vs 变体的对比"""
    if not results:
        return

    print("\n" + "="*70)
    print("示例 5: 原始论文 vs 变体对比")
    print("="*70)

    # 分离原始和变体
    original = [r for r in results if r['variant_type'] == 'original']
    variants = [r for r in results if r['variant_type'] != 'original']

    if not original or not variants:
        print("❌ 没有足够的数据进行对比")
        return

    # 统计对比
    print(f"\n原始论文 (n={len(original)}):")
    orig_avg = sum(r['evaluation']['avg_rating'] for r in original) / len(original)
    orig_accept = sum(1 for r in original if 'accept' in r['evaluation']['paper_decision'].lower())
    orig_accept_rate = (orig_accept / len(original)) * 100
    print(f"  平均评分: {orig_avg:.2f}")
    print(f"  接受率: {orig_accept_rate:.1f}% ({orig_accept}/{len(original)})")

    print(f"\n变体论文 (n={len(variants)}):")
    var_avg = sum(r['evaluation']['avg_rating'] for r in variants) / len(variants)
    var_accept = sum(1 for r in variants if 'accept' in r['evaluation']['paper_decision'].lower())
    var_accept_rate = (var_accept / len(variants)) * 100
    print(f"  平均评分: {var_avg:.2f}")
    print(f"  接受率: {var_accept_rate:.1f}% ({var_accept}/{len(variants)})")

    print(f"\n差异:")
    print(f"  评分差: {orig_avg - var_avg:+.2f}")
    print(f"  接受率差: {orig_accept_rate - var_accept_rate:+.1f}%")


def example_6_export_to_csv(results):
    """示例 6: 导出为 CSV 格式"""
    if not results:
        return

    print("\n" + "="*70)
    print("示例 6: 导出为 CSV")
    print("="*70)

    import csv

    output_file = RESULTS_DIR / "evaluation_results_export.csv"

    # 准备 CSV 数据
    fieldnames = [
        'paper_id', 'base_paper_id', 'title', 'variant_type', 'dataset_split',
        'avg_rating', 'paper_decision', 'confidence',
        'originality', 'quality', 'clarity', 'significance',
        'text_length', 'evaluation_timestamp'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for r in results:
            row = {
                'paper_id': r['paper_id'],
                'base_paper_id': r.get('base_paper_id', ''),
                'title': r['title'],
                'variant_type': r['variant_type'],
                'dataset_split': r.get('dataset_split', ''),
                'avg_rating': r['evaluation']['avg_rating'],
                'paper_decision': r['evaluation']['paper_decision'],
                'confidence': r['evaluation']['confidence'],
                'originality': r['evaluation']['originality'],
                'quality': r['evaluation']['quality'],
                'clarity': r['evaluation']['clarity'],
                'significance': r['evaluation']['significance'],
                'text_length': r['text_length'],
                'evaluation_timestamp': r['evaluation_timestamp']
            }
            writer.writerow(row)

    print(f"\n✓ 已导出 {len(results)} 条记录到: {output_file}")
    print(f"  可以用 Excel 或其他工具打开查看")


def main():
    print("="*70)
    print("评估结果读取与分析示例")
    print("="*70)

    # 运行所有示例
    results = example_1_read_jsonl()

    if results:
        example_2_statistics(results)
        example_3_variant_comparison(results)
        example_4_top_papers(results)
        example_5_original_vs_variants(results)
        example_6_export_to_csv(results)
    else:
        print("\n❌ 没有找到评估结果文件")
        print("   请先运行: python scripts/batch_evaluate_papers.py")

    print("\n" + "="*70)
    print("示例完成！")
    print("="*70)


if __name__ == "__main__":
    main()

