# python
import re
import json
import math
import random
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import matplotlib.pyplot as plt

from ai_researcher import CycleReviewer


# ========== 配置区域（可在命令行或外部修改） ==========
SAMPLE_SIZE = 500
BATCH_SIZE = 8
SEED = 12345
OUTPUT_JSON = Path("workflow_results.json")
FIG_DIR = Path("figs")
# 支持的变体，后续可在 VARIANT_FUNCS 中增加新项
VARIANT_NAMES = ["original", "no_abstract"]
# 训练/测试数据文件（jsonl）
TRAIN_JSONL = Path("util/train_extracted_sample.jsonl")
TEST_JSONL = Path("util/test_extracted_sample.jsonl")
# =====================================================


def load_papers_from_jsonl(path: Path) -> List[Dict]:
    papers: List[Dict] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                title = obj.get("title") or obj.get("id") or f"{path.stem}_{i}"
                text = obj.get("text") or obj.get("latex") or ""
                # Use 'text' as the canonical field (remove reliance on 'latex')
                papers.append({
                    "id": obj.get("id"),
                    "title": title,
                    "text": text,
                    "path": f"{path}:{i}",
                    "rates": obj.get("rates"),
                    "decision": obj.get("decision"),
                })
    except FileNotFoundError:
        return []
    return papers


# 简单的文本清洗器：移除 ABSTRACT 段或 CONCLUSION 段
RE_ABSTRACT = re.compile(r"(?:^|\n)\s*(?:ABSTRACT|Abstract|abstract)\s*[:\-]?\s*(.+?)(?=\n\s*\d|\n[A-Z]{2,}|$)", re.S)
RE_CONCLUSION = re.compile(r"(?:^|\n)\s*(?:CONCLUSION|Conclusions|Conclusion|conclusion|concluding remarks)\s*[:\-]?\s*(.+?)(?=\n\s*\d|\n[A-Z]{2,}|$)", re.S)


def remove_abstract(text: str) -> str:
    return RE_ABSTRACT.sub("\n", text)


def remove_conclusion(text: str) -> str:
    return RE_CONCLUSION.sub("\n", text)


VARIANT_FUNCS = {
    "original": lambda s: s,
    "no_abstract": remove_abstract,
}


def sample_papers(papers: List[Dict], n: int, seed: int) -> List[Dict]:
    if len(papers) <= n:
        return list(papers)
    rnd = random.Random(seed)
    return rnd.sample(papers, n)


def chunk_iterable(iterable: List, size: int):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def safe_evaluate(reviewer: CycleReviewer, text_list: List[str]) -> List[Optional[Dict]]:
    """
    调用 reviewer.evaluate，捕获异常并保证返回同长度的列表（用 None 填充失败项）。
    """
    try:
        res = reviewer.evaluate(text_list)
        if res is None:
            return [None] * len(text_list)
        # 有时返回长度可能不全，补齐
        if len(res) < len(text_list):
            res = list(res) + [None] * (len(text_list) - len(res))
        return res
    except Exception:
        return [None] * len(text_list)


def extract_score(review: Optional[Dict]) -> Optional[float]:
    """
    从审稿结果中提取数值评分（优先 'avg_rating'），如果缺失返回 None。
    """
    if not review or not isinstance(review, dict):
        return None
    for key in ("avg_rating", "score", "rating"):
        v = review.get(key)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except Exception:
                continue
    return None


def evaluate_variants_for_sampled(papers: List[Dict],
                                  reviewer: CycleReviewer,
                                  variant_names: List[str],
                                  batch_size: int,
                                  seed: int) -> Dict:
    """
    对传入论文列表逐篇处理：先评估原文作为基线，再对每个变体批量评估，返回结果字典：
    {
      title: {
        "path": ...,
        "scores": { variant_name: score_or_None },
      }, ...
    }
    """
    results = {}
    # 先对所有原文评估（分块），使用 'text' 字段
    titles = [p["title"] for p in papers]
    texts = [p["text"] for p in papers]
    all_orig_reviews = []
    for chunk in chunk_iterable(texts, batch_size):
        all_orig_reviews.extend(safe_evaluate(reviewer, chunk))
    # 提取原始分数
    orig_scores = [extract_score(r) for r in all_orig_reviews]
    for p, sc in zip(papers, orig_scores):
        results[p["title"]] = {"path": p.get("path"), "scores": {"original": sc}}
    # 对每个变体类型（除 original）批量评估
    for vname in variant_names:
        if vname == "original":
            continue
        # 生成变体文本列表
        var_text_list = [VARIANT_FUNCS[vname](p["text"]) for p in papers]
        var_reviews = []
        for chunk in chunk_iterable(var_text_list, batch_size):
            var_reviews.extend(safe_evaluate(reviewer, chunk))
        var_scores = [extract_score(r) for r in var_reviews]
        for p, sc in zip(papers, var_scores):
            results[p["title"]]["scores"][vname] = sc
    return results


