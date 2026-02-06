# Dataset Format and Analysis Guide

## 📦 Generated Dataset Overview

### Output Files
```
util/
├── train_with_variants.jsonl  # Training set with all variants
└── test_with_variants.jsonl   # Test set with all variants
```

### File Format: JSONL (JSON Lines)
- One JSON object per line
- UTF-8 encoding
- Each object represents one paper variant

---

## 📊 Data Structure

### JSON Schema
```json
{
  "id": "string",              // Unique identifier (e.g., "paper_001_no_abstract")
  "title": "string",           // Title with variant label (e.g., "Title [no_abstract]")
  "original_title": "string",  // Original paper title
  "variant_type": "string",    // Variant type (see below)
  "text": "string",            // Processed paper content
  "original_id": "string|null",// Original paper ID
  "original_path": "string",   // Source file location
  "rates": "array|null",       // Review scores [6, 7, 8]
  "decision": "string|null"    // Review decision ("accept"/"reject")
}
```

### Available Fields for Analysis

| Field | Type | Use for Visualization |
|-------|------|----------------------|
| `variant_type` | string | **Main grouping variable**: Compare different variants |
| `decision` | string | **Classification**: Accept/reject analysis |
| `rates` | array | **Numerical analysis**: Rating score distribution |
| `text` | string | **Text analysis**: Length, content analysis |
| `original_id` | string | **Grouping**: Group variants from same paper |
| `original_path` | string | **Tracking**: Trace back to source |

---

## 🎯 9 Variant Types

Each paper generates 9 variants:

| Variant Type | Description | Expected Reduction |
|--------------|-------------|-------------------|
| `original` | Original paper | 0% |
| `no_abstract` | Abstract removed | 5-10% |
| `no_conclusion` | Conclusion removed | 3-5% |
| `no_introduction` | Introduction removed | 5-15% |
| `no_references` | References removed | 10-20% |
| `no_experiments` | Experiments removed | 15-25% |
| `no_methods` | Methods removed | 10-20% |
| `no_formulas` | All formulas removed | 1-5% |
| `no_figures` | All figures removed | 1-3% |

---

## 📈 Visualization Examples

### 1. Quick Start: Run Analysis Script
```bash
python analyze_dataset.py
```

This generates:
- `analysis_output/train/` - Training set visualizations
- `analysis_output/test/` - Test set visualizations
- Statistical reports in `.txt` format

### 2. Generated Visualizations

#### A. Variant Distribution Bar Chart
Shows count of each variant type (should be equal in strict mode)

#### B. Text Length Box Plot
Compares text length distribution across variants

#### C. Text Reduction Bar Chart
Shows average percentage reduction per variant type

#### D. Decision-Variant Heatmap
Cross-tabulation of decisions and variant types

#### E. Rating Distribution Histogram
Distribution of review scores

---

## 🔍 Common Analysis Tasks

### Task 1: Load Dataset
```python
import json

data = []
with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

print(f"Loaded {len(data)} records")
```

### Task 2: Group by Original Paper
```python
from collections import defaultdict

papers = defaultdict(list)
for item in data:
    original_id = item.get('original_id') or item.get('original_path')
    papers[original_id].append(item)

print(f"Total unique papers: {len(papers)}")
```

### Task 3: Filter by Variant Type
```python
no_abstract_variants = [item for item in data if item['variant_type'] == 'no_abstract']
print(f"Found {len(no_abstract_variants)} 'no_abstract' variants")
```

### Task 4: Analyze by Decision
```python
from collections import Counter

decisions = Counter(item.get('decision', 'unknown') for item in data)
print("Decision distribution:", decisions)

# Get accepted papers only
accepted = [item for item in data if item.get('decision') == 'accept']
```

### Task 5: Text Length Analysis
```python
import pandas as pd

df = pd.DataFrame([
    {
        'variant_type': item['variant_type'],
        'text_length': len(item['text']),
        'decision': item.get('decision', 'unknown')
    }
    for item in data
])

# Calculate average length per variant
avg_lengths = df.groupby('variant_type')['text_length'].mean()
print(avg_lengths)
```

### Task 6: Calculate Reduction Rate
```python
from collections import defaultdict

papers = defaultdict(dict)
for item in data:
    original_id = item.get('original_id') or item.get('original_path')
    papers[original_id][item['variant_type']] = len(item['text'])

for paper_id, variants in papers.items():
    original_len = variants.get('original', 0)
    if original_len > 0:
        for variant_type, length in variants.items():
            if variant_type != 'original':
                reduction = (1 - length / original_len) * 100
                print(f"{paper_id} - {variant_type}: {reduction:.2f}% reduction")
```

