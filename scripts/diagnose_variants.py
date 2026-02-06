"""
Diagnose which variants are failing and why
"""
import json
from collections import Counter, defaultdict

print("Analyzing generated dataset...")
print("=" * 60)

# Load generated data
train_variants = Counter()
test_variants = Counter()

with open('../util/train_with_variants.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        train_variants[obj['variant_type']] += 1

with open('../util/test_with_variants.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        test_variants[obj['variant_type']] += 1

# Display results
print("\nTRAIN SET VARIANT DISTRIBUTION:")
print("-" * 60)
total_train = sum(train_variants.values())
for variant, count in sorted(train_variants.items()):
    percentage = (count / total_train) * 100
    print(f"  {variant:20s}: {count:4d} ({percentage:5.1f}%)")

print(f"\n  TOTAL: {total_train}")

print("\n\nTEST SET VARIANT DISTRIBUTION:")
print("-" * 60)
total_test = sum(test_variants.values())
for variant, count in sorted(test_variants.items()):
    percentage = (count / total_test) * 100
    print(f"  {variant:20s}: {count:4d} ({percentage:5.1f}%)")

print(f"\n  TOTAL: {total_test}")

# Calculate success rates
print("\n\nSUCCESS RATE ANALYSIS:")
print("=" * 60)

expected_train = 418  # Target
expected_test = 78    # Target

print(f"\nTrain set:")
for variant in ['original', 'no_abstract', 'no_conclusion', 'no_introduction',
                'no_references', 'no_experiments', 'no_methods', 'no_formulas', 'no_figures']:
    count = train_variants.get(variant, 0)
    rate = (count / expected_train) * 100
    status = "✅" if rate > 90 else "⚠️" if rate > 50 else "❌"
    print(f"  {status} {variant:20s}: {count:3d}/{expected_train} ({rate:5.1f}%)")

print(f"\nTest set:")
for variant in ['original', 'no_abstract', 'no_conclusion', 'no_introduction',
                'no_references', 'no_experiments', 'no_methods', 'no_formulas', 'no_figures']:
    count = test_variants.get(variant, 0)
    rate = (count / expected_test) * 100
    status = "✅" if rate > 90 else "⚠️" if rate > 50 else "❌"
    print(f"  {status} {variant:20s}: {count:3d}/{expected_test} ({rate:5.1f}%)")

# Identify problematic variants
print("\n\nPROBLEMATIC VARIANTS (< 50% success):")
print("=" * 60)
problematic = []
for variant in train_variants:
    train_rate = (train_variants[variant] / expected_train) * 100
    test_rate = (test_variants.get(variant, 0) / expected_test) * 100
    if train_rate < 50 or test_rate < 50:
        problematic.append((variant, train_rate, test_rate))

if problematic:
    for variant, train_rate, test_rate in problematic:
        print(f"  ❌ {variant}")
        print(f"     Train: {train_rate:.1f}% | Test: {test_rate:.1f}%")
else:
    print("  ✅ All variants have >50% success rate!")

print("\n" + "=" * 60)

