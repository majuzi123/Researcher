"""
示例脚本：如何查询和使用评估结果数据

演示：
1. 加载评估结果
2. 查询特定论文的所有变体
3. 比较各变体的性能
4. 生成简单的对比报告
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

# 配置
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "evaluation_results"


def load_evaluation_results(results_file=None):
    """加载评估结果"""
    if results_file is None:
        # 找到最新的结果文件
        result_files = list(RESULTS_DIR.glob('evaluation_results_*.jsonl'))
        if not result_files:
            print("❌ 未找到评估结果文件")
            print(f"请先运行: python scripts/batch_evaluate_papers.py")
            return None
        results_file = max(result_files, key=lambda p: p.stat().st_mtime)

    print(f"📁 加载文件: {results_file.name}")

    data = []
    with open(results_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))

    print(f"✅ 加载了 {len(data)} 条评估记录\n")
    return data


def example_1_basic_stats(data):
    """示例1: 基本统计"""
    print("="*70)
    print("示例 1: 基本统计")
    print("="*70)

    df = pd.DataFrame(data)

    # 展开 evaluation 字典
    for key in ['avg_rating', 'paper_decision', 'originality', 'quality', 'clarity', 'significance']:
        df[key] = df['evaluation'].apply(lambda x: x.get(key))

    print(f"总评估记录: {len(df)}")
    print(f"论文数量: {df['paper_id'].nunique()}")
    print(f"变体类型: {df['variant_type'].unique().tolist()}")
    print(f"\n评分统计:")
    print(f"  平均分: {df['avg_rating'].mean():.2f}")
    print(f"  中位数: {df['avg_rating'].median():.2f}")
    print(f"  最高分: {df['avg_rating'].max():.2f}")
    print(f"  最低分: {df['avg_rating'].min():.2f}")
    print()


def example_2_variant_comparison(data):
    """示例2: 变体对比"""
    print("="*70)
    print("示例 2: 变体对比")
    print("="*70)

    df = pd.DataFrame(data)
    for key in ['avg_rating', 'paper_decision', 'originality', 'quality', 'clarity', 'significance']:
        df[key] = df['evaluation'].apply(lambda x: x.get(key))

    print(f"{'变体类型':<20} {'数量':>6} {'平均评分':>10} {'接受率':>10}")
    print("-" * 70)

    for variant in sorted(df['variant_type'].unique()):
        variant_df = df[df['variant_type'] == variant]
        count = len(variant_df)
        avg_rating = variant_df['avg_rating'].mean()
        accept_rate = variant_df['paper_decision'].str.contains('Accept', case=False).sum() / count * 100

        print(f"{variant:<20} {count:>6} {avg_rating:>10.2f} {accept_rate:>9.1f}%")

    print()


def example_3_paper_variants(data, paper_id=None):
    """示例3: 查看特定论文的所有变体"""
    print("="*70)
    print("示例 3: 特定论文的所有变体")
    print("="*70)

    # 如果没有指定 paper_id，随机选一个
    if paper_id is None:
        paper_ids = list(set(item['paper_id'] for item in data))
        if paper_ids:
            paper_id = paper_ids[0]

    print(f"论文ID: {paper_id}\n")

    # 找到该论文的所有变体
    paper_variants = [item for item in data if item['paper_id'] == paper_id]

    if not paper_variants:
        print(f"❌ 未找到论文 {paper_id}")
        return

    # 显示论文信息
    print(f"标题: {paper_variants[0]['title']}")
    print(f"数据集: {paper_variants[0]['dataset_split']}")
    print(f"\n各变体评分对比:")
    print(f"{'变体':<20} {'评分':>8} {'决定':>15} {'原创性':>8} {'质量':>8} {'清晰度':>8} {'重要性':>8}")
    print("-" * 100)

    # 按变体排序
    variant_order = ['original', 'no_abstract', 'no_introduction', 'no_methods', 'no_experiments', 'no_conclusion']
    sorted_variants = sorted(paper_variants, key=lambda x: variant_order.index(x['variant_type']) if x['variant_type'] in variant_order else 999)

    for item in sorted_variants:
        eval_data = item['evaluation']
        print(f"{item['variant_type']:<20} "
              f"{eval_data['avg_rating']:>8.2f} "
              f"{eval_data['paper_decision']:>15} "
              f"{eval_data['originality']:>8.1f} "
              f"{eval_data['quality']:>8.1f} "
              f"{eval_data['clarity']:>8.1f} "
              f"{eval_data['significance']:>8.1f}")

    print()


def example_4_impact_analysis(data):
    """示例4: 影响分析 - 缺少哪个部分影响最大"""
    print("="*70)
    print("示例 4: 影响分析")
    print("="*70)

    df = pd.DataFrame(data)
    df['avg_rating'] = df['evaluation'].apply(lambda x: x.get('avg_rating'))

    # 计算 original 的平均评分
    original_rating = df[df['variant_type'] == 'original']['avg_rating'].mean()

    print(f"Original 平均评分: {original_rating:.2f}\n")
    print(f"{'变体':<20} {'平均评分':>10} {'评分下降':>10} {'影响程度':>10}")
    print("-" * 70)

    variants = [v for v in df['variant_type'].unique() if v != 'original']
    impacts = []

    for variant in variants:
        variant_rating = df[df['variant_type'] == variant]['avg_rating'].mean()
        impact = original_rating - variant_rating
        impacts.append((variant, variant_rating, impact))

    # 按影响程度排序
    impacts.sort(key=lambda x: x[2], reverse=True)

    for variant, rating, impact in impacts:
        impact_pct = (impact / original_rating) * 100
        print(f"{variant:<20} {rating:>10.2f} {impact:>10.2f} {impact_pct:>9.1f}%")

    print(f"\n💡 结论: '{impacts[0][0]}' 部分对评分影响最大 (下降 {impacts[0][2]:.2f} 分)")
    print()


def example_5_find_top_papers(data, n=5):
    """示例5: 找出评分最高的论文"""
    print("="*70)
    print(f"示例 5: 评分最高的 {n} 篇论文")
    print("="*70)

    df = pd.DataFrame(data)
    df['avg_rating'] = df['evaluation'].apply(lambda x: x.get('avg_rating'))

    top_papers = df.nlargest(n, 'avg_rating')

    print(f"{'排名':>4} {'评分':>8} {'变体':>20} 论文标题")
    print("-" * 100)

    for i, (_, row) in enumerate(top_papers.iterrows(), 1):
        title = row['title'][:50] + '...' if len(row['title']) > 50 else row['title']
        print(f"{i:>4} {row['avg_rating']:>8.2f} {row['variant_type']:>20} {title}")

    print()


def example_6_export_to_csv(data):
    """示例6: 导出为 CSV 便于 Excel 分析"""
    print("="*70)
    print("示例 6: 导出为 CSV")
    print("="*70)

    df = pd.DataFrame(data)

    # 展开 evaluation 字典
    for key in ['avg_rating', 'paper_decision', 'confidence', 'originality', 'quality', 'clarity', 'significance']:
        df[key] = df['evaluation'].apply(lambda x: x.get(key))

    # 选择需要的列
    export_df = df[['paper_id', 'title', 'variant_type', 'dataset_split',
                    'avg_rating', 'paper_decision', 'originality', 'quality', 'clarity', 'significance']]

    output_file = PROJECT_ROOT / 'evaluation_data_export.csv'
    export_df.to_csv(output_file, index=False, encoding='utf-8-sig')  # utf-8-sig for Excel

    print(f"✅ 数据已导出到: {output_file}")
    print(f"   共 {len(export_df)} 条记录")
    print(f"   可以用 Excel 打开查看")
    print()


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("评估结果数据查询示例")
    print("="*70 + "\n")

    # 加载数据
    data = load_evaluation_results()
    if not data:
        return

    # 运行示例
    example_1_basic_stats(data)
    example_2_variant_comparison(data)
    example_3_paper_variants(data)
    example_4_impact_analysis(data)
    example_5_find_top_papers(data, n=5)
    example_6_export_to_csv(data)

    print("="*70)
    print("✅ 所有示例运行完成")
    print("="*70)
    print("\n💡 提示:")
    print("  - 评估数据保存在: evaluation_results/")
    print("  - 分析报告保存在: analysis_output/")
    print("  - 查看详细文档: scripts/DATA_FLOW_GUIDE.md")
    print()


if __name__ == "__main__":
    main()