---

## 📊 Custom Visualization Examples

### Example 1: Variant Type Pie Chart
```python
import matplotlib.pyplot as plt
from collections import Counter

variant_counts = Counter(item['variant_type'] for item in data)

plt.figure(figsize=(10, 8))
plt.pie(variant_counts.values(), labels=variant_counts.keys(), autopct='%1.1f%%')
plt.title("Variant Type Distribution")
plt.savefig("variant_pie.png")
plt.show()
```

### Example 2: Decision Comparison
```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.DataFrame([
    {
        'variant_type': item['variant_type'],
        'decision': item.get('decision', 'unknown')
    }
    for item in data
])

# Count plot
plt.figure(figsize=(12, 6))
sns.countplot(data=df, x='variant_type', hue='decision')
plt.xticks(rotation=45)
plt.title("Decision Distribution by Variant Type")
plt.tight_layout()
plt.savefig("decision_comparison.png")
plt.show()
```

### Example 3: Text Length Violin Plot
```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.DataFrame([
    {
        'variant_type': item['variant_type'],
        'text_length': len(item['text'])
    }
    for item in data
])

plt.figure(figsize=(14, 6))
sns.violinplot(data=df, x='variant_type', y='text_length')
plt.xticks(rotation=45)
plt.title("Text Length Distribution (Violin Plot)")
plt.tight_layout()
plt.savefig("text_length_violin.png")
plt.show()
```

### Example 4: Rating Score Box Plot
```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df_data = []
for item in data:
    if item.get('rates'):
        for score in item['rates']:
            df_data.append({
                'variant_type': item['variant_type'],
                'score': score
            })

df = pd.DataFrame(df_data)

plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='variant_type', y='score')
plt.xticks(rotation=45)
plt.title("Rating Score Distribution by Variant Type")
plt.tight_layout()
plt.savefig("rating_boxplot.png")
plt.show()
```

---

## 💡 Advanced Analysis Ideas

### 1. Correlation Analysis
Analyze if certain variants affect acceptance rates differently

### 2. Text Similarity
Compare how similar variants are to the original using cosine similarity

### 3. Section Importance
Determine which sections have the most impact on paper decisions

### 4. Length vs Quality
Correlate text length reduction with rating scores

### 5. Variant Combinations
Analyze effects of removing multiple sections (future extension)

---

## ✅ Data Quality Checks

### Check 1: Verify All Papers Have 9 Variants
```python
from collections import defaultdict

papers = defaultdict(set)
expected_variants = {
    'original', 'no_abstract', 'no_conclusion', 'no_introduction',
    'no_references', 'no_experiments', 'no_methods', 'no_formulas', 'no_figures'
}

for item in data:
    original_id = item.get('original_id') or item.get('original_path')
    papers[original_id].add(item['variant_type'])

complete = sum(1 for variants in papers.values() if variants == expected_variants)
print(f"Complete papers: {complete}/{len(papers)}")
```

### Check 2: Verify Text Reduction
```python
# All variants (except original) should be shorter or equal length
for item in data:
    if item['variant_type'] != 'original':
        # Check if text is not empty
        if len(item['text'].strip()) < 50:
            print(f"WARNING: Very short text in {item['id']}")
```

---

## 📚 Reference Files

- `DATASET_FORMAT.md` - Detailed format specification and examples
- `analyze_dataset.py` - Automated analysis script
- `example_dataset.jsonl` - Sample data for reference
- `generate_variant_dataset.py` - Dataset generation script
- `VARIANT_GENERATION_LOGIC.md` - Logic documentation

---

## 🚀 Quick Usage

1. **Generate dataset:**
   ```bash
   python generate_variant_dataset.py
   ```

2. **Analyze results:**
   ```bash
   python analyze_dataset.py
   ```

3. **View statistics:**
   ```bash
   cat analysis_output/train/statistics_report.txt
   ```

4. **Custom analysis:**
   - Load data using examples above
   - Create your own visualizations
   - Export results for further processing

---

## 📞 Dataset Statistics Summary

Expected output for 10% sampling of 1000 papers:

```
Total records: 900 (100 papers × 9 variants)
Unique papers: 100
Variant type counts: 100 each
Complete papers: 100/100
```

All visualizations saved to `analysis_output/` directory.

