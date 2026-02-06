# python
"""
Paper Variant Dataset Generator
Function: Sample papers by ratio, generate various variants, and consolidate them into a complete dataset (JSONL format)
"""

import re
import json
import random
from pathlib import Path
from typing import List, Dict, Optional


# ========== Configuration ==========
# Sampling ratio (between 0-1)
SAMPLE_RATIO = 1.0  # Changed to 1.0 - process all papers, then filter successful ones
SEED = 12345

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Source data files (relative to project root)
SOURCE_TRAIN_JSONL = PROJECT_ROOT / "train.jsonl"
SOURCE_TEST_JSONL = PROJECT_ROOT / "test.jsonl"
# Output dataset files (relative to project root)
OUTPUT_TRAIN_JSONL = PROJECT_ROOT / "util/train_with_variants.jsonl"
OUTPUT_TEST_JSONL = PROJECT_ROOT / "util/test_with_variants.jsonl"
# Strict mode: If any variant generation fails, discard the entire paper and sample a new one
# Lenient mode (False): Allow partial variant generation
STRICT_MODE = True  # Changed to True - only keep papers with all variants
# Maximum retry attempts for supplementary sampling (to prevent infinite loops)
MAX_RETRY_ATTEMPTS = 100
# ====================================


# ===== Variant Generation Function Definitions =====

# Updated regex patterns to match various section heading formats:
# - With or without numbering (e.g., "5. CONCLUSION" or "CONCLUSION")
# - All caps or title case
# - Special formats like "CONCLUSION & FUTURE WORK"

RE_ABSTRACT = re.compile(
    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:ABSTRACT|Abstract|abstract)\s*[:\-]?\s*\n",
    re.S
)
RE_CONCLUSION = re.compile(
    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:CONCLUSION[S]?(?:\s*(?:&|AND)\s*FUTURE\s*WORK)?|Conclusion[s]?(?:\s*(?:&|and)\s*[Ff]uture\s*[Ww]ork)?|conclusion[s]?|CONCLUDING\s*REMARKS?|Concluding\s*Remarks?|concluding\s*remarks?)\s*[:\-]?\s*\n",
    re.S
)
RE_INTRODUCTION = re.compile(
    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:INTRODUCTION|Introduction|introduction)\s*[:\-]?\s*\n",
    re.S
)
RE_REFERENCES = re.compile(
    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:REFERENCES|References|references|BIBLIOGRAPHY|Bibliography|bibliography)\s*[:\-]?\s*\n",
    re.S
)
RE_EXPERIMENTS = re.compile(
    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:EXPERIMENTS?|Experiments?|experiments?|EXPERIMENTAL\s*RESULTS?|Experimental\s*Results?|experimental\s*results?)\s*[:\-]?\s*\n",
    re.S
)
RE_METHODS = re.compile(
    r"(?:^|\n)\s*(?:\d+\.?\s*)?(?:METHODS?|Methods?|methods?|METHODOLOGY|Methodology|methodology|APPROACH|Approach|approach)\s*[:\-]?\s*\n",
    re.S
)
# Match formulas: LaTeX formulas and common mathematical symbols
RE_FORMULAS = re.compile(
    r"(?:\$\$.*?\$\$|\$.*?\$|\\begin\{equation\}.*?\\end\{equation\}|\\begin\{align\}.*?\\end\{align\}|\\begin\{eqnarray\}.*?\\end\{eqnarray\}|\\[.*?\\])",
    re.S
)
# Match figures: LaTeX figure environments and common image references
RE_FIGURES = re.compile(
    r"(?:\\begin\{figure\}.*?\\end\{figure\}|\\includegraphics.*?(?:\}|\n)|\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}|!\[.*?\]\(.*?\)|<img.*?>)",
    re.S
)


def variant_original(text: str) -> tuple[str, bool]:
    """Original paper, no modifications"""
    return text, True  # Original version always succeeds


