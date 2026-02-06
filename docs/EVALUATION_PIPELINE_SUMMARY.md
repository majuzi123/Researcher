# Paper Evaluation Pipeline - Files Summary

## 📦 Created Files

### 1. Main Scripts

#### `scripts/batch_evaluate_papers.py`
**Purpose**: Batch evaluation of paper variants using CycleReviewer

**Features**:
- Samples 100 papers (80 train, 20 test) from generated dataset
- Evaluates each paper using CycleReviewer AI model
- Saves detailed results in JSONL format
- Generates summary statistics
- Configurable sample size, train/test ratio, model size

**Key Configuration**:
```python
SAMPLE_SIZE = 100      # Total papers to evaluate
TRAIN_RATIO = 0.8      # 80% from train, 20% from test
MODEL_SIZE = "8B"      # CycleReviewer model size
SEED = 42              # Reproducibility
```

**Output**:
- `evaluation_results/evaluation_results_TIMESTAMP.jsonl`
- `evaluation_results/evaluation_summary_TIMESTAMP.json`

---

#### `scripts/analyze_evaluation_results.py`
**Purpose**: Comprehensive statistical analysis and visualization

**Features**:
- Overall statistics (mean, median, std, quartiles)
- Variant-specific analysis
- Rating range analysis (Poor/Fair/Good/Excellent)
- Original vs variants comparison with t-test
- 8 visualization plots
- Detailed text report

**Analysis Types**:
1. Overall statistics
2. By variant type (6 variants)
3. By rating range (4 ranges)
4. Original vs variants comparison
5. Correlation analysis
6. Distribution analysis

**Output** (in `analysis_output/TIMESTAMP/`):
- `overall_statistics.json`
- `variant_statistics.csv`
- `rating_range_statistics.json`
- `original_vs_variants.json`
- `processed_data.csv`
- `analysis_report.txt`
- 8 PNG visualization files

---

#### `scripts/test_evaluation_pipeline.py`
**Purpose**: Test and verify the evaluation pipeline setup

**Tests**:
1. Data loading (train/test JSONL files)
2. Data structure validation
3. Package imports (pandas, numpy, matplotlib, seaborn, scipy, tqdm)
4. CycleReviewer import
5. Output directory creation
6. Optional: Mini evaluation (2 papers)

**Usage**:
```bash
python scripts/test_evaluation_pipeline.py
```

---

### 2. Documentation

#### `scripts/README_EVALUATION.md` (English)
- Detailed usage instructions
- Configuration options
- Output file descriptions
- Troubleshooting guide
- Example workflow

#### `docs/EVALUATION_GUIDE_CN.md` (Chinese)
- 中文使用指南
- 快速开始步骤
- 配置选项说明
- 常见问题解答
- 最佳实践

---

## 🎯 Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Step 0: Generate Variant Dataset (Already Done)            │
│   - 6 variant types per paper                              │
│   - Train: 4,272 samples (712 papers × 6)                  │
│   - Test: 1,086 samples (181 papers × 6)                   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Test Pipeline (Optional but Recommended)           │
│   python scripts/test_evaluation_pipeline.py               │
│   - Verifies environment                                   │
│   - Checks dependencies                                    │
│   - Tests data loading                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Batch Evaluation                                   │
│   python scripts/batch_evaluate_papers.py                  │
│   - Samples 100 papers (80 train + 20 test)                │
│   - Evaluates with CycleReviewer                           │
│   - Saves results to evaluation_results/                   │
│   Time: ~15-30 minutes                                     │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Analysis & Visualization                           │
│   python scripts/analyze_evaluation_results.py             │
│   - Loads latest evaluation results                        │
│   - Generates statistics                                   │
│   - Creates 8 visualization plots                          │
│   - Saves to analysis_output/TIMESTAMP/                    │
│   Time: ~1-2 minutes                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Review Results                                     │
│   - Read analysis_report.txt                               │
│   - View PNG charts                                        │
│   - Examine CSV data                                       │
│   - Check JSON statistics                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Analysis Outputs Explained

### Statistics Files

1. **overall_statistics.json**
   - Total papers evaluated
   - Rating statistics (mean, median, std, min, max, quartiles)
   - Aspect ratings (originality, quality, clarity, significance)
   - Decision distribution
   - Variant distribution

2. **variant_statistics.csv**
   Columns:
   - variant_type
   - count
   - avg_rating_mean, avg_rating_std
   - originality, quality, clarity, significance
   - accept_rate, reject_rate

3. **rating_range_statistics.json**
   For each range (Poor/Fair/Good/Excellent):
   - Count and percentage
   - Average aspect scores
   - Variant distribution
   - Top variant

4. **original_vs_variants.json**
   - Original papers stats
   - All variants stats
   - T-test results (t-statistic, p-value)
   - Significance indicator

