# Language Detection Issues & Solutions

## Problem Description

You're experiencing two main issues:
1. **False language detection** - The app creates MD files for languages that aren't actually in the document
2. **Content not separated** - All language files contain the same mixed content instead of being properly separated by language

## Why This Happens

### Root Causes:

1. **Short Text Chunks**: Language detection requires sufficient text (minimum 50-100 characters). Shorter paragraphs often return "unknown" or incorrect languages.

2. **Mixed Content**: If your PDF has mixed language content within the same paragraph (e.g., "This is English avec quelques mots en français"), the detector picks the dominant language, which may not be what you expect.

3. **Low Confidence Detection**: When text is ambiguous, the system may detect multiple languages with low confidence, creating extra files.

4. **No Actual Language Separation**: If your PDF doesn't have clear language-based sections (e.g., all paragraphs are in one language, or languages are randomly mixed), the app can't separate them meaningfully.

## Diagnosis Tool

I've created a diagnostic tool to analyze your PDFs. Run it like this:

```bash
source venv/bin/activate
python diagnose_pdf.py your_file.pdf
```

This will show you:
- What languages are detected in each paragraph
- Whether a repeating pattern is found
- Why certain content might be misclassified
- Recommendations for your specific document

## Solutions

### Solution 1: Increase Minimum Paragraph Length

Edit the configuration to require longer text for language detection:

```bash
source venv/bin/activate
python main.py
```

Then in **Settings**:
- Set "Minimum Paragraph Length" to **150** (default is 50)
- This will skip short paragraphs that cause false detections

### Solution 2: Filter Out Low-Confidence Detections

Modify `/linguasplit/core/extractors/base_extractor.py` line 121:

```python
def _detect_block_language(self, text: str, min_length: int = 50) -> str:
    # ...existing code...
    
    language, confidence = self.language_detector.detect_language(text)
    
    # Add minimum confidence threshold
    if confidence < 0.6:  # Only accept 60%+ confidence
        return 'unknown'
    
    return language
```

### Solution 3: Check Your PDF Structure

Use the diagnostic tool to understand your PDF:

```bash
python diagnose_pdf.py your_file.pdf
```

#### If you see many "unknown" paragraphs:
- Your paragraphs are too short
- Increase minimum paragraph length in settings

#### If you see many different languages:
- False positives from ambiguous short text
- Consider using Solution 2 (confidence threshold)

#### If no pattern is detected:
- Your PDF doesn't have a repeating language structure
- Content will be grouped by language (all English together, all French together)
- This is normal for documents without parallel translations

### Solution 4: Manual Language Hints

If you know what languages are in your document, you can provide hints:

In the processing config:
```python
config = {
    'language_hints': ['english', 'french'],  # Only expect these languages
    'save_separate': True
}
```

### Solution 5: Single Language Documents

If your PDF is actually in **one language only** but getting split incorrectly:

1. Check with diagnostic tool: `python diagnose_pdf.py your_file.pdf`
2. If it confirms single language, the app is working correctly - it just detects one language
3. You'll get one output file for that language

## Understanding Output Files

### Normal Behavior:

**For a document with English and French:**
```
document_english.md    <- All English content
document_french.md     <- All French content
```

### What You're Seeing (Problem):

```
document_english.md    <- Mixed content (English + French)
document_french.md     <- Mixed content (English + French) 
document_spanish.md    <- False detection (not in document)
document_unknown.md    <- Short/ambiguous paragraphs
```

## Quick Fixes to Try Now

### Fix 1: Increase Minimum Length
```bash
source venv/bin/activate
python main.py
# In Settings -> Processing
# Set "Minimum Paragraph Length" to 150 or 200
```

### Fix 2: Run Diagnostic First
```bash
source venv/bin/activate
python diagnose_pdf.py /path/to/your/file.pdf
```

This will tell you exactly what's being detected and why.

### Fix 3: Check One of Your Output Files

Look at one of the generated `.md` files:
- Is the content actually in that language?
- Or is it mixed?
- If mixed, the separation isn't working

## Expected Document Types

LinguaSplit works best with:

✅ **Parallel translations** - Same content in multiple languages, paragraph by paragraph
- Example: Paragraph 1 (English), Paragraph 2 (French), Paragraph 3 (English), Paragraph 4 (French)...

✅ **Section-based** - Large sections in one language, then another
- Example: Pages 1-5 (English), Pages 6-10 (French)

✅ **Column-based** - Multiple columns, each in a different language
- Example: Left column (English), Right column (French)

❌ **Within-paragraph mixing** - Multiple languages in the same paragraph
- Example: "This sentence is English. Cette phrase est français." (in same paragraph)
- This is very hard to separate reliably

## Next Steps

1. **Run the diagnostic tool** on one of your PDFs:
   ```bash
   python diagnose_pdf.py your_file.pdf
   ```

2. **Share the output with me** so I can see exactly what's being detected

3. **Based on the diagnostic**, I can:
   - Adjust the detection thresholds
   - Fix the grouping logic
   - Add confidence filters
   - Modify the extraction strategy

## Example Usage

```bash
# Activate environment
source venv/bin/activate

# Diagnose your PDF
python diagnose_pdf.py ~/Documents/my_document.pdf

# Review the output to understand what's happening

# Then re-process with adjusted settings
python main.py
```

---

**To fix your specific issue**, please run the diagnostic tool on one of your PDFs and share the output. That will tell us exactly what's going wrong!