def variant_no_abstract(text: str) -> tuple[str, bool]:
    """Remove abstract section"""
    # Find ABSTRACT heading and remove content until next major section
    lines = text.split('\n')
    start_idx = -1
    end_idx = len(lines)

    # Find start of abstract
    for i, line in enumerate(lines):
        if re.search(r'^\s*(\d+\.?\s*)?ABSTRACT\s*[:\-]?\s*$', line, re.I):
            start_idx = i
            break

    if start_idx == -1:
        return text, False  # Not found

    # Find end (next section starting with number or all-caps)
    for i in range(start_idx + 1, len(lines)):
        if re.search(r'^\s*\d+\.?\s+[A-Z]', lines[i]) or \
           re.search(r'^\s*[A-Z]{3,}[A-Z\s]*\s*[:\-]?\s*$', lines[i]):
            end_idx = i
            break

    # Remove the section
    result = '\n'.join(lines[:start_idx] + lines[end_idx:])
    return result, True


def variant_no_conclusion(text: str) -> tuple[str, bool]:
    """Remove conclusion section"""
    lines = text.split('\n')
    start_idx = -1
    end_idx = len(lines)

    # Find start
    for i, line in enumerate(lines):
        if re.search(r'^\s*(\d+\.?\s*)?(CONCLUSION[S]?|CONCLUDING\s+REMARKS?)\s*(&|\s+AND\s+FUTURE\s+WORK)?\s*[:\-]?\s*$', line, re.I):
            start_idx = i
            break

    if start_idx == -1:
        return text, False

    # Find end
    for i in range(start_idx + 1, len(lines)):
        if re.search(r'^\s*\d+\.?\s+[A-Z]', lines[i]) or \
           re.search(r'^\s*[A-Z]{3,}[A-Z\s]*\s*[:\-]?\s*$', lines[i]):
            end_idx = i
            break

    result = '\n'.join(lines[:start_idx] + lines[end_idx:])
    return result, True


def variant_no_introduction(text: str) -> tuple[str, bool]:
    """Remove introduction section"""
    lines = text.split('\n')
    start_idx = -1
    end_idx = len(lines)

    for i, line in enumerate(lines):
        if re.search(r'^\s*(\d+\.?\s*)?INTRODUCTION\s*[:\-]?\s*$', line, re.I):
            start_idx = i
            break

    if start_idx == -1:
        return text, False

    for i in range(start_idx + 1, len(lines)):
        if re.search(r'^\s*\d+\.?\s+[A-Z]', lines[i]) or \
           re.search(r'^\s*[A-Z]{3,}[A-Z\s]*\s*[:\-]?\s*$', lines[i]):
            end_idx = i
            break

    result = '\n'.join(lines[:start_idx] + lines[end_idx:])
    return result, True


def variant_no_references(text: str) -> tuple[str, bool]:
    """Remove references section - typically at end"""
    lines = text.split('\n')
    start_idx = -1

    # Find REFERENCES (usually near the end)
    for i, line in enumerate(lines):
        if re.search(r'^\s*(\d+\.?\s*)?(REFERENCES?|BIBLIOGRAPHY)\s*[:\-]?\s*$', line, re.I):
            start_idx = i
            break

    if start_idx == -1:
        return text, False

    # Remove from REFERENCES to end
    result = '\n'.join(lines[:start_idx])
    return result, True


def variant_no_experiments(text: str) -> tuple[str, bool]:
    """Remove experiments section"""
    lines = text.split('\n')
    start_idx = -1
    end_idx = len(lines)

    for i, line in enumerate(lines):
        if re.search(r'^\s*(\d+\.?\s*)?(EXPERIMENTS?|EXPERIMENTAL\s+RESULTS?)\s*[:\-]?\s*$', line, re.I):
            start_idx = i
            break

    if start_idx == -1:
        return text, False

    for i in range(start_idx + 1, len(lines)):
        if re.search(r'^\s*\d+\.?\s+[A-Z]', lines[i]) or \
           re.search(r'^\s*[A-Z]{3,}[A-Z\s]*\s*[:\-]?\s*$', lines[i]):
            end_idx = i
            break

    result = '\n'.join(lines[:start_idx] + lines[end_idx:])
    return result, True


def variant_no_methods(text: str) -> tuple[str, bool]:
    """Remove methods section"""
    lines = text.split('\n')
    start_idx = -1
    end_idx = len(lines)

    for i, line in enumerate(lines):
        if re.search(r'^\s*(\d+\.?\s*)?(METHODS?|METHODOLOGY|APPROACH)\s*[:\-]?\s*$', line, re.I):
            start_idx = i
            break

    if start_idx == -1:
        return text, False

    for i in range(start_idx + 1, len(lines)):
        if re.search(r'^\s*\d+\.?\s+[A-Z]', lines[i]) or \
           re.search(r'^\s*[A-Z]{3,}[A-Z\s]*\s*[:\-]?\s*$', lines[i]):
            end_idx = i
            break

    result = '\n'.join(lines[:start_idx] + lines[end_idx:])
    return result, True


