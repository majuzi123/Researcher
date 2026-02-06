# Paper Evaluation and Analysis Pipeline

This directory contains scripts for batch evaluation of paper variants and comprehensive analysis of the results.

## 📚 Documentation

- 🚀 **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - Quick reference guide (Start here!)
- 📘 **[BATCH_EVALUATION_FIX.md](./BATCH_EVALUATION_FIX.md)** - Latest fixes and improvements
- 📗 **[DATA_FLOW_GUIDE.md](./DATA_FLOW_GUIDE.md)** - Complete data flow and field documentation
- 📕 **[README_SCRIPTS.md](./README_SCRIPTS.md)** - Script documentation index
- 💻 **[example_query_results.py](./example_query_results.py)** - Example code for querying results

## Overview

1. **`batch_evaluate_papers.py`** - Samples and evaluates 100 base papers (each with all variants)
2. **`analyze_evaluation_results.py`** - Performs statistical analysis and generates visualizations

## Prerequisites

```bash
pip install pandas numpy matplotlib seaborn scipy tqdm
```

## Usage

### Step 1: Batch Evaluation

Evaluates a sample of 100 papers (80 from train, 20 from test) using CycleReviewer:

```bash
cd D:\Mike\PycharmProjects\Researcher
python scripts/batch_evaluate_papers.py
```

**Configuration** (in `batch_evaluate_papers.py`):
- `SAMPLE_SIZE = 100` - Total papers to evaluate
- `TRAIN_RATIO = 0.8` - Ratio of train vs test papers
- `MODEL_SIZE = "8B"` - CycleReviewer model size
- `SEED = 42` - Random seed for reproducibility

**Output**:
- `evaluation_results/evaluation_results_YYYYMMDD_HHMMSS.jsonl` - Detailed results
- `evaluation_results/evaluation_summary_YYYYMMDD_HHMMSS.json` - Summary statistics

### Step 2: Analysis

Analyzes the evaluation results and generates comprehensive statistics and visualizations:

```bash
python scripts/analyze_evaluation_results.py
```

**Output Directory**: `analysis_output/YYYYMMDD_HHMMSS/`

**Generated Files**:

#### Statistics Files:
- `overall_statistics.json` - Overall statistics across all papers
- `variant_statistics.csv` - Statistics grouped by variant type
- `rating_range_statistics.json` - Analysis by rating ranges
- `original_vs_variants.json` - Comparison between original and variant papers
- `processed_data.csv` - Full processed dataset in CSV format
- `analysis_report.txt` - Detailed text report

#### Visualizations:
- `rating_distribution.png` - Histogram of rating distribution
- `ratings_by_variant_boxplot.png` - Box plot of ratings by variant
- `ratings_by_variant_violin.png` - Violin plot of ratings by variant
- `decision_distribution.png` - Pie chart of paper decisions
- `aspect_ratings.png` - Bar chart of average aspect ratings
- `variant_decision_heatmap.png` - Heatmap of variant types vs decisions
- `correlation_heatmap.png` - Correlation matrix of evaluation aspects
- `text_length_vs_rating.png` - Scatter plot of text length vs rating

## Analysis Features

### 1. Overall Statistics
- Rating statistics (mean, median, std, min, max, quartiles)
- Aspect ratings (originality, quality, clarity, significance)
- Decision distribution
- Variant type distribution

### 2. Variant Type Analysis
- Per-variant statistics
- Accept/reject rates by variant
- Average ratings by variant
- Aspect scores by variant

### 3. Rating Range Analysis
Papers grouped into ranges:
- Poor (0-3)
- Fair (3-5)
- Good (5-7)
- Excellent (7-10)

Statistics for each range:
- Count and percentage
- Variant distribution
- Average aspect scores

### 4. Original vs Variants Comparison
- Statistical comparison (t-test)
- Accept rate comparison
- Aspect rating comparison
- Significance testing

### 5. Visualizations
- Distribution plots
- Comparative analysis
- Correlation analysis
- Trend analysis

## Example Workflow

```bash
# 1. Generate variant dataset (already done)
python scripts/generate_variant_dataset.py

# 2. Evaluate sample of papers
python scripts/batch_evaluate_papers.py
# Output: evaluation_results/evaluation_results_20260207_143022.jsonl

# 3. Analyze results
python scripts/analyze_evaluation_results.py
# Output: analysis_output/20260207_143530/

# 4. View results
# - Check analysis_output/20260207_143530/analysis_report.txt
# - View PNG visualizations
# - Open CSV files in Excel/spreadsheet software
```

## Customization

### Modify Sample Size and Ratio

Edit `batch_evaluate_papers.py`:
```python
SAMPLE_SIZE = 200  # Increase to 200 base papers (= 1200 total evaluations)
TRAIN_RATIO = 0.75  # Force 75% train, 25% test (instead of auto-calculate)
# Or keep TRAIN_RATIO = None for automatic calculation based on dataset
```

### Change Rating Bins

Edit `analyze_evaluation_results.py`:
```python
RATING_BINS = [0, 2, 4, 6, 8, 10]  # More granular bins
RATING_LABELS = ['Very Poor', 'Poor', 'Fair', 'Good', 'Excellent']
```

### Add Custom Analysis

Add new analysis function in `analyze_evaluation_results.py`:
```python
def analyze_custom_metric(df: pd.DataFrame, output_path: Path):
    # Your custom analysis
    pass

# Call in main()
custom_results = analyze_custom_metric(df, output_path)
```

## Data Format

### Evaluation Results (JSONL)

Each line contains:
```json
{
  "paper_id": "paper_123",
  "title": "Paper Title",
  "variant_type": "no_abstract",
  "dataset_split": "train",
  "evaluation": {
    "avg_rating": 7.5,
    "paper_decision": "Accept",
    "confidence": 4,
    "originality": 8,
    "quality": 7,
    "clarity": 7,
    "significance": 8,
    "strength": ["...", "..."],
    "weaknesses": ["...", "..."],
    "meta_review": "..."
  },
  "text_length": 15234,
  "evaluation_timestamp": "2026-02-07T14:30:22.123456"
}
```

## Troubleshooting

### Issue: "No evaluation results found"
- Ensure `batch_evaluate_papers.py` has been run first
- Check `evaluation_results/` directory exists

### Issue: Out of memory
- Reduce `SAMPLE_SIZE` in batch evaluation
- Process results in batches

### Issue: Slow evaluation
- Reduce `SAMPLE_SIZE`
- Use smaller `MODEL_SIZE` (e.g., "4B")
- Run on GPU if available

## Notes

- Evaluation takes approximately 5-10 seconds per paper
- For 100 papers, expect ~15-30 minutes runtime
- Results are timestamped to avoid overwrites
- All scripts use UTF-8 encoding for international characters

## Citation

If you use these scripts in your research, please cite the original CycleReviewer paper and this codebase.

