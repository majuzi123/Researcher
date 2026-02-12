import argparse
import json
import os
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import rankdata, wilcoxon


def holm_adjust(pvals: List[float]) -> List[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    adjusted = np.empty(m, dtype=float)
    running_max = 0.0
    for i, idx in enumerate(order):
        adj = (m - i) * pvals[idx]
        running_max = max(running_max, adj)
        adjusted[idx] = min(1.0, running_max)
    return adjusted.tolist()


def bh_adjust(pvals: List[float]) -> List[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    adjusted_sorted = np.empty(m, dtype=float)
    for i, idx in enumerate(order, start=1):
        adjusted_sorted[i - 1] = pvals[idx] * m / i
    for i in range(m - 2, -1, -1):
        adjusted_sorted[i] = min(adjusted_sorted[i], adjusted_sorted[i + 1])
    adjusted = np.empty(m, dtype=float)
    for i, idx in enumerate(order):
        adjusted[idx] = min(1.0, adjusted_sorted[i])
    return adjusted.tolist()


def rank_biserial_from_diff(diff: np.ndarray) -> float:
    non_zero = diff[diff != 0]
    if non_zero.size == 0:
        return 0.0
    abs_ranks = rankdata(np.abs(non_zero), method="average")
    w_pos = abs_ranks[non_zero > 0].sum()
    w_neg = abs_ranks[non_zero < 0].sum()
    denom = w_pos + w_neg
    if denom == 0:
        return 0.0
    return float((w_pos - w_neg) / denom)


def load_dataframe(jsonl_path: str) -> pd.DataFrame:
    rows: List[Dict] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            evaluation = r.get("evaluation") if isinstance(r.get("evaluation"), dict) else {}
            rows.append(
                {
                    "base_paper_id": r.get("base_paper_id"),
                    "variant_type": r.get("variant_type"),
                    "rating": evaluation.get("avg_rating"),
                }
            )
    df = pd.DataFrame(rows)
    return df[df["rating"].notnull()].copy()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Wilcoxon signed-rank test: each variant vs original (paired by base_paper_id)."
    )
    parser.add_argument(
        "--jsonl-path",
        default="../evaluation_results/evaluation_results_20260212_054243.jsonl",
        help="Input evaluation JSONL path.",
    )
    parser.add_argument(
        "--outdir",
        default="../analysis_output/evaluted_results",
        help="Output directory for CSV/TXT results.",
    )
    parser.add_argument(
        "--alternative",
        default="two-sided",
        choices=["two-sided", "greater", "less"],
        help="Alternative hypothesis for scipy.stats.wilcoxon.",
    )
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    df = load_dataframe(args.jsonl_path)

    pivot = df.pivot_table(index="base_paper_id", columns="variant_type", values="rating")
    if "original" not in pivot.columns:
        raise ValueError("No 'original' variant found in data.")

    variants = [v for v in pivot.columns if v != "original"]
    results = []

    for vt in variants:
        pair = pivot[["original", vt]].dropna()
        n_pairs = int(pair.shape[0])
        if n_pairs == 0:
            continue

        diff = (pair[vt] - pair["original"]).to_numpy(dtype=float)
        non_zero = diff[diff != 0]
        n_nonzero = int(non_zero.size)
        median_diff = float(np.median(diff))
        mean_diff = float(np.mean(diff))
        rbc = rank_biserial_from_diff(diff)

        if n_nonzero == 0:
            stat = np.nan
            p_value = 1.0
            note = "all differences are zero"
        else:
            test = wilcoxon(
                pair[vt].to_numpy(dtype=float),
                pair["original"].to_numpy(dtype=float),
                alternative=args.alternative,
                zero_method="wilcox",
            )
            stat = float(test.statistic)
            p_value = float(test.pvalue)
            note = ""

        results.append(
            {
                "variant_type": vt,
                "n_pairs": n_pairs,
                "n_nonzero": n_nonzero,
                "median_diff_variant_minus_original": median_diff,
                "mean_diff_variant_minus_original": mean_diff,
                "rank_biserial_correlation": rbc,
                "wilcoxon_statistic": stat,
                "p_value_raw": p_value,
                "note": note,
            }
        )

    if not results:
        raise ValueError("No valid variant pairs found for Wilcoxon test.")

    pvals = [r["p_value_raw"] for r in results]
    p_holm = holm_adjust(pvals)
    p_bh = bh_adjust(pvals)
    for i, r in enumerate(results):
        r["p_value_holm"] = p_holm[i]
        r["p_value_bh_fdr"] = p_bh[i]

    result_df = pd.DataFrame(results).sort_values("p_value_raw", ascending=True)

    csv_path = os.path.join(args.outdir, "wilcoxon_variant_vs_original.csv")
    txt_path = os.path.join(args.outdir, "wilcoxon_variant_vs_original_summary.txt")
    result_df.to_csv(csv_path, index=False)

    lines = [
        "Wilcoxon Signed-Rank Test: variant vs original",
        f"input_jsonl: {args.jsonl_path}",
        f"alternative: {args.alternative}",
        f"num_variants_tested: {len(result_df)}",
        "",
        "Columns:",
        "- n_pairs: number of paired papers with both original and variant ratings",
        "- n_nonzero: number of non-zero differences used by Wilcoxon",
        "- rank_biserial_correlation: effect size (positive means variant tends to score higher)",
        "- p_value_holm / p_value_bh_fdr: multiple-testing corrected p-values",
        "",
    ]
    lines.extend(result_df.to_string(index=False).splitlines())
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Saved Wilcoxon results to {csv_path}")
    print(f"Saved summary to {txt_path}")


if __name__ == "__main__":
    main()
