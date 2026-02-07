#!/usr/bin/env python3
"""
Batch Evaluation Script for Adversarial Attack Variants
评估攻击变体数据集，测试 CycleReviewer 对提示注入攻击的鲁棒性

与原始 batch_evaluate_papers.py 类似，但针对攻击实验优化：
- 使用攻击变体数据集
- 增加攻击相关的统计指标
- 支持断点续跑
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import sys
from tqdm import tqdm
import logging
from collections import Counter
import statistics

# Add parent directory to path to import ai_researcher
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai_researcher import CycleReviewer


# ========== Configuration ==========
PROJECT_ROOT = Path(__file__).parent.parent

# 数据集路径（攻击变体数据集）
TRAIN_DATASET = PROJECT_ROOT / "util" / "train_with_attacks.jsonl"
TEST_DATASET = PROJECT_ROOT / "util" / "test_with_attacks.jsonl"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "evaluation_results_attack"
LOG_DIR = PROJECT_ROOT / "evaluation_logs"

# 评估配置
SAMPLE_SIZE = 100  # 基础论文数量（与原实验一致）
SEED = 42  # 随机种子（与原实验一致）
MODEL_SIZE = "8B"

# 断点续跑配置
RESUME_FROM = None  # 设为文件路径可指定续跑文件


# ========== Logging Setup ==========
def setup_logging():
    """Setup logging to both console and file"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOG_DIR / f'attack_eval_log_{timestamp}.txt'

    logger = logging.getLogger('AttackEvaluator')
    logger.setLevel(logging.DEBUG)
    logger.handlers = []

    # File handler
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


logger, LOG_FILE = setup_logging()


def get_base_paper_id(paper: Dict) -> str:
    """获取论文的基础ID"""
    original_id = paper.get("original_id")
    if original_id:
        return str(original_id)

    paper_id = paper.get("paper_id")
    if paper_id:
        return str(paper_id)

    pid = paper.get("id", "")
    # 移除变体后缀
    if "_attack_" in pid:
        return pid.split("_attack_")[0]
    if "_original" in pid:
        return pid.replace("_original", "")
    return pid


def load_dataset(filepath: Path) -> List[Dict]:
    """加载数据集"""
    logger.info(f"Loading dataset from: {filepath}")
    papers = []

    if not filepath.exists():
        logger.error(f"  File not found: {filepath}")
        return papers

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    papers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    logger.info(f"  Loaded {len(papers)} papers from {filepath.name}")
    return papers


