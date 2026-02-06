"""
Quick test script to verify the evaluation and analysis pipeline
Tests with a small sample (5 papers) to ensure everything works
"""

import json
import sys
from pathlib import Path

# Test configurations
TEST_SAMPLE_SIZE = 5
TEST_OUTPUT_DIR = "test_evaluation_results"


def test_data_loading():
    """Test if we can load the variant dataset"""
    print("\n[TEST 1] Testing data loading...")

    # Get the project root directory (parent of scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    train_file = project_root / "util" / "train_with_variants.jsonl"
    test_file = project_root / "util" / "test_with_variants.jsonl"

    if not train_file.exists():
        print(f"❌ FAILED: {train_file} not found")
        return False

    if not test_file.exists():
        print(f"❌ FAILED: {test_file} not found")
        return False

    # Load a few records
    train_count = 0
    test_count = 0

    with open(train_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                train_count += 1
                if train_count == 1:
                    print(f"  Sample train record keys: {list(record.keys())}")
                if train_count >= 5:
                    break

    with open(test_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                test_count += 1
                if test_count >= 5:
                    break

    print(f"✅ PASSED: Loaded {train_count} train and {test_count} test records")
    return True


def test_sample_structure():
    """Test if the data has required fields"""
    print("\n[TEST 2] Testing data structure...")

    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    train_file = project_root / "util" / "train_with_variants.jsonl"

    required_fields = ['text', 'variant_type', 'title']  # Changed: 'paper_text' -> 'text'

    with open(train_file, 'r', encoding='utf-8') as f:
        record = json.loads(f.readline())

    missing_fields = []
    for field in required_fields:
        if field not in record:
            missing_fields.append(field)

    if missing_fields:
        print(f"❌ FAILED: Missing fields: {missing_fields}")
        print(f"  Available fields: {list(record.keys())}")
        return False

    # Check text is not empty
    if not record.get('text') or len(record['text']) < 100:
        print(f"❌ FAILED: text field is empty or too short")
        return False

    print(f"✅ PASSED: All required fields present")
    print(f"  Variant type: {record['variant_type']}")
    print(f"  Title: {record['title'][:50]}...")
    print(f"  Text length: {len(record['text'])} chars")
    return True


def test_imports():
    """Test if all required packages are available"""
    print("\n[TEST 3] Testing package imports...")

    packages = {
        'pandas': 'pandas',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib.pyplot',
        'seaborn': 'seaborn',
        'scipy': 'scipy.stats',
        'tqdm': 'tqdm'
    }

    failed = []

    for name, import_path in packages.items():
        try:
            __import__(import_path)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            failed.append(name)

    if failed:
        print(f"❌ FAILED: Missing packages: {', '.join(failed)}")
        print(f"  Install with: pip install {' '.join(failed)}")
        return False

    print(f"✅ PASSED: All packages available")
    return True


def test_ai_researcher():
    """Test if CycleReviewer can be imported"""
    print("\n[TEST 4] Testing CycleReviewer import...")

    try:
        from ai_researcher import CycleReviewer
        print(f"  ✓ CycleReviewer imported successfully")
        print(f"✅ PASSED: CycleReviewer available")
        return True
    except ImportError as e:
        print(f"❌ FAILED: Cannot import CycleReviewer: {e}")
        return False


def test_output_directories():
    """Test if we can create output directories"""
    print("\n[TEST 5] Testing output directory creation...")

    test_dirs = [
        Path("evaluation_results"),
        Path("analysis_output"),
        Path(TEST_OUTPUT_DIR)
    ]

    for dir_path in test_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {dir_path} created/verified")
        except Exception as e:
            print(f"  ✗ {dir_path} - FAILED: {e}")
            return False

    print(f"✅ PASSED: All directories can be created")
    return True


def run_mini_evaluation():
    """Run a mini evaluation with 2 papers"""
    print("\n[TEST 6] Running mini evaluation (2 papers)...")

    try:
        from ai_researcher import CycleReviewer

        # Get the project root directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        train_file = project_root / "util" / "train_with_variants.jsonl"

        # Load 2 papers
        papers = []
        with open(train_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 2:
                    break
                if line.strip():
                    papers.append(json.loads(line))

        print(f"  Loaded {len(papers)} papers for testing")

        # Initialize reviewer
        print(f"  Initializing CycleReviewer...")
        reviewer = CycleReviewer(model_size="8B")

        # Evaluate first paper
        print(f"  Evaluating paper 1...")
        paper_text = papers[0].get('text', '')  # Changed: 'paper_text' -> 'text'

        if not paper_text or len(paper_text) < 100:
            print(f"❌ FAILED: Paper text is empty or too short")
            return False

        reviews = reviewer.evaluate([paper_text])

        if not reviews or not reviews[0]:
            print(f"❌ FAILED: Evaluation returned no results")
            return False

        review = reviews[0]
        print(f"  ✓ Evaluation successful")
        print(f"    Rating: {review.get('avg_rating', 'N/A')}")
        print(f"    Decision: {review.get('paper_decision', 'N/A')}")

        print(f"✅ PASSED: Mini evaluation completed")
        return True

    except Exception as e:
        print(f"❌ FAILED: Evaluation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*70)
    print("EVALUATION PIPELINE TEST SUITE")
    print("="*70)

    tests = [
        ("Data Loading", test_data_loading),
        ("Data Structure", test_sample_structure),
        ("Package Imports", test_imports),
        ("CycleReviewer Import", test_ai_researcher),
        ("Output Directories", test_output_directories),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ EXCEPTION in {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Optional: Run mini evaluation (may be slow)
    print("\n" + "="*70)
    run_eval = input("Run mini evaluation test? (requires LLM, may be slow) [y/N]: ")
    if run_eval.lower() == 'y':
        results.append(("Mini Evaluation", run_mini_evaluation()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("\n" + "="*70)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! You're ready to run the evaluation pipeline.")
        print("\nNext steps:")
        print("  1. python scripts/batch_evaluate_papers.py")
        print("  2. python scripts/analyze_evaluation_results.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues before proceeding.")

    print("="*70)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