def variant_no_formulas(text: str) -> tuple[str, bool]:
    """Remove all formulas"""
    pattern = RE_FORMULAS
    matched = pattern.search(text) is not None
    result = pattern.sub(" ", text) if matched else text
    return result, matched


def variant_no_figures(text: str) -> tuple[str, bool]:
    """Remove all figures"""
    pattern = RE_FIGURES
    matched = pattern.search(text) is not None
    result = pattern.sub("\n", text) if matched else text
    return result, matched


# Variant function mapping table
# Include high and medium success rate variants (6 variants total)
VARIANT_FUNCS = {
    "original": variant_original,
    "no_abstract": variant_no_abstract,
    "no_introduction": variant_no_introduction,
    "no_conclusion": variant_no_conclusion,      # 66-70% - Added
    "no_experiments": variant_no_experiments,    # 59-68% - Added
    "no_methods": variant_no_methods,            # 27-36% - Added
    # "no_formulas": variant_no_formulas,        # 9% - Removed (too low)
    # "no_figures": variant_no_figures,          # 1-4% - Still too low
    # "no_references": variant_no_references,    # 0% - Still failing
}


# ===== Data Loading and Processing Functions =====

def load_papers_from_jsonl(path: Path) -> List[Dict]:
    """Load paper data from JSONL file"""
    papers: List[Dict] = []
    if not path.exists():
        print(f"[WARN] File does not exist: {path}")
        return papers

    try:
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[WARN] Failed to parse line {i}, skipping")
                    continue

                title = obj.get("title") or obj.get("id") or f"paper_{i}"

                # Extract text from different possible fields
                text = ""

                # Try standard fields first
                if obj.get("text"):
                    text = obj["text"]
                elif obj.get("latex"):
                    text = obj["latex"]
                # Try messages field (for conversation-style data)
                elif obj.get("messages"):
                    messages = obj["messages"]
                    # Look for paper text in messages (usually in 'user' role)
                    for msg in messages:
                        content = msg.get("content", "")
                        # Paper text usually starts with title or ABSTRACT and is long
                        if len(content) > 1000 and (
                            "ABSTRACT" in content.upper()[:500] or
                            "INTRODUCTION" in content.upper()[:500] or
                            content.strip().startswith("Title:")
                        ):
                            text = content
                            break

                    # If no suitable content found, try the longest message
                    if not text and messages:
                        longest_msg = max(messages, key=lambda m: len(m.get("content", "")))
                        text = longest_msg.get("content", "")

                papers.append({
                    "id": obj.get("id"),
                    "title": title,
                    "text": text,
                    "original_path": f"{path}:{i}",
                    "rates": obj.get("rates"),
                    "decision": obj.get("decision"),
                })
    except Exception as e:
        print(f"[ERROR] Failed to load file {path}: {e}")
        return []

    return papers


def sample_papers(papers: List[Dict], ratio: float, seed: int) -> List[Dict]:
    """Randomly sample papers by ratio"""
    n = max(1, int(len(papers) * ratio))
    rnd = random.Random(seed)
    return rnd.sample(papers, min(n, len(papers)))


