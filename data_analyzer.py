# python
import json
import os
import csv
import re
import traceback
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")


class PaperReviewAnalyzer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data = []
        self.df = None

        base = os.path.splitext(os.path.basename(self.file_path))[0]
        self.output_dir = f"{base}_output"
        os.makedirs(self.output_dir, exist_ok=True)

        ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S_%f")
        self.log_file = os.path.join(self.output_dir, f"all_logs_{ts}.txt")

    def _append_log(self, content: str, prefix: str = "log") -> str:
        if isinstance(content, (list, tuple)):
            content = "\n".join(str(x) for x in content)
        ts = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{ts}] [{prefix}] {content}\n\n"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception:
            # best-effort: avoid raising in analysis
            pass
        return self.log_file

    def log(self, content, prefix: str = "log") -> str:
        return self._append_log(content, prefix)

    def load_data(self) -> bool:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        self.data.append(obj)
                    except Exception:
                        # ignore malformed lines but log them
                        self.log(f"Failed to parse line: {line[:200]}", "load_parse_error")
            self.log(f"Successfully loaded {len(self.data)} records", "load_data_success")
            return True
        except FileNotFoundError:
            self.log(f"File ` {self.file_path} ` not found", "load_data_error")
            return False
        except Exception as e:
            self.log(f"Error while loading file: {e}\n{traceback.format_exc()}", "load_data_exception")
            return False

    def create_dataframe(self) -> pd.DataFrame:
        records = []
        for item in self.data:
            paper_id = item.get("id", "")
            title = item.get("title", "")
            decision = item.get("decision", "")
            rates = item.get("rates", []) or []
            review_contexts = item.get("review_contexts", []) or []

            # Pair reviews and rates; if lengths mismatch, pair up to min length and
            # add any leftover as entries with missing counterpart.
            min_len = min(len(rates), len(review_contexts))
            for i in range(min_len):
                records.append({
                    "paper_id": paper_id,
                    "title": title,
                    "decision": decision,
                    "rating": rates[i],
                    "review_content": review_contexts[i],
                    "review_index": i
                })
            # leftover ratings
            if len(rates) > min_len:
                for i in range(min_len, len(rates)):
                    records.append({
                        "paper_id": paper_id,
                        "title": title,
                        "decision": decision,
                        "rating": rates[i],
                        "review_content": "",
                        "review_index": i
                    })
            # leftover review texts
            if len(review_contexts) > min_len:
                for i in range(min_len, len(review_contexts)):
                    records.append({
                        "paper_id": paper_id,
                        "title": title,
                        "decision": decision,
                        "rating": np.nan,
                        "review_content": review_contexts[i],
                        "review_index": i
                    })

        self.df = pd.DataFrame(records)
        # normalize rating to numeric where possible
        if "rating" in self.df.columns:
            self.df["rating"] = pd.to_numeric(self.df["rating"], errors="coerce")
        self.log(f"Created DataFrame: {0 if self.df is None else self.df.shape[0]} rows, {0 if self.df is None else self.df.shape[1]} columns", "create_dataframe")
        return self.df

    def basic_statistics(self):
        self.log("=" * 50, "basic_stats_sep")
        self.log("Basic Statistics", "basic_stats_title")
        self.log("=" * 50, "basic_stats_sep2")

        total_papers = len(self.data)
        total_reviews = 0 if self.df is None else len(self.df)
        avg_reviews = (total_reviews / total_papers) if total_papers > 0 else 0.0

        self.log(f"Total papers: {total_papers}", "basic_total_papers")
        self.log(f"Total review entries: {total_reviews}", "basic_total_reviews")
        self.log(f"Average reviews per paper: {avg_reviews:.2f}", "basic_avg_reviews")

        if self.df is None or self.df.empty:
            self.log("No review data available for statistics.", "basic_no_data")
            return

        # decision distribution at paper level
        decision_counts = self.df.groupby("paper_id")["decision"].first().value_counts()
        self.log("Decision distribution:", "basic_decision_title")
        for decision, count in decision_counts.items():
            self.log(f"{decision}: {count} papers", "basic_decision_item")

        # rating statistics
        if "rating" in self.df.columns and not self.df["rating"].dropna().empty:
            ratings = self.df["rating"].dropna()
            self.log("Rating statistics:", "basic_rating_title")
            self.log(f"Mean: {ratings.mean():.2f}", "basic_rating_mean")
            self.log(f"Median: {ratings.median():.2f}", "basic_rating_median")
            self.log(f"Std: {ratings.std():.2f}", "basic_rating_std")
            self.log(f"Min: {ratings.min()}", "basic_rating_min")
            self.log(f"Max: {ratings.max()}", "basic_rating_max")

            rating_distribution = ratings.value_counts().sort_index()
            self.log("Rating distribution:", "basic_rating_dist_title")
            for rating, count in rating_distribution.items():
                self.log(f"Rating {rating}: {count} times", "basic_rating_dist_item")
        else:
            self.log("No numeric ratings found.", "basic_no_ratings")

    def plot_rating_distribution(self):
        if self.df is None or self.df.empty:
            self.log("No data to plot.", "plot_no_data")
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # Histogram of ratings
        if "rating" in self.df.columns:
            axes[0, 0].hist(self.df["rating"].dropna(), bins=20, alpha=0.7, color="skyblue", edgecolor="black")
            axes[0, 0].set_xlabel("Rating")
            axes[0, 0].set_ylabel("Frequency")
            axes[0, 0].set_title("Review Rating Distribution")
            axes[0, 0].grid(True, alpha=0.3)
        else:
            axes[0, 0].text(0.5, 0.5, "No rating data", ha="center")

        # Ratings by final decision (boxplot)
        decision_ratings = []
        decisions = []
        for paper in self.data:
            rates = paper.get("rates", []) or []
            decision = paper.get("decision", "")
            for r in rates:
                try:
                    val = float(r)
                except Exception:
                    val = np.nan
                if not np.isnan(val):
                    decision_ratings.append(val)
                    decisions.append(decision)
        if decision_ratings:
            decision_df = pd.DataFrame({"rating": decision_ratings, "decision": decisions})
            sns.boxplot(data=decision_df, x="decision", y="rating", ax=axes[0, 1])
            axes[0, 1].set_title("Rating Distribution by Decision")
            axes[0, 1].set_xlabel("Final Decision")
            axes[0, 1].set_ylabel("Rating")
        else:
            axes[0, 1].text(0.5, 0.5, "No decision-rated data", ha="center")

        # Rating pie chart
        if "rating" in self.df.columns and not self.df["rating"].dropna().empty:
            rating_counts = self.df["rating"].dropna().value_counts()
            axes[1, 0].pie(rating_counts.values, labels=rating_counts.index, autopct="%1.1f%%")
            axes[1, 0].set_title("Rating Distribution Pie Chart")
        else:
            axes[1, 0].text(0.5, 0.5, "No rating data", ha="center")

        # Decision pie chart
        decision_counts = self.df.groupby("paper_id")["decision"].first().value_counts()
        if not decision_counts.empty:
            axes[1, 1].pie(decision_counts.values, labels=decision_counts.index, autopct="%1.1f%%")
            axes[1, 1].set_title("Decision Distribution Pie Chart")
        else:
            axes[1, 1].text(0.5, 0.5, "No decision data", ha="center")

        plt.tight_layout()
        fig_path = os.path.join(self.output_dir, f"rating_distribution_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
        fig.savefig(fig_path, bbox_inches="tight")
        plt.close(fig)
        self.log(f"Saved plot to: {fig_path}", "plot_rating_saved")

    def analyze_review_content(self):
        if self.df is None or self.df.empty:
            self.log("No review content to analyze.", "content_no_data")
            return

        self.log("=" * 50, "content_sep")
        self.log("Review Content Analysis", "content_title")
        self.log("=" * 50, "content_sep2")

        review_lengths = self.df["review_content"].astype(str).str.len()
        self.log(f"Average review length: {review_lengths.mean():.2f} characters", "content_avg_len")
        self.log(f"Review length std: {review_lengths.std():.2f} characters", "content_len_std")
        self.log(f"Shortest review: {int(review_lengths.min())} characters", "content_min_len")
        self.log(f"Longest review: {int(review_lengths.max())} characters", "content_max_len")

        all_reviews = " ".join(self.df["review_content"].astype(str)).lower()
        words = re.findall(r"\b[a-z]{4,}\b", all_reviews)
        word_freq = Counter(words)

        self.log("Top 20 most common words:", "content_top20_title")
        for word, count in word_freq.most_common(20):
            self.log(f"{word}: {count}", "content_top20_item")

        top_words = dict(word_freq.most_common(10))
        if top_words:
            fig = plt.figure(figsize=(10, 5))
            plt.bar(list(top_words.keys()), list(top_words.values()), color="lightcoral")
            plt.title("Top 10 Words in Review Content")
            plt.xlabel("Word")
            plt.ylabel("Frequency")
            plt.xticks(rotation=45)
            plt.tight_layout()
            fig_path = os.path.join(self.output_dir, f"top_words_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
            fig.savefig(fig_path, bbox_inches="tight")
            plt.close(fig)
            self.log(f"Saved plot to: {fig_path}", "content_top_words_saved")

    def analyze_decision_patterns(self):
        self.log("=" * 50, "decision_sep")
        self.log("Decision Patterns Analysis", "decision_title")
        self.log("=" * 50, "decision_sep2")

        paper_stats = []
        for paper in self.data:
            rates = paper.get("rates", []) or []
            numeric = []
            for r in rates:
                try:
                    numeric.append(float(r))
                except Exception:
                    pass
            if not numeric:
                continue
            pid = paper.get("id", "")
            d = paper.get("decision", "")
            paper_stats.append({
                "paper_id": pid,
                "decision": d,
                "avg_rating": float(np.mean(numeric)),
                "rating_std": float(np.std(numeric, ddof=0)) if len(numeric) > 0 else 0.0,
                "min_rating": float(np.min(numeric)),
                "max_rating": float(np.max(numeric)),
                "num_reviews": len(numeric)
            })

        if not paper_stats:
            self.log("No valid paper data found", "decision_no_data")
            return

        stats_df = pd.DataFrame(paper_stats)
        self.log("Rating statistics grouped by decision:", "decision_stats_title")
        decision_stats = stats_df.groupby("decision").agg(
            avg_rating_mean=("avg_rating", "mean"),
            avg_rating_std=("avg_rating", "std"),
            avg_num_reviews=("num_reviews", "mean"),
            paper_count=("paper_id", "count")
        ).round(3)
        self.log(decision_stats.to_string(), "decision_grouped_stats")

        fig, axes = plt.subplots(2, 2, figsize=(14, 11))
        sns.boxplot(data=stats_df, x="decision", y="avg_rating", ax=axes[0, 0])
        axes[0, 0].set_title("Decision vs Average Rating")
        sns.boxplot(data=stats_df, x="decision", y="rating_std", ax=axes[0, 1])
        axes[0, 1].set_title("Decision vs Rating Std")
        sns.boxplot(data=stats_df, x="decision", y="num_reviews", ax=axes[1, 0])
        axes[1, 0].set_title("Decision vs Number of Reviews")
        stats_df["rating_range"] = stats_df["max_rating"] - stats_df["min_rating"]
        sns.boxplot(data=stats_df, x="decision", y="rating_range", ax=axes[1, 1])
        axes[1, 1].set_title("Decision vs Rating Range")

        plt.tight_layout()
        fig_path = os.path.join(self.output_dir, f"decision_patterns_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
        fig.savefig(fig_path, bbox_inches="tight")
        plt.close(fig)
        self.log(f"Saved plot to: {fig_path}", "decision_patterns_saved")

    def analyze_review_structure(self):
        if self.df is None or self.df.empty:
            self.log("No review content to analyze structure.", "structure_no_data")
            return

        self.log("=" * 50, "structure_sep")
        self.log("Review Structure Analysis", "structure_title")
        self.log("=" * 50, "structure_sep2")

        section_patterns = {
            "summary": r"\bsummary\b|\bsummary:\b|#+\s*summary",
            "soundness": r"\bsoundness\b|\bsoundness:\b|#+\s*soundness",
            "presentation": r"\bpresentation\b|\bpresentation:\b|#+\s*presentation",
            "contribution": r"\bcontribution\b|\bcontribution:\b|#+\s*contribution",
            "strengths": r"\bstrengths\b|\bstrengths:\b|#+\s*strengths",
            "weaknesses": r"\bweaknesses\b|\bweaknesses:\b|#+\s*weaknesses",
            "questions": r"\bquestions\b|\bquestions:\b|#+\s*questions",
            "rating": r"\brating\b|\brating:\b|#+\s*rating",
            "confidence": r"\bconfidence\b|\bconfidence:\b|#+\s*confidence",
        }

        section_counts = {k: 0 for k in section_patterns.keys()}

        for review in self.df["review_content"].astype(str):
            text = review.lower()
            for section, pattern in section_patterns.items():
                if re.search(pattern, text):
                    section_counts[section] += 1

        self.log("Frequency of sections in reviews:", "structure_freq_title")
        for section, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.df)) * 100 if len(self.df) > 0 else 0.0
            self.log(f"{section.capitalize()}: {count} ({percentage:.1f}%)", "structure_freq_item")

        fig = plt.figure(figsize=(12, 6))
        sections = list(section_counts.keys())
        counts = list(section_counts.values())
        plt.bar(sections, counts, color="lightgreen")
        plt.title("Review Structure Analysis")
        plt.xlabel("Section")
        plt.ylabel("Occurrences")
        plt.xticks(rotation=45)
        plt.tight_layout()
        fig_path = os.path.join(self.output_dir, f"review_structure_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
        fig.savefig(fig_path, bbox_inches="tight")
        plt.close(fig)
        self.log(f"Saved plot to: {fig_path}", "structure_plot_saved")

    def paper_level_analysis(self):
        self.log("=" * 50, "paper_sep")
        self.log("Paper-level Analysis", "paper_title")
        self.log("=" * 50, "paper_sep2")

        paper_info = []
        grouped = defaultdict(list)
        for row in (self.df.to_dict(orient="records") if self.df is not None else []):
            pid = row.get("paper_id", "")
            grouped[pid].append(row)

        for pid, rows in grouped.items():
            title = rows[0].get("title", "")
            decision = rows[0].get("decision", "")
            ratings = [r.get("rating") for r in rows if r.get("rating") is not None and not np.isnan(r.get("rating"))]
            num_reviews = len(ratings)
            avg_rating = float(np.mean(ratings)) if ratings else np.nan
            paper_info.append({
                "paper_id": pid,
                "title": title,
                "decision": decision,
                "num_reviews": num_reviews,
                "avg_rating": avg_rating
            })

        paper_df = pd.DataFrame(paper_info)
        self.log("Paper statistics summary:", "paper_summary_title")
        if not paper_df.empty:
            self.log(f"Average reviews per paper: {paper_df['num_reviews'].mean():.2f}", "paper_avg_reviews")
            title_lengths = paper_df["title"].astype(str).str.len()
            self.log(f"Average title length: {title_lengths.mean():.2f} characters", "paper_title_len")

            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            paper_df["avg_rating"].dropna().hist(ax=axes[0], bins=20, alpha=0.7, color="lightblue", edgecolor="black")
            axes[0].set_xlabel("Average Rating")
            axes[0].set_ylabel("Number of Papers")
            axes[0].set_title("Distribution of Paper Average Ratings")
            paper_df["num_reviews"].hist(ax=axes[1], bins=10, alpha=0.7, color="lightyellow", edgecolor="black")
            axes[1].set_xlabel("Number of Reviews")
            axes[1].set_ylabel("Number of Papers")
            axes[1].set_title("Distribution of Reviews per Paper")
            plt.tight_layout()
            fig_path = os.path.join(self.output_dir, f"paper_level_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
            fig.savefig(fig_path, bbox_inches="tight")
            plt.close(fig)
            self.log(f"Saved plot to: {fig_path}", "paper_level_plot_saved")
        else:
            self.log("No paper-level data available.", "paper_no_data")

    def correlation_analysis(self):
        self.log("=" * 50, "corr_sep")
        self.log("Correlation Analysis", "corr_title")
        self.log("=" * 50, "corr_sep2")

        paper_correlations = []
        for paper in self.data:
            rates = paper.get("rates", []) or []
            numeric = []
            for r in rates:
                try:
                    numeric.append(float(r))
                except Exception:
                    pass
            if len(numeric) < 2:
                continue
            pid = paper.get("id", "")
            d = paper.get("decision", "")
            paper_correlations.append({
                "paper_id": pid,
                "decision": d,
                "rating_variance": float(np.var(numeric, ddof=0)),
                "rating_range": float(np.max(numeric) - np.min(numeric)),
                "num_reviews": len(numeric)
            })

        if not paper_correlations:
            self.log("Not enough papers with multiple ratings for correlation analysis.", "corr_not_enough")
            return

        corr_df = pd.DataFrame(paper_correlations)
        decision_variance = corr_df.groupby("decision")["rating_variance"].mean()
        self.log("Relationship between rating variance and decisions:", "corr_variance_title")
        for decision, variance in decision_variance.items():
            self.log(f"{decision}: mean variance {variance:.4f}", "corr_variance_item")

        numeric_columns = ["rating_variance", "rating_range", "num_reviews"]
        correlation_matrix = corr_df[numeric_columns].corr()
        self.log("Numeric variables correlation matrix:", "corr_matrix_title")
        self.log(correlation_matrix.round(3).to_string(), "corr_matrix")

        fig = plt.figure(figsize=(7, 6))
        sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", center=0, square=True, fmt=".3f")
        plt.title("Correlation Heatmap of Numeric Variables")
        plt.tight_layout()
        fig_path = os.path.join(self.output_dir, f"correlation_heatmap_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S_%f')}.png")
        fig.savefig(fig_path, bbox_inches="tight")
        plt.close(fig)
        self.log(f"Saved plot to: {fig_path}", "corr_heatmap_saved")

    def export_results(self):
        if self.df is None:
            self.log("No data to export.", "export_no_data")
            return

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"processed_reviews_{timestamp}.csv"
        csv_path = os.path.join(self.output_dir, csv_filename)

        try:
            self.df.to_csv(csv_path, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
        except Exception:
            try:
                self.df.to_csv(csv_path, index=False, encoding="utf-8", quoting=csv.QUOTE_NONE, escapechar="\\")
            except Exception as e2:
                self.log(f"Failed to save CSV: {e2}\n{traceback.format_exc()}", "export_csv_failed")
                return

        self.log(f"Processed data saved to: {csv_path}", "export_csv_saved")

        summary = [
            "Academic Paper Review Dataset Export Summary",
            "=" * 50,
            f"Export time: {pd.Timestamp.now()}",
            f"Total papers: {len(self.data)}",
            f"Total review entries: {len(self.df)}",
        ]
        self.log("\n".join(summary), "export_summary")

    def run_complete_analysis(self) -> pd.DataFrame:
        if not self.load_data():
            return None

        self.create_dataframe()

        self.log("Starting analysis of academic paper review dataset...", "run_start")
        self.log("=" * 60, "run_sep")

        self.basic_statistics()
        self.plot_rating_distribution()
        self.analyze_review_content()
        self.analyze_decision_patterns()
        self.analyze_review_structure()
        self.paper_level_analysis()
        self.correlation_analysis()

        self.export_results()

        self.log("=" * 60, "run_end_sep")
        self.log("Analysis complete!", "run_complete")
        if self.df is not None:
            self.log(f"DataFrame shape: {self.df.shape}", "run_df_shape")
            self.log(f"Columns: {list(self.df.columns)}", "run_columns")

        return self.df