5. **processed_data.csv**
   Full dataset with columns:
   - paper_id, title, variant_type, dataset_split
   - avg_rating, paper_decision, confidence
   - originality, quality, clarity, significance
   - text_length, num_strengths, num_weaknesses

6. **analysis_report.txt**
   - Overall statistics section
   - Variant type analysis section
   - Top 10 rated papers
   - Bottom 10 rated papers

### Visualization Files

1. **rating_distribution.png**
   - Histogram of all ratings
   - Mean and median lines

2. **ratings_by_variant_boxplot.png**
   - Box plot for each variant
   - Shows median, quartiles, outliers

3. **ratings_by_variant_violin.png**
   - Violin plot (distribution shape)
   - Shows probability density

4. **decision_distribution.png**
   - Pie chart of Accept/Reject/etc.

5. **aspect_ratings.png**
   - Bar chart of 4 aspects
   - Shows average scores

6. **variant_decision_heatmap.png**
   - Rows: variant types
   - Columns: decisions
   - Values: count

7. **correlation_heatmap.png**
   - Correlation matrix
   - Variables: avg_rating, originality, quality, clarity, significance, confidence

8. **text_length_vs_rating.png**
   - Scatter plot
   - Trend line showing relationship

---

## 🔧 Customization Examples

### Example 1: Evaluate 200 Papers

```python
# Edit batch_evaluate_papers.py
SAMPLE_SIZE = 200
TRAIN_RATIO = 0.8
```

### Example 2: Change Rating Bins

```python
# Edit analyze_evaluation_results.py
RATING_BINS = [0, 2, 4, 6, 8, 10]
RATING_LABELS = ['Very Poor', 'Poor', 'Fair', 'Good', 'Excellent']
```

### Example 3: Add Custom Analysis

```python
# In analyze_evaluation_results.py

def analyze_text_length_effect(df: pd.DataFrame, output_path: Path):
    """Analyze how text length affects ratings"""
    # Create bins by text length
    df['length_bin'] = pd.qcut(df['text_length'], q=4, labels=['Short', 'Medium', 'Long', 'Very Long'])
    
    # Calculate stats
    length_stats = df.groupby('length_bin')['avg_rating'].agg(['mean', 'count', 'std'])
    
    # Save
    length_stats.to_csv(output_path / 'text_length_analysis.csv')
    
    return length_stats

# Call in main()
length_results = analyze_text_length_effect(df, output_path)
```

---

## 📋 Checklist for Running

- [ ] Generated variant dataset exists (`util/train_with_variants.jsonl` and `util/test_with_variants.jsonl`)
- [ ] All dependencies installed (`pip install pandas numpy matplotlib seaborn scipy tqdm`)
- [ ] CycleReviewer available (`from ai_researcher import CycleReviewer` works)
- [ ] Test pipeline passes (`python scripts/test_evaluation_pipeline.py`)
- [ ] Sufficient disk space (~100MB for results)
- [ ] Stable internet connection (for LLM API calls)
- [ ] 30+ minutes available for evaluation

---

## 🎓 Understanding the Results

### What is a "good" average rating?
- **< 3**: Poor quality, likely reject
- **3-5**: Fair quality, borderline
- **5-7**: Good quality, likely accept with revisions
- **7-10**: Excellent quality, strong accept

### What do the variants tell us?
- **original**: Baseline performance
- **no_abstract**: Impact of abstract on review
- **no_introduction**: Impact of introduction
- **no_conclusion**: Impact of conclusion
- **no_experiments**: Impact of experimental section
- **no_methods**: Impact of methodology section

### Key questions to explore:
1. Which variant performs best/worst?
2. Is there a significant difference between original and variants?
3. Which sections are most critical for high ratings?
4. Do certain variants get more "Accept" decisions?
5. How do the 4 aspects (originality, quality, clarity, significance) correlate?

---

## 🚨 Troubleshooting

### Error: "No evaluation results found"
**Solution**: Run `batch_evaluate_papers.py` first

### Error: "ModuleNotFoundError: No module named 'XXX'"
**Solution**: `pip install XXX`

### Error: Out of memory
**Solution**: Reduce `SAMPLE_SIZE` or run on a machine with more RAM

### Slow evaluation
**Solution**: 
- Use smaller `MODEL_SIZE` (e.g., "4B")
- Reduce `SAMPLE_SIZE`
- Run overnight

### Empty or invalid results
**Solution**: 
- Check if papers have `paper_text` field
- Verify text is not empty
- Check LLM API is working

---

## 📞 Support

For issues or questions:
1. Check documentation: `README_EVALUATION.md` and `EVALUATION_GUIDE_CN.md`
2. Run test script: `test_evaluation_pipeline.py`
3. Review error messages and stack traces
4. Check data format matches expected structure

---

**Happy Evaluating!** 🎉

