# Paper Variant Generation Logic Documentation

## 📋 Core Improvements

### Previous Issues
- Only checked the length of generated results
- Could not distinguish between "paper lacks this section" and "generation failed"
- Example: A paper without an Experiments section would be identical after deletion, but was judged as success

### Current Solution
Each variant function returns a tuple `(processed_text, content_matched)`

```python
def variant_no_abstract(text: str) -> tuple[str, bool]:
    """Remove abstract section"""
    result = RE_ABSTRACT.sub("\n", text)
    matched = RE_ABSTRACT.search(text) is not None  # Check if abstract was matched
    return result, matched
```

---

## ✅ 5-Layer Success Criteria for Variant Generation

### Layer 1: Original Text Validity
```python
if not original_text or not isinstance(original_text, str):
    return [], False  # ❌ Failure
```

### Layer 2: Function Execution Without Exceptions
```python
try:
    result = func(original_text)
except Exception:
    # ❌ Failure
```

### Layer 3: Return Value Type Check
```python
if variant_text is None:              # ❌ Failure
elif not isinstance(variant_text, str):  # ❌ Failure
```

### Layer 4: **Regex Match Check (New!)**
```python
if variant_name != "original" and not matched:
    # ❌ Failure: Did not match content to delete
    print(f"[WARN] Variant {variant_name} matched no content, paper may lack this section")
```

### Layer 5: Generated Result Length Check
```python
if len(variant_text) < 50 and variant_name != "original":
    # ❌ Failure: Text too short after deletion
```

---

## 🎯 Real-World Application Scenarios

### Scenario 1: Paper Lacks a Section
```
Paper A has no "Experiments" section
→ variant_no_experiments returns (original_text, False)
→ matched = False
→ Strict mode: Entire paper discarded, supplement with new paper
→ Lenient mode: Skip this variant, keep other variants
```

### Scenario 2: Regex Match Error Causing Over-deletion
```
Paper B has "Experiments" section
→ variant_no_experiments returns (30 chars text, True)
→ matched = True, but length < 50
→ Judged as failure (possible regex issue)
```

### Scenario 3: Normal Generation
```
Paper C has "Experiments" section
→ variant_no_experiments returns (3500 chars text, True)
→ matched = True, length >= 50
→ ✅ Successfully generated variant
```

---

## 📊 Mode Comparison

| Mode | Behavior on Single Variant Failure | Data Quality | Data Quantity |
|------|-----------------------------------|--------------|---------------|
| **Strict Mode** (default) | Discard entire paper<br>Supplement with new paper from pool | High (all papers have complete 9 variants) | Stable |
| **Lenient Mode** | Skip failed variant<br>Keep other successful variants | Lower (inconsistent variant counts) | Possibly less |

---

## 🔧 Configuration

```python
# Configure at top of file
STRICT_MODE = True  # Recommended to use strict mode
MAX_RETRY_ATTEMPTS = 100  # Maximum supplementary attempts
```

---

## 📈 Statistics Output Example

```
[INFO] Train set: Total 1000 papers, target sample 100 papers
[WARN] Variant no_experiments matched no content (Paper A), paper may lack this section
[INFO] Strict mode: Paper 'Paper A' discarded due to variant no_experiments failure
[INFO] Supplementing paper: Paper B (Attempt 1/100)
...
[INFO] Train set total variants: 900
[INFO] ========== Dataset Statistics ==========
Train set:
  - Target paper count: 100
  - Actual success count: 100
  - Variant type count: 9
  - Total sample count: 900
```

---

## 🎓 Summary

**Improved judgment logic is more intelligent:**
- ✅ Can identify whether paper contains specific sections
- ✅ Can distinguish between "missing section" and "generation failure"
- ✅ Ensures dataset quality and consistency
- ✅ Provides detailed failure reason logs

This makes the generated dataset more reliable for model training!

