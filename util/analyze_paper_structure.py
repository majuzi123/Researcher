"""
Conservative extractor for top-level section headings from messages[1]['content'] in JSONL files.

Usage:
    python util\analyze_paper_structure.py --files train.jsonl test.jsonl --output util\new_headings_counts --top 50

The extractor focuses on top-level headings only (e.g. "ABSTRACT", "1 INTRODUCTION", "4 CONCLUSION AND DISCUSSION").
"""
import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
import csv


def extract_headings(text: str):
    """Return a list of top-level heading strings from text (conservative).

    Returns normalized uppercase headings, e.g. 'ABSTRACT', '1 INTRODUCTION', 'CONCLUSION'.
    """
    if not text:
        return []

    # normalize newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [ln.strip() for ln in text.split('\n') if ln.strip()]

    def clean_tail_nums(s: str) -> str:
        # remove trailing comma-number fragments and trailing standalone numbers
        s = re.sub(r'(?:,\s*\d+)+$', '', s)
        s = re.sub(r'\s+\d+$', '', s)
        return s.strip()

    def looks_like_decimal_sequence(s: str) -> bool:
        return bool(re.match(r'^[0-9]+(\.[0-9]+)?([ \t,]+[0-9]+(\.[0-9]+)?)+$', s))

    def is_pure_numeric_punct(s: str) -> bool:
        return bool(re.match(r'^[\d\s.,:/;\-()\[\]<>]+$', s))

    def top_numbered_heading(s: str):
        # integer-leading headings like "4 CONCLUSION..." but NOT "1.1"
        m = re.match(r'^\s*(\d+)\s+(?!\d+\.)\s*(.+)$', s)
        if not m:
            return None
        num = m.group(1)
        title = clean_tail_nums(m.group(2).strip())
        if not re.search(r'[A-Za-z]', title):
            return None
        words = [w for w in re.split(r'\s+', title) if w]
        if len(words) == 0:
            return None
        if len(words) == 1 and len(words[0]) < 3:
            return None
        digits = len(re.findall(r'\d', title))
        if digits / max(1, len(title)) > 0.6:
            return None
        title_norm = re.sub(r'\s{2,}', ' ', title).upper()
        return f"{num} {title_norm}"

    def top_unnumbered_heading(s: str):
        s0 = clean_tail_nums(s)
        if not re.search(r'[A-Za-z]', s0):
            return None
        if is_pure_numeric_punct(s0) or looks_like_decimal_sequence(s0):
            return None
        words = [w for w in re.split(r"\s+", s0) if w]
        if len(words) == 1:
            if len(words[0]) >= 4:
                return words[0].upper()
            return None
        if len(words) >= 2 and any(len(w) >= 3 for w in words):
            digits = len(re.findall(r'\d', s0))
            if digits / max(1, len(s0)) > 0.6:
                return None
            return re.sub(r'\s{2,}', ' ', s0).upper()
        return None

    # section keywords to accept
    SECTION_KEYWORDS = [
        'abstract', 'introduction', 'related work', 'related works', 'related', 'background', 'preliminary', 'preliminaries',
        'method', 'methods', 'methodology', 'approach', 'approaches', 'experiments', 'experiment', 'results', 'evaluation',
        'discussion', 'conclusion', 'conclusions', 'conclusion and discussion', 'future work', 'limitations', 'acknowledgement',
        'acknowledgements', 'references', 'appendix', 'ethics statement', 'reproducibility statement'
    ]

    CANONICAL_MAP = {
        'RELATED WORKS': 'RELATED WORK',
        'RELATED': 'RELATED WORK',
        'METHODS': 'METHOD',
        'METHODOLOGY': 'METHOD',
        'EXPERIMENT': 'EXPERIMENTS',
        'CONCLUSIONS': 'CONCLUSION',
        'ACKNOWLEDGEMENTS': 'ACKNOWLEDGEMENT',
        'PRELIMINARIES': 'PRELIMINARY'
    }

    # canonical whitelist - only keep these as final headings
    ALLOWED_SECTIONS = {
        'ABSTRACT', 'INTRODUCTION', 'RELATED WORK', 'BACKGROUND', 'PRELIMINARY', 'METHOD', 'EXPERIMENTS', 'RESULTS',
        'EVALUATION', 'DISCUSSION', 'CONCLUSION', 'FUTURE WORK', 'LIMITATIONS', 'ACKNOWLEDGEMENT', 'REFERENCES', 'APPENDIX',
        'ETHICS STATEMENT', 'REPRODUCIBILITY STATEMENT', 'REPRODUCIBILITY'
    }

    def contains_section_keyword(s: str) -> bool:
        sl = s.lower()
        for kw in SECTION_KEYWORDS:
            if kw in sl:
                return True
        return False

    def canonicalize(s: str):
        s2 = re.sub(r'\s{2,}', ' ', s).strip()
        mnum = re.match(r'^(\d+)\s+(.+)$', s2)
        if mnum:
            num = mnum.group(1)
            body = mnum.group(2).upper()
            # map variants
            if body in CANONICAL_MAP:
                cand = CANONICAL_MAP[body]
            else:
                # try match any keyword inside
                matched = None
                for kw in SECTION_KEYWORDS:
                    if kw in body.lower():
                        matched = kw.upper()
                        break
                cand = matched if matched else body
            if cand in ALLOWED_SECTIONS:
                return f"{num} {cand}"
            return None
        up = s2.upper()
        if up in CANONICAL_MAP:
            up = CANONICAL_MAP[up]
        else:
            matched = None
            for kw in SECTION_KEYWORDS:
                if kw in up.lower():
                    matched = kw.upper()
                    break
            if matched:
                up = matched
        if up in ALLOWED_SECTIONS:
            return up
        return None

    out = []
    seen = set()

    # LaTeX \section{...}
    for m in re.finditer(r"\\section\*?\{([^}]+)\}", text):
        candidate = clean_tail_nums(m.group(1).strip())
        h = top_unnumbered_heading(candidate)
        if not h:
            continue
        if not contains_section_keyword(h):
            continue
        h = canonicalize(h)
        if h not in seen:
            seen.add(h)
            out.append(h)

    # Markdown level-1 headers
    for m in re.finditer(r'(?m)^\s{0,3}#\s*(.+?)\s*$', text):
        candidate = clean_tail_nums(m.group(1).strip())
        h = top_unnumbered_heading(candidate)
        if not h:
            continue
        if not contains_section_keyword(h):
            continue
        h = canonicalize(h)
        if h not in seen:
            seen.add(h)
            out.append(h)

    # scan lines
    for ln in lines:
        if len(ln) < 2:
            continue
        if is_pure_numeric_punct(ln):
            continue
        if looks_like_decimal_sequence(ln):
            continue
        if re.match(r'^\s*\d+\.\d+', ln):
            continue

        hnum = top_numbered_heading(ln)
        if hnum:
            if contains_section_keyword(hnum):
                hnum = canonicalize(hnum)
                if hnum not in seen:
                    seen.add(hnum)
                    out.append(hnum)
                    continue
        hun = top_unnumbered_heading(ln)
        if hun and hun not in seen:
            if not contains_section_keyword(hun):
                continue
            hun = canonicalize(hun)
            if hun not in seen:
                seen.add(hun)
                out.append(hun)
    return out


