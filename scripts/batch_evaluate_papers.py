"""
Batch Evaluation Script for Paper Variants
Samples 100 papers from generated dataset and evaluates them using CycleReviewer
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import sys
from tqdm import tqdm

# Add parent directory to path to import ai_researcher
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_researcher import CycleReviewer


# ========== Configuration ==========
# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
TRAIN_DATASET = PROJECT_ROOT / "util" / "train_with_variants.jsonl"
TEST_DATASET = PROJECT_ROOT / "util" / "test_with_variants.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "evaluation_results"
SAMPLE_SIZE = 100  # Total number of papers to sample
TRAIN_RATIO = None  # Auto-calculate based on actual dataset ratio (set to number for fixed ratio)
SEED = 42
MODEL_SIZE = "8B"  # CycleReviewer model size


def load_dataset(filepath: str) -> List[Dict]:
    """Load papers from JSONL file"""
    papers = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                papers.append(json.loads(line))
    return papers


def sample_papers(train_papers: List[Dict], test_papers: List[Dict],
                  total_samples: int, train_ratio: float, seed: int) -> List[Dict]:
    """
    Sample papers proportionally from train and test sets

    Returns:
        List of sampled papers with metadata
    """
    random.seed(seed)

    # Calculate sample sizes
    train_sample_size = int(total_samples * train_ratio)
    test_sample_size = total_samples - train_sample_size

    print(f"[INFO] Sampling {train_sample_size} from train, {test_sample_size} from test")

    # Sample
    train_sampled = random.sample(train_papers, min(train_sample_size, len(train_papers)))
    test_sampled = random.sample(test_papers, min(test_sample_size, len(test_papers)))

    # Add metadata
    for paper in train_sampled:
        paper['dataset_split'] = 'train'
    for paper in test_sampled:
        paper['dataset_split'] = 'test'

    all_sampled = train_sampled + test_sampled
    random.shuffle(all_sampled)

    return all_sampled


def evaluate_papers(papers: List[Dict], reviewer: CycleReviewer) -> List[Dict]:
    """
    Evaluate papers using CycleReviewer

    Returns:
        List of evaluation results
    """
    results = []

    print(f"\n[INFO] Evaluating {len(papers)} papers...")

    for i, paper in enumerate(tqdm(papers, desc="Evaluating papers")):
        try:
            # Extract paper text
            paper_text = paper.get('text', '')  # Changed: 'paper_text' -> 'text'

            if not paper_text or len(paper_text) < 100:
                print(f"[WARN] Paper {i+1} has empty or too short text, skipping")
                continue

            # Evaluate
            reviews = reviewer.evaluate([paper_text])

            if reviews and reviews[0]:
                review = reviews[0]

                # Create result record
                result = {
                    'paper_id': paper.get('paper_id', f'paper_{i}'),
                    'title': paper.get('title', 'Unknown'),
                    'variant_type': paper.get('variant_type', 'unknown'),
                    'dataset_split': paper.get('dataset_split', 'unknown'),
                    'evaluation': {
                        'avg_rating': review.get('avg_rating', 0),
                        'paper_decision': review.get('paper_decision', 'Unknown'),
                        'confidence': review.get('confidence', 0),
                        'strength': review.get('strength', []),
                        'weaknesses': review.get('weaknesses', []),
                        'meta_review': review.get('meta_review', ''),
                        'originality': review.get('originality', 0),
                        'quality': review.get('quality', 0),
                        'clarity': review.get('clarity', 0),
                        'significance': review.get('significance', 0),
                    },
                    'text_length': len(paper_text),
                    'evaluation_timestamp': datetime.now().isoformat()
                }

                results.append(result)

            else:
                print(f"[WARN] Paper {i+1} evaluation returned empty result")

        except Exception as e:
            print(f"[ERROR] Failed to evaluate paper {i+1}: {e}")
            continue

    return results


def save_results(results: List[Dict], output_dir: Path):
    """Save evaluation results to files"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save detailed results as JSONL
    results_file = output_path / f'evaluation_results_{timestamp}.jsonl'
    with open(results_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')

    print(f"[INFO] Saved detailed results to {results_file}")

    # Save summary statistics
    summary = {
        'total_papers': len(results),
        'timestamp': timestamp,
        'config': {
            'sample_size': SAMPLE_SIZE,
            'train_ratio': TRAIN_RATIO,
            'model_size': MODEL_SIZE,
            'seed': SEED
        },
        'variant_distribution': {},
        'decision_distribution': {},
        'rating_statistics': {
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0,
            'std': 0
        }
    }

    # Count variants
    from collections import Counter
    variant_counts = Counter(r['variant_type'] for r in results)
    summary['variant_distribution'] = dict(variant_counts)

    # Count decisions
    decision_counts = Counter(r['evaluation']['paper_decision'] for r in results)
    summary['decision_distribution'] = dict(decision_counts)

    # Rating statistics
    ratings = [r['evaluation']['avg_rating'] for r in results]
    if ratings:
        import statistics
        summary['rating_statistics']['mean'] = statistics.mean(ratings)
        summary['rating_statistics']['median'] = statistics.median(ratings)
        summary['rating_statistics']['min'] = min(ratings)
        summary['rating_statistics']['max'] = max(ratings)
        summary['rating_statistics']['std'] = statistics.stdev(ratings) if len(ratings) > 1 else 0

    summary_file = output_path / f'evaluation_summary_{timestamp}.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"[INFO] Saved summary to {summary_file}")

    return results_file, summary_file


def main():
    print("="*70)
    print("Batch Paper Evaluation Script")
    print("="*70)

    # Load datasets
    print(f"\n[INFO] Loading datasets...")
    train_papers = load_dataset(TRAIN_DATASET)
    test_papers = load_dataset(TEST_DATASET)

    print(f"[INFO] Loaded {len(train_papers)} train papers, {len(test_papers)} test papers")

    # Sample papers
    print(f"\n[INFO] Sampling {SAMPLE_SIZE} papers...")
    sampled_papers = sample_papers(train_papers, test_papers, SAMPLE_SIZE, TRAIN_RATIO, SEED)

    # Count variant types in sample
    from collections import Counter
    variant_counts = Counter(p.get('variant_type', 'unknown') for p in sampled_papers)
    print(f"\n[INFO] Sampled papers by variant type:")
    for variant, count in sorted(variant_counts.items()):
        print(f"  {variant}: {count}")

    # Initialize reviewer
    print(f"\n[INFO] Initializing CycleReviewer (model size: {MODEL_SIZE})...")
    reviewer = CycleReviewer(model_size=MODEL_SIZE)

    # Evaluate papers
    results = evaluate_papers(sampled_papers, reviewer)

    # Save results
    print(f"\n[INFO] Saving results...")
    results_file, summary_file = save_results(results, OUTPUT_DIR)

    # Print summary
    print("\n" + "="*70)
    print("Evaluation Complete!")
    print("="*70)
    print(f"Total papers evaluated: {len(results)}/{SAMPLE_SIZE}")
    print(f"Results saved to: {results_file}")
    print(f"Summary saved to: {summary_file}")
    print("="*70)


if __name__ == "__main__":
    main()

