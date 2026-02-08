"""
Test script to verify the sampling logic
"""

import json
import random
from typing import List, Dict

def group_papers_by_id(papers: List[Dict]) -> Dict[str, List[Dict]]:
    """Group papers by paper_id"""
    grouped = {}
    for paper in papers:
        paper_id = paper.get('paper_id', '')
        if paper_id not in grouped:
            grouped[paper_id] = []
        grouped[paper_id].append(paper)
    return grouped


def test_sampling():
    """Test the sampling logic with mock data"""

    # Create mock data: 10 papers, each with 6 variants
    mock_papers = []
    variants = ['original', 'no_abstract', 'no_introduction', 'no_methods', 'no_experiments', 'no_conclusion']

    for i in range(10):
        for variant in variants:
            mock_papers.append({
                'paper_id': f'paper_{i}',
                'title': f'Paper {i}',
                'variant_type': variant,
                'text': f'This is the {variant} version of paper {i}'
            })

    print(f"Created {len(mock_papers)} mock papers (10 base papers × 6 variants)")

    # Test grouping
    grouped = group_papers_by_id(mock_papers)
    print(f"\nGrouped into {len(grouped)} unique papers")

    # Verify each paper has all variants
    for paper_id, variants_list in grouped.items():
        variant_types = [v['variant_type'] for v in variants_list]
        print(f"{paper_id}: {len(variants_list)} variants - {sorted(variant_types)}")

    # Test sampling
    random.seed(42)
    sample_size = 3  # Sample 3 base papers

    paper_ids = list(grouped.keys())
    sampled_ids = random.sample(paper_ids, sample_size)

    print(f"\nSampled {sample_size} base papers: {sampled_ids}")

    # Collect all variants for sampled papers
    all_sampled = []
    for paper_id in sampled_ids:
        for paper in grouped[paper_id]:
            all_sampled.append(paper)

    print(f"Total papers with all variants: {len(all_sampled)}")
    print(f"Expected: {sample_size} × 6 variants = {sample_size * 6}")

    # Count variants
    from collections import Counter
    variant_counts = Counter(p['variant_type'] for p in all_sampled)
    print(f"\nVariant distribution:")
    for variant, count in sorted(variant_counts.items()):
        print(f"  {variant}: {count}")

    # Verify each variant appears exactly sample_size times
    print("\n✓ PASS: Each variant should appear exactly 3 times")
    for variant, count in variant_counts.items():
        assert count == sample_size, f"Expected {sample_size} but got {count} for {variant}"
    print("✓ All checks passed!")


if __name__ == "__main__":
    test_sampling()

