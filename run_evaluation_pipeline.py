"""
Quick Start Script - Run Complete Evaluation Pipeline
Executes test -> evaluation -> analysis in sequence
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def run_script(script_path, description):
    """Run a Python script and handle errors"""
    print_header(description)
    print(f"Running: {script_path}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            capture_output=False,
            text=True
        )

        print(f"\n✅ {description} completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error running {description}: {e}")
        return False


def main():
    print_header("PAPER EVALUATION PIPELINE - QUICK START")

    # Get user confirmation
    print("This script will run the complete evaluation pipeline:")
    print("  1. Test environment (quick)")
    print("  2. Batch evaluation (~15-30 minutes for 100 papers)")
    print("  3. Results analysis (~1-2 minutes)")
    print()

    response = input("Continue? [y/N]: ")
    if response.lower() != 'y':
        print("Aborted by user.")
        return

    # Step 1: Test
    test_script = Path("scripts/test_evaluation_pipeline.py")
    if not run_script(test_script, "Step 1: Environment Test"):
        print("\n⚠️  Test failed. Please fix issues before continuing.")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            return

    # Step 2: Evaluation
    eval_script = Path("scripts/batch_evaluate_papers.py")
    if not run_script(eval_script, "Step 2: Batch Evaluation"):
        print("\n⚠️  Evaluation failed. Cannot proceed to analysis.")
        return

    # Step 3: Analysis
    analysis_script = Path("scripts/analyze_evaluation_results.py")
    if not run_script(analysis_script, "Step 3: Results Analysis"):
        print("\n⚠️  Analysis failed.")
        return

    # Success!
    print_header("PIPELINE COMPLETED SUCCESSFULLY! 🎉")
    print("Results saved to:")
    print("  - evaluation_results/     (evaluation data)")
    print("  - analysis_output/        (analysis and visualizations)")
    print()
    print("Next steps:")
    print("  1. Review analysis_output/TIMESTAMP/analysis_report.txt")
    print("  2. View PNG visualization files")
    print("  3. Open CSV files for detailed data")
    print()


if __name__ == "__main__":
    main()

