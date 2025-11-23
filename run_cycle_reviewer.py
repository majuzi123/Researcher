"""
A clean, runnable script version of Tutorial 2:
Using CycleReviewer to review scientific papers.
"""

import json
import sys
from ai_researcher import CycleReviewer


# ===========================================================
# Utility Functions
# ===========================================================

def load_papers(json_path: str):
    """Load paper JSON file."""
    print(f"[INFO] Loading papers from {json_path} ...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"[INFO] Loaded {len(papers)} papers.")
        return papers
    except Exception as e:
        print(f"[ERROR] Failed to load JSON file: {e}")
        sys.exit(1)


def print_paper_summary(paper):
    """Print title and basic statistics."""
    print("\n================= PAPER SUMMARY =================")
    print(f"Title: {paper['title']}")
    print(f"Abstract length: {len(paper['abstract'])} characters")
    # print(f"LaTeX length: {len(paper['latex'])} characters")
    print("=================================================\n")


def run_review(model_size: str, papers):
    """Initialize reviewer, run evaluation."""
    print(f"[INFO] Initializing CycleReviewer model: {model_size}")
    reviewer = CycleReviewer(model_size=model_size)

    latex_list = [p["latex"] for p in papers]

    print("[INFO] Reviewing papers ... (this may take time)")
    review_results = reviewer.evaluate(latex_list)

    print("[INFO] Review completed.")
    return review_results


def print_review_summary(papers, reviews):
    """Print rating summary for each paper."""
    print("\n================= REVIEW SUMMARY =================\n")

    for idx, r in enumerate(reviews):
        if r is None:
            print(f"[WARNING] Paper {idx} returned no review.")
            continue

        print(f"Title: {papers[idx]['title']}")
        print(f"Average Rating: {r['avg_rating']:.2f} / 10")
        print(f"Decision: {r['paper_decision']}")
        print(f"Reviewers: {len(r['rating'])}")

        print("\nRatings:")
        for i, rating in enumerate(r["rating"]):
            print(f"  Reviewer {i + 1}: {rating}")

        print("-" * 40)


def print_strengths_and_weaknesses(review):
    """Print strengths and weaknesses of the final paper in the list."""
    print("\n================= KEY STRENGTHS =================")
    for i, s in enumerate(review["strength"]):
        short = s if len(s) <= 500 else s[:500] + "..."
        print(f"\nReviewer {i+1}:\n{short}")

    print("\n================= KEY WEAKNESSES =================")
    for i, w in enumerate(review["weaknesses"]):
        short = w if len(w) <= 500 else w[:500] + "..."
        print(f"\nReviewer {i+1}:\n{short}")


def print_meta_review(review):
    """Print meta review."""
    print("\n================= META REVIEW =================")
    print(review["meta_review"])

    print("\n--- justification_for_why_not_higher_score ---")
    print(review.get("justification_for_why_not_higher_score", ""))

    print("\n--- justification_for_why_not_lower_score ---")
    print(review.get("justification_for_why_not_lower_score", ""))


# ===========================================================
# Main Script
# ===========================================================

def main():
    # 1. Load paper
    papers = load_papers("Tutorial/demo_data.json")
    print_paper_summary(papers[0])

    # 2. Run CycleReviewer
    reviews = run_review(model_size="8B", papers=papers)

    # 3. Print summary
    print_review_summary(papers, reviews)

    # 4. Inspect the last review in detail
    last_review = next((r for r in reversed(reviews) if r is not None), None)
    if last_review:
        print_strengths_and_weaknesses(last_review)
        print_meta_review(last_review)


if __name__ == "__main__":
    main()
