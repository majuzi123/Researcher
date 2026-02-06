"""
Quick test to verify the paper grouping logic
"""
import json
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent
TRAIN_DATASET = PROJECT_ROOT / "util" / "train_with_variants.jsonl"

def get_base_paper_id(paper):
    """Same logic as in batch_evaluate_papers.py"""
    original_id = paper.get("original_id")
    if original_id:
        return str(original_id)

    original_path = paper.get("original_path")
    if original_path:
        return str(original_path)

    paper_id = paper.get("paper_id")
    if paper_id:
        return str(paper_id)

    title = paper.get("original_title") or paper.get("title")
    return str(title) if title else ""

# Load first 100 records
print("Loading first 100 records from train set...")
papers = []
with open(TRAIN_DATASET, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i >= 100:
            break
        papers.append(json.loads(line))

# Group by base_paper_id
grouped = {}
for paper in papers:
    base_id = get_base_paper_id(paper)
    if base_id not in grouped:
        grouped[base_id] = []
    grouped[base_id].append(paper['variant_type'])

print(f"\nTotal records loaded: {len(papers)}")
print(f"Unique base papers: {len(grouped)}")
print(f"Expected unique papers: ~{len(papers) // 6} (if 6 variants per paper)")

# Show variant distribution for first few papers
print("\nFirst 5 papers and their variants:")
for i, (base_id, variants) in enumerate(list(grouped.items())[:5]):
    # Get title from first variant
    title = next((p['title'] for p in papers if get_base_paper_id(p) == base_id), 'Unknown')
    print(f"\n{i+1}. Base ID: {base_id[:50]}...")
    print(f"   Title: {title[:60]}...")
    print(f"   Variants ({len(variants)}): {sorted(variants)}")

# Check if grouping is working correctly
variant_counts = Counter(len(v) for v in grouped.values())
print(f"\nVariants per paper distribution:")
for count, num_papers in sorted(variant_counts.items()):
    print(f"  {count} variants: {num_papers} papers")

# Expected: most papers should have 6 variants
if 6 in variant_counts and variant_counts[6] == len(grouped):
    print("\n✅ Perfect! All papers have 6 variants")
elif 6 in variant_counts and variant_counts[6] > len(grouped) * 0.8:
    print("\n✅ Good! Most papers have 6 variants")
else:
    print("\n⚠️  Warning: Not all papers have 6 variants")
    print("   This might indicate a grouping problem")

