#!/usr/bin/env python3
"""
Advanced analysis and plotting for attack evaluation results.

Input schema (expected per record):
- base_paper_id
- attack_type
- attack_position
- section_found (optional)
- evaluation.avg_rating
- evaluation.paper_decision
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def find_latest_attack_results(results_dir: Path) -> Path:
    files = sorted(
        results_dir.glob("attack_results_*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        raise FileNotFoundError(f"No attack result files found in: {results_dir}")
    non_incremental = [f for f in files if "incremental" not in f.name]
    return non_incremental[0] if non_incremental else files[0]


def load_records(jsonl_path: Path) -> pd.DataFrame:
    rows = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            evaluation = record.get("evaluation", {}) if isinstance(record.get("evaluation"), dict) else {}
            rows.append(
                {
                    "base_paper_id": str(record.get("base_paper_id", "")),
                    "paper_id": str(record.get("paper_id", "")),
                    "variant_type": str(record.get("variant_type", "")),
                    "attack_type": str(record.get("attack_type", "none")),
                    "attack_position": str(record.get("attack_position", "none")),
                    "section_found": bool(record.get("section_found", True)),
                    "dataset_split": str(record.get("dataset_split", "")),
                    "rating": evaluation.get("avg_rating"),
                    "decision": evaluation.get("paper_decision"),
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("No valid rows loaded from JSONL.")
    df = df[df["rating"].notnull()].copy()
    return df


def decision_to_binary(decision: str) -> float:
    if not isinstance(decision, str):
        return np.nan
    lowered = decision.lower()
    if "accept" in lowered:
        return 1.0
    if "reject" in lowered:
        return 0.0
    return np.nan


def build_attack_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = df[(df["attack_type"] == "none") | (df["attack_position"] == "none") | (df["variant_type"] == "original")].copy()
    base = (
        base.sort_values(["base_paper_id"])
        .drop_duplicates(subset=["base_paper_id"], keep="first")
        [["base_paper_id", "rating", "decision"]]
        .rename(columns={"rating": "base_rating", "decision": "base_decision"})
    )

    attack_df = df[df["attack_type"] != "none"].copy()
    attack_df = attack_df.merge(base, on="base_paper_id", how="left")
    attack_df = attack_df[attack_df["base_rating"].notnull()].copy()
    attack_df["rating_delta"] = attack_df["rating"] - attack_df["base_rating"]
    attack_df["accept"] = attack_df["decision"].map(decision_to_binary)
    attack_df["base_accept"] = attack_df["base_decision"].map(decision_to_binary)
    attack_df["decision_pair"] = attack_df["base_decision"].fillna("NA") + " -> " + attack_df["decision"].fillna("NA")
    attack_df["delta_sign"] = np.where(
        attack_df["rating_delta"] > 0,
        "up",
        np.where(attack_df["rating_delta"] < 0, "down", "same"),
    )
    return base, attack_df


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _render_table_image(df: pd.DataFrame, title: str, out_path: Path, font_size: int = 9) -> None:
    display_df = df.copy()
    for col in display_df.columns:
        if pd.api.types.is_float_dtype(display_df[col]):
            display_df[col] = display_df[col].map(lambda x: f"{x:.4f}")

    fig_h = max(3.5, 0.45 * (len(display_df) + 1))
    fig, ax = plt.subplots(figsize=(14, fig_h))
    ax.axis("off")
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1, 1.4)
    plt.title(title, pad=16)
    plt.tight_layout()
    plt.savefig(out_path, dpi=220)
    plt.close()


def _render_top_cases_bar(attack_df: pd.DataFrame, outdir: Path) -> None:
    top_pos = attack_df.nlargest(20, "rating_delta").copy()
    top_pos["label"] = top_pos["base_paper_id"] + " | " + top_pos["attack_type"] + "@" + top_pos["attack_position"]
    top_pos = top_pos.sort_values("rating_delta", ascending=True)

    plt.figure(figsize=(14, 9))
    plt.barh(top_pos["label"], top_pos["rating_delta"], color="#ef5350")
    plt.axvline(0, color="black", linestyle="--", linewidth=1)
    plt.title("Top 20 Positive Delta Cases")
    plt.xlabel("Rating Delta")
    plt.tight_layout()
    plt.savefig(outdir / "top_positive_cases_barh.png")
    plt.close()

    top_neg = attack_df.nsmallest(20, "rating_delta").copy()
    top_neg["label"] = top_neg["base_paper_id"] + " | " + top_neg["attack_type"] + "@" + top_neg["attack_position"]
    top_neg = top_neg.sort_values("rating_delta", ascending=True)

    plt.figure(figsize=(14, 9))
    plt.barh(top_neg["label"], top_neg["rating_delta"], color="#66bb6a")
    plt.axvline(0, color="black", linestyle="--", linewidth=1)
    plt.title("Top 20 Negative Delta Cases")
    plt.xlabel("Rating Delta")
    plt.tight_layout()
    plt.savefig(outdir / "top_negative_cases_barh.png")
    plt.close()


def save_summary_tables(base_df: pd.DataFrame, attack_df: pd.DataFrame, outdir: Path) -> dict:
    base_count = base_df["base_paper_id"].nunique()

    type_summary = (
        attack_df.groupby("attack_type")
        .agg(
            count=("rating", "size"),
            mean_rating=("rating", "mean"),
            mean_delta=("rating_delta", "mean"),
            median_delta=("rating_delta", "median"),
            std_delta=("rating_delta", "std"),
            positive_rate=("delta_sign", lambda s: (s == "up").mean()),
            negative_rate=("delta_sign", lambda s: (s == "down").mean()),
            same_rate=("delta_sign", lambda s: (s == "same").mean()),
            accept_rate=("accept", "mean"),
        )
        .reset_index()
        .sort_values("mean_delta", ascending=False)
    )
    type_summary["coverage_vs_base"] = type_summary["count"] / base_count
    _render_table_image(type_summary, "Attack Type Summary", outdir / "attack_type_summary_table.png")

    position_summary = (
        attack_df.groupby("attack_position")
        .agg(
            count=("rating", "size"),
            mean_rating=("rating", "mean"),
            mean_delta=("rating_delta", "mean"),
            median_delta=("rating_delta", "median"),
            std_delta=("rating_delta", "std"),
            positive_rate=("delta_sign", lambda s: (s == "up").mean()),
            negative_rate=("delta_sign", lambda s: (s == "down").mean()),
            same_rate=("delta_sign", lambda s: (s == "same").mean()),
            accept_rate=("accept", "mean"),
        )
        .reset_index()
        .sort_values("mean_delta", ascending=False)
    )
    _render_table_image(position_summary, "Attack Position Summary", outdir / "attack_position_summary_table.png")

    tp_delta = attack_df.pivot_table(
        index="attack_type",
        columns="attack_position",
        values="rating_delta",
        aggfunc="mean",
    ).sort_index()

    tp_accept = attack_df.pivot_table(
        index="attack_type",
        columns="attack_position",
        values="accept",
        aggfunc="mean",
    ).sort_index()

    transition = (
        attack_df.groupby(["attack_type", "decision_pair"])
        .size()
        .rename("count")
        .reset_index()
    )
    transition["ratio"] = transition["count"] / transition.groupby("attack_type")["count"].transform("sum")
    _render_table_image(
        transition.sort_values(["attack_type", "ratio"], ascending=[True, False]),
        "Decision Transition Summary (by Attack Type)",
        outdir / "decision_transition_summary_table.png",
        font_size=8,
    )
    _render_top_cases_bar(attack_df, outdir)

    per_paper = (
        attack_df.groupby("base_paper_id")
        .agg(
            mean_delta=("rating_delta", "mean"),
            std_delta=("rating_delta", "std"),
            max_delta=("rating_delta", "max"),
            min_delta=("rating_delta", "min"),
        )
        .reset_index()
    )
    _render_table_image(
        per_paper.sort_values("mean_delta", ascending=False).head(20),
        "Top 20 Papers by Mean Attack Delta",
        outdir / "top20_papers_mean_delta_table.png",
    )

    return {
        "type_summary": type_summary,
        "position_summary": position_summary,
        "tp_delta": tp_delta,
        "tp_accept": tp_accept,
        "transition": transition,
        "per_paper": per_paper,
    }


def plot_charts(base_df: pd.DataFrame, attack_df: pd.DataFrame, outdir: Path) -> None:
    sns.set_theme(style="whitegrid")

    # 1. Baseline vs Attack rating distribution
    plt.figure(figsize=(10, 6))
    sns.kdeplot(base_df["base_rating"], label="baseline (none/original)", fill=True, alpha=0.25)
    sns.kdeplot(attack_df["rating"], label="attacked", fill=True, alpha=0.25)
    plt.title("Rating Distribution: Baseline vs Attacked")
    plt.xlabel("Rating")
    plt.ylabel("Density")
    plt.legend()
    plt.tight_layout()
    plt.savefig(outdir / "rating_distribution_baseline_vs_attack.png")
    plt.close()

    # 2. Delta by attack type
    type_order = (
        attack_df.groupby("attack_type")["rating_delta"]
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=attack_df, x="attack_type", y="rating_delta", order=type_order)
    plt.axhline(0, color="red", linestyle="--", linewidth=1)
    plt.title("Rating Delta by Attack Type")
    plt.xlabel("Attack Type")
    plt.ylabel("Rating Delta (attack - baseline)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(outdir / "box_rating_delta_by_attack_type.png")
    plt.close()

    # 3. Delta by attack position
    pos_order = (
        attack_df.groupby("attack_position")["rating_delta"]
        .mean()
        .sort_values(ascending=False)
        .index
        .tolist()
    )
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=attack_df, x="attack_position", y="rating_delta", order=pos_order)
    plt.axhline(0, color="red", linestyle="--", linewidth=1)
    plt.title("Rating Delta by Attack Position")
    plt.xlabel("Attack Position")
    plt.ylabel("Rating Delta (attack - baseline)")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(outdir / "box_rating_delta_by_attack_position.png")
    plt.close()

    # 4. Heatmap: type x position mean delta
    delta_pivot = attack_df.pivot_table(
        index="attack_type", columns="attack_position", values="rating_delta", aggfunc="mean"
    )
    plt.figure(figsize=(10, 6))
    sns.heatmap(delta_pivot, annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Mean Rating Delta: Attack Type x Position")
    plt.tight_layout()
    plt.savefig(outdir / "heatmap_mean_delta_type_position.png")
    plt.close()

    # 5. Heatmap: type x position accept rate
    accept_pivot = attack_df.pivot_table(
        index="attack_type", columns="attack_position", values="accept", aggfunc="mean"
    )
    plt.figure(figsize=(10, 6))
    sns.heatmap(accept_pivot, annot=True, fmt=".2f", cmap="YlGnBu", vmin=0, vmax=1)
    plt.title("Accept Rate: Attack Type x Position")
    plt.tight_layout()
    plt.savefig(outdir / "heatmap_accept_rate_type_position.png")
    plt.close()

    # 6. Positive/down/same stacked by attack type
    sign_counts = (
        attack_df.groupby(["attack_type", "delta_sign"])
        .size()
        .unstack(fill_value=0)
        .reindex(type_order)
    )
    sign_ratio = sign_counts.div(sign_counts.sum(axis=1), axis=0)
    sign_ratio = sign_ratio.reindex(columns=["up", "same", "down"], fill_value=0)
    sign_ratio.plot(
        kind="bar",
        stacked=True,
        figsize=(10, 6),
        color=["#ef5350", "#ffca28", "#66bb6a"],
    )
    plt.title("Delta Sign Ratio by Attack Type")
    plt.xlabel("Attack Type")
    plt.ylabel("Ratio")
    plt.legend(title="delta_sign")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(outdir / "stacked_delta_sign_by_attack_type.png")
    plt.close()

    # 7. Decision transitions by attack type
    trans = (
        attack_df.groupby(["attack_type", "decision_pair"])
        .size()
        .unstack(fill_value=0)
        .reindex(type_order)
    )
    trans_ratio = trans.div(trans.sum(axis=1), axis=0)
    trans_ratio.plot(kind="bar", stacked=True, figsize=(12, 6), colormap="tab20")
    plt.title("Decision Transition Ratio by Attack Type")
    plt.xlabel("Attack Type")
    plt.ylabel("Ratio")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(outdir / "stacked_decision_transition_by_attack_type.png")
    plt.close()

    # 8. Section found vs not-found
    if attack_df["section_found"].nunique() > 1:
        plt.figure(figsize=(8, 6))
        sns.boxplot(data=attack_df, x="section_found", y="rating_delta")
        plt.axhline(0, color="red", linestyle="--", linewidth=1)
        plt.title("Rating Delta by section_found")
        plt.xlabel("Section Found")
        plt.ylabel("Rating Delta")
        plt.tight_layout()
        plt.savefig(outdir / "box_rating_delta_section_found.png")
        plt.close()

    # 9. Accept rate bar by type and position
    type_accept = attack_df.groupby("attack_type")["accept"].mean().reindex(type_order)
    plt.figure(figsize=(10, 6))
    type_accept.plot(kind="bar", color="#42a5f5")
    plt.ylim(0, 1)
    plt.title("Accept Rate by Attack Type")
    plt.xlabel("Attack Type")
    plt.ylabel("Accept Rate")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(outdir / "bar_accept_rate_by_attack_type.png")
    plt.close()

    pos_accept = attack_df.groupby("attack_position")["accept"].mean().reindex(pos_order)
    plt.figure(figsize=(10, 6))
    pos_accept.plot(kind="bar", color="#26a69a")
    plt.ylim(0, 1)
    plt.title("Accept Rate by Attack Position")
    plt.xlabel("Attack Position")
    plt.ylabel("Accept Rate")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(outdir / "bar_accept_rate_by_attack_position.png")
    plt.close()

    # 10. Scatter: baseline score vs delta
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=attack_df, x="base_rating", y="rating_delta", hue="attack_type", alpha=0.35, s=25)
    plt.axhline(0, color="red", linestyle="--", linewidth=1)
    plt.title("Baseline Score vs Rating Delta")
    plt.xlabel("Baseline Rating")
    plt.ylabel("Rating Delta")
    plt.tight_layout()
    plt.savefig(outdir / "scatter_baseline_vs_delta.png")
    plt.close()

    # 11. Per-paper mean delta histogram
    per_paper = attack_df.groupby("base_paper_id")["rating_delta"].mean()
    plt.figure(figsize=(9, 6))
    sns.histplot(per_paper, bins=30, kde=True)
    plt.axvline(0, color="red", linestyle="--", linewidth=1)
    plt.title("Histogram: Mean Attack Delta per Paper")
    plt.xlabel("Mean Delta per Paper")
    plt.tight_layout()
    plt.savefig(outdir / "hist_mean_delta_per_paper.png")
    plt.close()

    # 12. Count heatmap to verify balanced design
    count_pivot = attack_df.pivot_table(
        index="attack_type", columns="attack_position", values="base_paper_id", aggfunc="count"
    )
    plt.figure(figsize=(10, 6))
    sns.heatmap(count_pivot, annot=True, fmt=".0f", cmap="Blues")
    plt.title("Sample Count: Attack Type x Position")
    plt.tight_layout()
    plt.savefig(outdir / "heatmap_count_type_position.png")
    plt.close()


def write_readme(input_file: Path, base_df: pd.DataFrame, attack_df: pd.DataFrame, outdir: Path) -> None:
    lines = [
        "# Attack Advanced Analysis Output",
        "",
        f"- Input file: `{input_file}`",
        f"- Base papers: `{base_df['base_paper_id'].nunique()}`",
        f"- Attack records: `{len(attack_df)}`",
        "",
        "## Figures",
        "- `attack_type_summary_table.png`",
        "- `attack_position_summary_table.png`",
        "- `decision_transition_summary_table.png`",
        "- `top20_papers_mean_delta_table.png`",
        "- `top_positive_cases_barh.png`",
        "- `top_negative_cases_barh.png`",
        "- `rating_distribution_baseline_vs_attack.png`",
        "- `box_rating_delta_by_attack_type.png`",
        "- `box_rating_delta_by_attack_position.png`",
        "- `heatmap_mean_delta_type_position.png`",
        "- `heatmap_accept_rate_type_position.png`",
        "- `stacked_delta_sign_by_attack_type.png`",
        "- `stacked_decision_transition_by_attack_type.png`",
        "- `bar_accept_rate_by_attack_type.png`",
        "- `bar_accept_rate_by_attack_position.png`",
        "- `scatter_baseline_vs_delta.png`",
        "- `hist_mean_delta_per_paper.png`",
        "- `heatmap_count_type_position.png`",
    ]
    if attack_df["section_found"].nunique() > 1:
        lines.append("- `box_rating_delta_section_found.png`")

    (outdir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def write_plot_explanation_doc(input_file: Path, base_df: pd.DataFrame, attack_df: pd.DataFrame, outdir: Path) -> None:
    base_n = base_df["base_paper_id"].nunique()
    attack_n = len(attack_df)
    lines = [
        "# Attack 图表说明与计算逻辑",
        "",
        f"- 输入文件: `{input_file}`",
        f"- baseline 论文数: `{base_n}`",
        f"- attack 样本数: `{attack_n}`",
        "",
        "## 核心派生字段",
        "- `base_rating`: 同一 `base_paper_id` 的 baseline（`attack_type=none` 或 `original`）评分。",
        "- `rating_delta = rating - base_rating`。",
        "- `accept`: `paper_decision` 包含 `accept` 记为 1，包含 `reject` 记为 0。",
        "- `decision_pair = base_decision -> decision`。",
        "- `delta_sign`: `rating_delta>0` 为 `up`，`<0` 为 `down`，`=0` 为 `same`。",
        "",
        "## 每张图说明",
        "1. `attack_type_summary_table.png`: 按 `attack_type` 聚合统计表。",
        "计算逻辑: `groupby(attack_type)` 后统计 count/mean_rating/mean_delta/median_delta/std_delta/positive_rate/negative_rate/same_rate/accept_rate。",
        "2. `attack_position_summary_table.png`: 按 `attack_position` 聚合统计表。",
        "计算逻辑: 与 attack_type 同理，只是分组键换成 `attack_position`。",
        "3. `decision_transition_summary_table.png`: 决策迁移统计表。",
        "计算逻辑: `groupby(attack_type, decision_pair).size()` 得 count，再在每个 attack_type 内归一化得 ratio。",
        "4. `top20_papers_mean_delta_table.png`: 每篇论文平均攻击效应 Top20。",
        "计算逻辑: `groupby(base_paper_id)` 统计 mean_delta/std_delta/max_delta/min_delta，按 mean_delta 降序取前20。",
        "5. `top_positive_cases_barh.png`: 单样本升分最大的 20 个 case（横向条形图）。",
        "计算逻辑: `nlargest(20, rating_delta)`，标签为 `base_paper_id | attack_type@attack_position`。",
        "6. `top_negative_cases_barh.png`: 单样本降分最大的 20 个 case（横向条形图）。",
        "计算逻辑: `nsmallest(20, rating_delta)`。",
        "7. `rating_distribution_baseline_vs_attack.png`: baseline 与攻击样本评分核密度对比。",
        "计算逻辑: 分别对 `base_rating` 与 `rating` 做 KDE。",
        "8. `box_rating_delta_by_attack_type.png`: 各攻击类型的 `rating_delta` 箱线图。",
        "计算逻辑: x=attack_type, y=rating_delta；红虚线 y=0 表示“无变化”。",
        "9. `box_rating_delta_by_attack_position.png`: 各攻击位置的 `rating_delta` 箱线图。",
        "计算逻辑: x=attack_position, y=rating_delta；红虚线 y=0。",
        "10. `heatmap_mean_delta_type_position.png`: 类型×位置 平均升降分热力图。",
        "计算逻辑: `pivot_table(index=attack_type, columns=attack_position, values=rating_delta, aggfunc=mean)`。",
        "11. `heatmap_accept_rate_type_position.png`: 类型×位置 Accept 率热力图。",
        "计算逻辑: 同上，只是 values=accept，aggfunc=mean。",
        "12. `stacked_delta_sign_by_attack_type.png`: 各类型 up/same/down 比例堆叠图。",
        "计算逻辑: 按 `(attack_type, delta_sign)` 计数后行归一化。",
        "13. `stacked_decision_transition_by_attack_type.png`: 各类型决策迁移比例堆叠图。",
        "计算逻辑: 按 `(attack_type, decision_pair)` 计数后行归一化。",
        "14. `bar_accept_rate_by_attack_type.png`: 各攻击类型 Accept 率柱状图。",
        "计算逻辑: `groupby(attack_type)['accept'].mean()`。",
        "15. `bar_accept_rate_by_attack_position.png`: 各攻击位置 Accept 率柱状图。",
        "计算逻辑: `groupby(attack_position)['accept'].mean()`。",
        "16. `scatter_baseline_vs_delta.png`: baseline 分数与分数变化散点图（按 attack_type 着色）。",
        "计算逻辑: 每条攻击样本一个点，x=base_rating, y=rating_delta。",
        "17. `hist_mean_delta_per_paper.png`: 每篇论文平均攻击效应分布直方图。",
        "计算逻辑: 先按 `base_paper_id` 求 mean(rating_delta)，再直方图 + KDE。",
        "18. `heatmap_count_type_position.png`: 类型×位置样本数热力图（检查数据平衡性）。",
        "计算逻辑: `pivot_table(..., values=base_paper_id, aggfunc=count)`。",
        "19. `box_rating_delta_section_found.png`（若存在）: 章节命中与未命中时的 `rating_delta` 对比。",
        "计算逻辑: x=section_found, y=rating_delta 的箱线图。",
        "",
        "## 关于横轴文本",
        "- 所有条形图/箱线图类图表都强制 `xticks(rotation=0)`，即横向显示标签。",
    ]
    (outdir / "PLOT_EXPLANATION_CN.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    project_root = Path(__file__).resolve().parent.parent
    default_results_dir = project_root / "evaluation_results_attack"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_output_dir = project_root / "analysis_output" / f"attack_{timestamp}"

    parser = argparse.ArgumentParser(description="Advanced plotting for attack evaluation results.")
    parser.add_argument("--input", type=Path, default=None, help="Attack results JSONL file")
    parser.add_argument("--results-dir", type=Path, default=default_results_dir, help="Directory to auto-find input")
    parser.add_argument("--output-dir", type=Path, default=default_output_dir, help="Output directory")
    args = parser.parse_args()

    input_file = args.input if args.input else find_latest_attack_results(args.results_dir)
    output_dir = args.output_dir
    ensure_dir(output_dir)

    df = load_records(input_file)
    base_df, attack_df = build_attack_dataframe(df)
    if attack_df.empty:
        raise ValueError("No attack rows found (attack_type != none).")

    save_summary_tables(base_df, attack_df, output_dir)
    plot_charts(base_df, attack_df, output_dir)
    write_readme(input_file, base_df, attack_df, output_dir)
    write_plot_explanation_doc(input_file, base_df, attack_df, output_dir)

    print(f"Analysis complete. Output directory: {output_dir}")
    print(f"Input file: {input_file}")
    print(f"Base papers: {base_df['base_paper_id'].nunique()}, attack records: {len(attack_df)}")


if __name__ == "__main__":
    main()