def process_files(file_paths):
    total_counter = Counter()
    per_file = defaultdict(Counter)
    processed = 0
    skipped = 0

    for fp in file_paths:
        p = Path(fp)
        if not p.exists():
            print(f"Warning: {fp} not found, skipping.")
            continue
        with p.open('r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    skipped += 1
                    continue
                messages = None
                if isinstance(obj, dict) and 'messages' in obj:
                    messages = obj['messages']
                elif isinstance(obj, list):
                    messages = obj
                else:
                    for v in obj.values():
                        if isinstance(v, list) and len(v) > 1 and isinstance(v[0], dict) and 'role' in v[0]:
                            messages = v
                            break
                if not messages or not isinstance(messages, list) or len(messages) < 2:
                    skipped += 1
                    continue
                m1 = messages[1]
                if isinstance(m1, dict) and 'content' in m1:
                    content = m1['content']
                elif isinstance(m1, str):
                    content = m1
                else:
                    skipped += 1
                    continue
                headings = extract_headings(content)
                if headings:
                    for h in headings:
                        total_counter[h] += 1
                        per_file[fp][h] += 1
                processed += 1
    return total_counter, per_file, processed, skipped


def save_results(counter, out_prefix="headings_counts"):
    with open(out_prefix + ".json", 'w', encoding='utf-8') as jf:
        json.dump(counter.most_common(), jf, ensure_ascii=False, indent=2)
    with open(out_prefix + ".csv", 'w', newline='', encoding='utf-8') as cf:
        writer = csv.writer(cf, quoting=csv.QUOTE_MINIMAL, escapechar='\\')
        writer.writerow(['heading', 'count'])
        for h, c in counter.most_common():
            writer.writerow([h, c])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and count top-level headings from JSONL files (messages[1][\'content\']).')
    parser.add_argument('--files', nargs='+', default=['../train.jsonl', '../test.jsonl'], help='List of JSONL files to process')
    parser.add_argument('--output', default='headings_counts', help='Output prefix for JSON/CSV files (no extension)')
    parser.add_argument('--top', type=int, default=100, help='Print top-N headings')
    args = parser.parse_args()

    total_counter, per_file, processed, skipped = process_files(args.files)

    print(f"Processed {processed} entries, skipped {skipped} lines that did not match expected structure.")
    print(f"Unique headings found: {len(total_counter)}")
    print("Top headings:")
    for h, c in total_counter.most_common(args.top):
        print(f"{c:6d}  {h}")

    save_results(total_counter, args.output)
    print(f"Results saved to {args.output}.json and {args.output}.csv")