def compute_diffs(results: Dict, variant_names: List[str]) -> Dict[str, List[float]]:
    """
    从每篇论文的 scores 中计算每个变体相对于原文的差值列表（variant - original），忽略任一侧为 None 的项。
    返回 dict: { variant_name: [diffs...] }
    """
    diffs = {v: [] for v in variant_names if v != "original"}
    for title, meta in results.items():
        scores = meta.get("scores", {})
        base = scores.get("original")
        if base is None:
            continue
        for v in diffs.keys():
            sc = scores.get(v)
            if sc is None:
                continue
            diffs[v].append(sc - base)
    return diffs


def plot_histograms(diffs: Dict[str, List[float]], dataset_name: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for vname, values in diffs.items():
        if not values:
            print(f"[WARN] {dataset_name} - {vname} 没有有效评分，跳过绘图。")
            continue
        arr = np.array(values)
        # 选择合适的 bin 数量（自动）
        bins = min(60, max(10, int(math.sqrt(len(arr)) * 2)))
        plt.figure(figsize=(7, 4.5))
        plt.hist(arr, bins=bins, color="#2b8cbe", edgecolor="#08306b")
        plt.axvline(0, color="k", linestyle="--", linewidth=1)
        plt.xlabel("变体分数 - 原始分数")
        plt.ylabel("论文数量")
        plt.title(f"{dataset_name}: {vname} (n={len(arr)})")
        plt.grid(axis="y", alpha=0.3)
        fname = out_dir / f"{dataset_name}_{vname}.png"
        plt.tight_layout()
        plt.savefig(fname)
        plt.close()
        print(f"[INFO] Saved {fname}")


def run_workflow(train_jsonl: Path,
                 test_jsonl: Path,
                 sample_size: int = SAMPLE_SIZE,
                 batch_size: int = BATCH_SIZE,
                 seed: int = SEED,
                 variant_names: Optional[List[str]] = None,
                 output_json: Path = OUTPUT_JSON,
                 fig_dir: Path = FIG_DIR):
    random.seed(seed)
    np.random.seed(seed)

    if variant_names is None:
        variant_names = VARIANT_NAMES

    # 加载数据
    train_papers = load_papers_from_jsonl(train_jsonl)
    test_papers = load_papers_from_jsonl(test_jsonl)
    if not train_papers or not test_papers:
        raise RuntimeError("训练集或测试集目录中未找到可用论文。")

    sampled_train = sample_papers(train_papers, sample_size, seed)
    sampled_test = sample_papers(test_papers, sample_size, seed + 1)

    print(f"[INFO] Train: found {len(train_papers)} papers, sampled {len(sampled_train)}")
    print(f"[INFO] Test: found {len(test_papers)} papers, sampled {len(sampled_test)}")

    reviewer = CycleReviewer(model_size="8B")

    # 评估训练集
    print("[INFO] Evaluating train samples...")
    train_results = evaluate_variants_for_sampled(sampled_train, reviewer, variant_names, batch_size, seed)
    # 评估测试集
    print("[INFO] Evaluating test samples...")
    test_results = evaluate_variants_for_sampled(sampled_test, reviewer, variant_names, batch_size, seed + 1)

    # 计算差值并绘图
    train_diffs = compute_diffs(train_results, variant_names)
    test_diffs = compute_diffs(test_results, variant_names)

    plot_histograms(train_diffs, "train", fig_dir)
    plot_histograms(test_diffs, "test", fig_dir)

    # 合并并写出 JSON 结果（包括原始评分与差值统计）
    summary = {
        "meta": {
            "sample_size": sample_size,
            "batch_size": batch_size,
            "seed": seed,
            "variant_names": variant_names,
        },
        "train": {
            "per_paper": train_results,
            "diffs": {k: v for k, v in train_diffs.items()},
        },
        "test": {
            "per_paper": test_results,
            "diffs": {k: v for k, v in test_diffs.items()},
        },
    }
    output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] Workflow finished. Results saved to {output_json} and figures to {fig_dir}/")


if __name__ == "__main__":
    run_workflow(TRAIN_JSONL, TEST_JSONL)