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
import re
import logging

# Add parent directory to path to import ai_researcher
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_researcher import CycleReviewer


# ========== Configuration ==========
# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
TRAIN_DATASET = PROJECT_ROOT / "util" / "train_with_variants.jsonl"
TEST_DATASET = PROJECT_ROOT / "util" / "test_with_variants.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "evaluation_results"
LOG_DIR = PROJECT_ROOT / "evaluation_logs"
SAMPLE_SIZE = 100  # Number of BASE papers to sample (each will have all variants)
TRAIN_RATIO = None  # Auto-calculate based on actual dataset ratio (set to number for fixed ratio)
SEED = 42
MODEL_SIZE = "8B"  # CycleReviewer model size


# ========== Logging Setup ==========
def setup_logging():
    """Setup logging to both console and file"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOG_DIR / f'evaluation_log_{timestamp}.txt'

    # Create logger
    logger = logging.getLogger('BatchEvaluator')
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers
    logger.handlers = []

    # File handler - detailed log
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s | %(levelname)-7s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_format)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Log file created: {log_file}")
    return logger, log_file


# Initialize logger
logger, LOG_FILE = setup_logging()

VARIANT_SUFFIXES = {
    "original",
    "no_abstract",
    "no_introduction",
    "no_methods",
    "no_experiments",
    "no_conclusion",
}


def get_base_paper_id(paper: Dict) -> str:
    """Return a stable base id used to group variants of the same paper."""
    # Priority 1: use original_id (all variants of same paper share this)
    original_id = paper.get("original_id")
    if original_id:
        return str(original_id)

    # Priority 2: use original_path
    original_path = paper.get("original_path")
    if original_path:
        return str(original_path)

    # Priority 3: try paper_id
    paper_id = paper.get("paper_id")
    if paper_id:
        return str(paper_id)

    # Last resort: use title
    title = paper.get("original_title") or paper.get("title")
    return str(title) if title else ""


def load_dataset(filepath: str) -> List[Dict]:
    """Load papers from JSONL file"""
    logger.info(f"Loading dataset from: {filepath}")
    papers = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                papers.append(json.loads(line))
    logger.info(f"  Loaded {len(papers)} papers from {Path(filepath).name}")
    return papers


def group_papers_by_id(papers: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group papers by paper_id (each paper_id has multiple variants)

    Returns:
        Dict mapping paper_id to list of variant papers
    """
    grouped = {}
    skipped = 0
    for paper in papers:
        paper_id = get_base_paper_id(paper)
        if not paper_id:
            skipped += 1
            continue
        if paper_id not in grouped:
            grouped[paper_id] = []
        grouped[paper_id].append(paper)

    if skipped > 0:
        logger.warning(f"  Skipped {skipped} papers with empty/missing paper_id")

    # Log some statistics about grouping
    if grouped:
        variant_counts = [len(v) for v in grouped.values()]
        logger.debug(f"  Variants per paper: min={min(variant_counts)}, max={max(variant_counts)}, avg={sum(variant_counts)/len(variant_counts):.1f}")

    return grouped


