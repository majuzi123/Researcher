# Generated Dataset Format Documentation

## 📄 File Format
- **Format**: JSONL (JSON Lines)
- **Encoding**: UTF-8
- **Structure**: One JSON object per line

## 📊 Data Structure

Each line in the output file contains a JSON object representing one paper variant with the following fields:

### Field Description

```json
{
  "id": "paper_id_variant_name",
  "title": "Original Paper Title [variant_name]",
  "original_title": "Original Paper Title",
  "variant_type": "variant_name",
  "text": "processed paper content...",
  "original_id": "original_paper_id",
  "original_path": "source_file.jsonl:line_number",
  "rates": [6, 7, 8],
  "decision": "accept"
}
```

### Field Specifications

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier combining original paper ID and variant type | `"paper_123_no_abstract"` |
| `title` | string | Modified title with variant type label | `"Deep Learning [no_abstract]"` |
| `original_title` | string | Original paper title without modification | `"Deep Learning"` |
| `variant_type` | string | Type of variant applied | `"original"`, `"no_abstract"`, `"no_conclusion"`, etc. |
| `text` | string | Processed paper text content | Full paper text with variant applied |
| `original_id` | string/null | Original paper ID from source file | `"paper_123"` or `null` |
| `original_path` | string | Source location in original file | `"train.jsonl:42"` |
| `rates` | array/null | Review scores from original paper | `[6, 7, 8]` or `null` |
| `decision` | string/null | Review decision from original paper | `"accept"`, `"reject"`, or `null` |

## 🎯 Variant Types

The dataset includes 9 variant types for each paper:

| Variant Type | Description |
|--------------|-------------|
| `original` | Original paper, no modifications |
| `no_abstract` | Abstract section removed |
| `no_conclusion` | Conclusion section removed |
| `no_introduction` | Introduction section removed |
| `no_references` | References section removed |
| `no_experiments` | Experiments section removed |
| `no_methods` | Methods section removed |
| `no_formulas` | All formulas removed |
| `no_figures` | All figures removed |

## 📈 Data Statistics Examples

### Example 1: Count variants by type
```python
import json
from collections import Counter

variant_counts = Counter()
with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        variant_counts[obj["variant_type"]] += 1

print(variant_counts)
# Output: {'original': 100, 'no_abstract': 100, 'no_conclusion': 100, ...}
```

### Example 2: Analyze by decision
```python
import json
from collections import defaultdict

decision_variants = defaultdict(list)
with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        decision = obj.get("decision", "unknown")
        decision_variants[decision].append(obj["variant_type"])

for decision, variants in decision_variants.items():
    print(f"{decision}: {len(variants)} variants")
```

### Example 3: Text length analysis
```python
import json
import matplotlib.pyplot as plt

data = {"variant_type": [], "text_length": []}
with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        data["variant_type"].append(obj["variant_type"])
        data["text_length"].append(len(obj["text"]))

# Plot
import pandas as pd
df = pd.DataFrame(data)
df.boxplot(by="variant_type", column="text_length", figsize=(12, 6))
plt.xticks(rotation=45)
plt.title("Text Length Distribution by Variant Type")
plt.ylabel("Text Length (characters)")
plt.tight_layout()
plt.savefig("text_length_distribution.png")
```

### Example 4: Group by original paper
```python
import json
from collections import defaultdict

papers = defaultdict(list)
with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        original_id = obj.get("original_id") or obj.get("original_path")
        papers[original_id].append(obj)

# Check if each paper has all 9 variants
for paper_id, variants in papers.items():
    if len(variants) != 9:
        print(f"Paper {paper_id} has only {len(variants)} variants")
```

## 📊 Visualization Examples

### 1. Variant Distribution Pie Chart
```python
import json
import matplotlib.pyplot as plt
from collections import Counter

variant_counts = Counter()
with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        variant_counts[obj["variant_type"]] += 1

plt.figure(figsize=(10, 8))
plt.pie(variant_counts.values(), labels=variant_counts.keys(), autopct='%1.1f%%')
plt.title("Variant Type Distribution")
plt.savefig("variant_distribution.png")
```

### 2. Decision vs Variant Heatmap
```python
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

data = []
with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        data.append({
            "variant_type": obj["variant_type"],
            "decision": obj.get("decision", "unknown")
        })

df = pd.DataFrame(data)
pivot = df.pivot_table(index="decision", columns="variant_type", aggfunc="size", fill_value=0)

plt.figure(figsize=(12, 6))
sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd")
plt.title("Decision vs Variant Type Heatmap")
plt.tight_layout()
plt.savefig("decision_variant_heatmap.png")
```

### 3. Text Length Reduction by Variant
```python
import json
import pandas as pd
import matplotlib.pyplot as plt

original_lengths = {}
variant_data = []

with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        original_id = obj.get("original_id") or obj.get("original_path")
        text_len = len(obj["text"])
        
        if obj["variant_type"] == "original":
            original_lengths[original_id] = text_len
        else:
            variant_data.append({
                "original_id": original_id,
                "variant_type": obj["variant_type"],
                "text_length": text_len
            })

# Calculate reduction percentage
for item in variant_data:
    original_len = original_lengths.get(item["original_id"], 1)
    item["reduction_pct"] = (1 - item["text_length"] / original_len) * 100

df = pd.DataFrame(variant_data)
df_avg = df.groupby("variant_type")["reduction_pct"].mean().sort_values(ascending=False)

plt.figure(figsize=(10, 6))
df_avg.plot(kind="bar")
plt.title("Average Text Reduction by Variant Type")
plt.ylabel("Reduction (%)")
plt.xlabel("Variant Type")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("text_reduction_by_variant.png")
```

## 🔍 Data Quality Checks

### Check for missing variants
```python
import json
from collections import defaultdict

papers = defaultdict(set)
expected_variants = {
    "original", "no_abstract", "no_conclusion", "no_introduction",
    "no_references", "no_experiments", "no_methods", "no_formulas", "no_figures"
}

with open("util/train_with_variants.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        original_id = obj.get("original_id") or obj.get("original_path")
        papers[original_id].add(obj["variant_type"])

incomplete_papers = []
for paper_id, variants in papers.items():
    missing = expected_variants - variants
    if missing:
        incomplete_papers.append((paper_id, missing))

print(f"Total papers: {len(papers)}")
print(f"Incomplete papers: {len(incomplete_papers)}")
for paper_id, missing in incomplete_papers[:5]:
    print(f"  {paper_id}: missing {missing}")
```

## 💡 Usage Tips

1. **Filtering by variant type**: Use the `variant_type` field to analyze specific variants
2. **Grouping by original paper**: Use `original_id` or `original_path` as the grouping key
3. **Comparing decisions**: Use the `decision` field to analyze how variants affect different paper categories
4. **Text analysis**: Use the `text` field for content-based analysis
5. **Quality metrics**: Use the `rates` field to correlate with review scores

## 📦 Output Files

```
util/
├── train_with_variants.jsonl  # Training set with all variants
└── test_with_variants.jsonl   # Test set with all variants
```

Each file contains:
- **Number of unique papers**: `SAMPLE_RATIO * original_papers`
- **Number of total records**: `unique_papers * 9 (variants)`
- **Example**: 10% of 1000 papers = 100 papers × 9 variants = 900 records

