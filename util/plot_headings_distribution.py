"""
Plot heading count distribution from util/headings_counts.json

Produces two images saved under util/:
 - headings_counts_hist.png  : histogram of heading counts (log scale option)
 - headings_top30.png        : horizontal bar chart of top 30 headings (counts)

Usage:
    python util\plot_headings_distribution.py --input util/headings_counts.json --outdir util --top 30

"""
import json
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import math


def load_counts(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # data expected as list of [heading, count]
    counts = []
    labels = []
    for item in data:
        if not isinstance(item, list) or len(item) < 2:
            continue
        label, cnt = item[0], item[1]
        # skip null/None labels? keep as 'UNKNOWN' optionally
        if label is None:
            label = 'UNKNOWN'
        try:
            cnt = int(cnt)
        except Exception:
            continue
        labels.append(label)
        counts.append(cnt)
    return labels, counts


def plot_hist(counts, outpath, bins=50):
    plt.figure(figsize=(8,5))
    plt.hist(counts, bins=bins, color='#2c7fb8', edgecolor='black')
    plt.xlabel('Heading count')
    plt.ylabel('Number of headings')
    plt.title('Distribution of heading counts')
    plt.grid(axis='y', alpha=0.4)
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def plot_hist_log(counts, outpath, bins=50):
    plt.figure(figsize=(8,5))
    # plot histogram with log y
    plt.hist(counts, bins=bins, color='#41ab5d', edgecolor='black')
    plt.yscale('log')
    plt.xlabel('Heading count')
    plt.ylabel('Number of headings (log scale)')
    plt.title('Heading counts distribution (log y)')
    plt.grid(axis='y', alpha=0.3, which='both')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def plot_top_labels(labels, counts, outpath, top=30):
    # sort by counts desc
    pairs = [(lab, c) for lab, c in zip(labels, counts)]
    pairs.sort(key=lambda x: x[1], reverse=True)
    top_pairs = pairs[:top]
    labs = [p[0] for p in top_pairs][::-1]  # reverse for horizontal bar
    vals = [p[1] for p in top_pairs][::-1]
    plt.figure(figsize=(10, max(4, 0.3*len(labs))))
    bars = plt.barh(range(len(labs)), vals, color='#fb6a4a')
    plt.yticks(range(len(labs)), labs)
    plt.xlabel('Count')
    plt.title(f'Top {len(labs)} headings by count')
    plt.tight_layout()
    plt.savefig(outpath, dpi=150)
    plt.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='headings_counts.json')
    parser.add_argument('--outdir', default='pictures')
    parser.add_argument('--top', type=int, default=300)
    parser.add_argument('--bins', type=int, default=50)
    args = parser.parse_args()

    inp = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    if not inp.exists():
        print(f"Input file {inp} not found")
        return

    labels, counts = load_counts(inp)
    if not counts:
        print("No counts found in input")
        return

    hist_path = outdir / 'headings_counts_hist.png'
    hist_log_path = outdir / 'headings_counts_hist_logy.png'
    top_path = outdir / f'headings_top{args.top}.png'

    plot_hist(counts, hist_path, bins=args.bins)
    plot_hist_log(counts, hist_log_path, bins=args.bins)
    plot_top_labels(labels, counts, top_path, top=args.top)

    total = len(counts)
    unique = sum(1 for c in counts if c==1)
    print(f"Wrote: {hist_path}, {hist_log_path}, {top_path}")
    print(f"Samples: {total}, single-count headings: {unique}")

if __name__ == '__main__':
    main()