def sample_papers(train_papers: List[Dict], test_papers: List[Dict],
                  total_samples: int, train_ratio: float, seed: int) -> List[Dict]:
    """
    Sample N base papers (each with all variants) proportionally from train and test sets

    Returns:
        List of sampled papers including all variants for each base paper
    """
    random.seed(seed)
    logger.info(f"Random seed set to: {seed}")

    # Group papers by paper_id
    logger.info("Grouping papers by base paper_id...")
    train_grouped = group_papers_by_id(train_papers)
    test_grouped = group_papers_by_id(test_papers)

    if len(train_grouped) <= 1 and len(train_papers) > 1:
        logger.warning("⚠️  Train set collapsed to <= 1 unique paper_id. Check id fields (paper_id/id).")
    if len(test_grouped) <= 1 and len(test_papers) > 1:
        logger.warning("⚠️  Test set collapsed to <= 1 unique paper_id. Check id fields (paper_id/id).")

    logger.info(f"Found {len(train_grouped)} unique base papers in train set")
    logger.info(f"Found {len(test_grouped)} unique base papers in test set")
    logger.info(f"Total unique base papers: {len(train_grouped) + len(test_grouped)}")

    # Auto-calculate ratio if not provided
    if train_ratio is None:
        total_base_papers = len(train_grouped) + len(test_grouped)
        train_ratio = len(train_grouped) / total_base_papers if total_base_papers > 0 else 0.5
        logger.info(f"Auto-calculated train_ratio: {train_ratio:.2%}")
    else:
        logger.info(f"Using fixed train_ratio: {train_ratio:.2%}")

    # Calculate sample sizes (number of BASE papers, not variants)
    train_sample_size = int(total_samples * train_ratio)
    test_sample_size = total_samples - train_sample_size

    logger.info(f"Target: {total_samples} base papers total")
    logger.info(f"  - Train: {train_sample_size} base papers ({train_sample_size/total_samples*100:.1f}%)")
    logger.info(f"  - Test:  {test_sample_size} base papers ({test_sample_size/total_samples*100:.1f}%)")

    # Sample paper IDs
    train_paper_ids = list(train_grouped.keys())
    test_paper_ids = list(test_grouped.keys())

    # Adjust if not enough papers
    actual_train_sample = min(train_sample_size, len(train_paper_ids))
    actual_test_sample = min(test_sample_size, len(test_paper_ids))

    if actual_train_sample < train_sample_size:
        logger.warning(f"  Only {len(train_paper_ids)} train papers available, sampling {actual_train_sample}")
    if actual_test_sample < test_sample_size:
        logger.warning(f"  Only {len(test_paper_ids)} test papers available, sampling {actual_test_sample}")

    logger.info("Sampling paper IDs...")
    sampled_train_ids = random.sample(train_paper_ids, actual_train_sample)
    sampled_test_ids = random.sample(test_paper_ids, actual_test_sample)

    logger.info(f"  Sampled {len(sampled_train_ids)} train paper IDs")
    logger.info(f"  Sampled {len(sampled_test_ids)} test paper IDs")

    # Collect ALL variants for sampled papers
    logger.info("Collecting all variants for sampled papers...")
    all_sampled = []

    for i, paper_id in enumerate(sampled_train_ids):
        variants = train_grouped[paper_id]
        for paper in variants:
            paper['dataset_split'] = 'train'
            paper['base_paper_id'] = paper_id  # Add base paper ID for reference
            all_sampled.append(paper)
        if (i + 1) % 20 == 0:
            logger.debug(f"  Processed {i+1}/{len(sampled_train_ids)} train papers...")

    for i, paper_id in enumerate(sampled_test_ids):
        variants = test_grouped[paper_id]
        for paper in variants:
            paper['dataset_split'] = 'test'
            paper['base_paper_id'] = paper_id
            all_sampled.append(paper)
        if (i + 1) % 20 == 0:
            logger.debug(f"  Processed {i+1}/{len(sampled_test_ids)} test papers...")

    logger.info(f"✓ Total papers with all variants: {len(all_sampled)}")

    # Verify variant distribution
    from collections import Counter
    variant_dist = Counter(p.get('variant_type', 'unknown') for p in all_sampled)
    logger.info("Variant distribution in sampled data:")
    for variant, count in sorted(variant_dist.items()):
        logger.info(f"  {variant}: {count}")

    return all_sampled


