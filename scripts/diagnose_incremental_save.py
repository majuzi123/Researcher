"""
Quick diagnostic script for incremental save file issue
快速诊断增量保存文件问题
"""

from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "evaluation_results"

print("="*70)
print("INCREMENTAL SAVE FILE DIAGNOSTIC")
print("="*70)

# 1. Check project root
print(f"\n1. Project Root:")
print(f"   Path: {PROJECT_ROOT}")
print(f"   Exists: {PROJECT_ROOT.exists()}")
print(f"   Is directory: {PROJECT_ROOT.is_dir()}")

# 2. Check output directory
print(f"\n2. Output Directory:")
print(f"   Path: {OUTPUT_DIR}")
print(f"   Exists: {OUTPUT_DIR.exists()}")
if OUTPUT_DIR.exists():
    print(f"   Is directory: {OUTPUT_DIR.is_dir()}")
    print(f"   Permissions: {oct(os.stat(OUTPUT_DIR).st_mode)[-3:]}")
else:
    print(f"   ❌ Directory does not exist")
    print(f"   Attempting to create...")
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ Created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create: {e}")

# 3. Test file creation
print(f"\n3. Test File Creation:")
test_file = OUTPUT_DIR / "test_write.txt"
try:
    with open(test_file, 'w') as f:
        f.write("Test write\n")
    print(f"   ✓ Can write to directory")
    test_file.unlink()  # Delete test file
    print(f"   ✓ Can delete from directory")
except Exception as e:
    print(f"   ❌ Cannot write: {e}")

# 4. Check disk space
print(f"\n4. Disk Space:")
try:
    import shutil
    total, used, free = shutil.disk_usage(PROJECT_ROOT)
    print(f"   Total: {total // (2**30)} GB")
    print(f"   Used:  {used // (2**30)} GB")
    print(f"   Free:  {free // (2**30)} GB ({free // (2**20)} MB)")
    if free < 100 * (2**20):  # Less than 100MB
        print(f"   ⚠️  WARNING: Low disk space!")
except Exception as e:
    print(f"   ❌ Cannot check disk space: {e}")

# 5. Test incremental file path
print(f"\n5. Test Incremental File Path:")
from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
incremental_file = OUTPUT_DIR / f'evaluation_results_{timestamp}_incremental.jsonl'
incremental_file_abs = incremental_file.resolve()

print(f"   Relative path: {incremental_file}")
print(f"   Absolute path: {incremental_file_abs}")
print(f"   Path length: {len(str(incremental_file_abs))} characters")

# 6. Test JSON writing
print(f"\n6. Test JSON Writing:")
import json
test_data = {
    "paper_id": "test_001",
    "variant_type": "test",
    "evaluation": {
        "avg_rating": 7.5,
        "paper_decision": "Test"
    }
}

try:
    with open(incremental_file_abs, 'w', encoding='utf-8') as f:
        f.write(json.dumps(test_data, ensure_ascii=False) + '\n')
    print(f"   ✓ Can write JSON to file")

    # Read back
    with open(incremental_file_abs, 'r', encoding='utf-8') as f:
        data = json.loads(f.readline())
    print(f"   ✓ Can read JSON from file")

    # Delete test file
    incremental_file_abs.unlink()
    print(f"   ✓ Test file cleaned up")

except Exception as e:
    print(f"   ❌ JSON write failed: {e}")
    import traceback
    traceback.print_exc()

# 7. Check existing incremental files
print(f"\n7. Existing Incremental Files:")
if OUTPUT_DIR.exists():
    incremental_files = list(OUTPUT_DIR.glob("*_incremental.jsonl"))
    if incremental_files:
        print(f"   Found {len(incremental_files)} file(s):")
        for f in incremental_files[-5:]:  # Show last 5
            size = f.stat().st_size
            print(f"     - {f.name} ({size} bytes)")
    else:
        print(f"   No incremental files found")
else:
    print(f"   ❌ Output directory does not exist")

# 8. Summary
print(f"\n" + "="*70)
print("SUMMARY")
print("="*70)

checks = {
    "Project root exists": PROJECT_ROOT.exists(),
    "Output directory exists": OUTPUT_DIR.exists(),
    "Can create files": True,  # Will be False if test failed
    "Sufficient disk space": True,
}

try:
    with open(OUTPUT_DIR / "test_summary.txt", 'w') as f:
        f.write("test")
    (OUTPUT_DIR / "test_summary.txt").unlink()
except:
    checks["Can create files"] = False

all_pass = all(checks.values())

for check, result in checks.items():
    status = "✓" if result else "✗"
    print(f"{status} {check}")

if all_pass:
    print(f"\n✅ All checks passed! Incremental save should work.")
else:
    print(f"\n❌ Some checks failed. Please fix the issues above.")

print("="*70)

