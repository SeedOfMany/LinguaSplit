# Duplicate Files Issue - Fixed

## Problem

When processing PDFs, LinguaSplit was creating more files than necessary:

1. **Duplicate language files** - Files with suffixes like `_2`, `_3`, `_4`
   - Example: `584 KB_french.md`, `584 KB_french_4.md`

2. **Incorrect language detection** - Files labeled with wrong language codes
   - Example: `385 KB_ca.md` (Catalan) when it was actually French

## Root Causes

### Issue 1: Duplicate Language Files

**Location**: `linguasplit/core/extractors/column_extractor.py` (lines 89-91)

**Problem**: When the same language was detected in multiple columns, the code was creating separate files with numeric suffixes instead of merging the content.

```python
# OLD CODE (WRONG)
if language in result:
    # If language already exists, append with suffix
    result[f"{language}_{column_id}"] = column_text
else:
    result[language] = column_text
```

**Why it happened**: 
- PDFs with 3-5 columns might have the same language detected in multiple columns
- Instead of merging the content, it created separate files for each column

### Issue 2: Language Misdetection

**Location**: `linguasplit/core/language_detector.py` (lines 102-140)

**Problem**: The `langdetect` library sometimes confuses similar languages:
- **French ↔ Catalan** (both Romance languages)
- **Kinyarwanda ↔ Swahili** (both Bantu languages)

**Examples**:
- Text: "Le Comité de sélection des candidats Commissaires..."
  - Detected as: `ca` (Catalan) ❌
  - Should be: `fr` (French) ✅

- Text: "Ingingo ya mbere Komisiyo y'Igihugu..."
  - Detected as: `sw` (Swahili) ❌
  - Should be: `rw` (Kinyarwanda) ✅

## Solutions Implemented

### Fix 1: Merge Same-Language Content

**File**: `linguasplit/core/extractors/column_extractor.py`

**Change**:
```python
# NEW CODE (CORRECT)
# Skip if language is unknown or invalid
if language == 'unknown' or not language:
    continue

# Add to result - merge if language already exists
if language in result:
    # Same language detected in multiple columns - merge with separator
    result[language] += "\n\n" + column_text
else:
    result[language] = column_text
```

**Benefits**:
- ✅ No more duplicate files (`_2`, `_3`, etc.)
- ✅ Content from same language is merged into one file
- ✅ Proper paragraph separation maintained with `\n\n`
- ✅ Skips 'unknown' language to avoid empty files

### Fix 2: Language Misdetection Correction

**File**: `linguasplit/core/language_detector.py`

**Change**:
```python
# Handle Catalan misdetection - often confuses French with Catalan
if primary.lang == 'ca':
    # Check if it's actually French
    french_keywords = ['le', 'la', 'de', 'et', 'est', 'que', 'des', 'les',
                      'dans', 'pour', 'son', 'une', 'par', 'du', 'commission']
    text_lower = text.lower()
    french_count = sum(1 for keyword in french_keywords 
                      if f' {keyword} ' in f' {text_lower} ')
    
    # If we find many French keywords, it's likely French
    if french_count >= 5:
        return ('french', 0.9)  # High confidence for French

# Handle Swahili misdetection - often confuses Kinyarwanda with Swahili
if primary.lang == 'sw':
    # Check if it's actually Kinyarwanda
    kiny_keywords = ['ingingo', 'komisiyo', 'abakomiseri', 'perezida', 'repubulika',
                    'itegeko', 'umutwe', 'umukomiseri', 'umwanya', 'abakozi',
                    'rwandaise', 'kigali', 'mu rwanda', 'ry\'u rwanda']
    text_lower = text.lower()
    kiny_count = sum(1 for keyword in kiny_keywords if keyword in text_lower)
    
    # If we find many Kinyarwanda keywords, it's likely Kinyarwanda
    if kiny_count >= 3:
        return ('kinyarwanda', 0.95)  # Very high confidence
```

**How it works**:
1. When `langdetect` returns `ca` (Catalan) or `sw` (Swahili)
2. Check for language-specific keywords
   - French: le, la, de, et, commission, etc.
   - Kinyarwanda: ingingo, komisiyo, abakomiseri, perezida, etc.
3. If enough keywords found, reclassify with high confidence
4. This catches the misdetection before it creates wrong files

## Test Results

### Before Fix
```
385 KB_ca.md              ❌ Wrong language (should be French)
385 KB_english.md         ✅
385 KB_kinyarwanda.md     ✅

584 KB_english.md         ✅
584 KB_english_2.md       ❌ Duplicate
584 KB_english_3.md       ❌ Duplicate
584 KB_french.md          ✅
584 KB_french_4.md        ❌ Duplicate
584 KB_swahili.md         ❌ Wrong language (should be Kinyarwanda)
```

**Issues**: 5 unnecessary/wrong files out of 9 total

### After Fix
```
385 KB_english.md         ✅
385 KB_french.md          ✅ Fixed (was 'ca')
385 KB_kinyarwanda.md     ✅

584 KB_english.md         ✅ Merged content
584 KB_french.md          ✅ Merged content
584 KB_kinyarwanda.md     ✅ Fixed (was 'swahili')
```

**Result**: Clean output - exactly 3 files per PDF (one per language)

## Benefits

1. **Clean Output** - No more confusing duplicate files
2. **Correct Languages** - Proper detection:
   - French (not Catalan)
   - Kinyarwanda (not Swahili)
3. **Complete Content** - Same-language content merged into single file
4. **Better Organization** - Easy to find the right file for each language

## Verification

To verify the fix works on your PDFs:

```bash
cd /Users/ruch/Documents/Projects/LinguaSplit
source venv/bin/activate

# Process your PDFs
python main.py

# Check for issues
ls -1 /path/to/output/*.md

# Should see:
# - One file per language per PDF
# - No _2, _3, _4 suffixes
# - No _ca files (unless actually Catalan)
```

## Summary

**Fixed in**:
- `linguasplit/core/extractors/column_extractor.py` - Merge same-language content
- `linguasplit/core/language_detector.py` - Correct Catalan → French misdetection

**Result**: Clean, organized output with exactly the files you need! ✅