def evaluate_papers(papers: List[Dict], reviewer: CycleReviewer) -> List[Dict]:
    """
    Evaluate papers using CycleReviewer

    Returns:
        List of evaluation results
    """
    results = []
    total = len(papers)
    success_count = 0
    skip_count = 0
    error_count = 0

    start_time = datetime.now()

    # Create incremental save file
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = start_time.strftime('%Y%m%d_%H%M%S')
    incremental_file = OUTPUT_DIR / f'evaluation_results_{timestamp}_incremental.jsonl'

    # Convert to absolute path to avoid any issues
    incremental_file = incremental_file.resolve()

    logger.info("=" * 70)
    logger.info(f"Starting evaluation of {total} papers")
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Incremental save file: {incremental_file}")
    logger.info("✓ Results will be saved immediately after each evaluation")
    logger.info("=" * 70)

    for i, paper in enumerate(tqdm(papers, desc="Evaluating papers")):
        paper_num = i + 1
        try:
            # Extract paper text
            paper_text = paper.get('text', '')
            variant_type = paper.get('variant_type', 'unknown')
            base_id = paper.get('base_paper_id', get_base_paper_id(paper))
            title = paper.get('title', 'Unknown')[:50]  # Truncate for display

            if not paper_text or len(paper_text) < 100:
                skip_count += 1
                logger.warning(f"[{paper_num}/{total}] SKIP: Empty or too short text ({len(paper_text)} chars) - {variant_type}")
                continue

            # Log progress every 10 papers or for important milestones
            if paper_num % 10 == 0 or paper_num <= 5:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = paper_num / elapsed if elapsed > 0 else 0
                eta_seconds = (total - paper_num) / rate if rate > 0 else 0
                eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s"
                logger.info(f"[{paper_num}/{total}] Processing: {variant_type} | Rate: {rate:.2f} papers/s | ETA: {eta_str}")

            # Evaluate
            logger.debug(f"[{paper_num}/{total}] Evaluating: {base_id} ({variant_type}) - {len(paper_text)} chars")
            reviews = reviewer.evaluate([paper_text])

            if reviews and reviews[0]:
                review = reviews[0]
                rating = review.get('avg_rating', 0)
                decision = review.get('paper_decision', 'Unknown')

                # Create result record
                result = {
                    'paper_id': paper.get('paper_id') or base_id,
                    'base_paper_id': base_id,
                    'title': paper.get('title', 'Unknown'),
                    'variant_type': variant_type,
                    'dataset_split': paper.get('dataset_split', 'unknown'),
                    'evaluation': {
                        'avg_rating': rating,
                        'paper_decision': decision,
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
                success_count += 1

                # Incremental save: append to file immediately
                try:
                    with open(incremental_file, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(result, ensure_ascii=False) + '\n')
                    logger.debug(f"[{paper_num}/{total}] ✓ Result: rating={rating:.1f}, decision={decision} (saved)")
                except Exception as save_error:
                    logger.error(f"[{paper_num}/{total}] ERROR saving to incremental file: {save_error}")
                    logger.error(f"  Incremental file path: {incremental_file}")
                    # Continue evaluation even if save fails
                    pass

            else:
                skip_count += 1
                logger.warning(f"[{paper_num}/{total}] SKIP: Empty evaluation result - {variant_type}")

        except Exception as e:
            error_count += 1
            logger.error(f"[{paper_num}/{total}] ERROR: {str(e)[:100]} - {paper.get('variant_type', 'unknown')}")
            continue

        # Periodic summary every 50 papers
        if paper_num % 50 == 0:
            logger.info("-" * 50)
            logger.info(f"Progress: {paper_num}/{total} ({paper_num/total*100:.1f}%)")
            logger.info(f"  Success: {success_count}, Skipped: {skip_count}, Errors: {error_count}")
            logger.info("-" * 50)

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("=" * 70)
    logger.info("EVALUATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total duration: {duration}")
    logger.info(f"Results: {success_count} success, {skip_count} skipped, {error_count} errors")
    logger.info(f"Incremental results saved to: {incremental_file}")
    logger.info(f"  ✓ Safe to resume from this file if needed")
    logger.info(f"Success rate: {success_count/total*100:.1f}%")
    if success_count > 0:
        logger.info(f"Average time per paper: {duration.total_seconds()/success_count:.2f}s")

    return results


def save_results(results: List[Dict], output_dir: Path):
    """Save evaluation results to files"""
    logger.info("=" * 70)
    logger.info("SAVING RESULTS")
    logger.info("=" * 70)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save detailed results as JSONL
    results_file = output_path / f'evaluation_results_{timestamp}.jsonl'
    logger.info(f"Saving detailed results to: {results_file}")
    with open(results_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    logger.info(f"  ✓ Saved {len(results)} evaluation records")

    # Save summary statistics
    from collections import Counter
    import statistics

    logger.info("Calculating summary statistics...")

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
        },
        'variant_statistics': {}
    }

    # Count variants
    variant_counts = Counter(r['variant_type'] for r in results)
    summary['variant_distribution'] = dict(variant_counts)

    # Count decisions
    decision_counts = Counter(r['evaluation']['paper_decision'] for r in results)
    summary['decision_distribution'] = dict(decision_counts)

    # Overall rating statistics
    ratings = [r['evaluation']['avg_rating'] for r in results]
    if ratings:
        summary['rating_statistics']['mean'] = statistics.mean(ratings)
        summary['rating_statistics']['median'] = statistics.median(ratings)
        summary['rating_statistics']['min'] = min(ratings)
        summary['rating_statistics']['max'] = max(ratings)
        summary['rating_statistics']['std'] = statistics.stdev(ratings) if len(ratings) > 1 else 0

        logger.info(f"Overall ratings: mean={summary['rating_statistics']['mean']:.2f}, "
                   f"median={summary['rating_statistics']['median']:.2f}, "
                   f"std={summary['rating_statistics']['std']:.2f}")

    # Statistics by variant type
    logger.info("Calculating per-variant statistics...")
    variants = set(r['variant_type'] for r in results)
    for variant in variants:
        variant_results = [r for r in results if r['variant_type'] == variant]
        variant_ratings = [r['evaluation']['avg_rating'] for r in variant_results]
        variant_decisions = Counter(r['evaluation']['paper_decision'] for r in variant_results)

        summary['variant_statistics'][variant] = {
            'count': len(variant_results),
            'avg_rating': statistics.mean(variant_ratings) if variant_ratings else 0,
            'median_rating': statistics.median(variant_ratings) if variant_ratings else 0,
            'std_rating': statistics.stdev(variant_ratings) if len(variant_ratings) > 1 else 0,
            'decision_distribution': dict(variant_decisions),
            'accept_rate': sum(1 for r in variant_results if 'accept' in r['evaluation']['paper_decision'].lower()) / len(variant_results) if variant_results else 0,
            'avg_originality': statistics.mean([r['evaluation']['originality'] for r in variant_results]) if variant_results else 0,
            'avg_quality': statistics.mean([r['evaluation']['quality'] for r in variant_results]) if variant_results else 0,
            'avg_clarity': statistics.mean([r['evaluation']['clarity'] for r in variant_results]) if variant_results else 0,
            'avg_significance': statistics.mean([r['evaluation']['significance'] for r in variant_results]) if variant_results else 0,
        }
        logger.debug(f"  {variant}: count={len(variant_results)}, avg_rating={summary['variant_statistics'][variant]['avg_rating']:.2f}")

    summary_file = output_path / f'evaluation_summary_{timestamp}.json'
    logger.info(f"Saving summary to: {summary_file}")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info("  ✓ Saved summary statistics")

    # Print variant comparison
    logger.info("")
    logger.info("=" * 70)
    logger.info("VARIANT COMPARISON RESULTS")
    logger.info("=" * 70)
    for variant in sorted(summary['variant_statistics'].keys()):
        stats = summary['variant_statistics'][variant]
        logger.info(f"\n{variant}:")
        logger.info(f"  Count:        {stats['count']}")
        logger.info(f"  Avg Rating:   {stats['avg_rating']:.2f} (median: {stats['median_rating']:.2f}, std: {stats['std_rating']:.2f})")
        logger.info(f"  Accept Rate:  {stats['accept_rate']:.1%}")
        logger.info(f"  Originality:  {stats['avg_originality']:.2f}")
        logger.info(f"  Quality:      {stats['avg_quality']:.2f}")
        logger.info(f"  Clarity:      {stats['avg_clarity']:.2f}")
        logger.info(f"  Significance: {stats['avg_significance']:.2f}")

    logger.info("")
    logger.info("Decision distribution:")
    for decision, count in sorted(decision_counts.items()):
        logger.info(f"  {decision}: {count} ({count/len(results)*100:.1f}%)")

    return results_file, summary_file


def main():
    logger.info("=" * 70)
    logger.info("BATCH PAPER EVALUATION SCRIPT")
    logger.info("=" * 70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("")
    logger.info("Configuration:")
    logger.info(f"  SAMPLE_SIZE:   {SAMPLE_SIZE} base papers")
    logger.info(f"  TRAIN_RATIO:   {TRAIN_RATIO if TRAIN_RATIO else 'auto-calculate'}")
    logger.info(f"  MODEL_SIZE:    {MODEL_SIZE}")
    logger.info(f"  SEED:          {SEED}")
    logger.info(f"  TRAIN_DATASET: {TRAIN_DATASET}")
    logger.info(f"  TEST_DATASET:  {TEST_DATASET}")
    logger.info(f"  OUTPUT_DIR:    {OUTPUT_DIR}")
    logger.info("")

    # Load datasets
    logger.info("=" * 70)
    logger.info("STEP 1: Loading datasets")
    logger.info("=" * 70)
    train_papers = load_dataset(TRAIN_DATASET)
    test_papers = load_dataset(TEST_DATASET)
    logger.info(f"Total loaded: {len(train_papers)} train + {len(test_papers)} test = {len(train_papers) + len(test_papers)} papers")

    # Sample papers (will get all variants for each base paper)
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 2: Sampling papers")
    logger.info("=" * 70)
    sampled_papers = sample_papers(train_papers, test_papers, SAMPLE_SIZE, TRAIN_RATIO, SEED)

    # Verify we have the expected number of variants
    expected_variants = ['original', 'no_abstract', 'no_introduction', 'no_methods', 'no_experiments', 'no_conclusion']
    expected_total = SAMPLE_SIZE * len(expected_variants)
    actual_total = len(sampled_papers)

    logger.info("")
    logger.info(f"Sampling verification:")
    logger.info(f"  Expected: {SAMPLE_SIZE} papers × {len(expected_variants)} variants = {expected_total} total")
    logger.info(f"  Actual:   {actual_total} papers")
    if actual_total != expected_total:
        logger.warning(f"  ⚠️  Mismatch! Difference: {actual_total - expected_total}")

    # Initialize reviewer
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 3: Initializing CycleReviewer")
    logger.info("=" * 70)
    logger.info(f"Model size: {MODEL_SIZE}")
    logger.info("Loading model... (this may take a few minutes)")
    reviewer = CycleReviewer(model_size=MODEL_SIZE)
    logger.info("✓ CycleReviewer initialized successfully")

    # Evaluate papers
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 4: Evaluating papers")
    logger.info("=" * 70)
    results = evaluate_papers(sampled_papers, reviewer)

    # Save results
    logger.info("")
    results_file, summary_file = save_results(results, OUTPUT_DIR)

    # Final summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("EXECUTION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total papers evaluated: {len(results)}/{len(sampled_papers)}")
    logger.info(f"Success rate: {len(results)/len(sampled_papers)*100:.1f}%")
    logger.info("")
    logger.info("Output files:")
    logger.info(f"  Results:  {results_file}")
    logger.info(f"  Summary:  {summary_file}")
    logger.info(f"  Log:      {LOG_FILE}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()