def generate_variants(paper: Dict, variant_funcs: Dict[str, callable], strict: bool = True) -> tuple[List[Dict], bool]:
    """
    Generate all variants for a paper, return list
    Each variant record contains: original title, variant name, variant text, etc.

    Args:
        paper: Paper data
        variant_funcs: Variant function mapping table
        strict: Strict mode, if True, return empty list if any variant fails

    Returns:
        (variants, success): List of variants and success flag
    """
    variants = []
    original_text = paper.get("text", "")
    all_success = True

    # Check if original text is valid
    if not original_text or not isinstance(original_text, str):
        print(f"[WARN] Paper '{paper.get('title', 'unknown')}' has empty or invalid original text, skipping")
        return [], False

    for variant_name, func in variant_funcs.items():
        variant_text = None
        success = False
        matched = False

        try:
            result = func(original_text)

            # Parse return value: could be (text, matched) or just text
            if isinstance(result, tuple) and len(result) == 2:
                variant_text, matched = result
            else:
                # Compatible with old version functions
                variant_text = result
                matched = True

            # Check if the generated variant is valid
            if variant_text is None:
                print(f"[WARN] Variant {variant_name} generated None ({paper['title']})")
            elif not isinstance(variant_text, str):
                print(f"[WARN] Variant {variant_name} generated wrong type ({paper['title']})")
                variant_text = None
            else:
                # Check if content was matched (except for original variant)
                if variant_name != "original" and not matched:
                    print(f"[WARN] Variant {variant_name} matched no content ({paper['title']}), paper may lack this section")
                    variant_text = None
                else:
                    # Check if variant text is too short (possible generation failure)
                    variant_text = variant_text.strip()
                    if len(variant_text) < 50 and variant_name != "original":
                        print(f"[WARN] Variant {variant_name} result too short ({paper['title']}), length={len(variant_text)}")
                        variant_text = None
                    else:
                        success = True

        except TypeError as e:
            print(f"[WARN] Type error generating variant {variant_name} ({paper['title']}): {e}")
        except AttributeError as e:
            print(f"[WARN] Attribute error generating variant {variant_name} ({paper['title']}): {e}")
        except Exception as e:
            print(f"[WARN] Failed to generate variant {variant_name} ({paper['title']}): {type(e).__name__}: {e}")

        if not success:
            all_success = False
            if strict:
                # In strict mode, any variant failure returns empty
                print(f"[INFO] Strict mode: Paper '{paper['title']}' discarded due to variant {variant_name} failure")
                return [], False
            else:
                # In lenient mode, skip failed variants
                continue

        variant_record = {
            "id": f"{paper.get('id')}_{variant_name}" if paper.get('id') else f"paper_{variant_name}",
            "title": f"{paper['title']} [{variant_name}]",
            "original_title": paper['title'],
            "variant_type": variant_name,
            "text": variant_text,
            "original_id": paper.get('id'),
            "original_path": paper.get('original_path'),
            "rates": paper.get('rates'),
            "decision": paper.get('decision'),
        }
        variants.append(variant_record)

    return variants, all_success


def save_papers_to_jsonl(papers: List[Dict], path: Path):
    """Save paper list to JSONL file"""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", encoding="utf-8") as f:
            for paper in papers:
                json.dump(paper, f, ensure_ascii=False)
                f.write("\n")
        print(f"[INFO] Saved {len(papers)} papers to {path}")
    except Exception as e:
        print(f"[ERROR] Failed to save file {path}: {e}")


def generate_variants_with_retry(
    sampled_papers: List[Dict],
    all_papers: List[Dict],
    variant_funcs: Dict[str, callable],
    target_count: int,
    seed: int,
    strict: bool = True,
    max_retry: int = MAX_RETRY_ATTEMPTS
) -> List[Dict]:
    """
    Generate variants, if strict mode fails then supplement with new papers

    Args:
        sampled_papers: Already sampled paper list
        all_papers: All available papers
        variant_funcs: Variant functions
        target_count: Target paper count
        seed: Random seed
        strict: Whether strict mode
        max_retry: Maximum retry attempts

    Returns:
        List of all generated variants
    """
    rnd = random.Random(seed)
    all_variants = []
    used_ids = set()  # Used paper IDs
    successful_papers = 0
    retry_count = 0

    # Mark already sampled papers
    for paper in sampled_papers:
        paper_id = paper.get('id') or paper.get('original_path')
        if paper_id:
            used_ids.add(paper_id)

    # Create candidate pool (unused papers)
    candidate_pool = [p for p in all_papers
                      if (p.get('id') or p.get('original_path')) not in used_ids]

    # Process already sampled papers first
    papers_to_process = list(sampled_papers)

    # Progress tracking
    total_to_process = len(sampled_papers)
    processed = 0

    while successful_papers < target_count and retry_count < max_retry:
        if not papers_to_process:
            # No more papers to process, supplement from candidate pool
            if not candidate_pool:
                print(f"[WARN] Candidate pool empty, cannot supplement. Current success: {successful_papers}/{target_count}")
                break

            # Randomly sample one to supplement
            new_paper = rnd.choice(candidate_pool)
            candidate_pool.remove(new_paper)
            papers_to_process.append(new_paper)
            retry_count += 1

        paper = papers_to_process.pop(0)
        paper_id = paper.get('id') or paper.get('original_path')

        processed += 1
        if processed % 100 == 0 or processed <= 10:
            print(f"[INFO] Progress: {processed}/{total_to_process} processed, {successful_papers} successful papers")

        variants, success = generate_variants(paper, variant_funcs, strict=strict)

        if strict and not success:
            # In strict mode failure, need to supplement
            continue

        if variants:
            all_variants.extend(variants)
            successful_papers += 1
            if paper_id:
                used_ids.add(paper_id)

    if successful_papers < target_count:
        print(f"[WARN] Finally only generated {successful_papers}/{target_count} papers' variants")

    return all_variants