def find_latest_incremental_file() -> Path:
    """查找最新的增量结果文件"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    incremental_files = list(OUTPUT_DIR.glob("attack_results_*_incremental.jsonl"))
    if not incremental_files:
        return None
    return max(incremental_files, key=lambda p: p.stat().st_mtime)


def load_completed_results(resume_file: Path) -> tuple:
    """加载已完成的评估结果"""
    results = []
    completed_keys = set()

    if not resume_file or not resume_file.exists():
        return results, completed_keys

    logger.info(f"Loading completed results from: {resume_file}")

    with open(resume_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    result = json.loads(line)
                    results.append(result)
                    key = f"{result.get('base_paper_id', '')}_{result.get('variant_type', '')}"
                    completed_keys.add(key)
                except json.JSONDecodeError as e:
                    logger.warning(f"  Skipping malformed line {line_num}: {e}")

    logger.info(f"  ✓ Loaded {len(results)} completed evaluations")
    return results, completed_keys


def evaluate_papers(papers: List[Dict], reviewer: CycleReviewer,
                    resume_file: Path = None, existing_results: List[Dict] = None,
                    completed_keys: set = None) -> List[Dict]:
    """评估论文"""
    results = list(existing_results) if existing_results else []
    completed_keys = completed_keys or set()

    total = len(papers)
    already_done = len(results)
    success_count = already_done
    skip_count = 0
    error_count = 0
    new_evaluations = 0

    start_time = datetime.now()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if resume_file and resume_file.exists():
        incremental_file = resume_file
    else:
        timestamp = start_time.strftime('%Y%m%d_%H%M%S')
        incremental_file = OUTPUT_DIR / f'attack_results_{timestamp}_incremental.jsonl'

    logger.info("=" * 70)
    logger.info(f"Starting evaluation of {total} papers")
    if already_done > 0:
        logger.info(f"  ✓ Resuming: {already_done} already completed")
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Incremental save file: {incremental_file}")
    logger.info("=" * 70)

    for i, paper in enumerate(tqdm(papers, desc="Evaluating")):
        paper_num = i + 1
        base_id = get_base_paper_id(paper)
        variant_type = paper.get('variant_type', 'unknown')
        paper_key = f"{base_id}_{variant_type}"

        if paper_key in completed_keys:
            continue

        try:
            paper_text = paper.get('text', '')

            if not paper_text or len(paper_text) < 100:
                skip_count += 1
                logger.warning(f"[{paper_num}/{total}] SKIP: Too short - {variant_type}")
                continue

            # 进度日志
            if paper_num % 10 == 0 or new_evaluations <= 3:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = new_evaluations / elapsed if elapsed > 0 and new_evaluations > 0 else 0.01
                remaining = total - (success_count + skip_count + error_count)
                eta_str = f"{int(remaining / rate / 60)}m" if rate > 0 else "?"
                logger.info(f"[{paper_num}/{total}] {variant_type} | New: {new_evaluations} | Rate: {rate:.2f}/s | ETA: {eta_str}")

            logger.debug(f"[{paper_num}/{total}] Evaluating: {base_id} ({variant_type})")

            # 评估
            reviews = reviewer.evaluate([paper_text])

            if reviews and reviews[0]:
                review = reviews[0]
                rating = review.get('avg_rating', 0)
                decision = review.get('paper_decision', 'Unknown')

                result = {
                    'paper_id': paper.get('id', base_id),
                    'base_paper_id': base_id,
                    'title': paper.get('original_title', paper.get('title', 'Unknown')),
                    'variant_type': variant_type,
                    'attack_type': paper.get('attack_type', 'none'),
                    'attack_position': paper.get('attack_position', 'none'),
                    'section_found': paper.get('section_found', True),  # 是否成功匹配到目标章节
                    'dataset_split': paper.get('dataset_split', 'unknown'),
                    'evaluation': {
                        'avg_rating': rating,
                        'paper_decision': decision,
                        'confidence': review.get('confidence', 0),
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
                new_evaluations += 1
                completed_keys.add(paper_key)

                # 增量保存
                with open(incremental_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(result, ensure_ascii=False) + '\n')

                logger.debug(f"[{paper_num}/{total}] ✓ rating={rating:.1f}, decision={decision}")
            else:
                skip_count += 1
                logger.warning(f"[{paper_num}/{total}] SKIP: Empty result - {variant_type}")

        except Exception as e:
            error_count += 1
            logger.error(f"[{paper_num}/{total}] ERROR: {str(e)[:100]}")
            continue

        # 定期摘要
        if new_evaluations > 0 and new_evaluations % 100 == 0:
            logger.info(f"Progress: {success_count} completed, {skip_count} skipped, {error_count} errors")

    # 完成
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("=" * 70)
    logger.info("EVALUATION COMPLETE")
    logger.info(f"Duration: {duration}")
    logger.info(f"Results: {success_count} (new: {new_evaluations})")
    logger.info(f"Incremental file: {incremental_file}")
    logger.info("=" * 70)

    return results


def analyze_attack_effectiveness(results: List[Dict]) -> Dict:
    """分析攻击效果"""
    analysis = {
        'total_papers': len(results),
        'by_attack_type': {},
        'by_attack_position': {},
        'by_variant': {},
        'attack_effectiveness': {},
    }

    # 获取原始版本的评分作为基准
    original_ratings = {}
    for r in results:
        if r.get('attack_type') == 'none' or r.get('variant_type') == 'original':
            base_id = r.get('base_paper_id')
            original_ratings[base_id] = r['evaluation']['avg_rating']

    # 按攻击类型统计
    attack_types = set(r.get('attack_type', 'none') for r in results)
    for attack_type in attack_types:
        subset = [r for r in results if r.get('attack_type') == attack_type]
        if not subset:
            continue

        ratings = [r['evaluation']['avg_rating'] for r in subset]
        decisions = [r['evaluation']['paper_decision'] for r in subset]

        analysis['by_attack_type'][attack_type] = {
            'count': len(subset),
            'avg_rating': statistics.mean(ratings),
            'median_rating': statistics.median(ratings),
            'std_rating': statistics.stdev(ratings) if len(ratings) > 1 else 0,
            'accept_rate': sum(1 for d in decisions if 'accept' in d.lower()) / len(decisions),
            'decision_dist': dict(Counter(decisions)),
        }

    # 按攻击位置统计
    positions = set(r.get('attack_position', 'none') for r in results)
    for pos in positions:
        subset = [r for r in results if r.get('attack_position') == pos]
        if not subset:
            continue

        ratings = [r['evaluation']['avg_rating'] for r in subset]
        decisions = [r['evaluation']['paper_decision'] for r in subset]

        analysis['by_attack_position'][pos] = {
            'count': len(subset),
            'avg_rating': statistics.mean(ratings),
            'median_rating': statistics.median(ratings),
            'accept_rate': sum(1 for d in decisions if 'accept' in d.lower()) / len(decisions),
        }

    # 计算攻击效果（相比原始版本的评分变化）
    if original_ratings:
        for attack_type in attack_types:
            if attack_type == 'none':
                continue

            rating_changes = []
            for r in results:
                if r.get('attack_type') == attack_type:
                    base_id = r.get('base_paper_id')
                    if base_id in original_ratings:
                        change = r['evaluation']['avg_rating'] - original_ratings[base_id]
                        rating_changes.append(change)

            if rating_changes:
                analysis['attack_effectiveness'][attack_type] = {
                    'avg_rating_change': statistics.mean(rating_changes),
                    'median_rating_change': statistics.median(rating_changes),
                    'positive_effect_rate': sum(1 for c in rating_changes if c > 0) / len(rating_changes),
                    'negative_effect_rate': sum(1 for c in rating_changes if c < 0) / len(rating_changes),
                    'no_effect_rate': sum(1 for c in rating_changes if c == 0) / len(rating_changes),
                }

    return analysis


def save_results(results: List[Dict], output_dir: Path):
    """保存评估结果和分析"""
    logger.info("=" * 70)
    logger.info("SAVING RESULTS")
    logger.info("=" * 70)

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 保存详细结果
    results_file = output_dir / f'attack_results_{timestamp}.jsonl'
    with open(results_file, 'w', encoding='utf-8') as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    logger.info(f"  Saved {len(results)} results to {results_file}")

    # 分析攻击效果
    analysis = analyze_attack_effectiveness(results)

    # 保存分析结果
    summary = {
        'timestamp': timestamp,
        'total_papers': len(results),
        'config': {
            'sample_size': SAMPLE_SIZE,
            'seed': SEED,
            'model_size': MODEL_SIZE,
        },
        'attack_analysis': analysis,
    }

    summary_file = output_dir / f'attack_summary_{timestamp}.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info(f"  Saved summary to {summary_file}")

    # 打印攻击效果分析
    logger.info("")
    logger.info("=" * 70)
    logger.info("ATTACK EFFECTIVENESS ANALYSIS")
    logger.info("=" * 70)

    logger.info("\nBy Attack Type:")
    for attack_type, stats in sorted(analysis['by_attack_type'].items()):
        logger.info(f"\n  {attack_type}:")
        logger.info(f"    Count:       {stats['count']}")
        logger.info(f"    Avg Rating:  {stats['avg_rating']:.2f}")
        logger.info(f"    Accept Rate: {stats['accept_rate']:.1%}")

    logger.info("\nBy Attack Position:")
    for pos, stats in sorted(analysis['by_attack_position'].items()):
        logger.info(f"\n  {pos}:")
        logger.info(f"    Count:       {stats['count']}")
        logger.info(f"    Avg Rating:  {stats['avg_rating']:.2f}")
        logger.info(f"    Accept Rate: {stats['accept_rate']:.1%}")

    if analysis['attack_effectiveness']:
        logger.info("\nAttack Effectiveness (vs Original):")
        for attack_type, effect in sorted(analysis['attack_effectiveness'].items()):
            logger.info(f"\n  {attack_type}:")
            logger.info(f"    Avg Rating Change:    {effect['avg_rating_change']:+.2f}")
            logger.info(f"    Positive Effect Rate: {effect['positive_effect_rate']:.1%}")
            logger.info(f"    Negative Effect Rate: {effect['negative_effect_rate']:.1%}")

    return results_file, summary_file


def main():
    logger.info("=" * 70)
    logger.info("ADVERSARIAL ATTACK EVALUATION SCRIPT")
    logger.info("=" * 70)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("")
    logger.info("Configuration:")
    logger.info(f"  SAMPLE_SIZE:   {SAMPLE_SIZE} base papers")
    logger.info(f"  MODEL_SIZE:    {MODEL_SIZE}")
    logger.info(f"  SEED:          {SEED}")
    logger.info(f"  TRAIN_DATASET: {TRAIN_DATASET}")
    logger.info(f"  TEST_DATASET:  {TEST_DATASET}")
    logger.info(f"  OUTPUT_DIR:    {OUTPUT_DIR}")

    # 检查断点续跑
    resume_file = None
    existing_results = []
    completed_keys = set()

    if RESUME_FROM is not None:
        resume_file = Path(RESUME_FROM)
    else:
        latest_file = find_latest_incremental_file()
        if latest_file:
            file_age_hours = (datetime.now().timestamp() - latest_file.stat().st_mtime) / 3600
            if file_age_hours < 24:
                logger.info(f"Found recent incremental file: {latest_file}")
                resume_file = latest_file

    if resume_file and resume_file.exists():
        existing_results, completed_keys = load_completed_results(resume_file)

    # 加载数据集
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 1: Loading datasets")
    logger.info("=" * 70)

    train_papers = load_dataset(TRAIN_DATASET)
    test_papers = load_dataset(TEST_DATASET)

    all_papers = train_papers + test_papers
    logger.info(f"Total: {len(all_papers)} papers ({len(train_papers)} train + {len(test_papers)} test)")

    if not all_papers:
        logger.error("No papers found! Run generate_attack_dataset.py first.")
        return

    # 统计变体分布
    variant_dist = Counter(p.get('variant_type', 'unknown') for p in all_papers)
    attack_dist = Counter(p.get('attack_type', 'none') for p in all_papers)

    logger.info("")
    logger.info("Attack type distribution:")
    for atype, count in sorted(attack_dist.items()):
        logger.info(f"  {atype}: {count}")

    # 初始化模型
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 2: Initializing CycleReviewer")
    logger.info("=" * 70)
    logger.info(f"Model size: {MODEL_SIZE}")
    logger.info("Loading model... (this may take a few minutes)")

    reviewer = CycleReviewer(model_size=MODEL_SIZE)
    logger.info("✓ CycleReviewer initialized")

    # 评估
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 3: Evaluating papers")
    logger.info("=" * 70)

    results = evaluate_papers(
        all_papers,
        reviewer,
        resume_file=resume_file,
        existing_results=existing_results,
        completed_keys=completed_keys
    )

    # 保存结果
    logger.info("")
    results_file, summary_file = save_results(results, OUTPUT_DIR)

    # 完成
    logger.info("")
    logger.info("=" * 70)
    logger.info("COMPLETE")
    logger.info("=" * 70)
    logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Evaluated: {len(results)} papers")
    logger.info("")
    logger.info("Output files:")
    logger.info(f"  Results: {results_file}")
    logger.info(f"  Summary: {summary_file}")
    logger.info(f"  Log:     {LOG_FILE}")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()


