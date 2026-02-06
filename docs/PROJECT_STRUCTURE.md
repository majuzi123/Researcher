# Project Structure

This project contains tools for paper variant dataset generation and analysis.

## 📁 Directory Structure

```
Researcher/
├── docs/                           # Documentation
│   ├── DATASET_ANALYSIS_GUIDE.md  # Guide for analyzing generated datasets
│   ├── DATASET_FORMAT.md          # Dataset format specification
│   └── VARIANT_GENERATION_LOGIC.md # Variant generation logic documentation
│
├── scripts/                        # Python scripts
│   ├── generate_variant_dataset.py # Main dataset generation script
│   ├── analyze_dataset.py         # Dataset analysis and visualization script
│   ├── batch_variant_evaluator.py # Batch evaluation script
│   └── data_analyzer.py           # Data analysis utilities
│
├── examples/                       # Example files
│   └── example_dataset.jsonl      # Sample dataset output
│
├── util/                          # Output directory (auto-generated)
│   ├── train_with_variants.jsonl  # Generated training set
│   └── test_with_variants.jsonl   # Generated test set
│
├── analysis_output/               # Analysis results (auto-generated)
│   ├── train/                     # Training set analysis
│   └── test/                      # Test set analysis
│
├── ai_researcher/                 # Core research module
├── Tutorial/                      # Tutorials and examples
├── evaluate/                      # Evaluation tools
├── generated_paper/               # Generated papers
├── train_output/                  # Training output
├── test_output/                   # Testing output
│
├── train.jsonl                    # Source training data
├── test.jsonl                     # Source test data
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
└── readme.md                      # Main README

```

## 🚀 Quick Start

### 1. Generate Variant Dataset
```bash
python scripts/generate_variant_dataset.py
```

This will:
- Sample papers from `train.jsonl` and `test.jsonl`
- Generate 9 variants for each paper
- Save results to `util/train_with_variants.jsonl` and `util/test_with_variants.jsonl`

### 2. Analyze Dataset
```bash
python scripts/analyze_dataset.py
```

This will:
- Load generated datasets
- Create various visualizations
- Generate statistical reports
- Save results to `analysis_output/`

### 3. Configuration
Edit the top of `scripts/generate_variant_dataset.py`:
```python
SAMPLE_RATIO = 0.1      # Sample 10% of papers
STRICT_MODE = True      # Ensure all variants succeed
MAX_RETRY_ATTEMPTS = 100 # Max retry for failed generations
```

## 📚 Documentation

- **[Dataset Analysis Guide](DATASET_ANALYSIS_GUIDE.md)** - Comprehensive guide for analyzing and visualizing the dataset
- **[Dataset Format](DATASET_FORMAT.md)** - Detailed specification of the output format
- **[Variant Generation Logic](VARIANT_GENERATION_LOGIC.md)** - How variants are generated and validated

## 🎯 Variant Types

The system generates 9 variants per paper:
1. `original` - Original paper (no modifications)
2. `no_abstract` - Abstract section removed
3. `no_conclusion` - Conclusion section removed
4. `no_introduction` - Introduction section removed
5. `no_references` - References section removed
6. `no_experiments` - Experiments section removed
7. `no_methods` - Methods section removed
8. `no_formulas` - All formulas removed
9. `no_figures` - All figures removed

## 📊 Output Format

Each variant is stored as a JSON object with the following fields:
```json
{
  "id": "paper_001_no_abstract",
  "title": "Paper Title [no_abstract]",
  "original_title": "Paper Title",
  "variant_type": "no_abstract",
  "text": "processed paper content...",
  "original_id": "paper_001",
  "original_path": "train.jsonl:1",
  "rates": [6, 7, 8],
  "decision": "accept"
}
```

## 🔧 Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- pandas
- matplotlib
- seaborn
- (see requirements.txt for complete list)

## 📈 Example Workflow

1. **Prepare data**: Place your papers in `train.jsonl` and `test.jsonl`
2. **Generate variants**: `python scripts/generate_variant_dataset.py`
3. **Analyze results**: `python scripts/analyze_dataset.py`
4. **View visualizations**: Check `analysis_output/train/` and `analysis_output/test/`
5. **Read statistics**: Open `analysis_output/train/statistics_report.txt`

## 💡 Tips

- Check `examples/example_dataset.jsonl` to see what the output looks like
- Modify `SAMPLE_RATIO` in the script to control dataset size
- Use `STRICT_MODE = False` for faster generation with possible missing variants
- All scripts can be run from the project root directory

## 📝 License

See [LICENSE.md](../LICENSE.md)