def run_workflow(source_train: Path,
                 source_test: Path,
                 output_train: Path,
                 output_test: Path,
                 sample_ratio: float = SAMPLE_RATIO,
                 seed: int = SEED,
                 variant_funcs: Optional[Dict] = None,
                 strict_mode: bool = STRICT_MODE):
    """Main workflow"""

    random.seed(seed)

    if variant_funcs is None:
        variant_funcs = VARIANT_FUNCS

    print("[INFO] Starting dataset generation...")
    print(f"[INFO] Config: sample_ratio={sample_ratio}, seed={seed}, strict_mode={strict_mode}")
    print(f"[INFO] Variant types: {list(variant_funcs.keys())}")

    # Load original data
    print("\n[INFO] Loading original data...")
    train_papers = load_papers_from_jsonl(source_train)
    test_papers = load_papers_from_jsonl(source_test)

    if not train_papers and not test_papers:
        raise RuntimeError("Failed to load any paper data!")

    # Calculate target sample count
    target_train = max(1, int(len(train_papers) * sample_ratio))
    target_test = max(1, int(len(test_papers) * sample_ratio))

    # Sample papers
    print("\n[INFO] Sampling papers...")
    sampled_train = sample_papers(train_papers, sample_ratio, seed)
    sampled_test = sample_papers(test_papers, sample_ratio, seed + 1)

    print(f"[INFO] Train set: Total {len(train_papers)} papers, target sample {target_train} papers")
    print(f"[INFO] Test set: Total {len(test_papers)} papers, target sample {target_test} papers")

    # Generate variants (support failure supplementation)
    print("\n[INFO] Generating variants...")
    train_with_variants = generate_variants_with_retry(
        sampled_train, train_papers, variant_funcs,
        target_train, seed, strict=strict_mode
    )
    test_with_variants = generate_variants_with_retry(
        sampled_test, test_papers, variant_funcs,
        target_test, seed + 1, strict=strict_mode
    )

    print(f"[INFO] Train set total variants: {len(train_with_variants)}")
    print(f"[INFO] Test set total variants: {len(test_with_variants)}")

    # Save output
    print("\n[INFO] Saving datasets...")
    save_papers_to_jsonl(train_with_variants, output_train)
    save_papers_to_jsonl(test_with_variants, output_test)

    # Statistics
    actual_train_papers = len(train_with_variants) // len(variant_funcs) if train_with_variants else 0
    actual_test_papers = len(test_with_variants) // len(variant_funcs) if test_with_variants else 0

    print("\n[INFO] ========== Dataset Statistics ==========")
    print(f"Train set:")
    print(f"  - Target paper count: {target_train}")
    print(f"  - Actual success count: {actual_train_papers}")
    print(f"  - Variant type count: {len(variant_funcs)}")
    print(f"  - Total sample count: {len(train_with_variants)}")
    print(f"Test set:")
    print(f"  - Target paper count: {target_test}")
    print(f"  - Actual success count: {actual_test_papers}")
    print(f"  - Variant type count: {len(variant_funcs)}")
    print(f"  - Total sample count: {len(test_with_variants)}")
    print(f"==========================================\n")
    print("[INFO] Workflow completed!")


if __name__ == "__main__":
    run_workflow(
        SOURCE_TRAIN_JSONL,
        SOURCE_TEST_JSONL,
        OUTPUT_TRAIN_JSONL,
        OUTPUT_TEST_JSONL,
        SAMPLE_RATIO,
        SEED
    )

