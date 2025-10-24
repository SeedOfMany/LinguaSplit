# LinguaSplit - Multi-Language PDF Document Extractor

Create a Python application with a GUI called "LinguaSplit" that intelligently extracts text from multi-language PDFs with various layout patterns and saves each language as a separate Markdown file.

## Overview

LinguaSplit processes ANY PDF documents that contain the same content in multiple languages. These documents can have different layout patterns, and the app must automatically detect and handle each pattern appropriately.

**Key Requirements:**
- Work with ANY multi-language PDF (not just specific document types)
- Support multiple languages (not limited to specific languages)
- Automatically detect layout patterns
- Extract and separate languages into individual Markdown files
- User-friendly GUI with real-time feedback
- Robust batch processing for large document sets

## Layout Patterns to Support

### Pattern 1: Side-by-Side Columns
```
┌────────────────┬────────────────┬────────────────┐
│ Language 1     │ Language 2     │ Language 3     │
│ text...        │ text...        │ text...        │
│                │                │                │
│ more text...   │ more text...   │ more text...   │
└────────────────┴────────────────┴────────────────┘
```
**Characteristics:**
- 2 or 3 parallel columns (sometimes more)
- Same content aligned horizontally across columns
- Each column maintains the same language throughout
- Common in: legal documents, official gazettes, parliamentary records

**Detection Strategy:**
- Analyze x-coordinates of text blocks
- Look for distinct vertical clusters of x-positions
- Verify consistent x-positions within each column

### Pattern 2: Sequential Paragraphs (Alternating)
```
[Paragraph 1 in Language A]

[Same paragraph in Language B]

[Same paragraph in Language C]

[Paragraph 2 in Language A]

[Same paragraph in Language B]

[Same paragraph in Language C]
...
```
**Characteristics:**
- Languages alternate in a repeating pattern
- Each paragraph is a translation of the previous one(s)
- Pattern repeats throughout document
- Common in: meeting minutes, reports, announcements

**Detection Strategy:**
- Extract paragraphs sequentially
- Detect language of each paragraph
- Identify repeating language sequence (e.g., A→B→C→A→B→C)
- Group parallel translations

### Pattern 3: Section Blocks
```
═══════════════════════════════
SECTION 1 (Entire section in Language A)
Multiple paragraphs...
Multiple pages potentially...
═══════════════════════════════

═══════════════════════════════
SECTION 2 (Entire section in Language B)
Same content, multiple paragraphs...
Same content, multiple pages...
═══════════════════════════════

═══════════════════════════════
SECTION 3 (Entire section in Language C)
Same content, multiple paragraphs...
═══════════════════════════════
```
**Characteristics:**
- Large continuous blocks per language
- Full document content repeated in each language
- Clear language boundaries (often page breaks)
- Common in: books, long reports, manuals

**Detection Strategy:**
- Extract text sequentially
- Detect language changes
- Identify where language switches occur
- Split into large language sections

### Pattern 4: Mixed/Hybrid
- Combination of above patterns
- Some sections in columns, others sequential
- Inconsistent layouts within same document

**Detection Strategy:**
- Analyze page-by-page or section-by-section
- Apply appropriate extraction method per section
- Combine results intelligently

## Core Functionality

### 1. Automatic Layout Detection

The app must intelligently determine which layout pattern is used in each document:

```python
class LayoutDetector:
    def detect_layout(self, pdf_path):
        """
        Analyzes PDF structure and returns layout information
        
        Returns: {
            'type': 'columns' | 'sequential_paragraphs' | 'sections' | 'mixed',
            'num_languages': int,
            'languages': ['lang1', 'lang2', ...],
            'confidence': float (0.0 to 1.0),
            'details': {...}
        }
        """
```

**Detection Algorithm Steps:**

1. **Extract Text Structure**
   - Get all text blocks with position data (x, y, width, height)
   - Preserve paragraph breaks and spacing
   - Note font sizes and styles (for header detection)

2. **Analyze Spatial Distribution**
   - **X-axis analysis:** Cluster x-coordinates to find columns
     - If 2-3 distinct x-clusters with consistent gaps → likely columns
     - If all text has similar x-position → sequential layout
   - **Y-axis analysis:** Check if multiple languages appear at same y-level
     - Parallel languages at same height → columns
     - Sequential y-positions with different languages → sequential

3. **Analyze Language Patterns**
   - Extract sample text from throughout document
   - Detect language of each text block
   - Look for patterns:
     - **Columns:** Multiple languages at same vertical positions
     - **Sequential:** Regular alternating pattern (A→B→C→A→B→C)
     - **Sections:** Long runs of same language before switching

4. **Calculate Confidence Score**
   - High confidence (>90%): Clear, consistent pattern
   - Medium confidence (60-90%): Likely pattern with some anomalies
   - Low confidence (<60%): Unclear or mixed pattern

5. **Handle Edge Cases**
   - Single language documents
   - Partial translations
   - Mixed patterns within same document

### 2. Language Detection

**Flexible, Extensible Language Detection:**

The app should support ANY language, not just specific ones. Implement a multi-strategy approach:

```python
class LanguageDetector:
    def detect_language(self, text, min_confidence=0.6):
        """
        Detects language using multiple methods
        
        Returns: (language_name, confidence_score)
        """
```

**Detection Strategies (in order of preference):**

1. **Statistical Language Detection (Primary)**
   - Use `langdetect` library for broad language support
   - Supports 50+ languages out of the box
   - Good for most common languages

2. **Character Set Analysis (Backup)**
   - Detect language families by character ranges:
     - Latin scripts (English, French, Spanish, etc.)
     - Cyrillic scripts (Russian, Ukrainian, etc.)
     - Asian scripts (Chinese, Japanese, Korean)
     - Arabic scripts
     - Indic scripts
   - Useful for disambiguating similar languages

3. **Keyword Pattern Matching (Fallback)**
   - For specific known languages, use keyword lists
   - User-configurable keyword patterns
   - Examples:
     ```python
     language_patterns = {
         'kinyarwanda': ['mu', 'ku', 'kwa', 'rya', 'iya', 'n\'uko'],
         'french': ['le', 'la', 'les', 'des', 'du', 'que', 'de'],
         'english': ['the', 'of', 'and', 'to', 'in', 'is'],
         # User can add more patterns
     }
     ```

4. **Frequency Analysis**
   - Analyze letter/character frequency distribution
   - Compare against known language profiles
   - Useful for identifying similar languages

**Implementation Requirements:**
- Return language name in lowercase (e.g., 'english', 'french', 'kinyarwanda')
- Return confidence score (0.0 to 1.0)
- Handle short text samples (may have low confidence)
- Aggregate multiple samples for better accuracy
- Allow user to override/confirm detected languages

### 3. Text Extraction by Pattern

#### For Column Layout:
```python
def extract_columns(self, pdf_path):
    """
    Extract text from side-by-side columns
    
    Process:
    1. Detect column boundaries using x-position clustering
    2. For each page:
       - Sort text blocks by y-position (top to bottom)
       - Assign each block to nearest column based on x-position
       - Maintain reading order within each column
    3. Combine pages by column (all pages of column 1, then column 2, etc.)
    4. Detect language of each column's content
    5. Return {language: full_text}
    """
```

**Column Detection Algorithm:**
```python
def detect_column_boundaries(page):
    # Get x-positions of all text blocks
    x_positions = [block.x for block in page.blocks]
    
    # Cluster x-positions (k-means or simple thresholding)
    clusters = cluster_positions(x_positions, min_gap=50)
    
    # Calculate column boundaries
    # columns[i] = (x_start, x_end, column_number)
    return column_boundaries
```

#### For Sequential Paragraph Layout:
```python
def extract_sequential_paragraphs(self, pdf_path):
    """
    Extract alternating language paragraphs
    
    Process:
    1. Extract all paragraphs in reading order
    2. Detect language of each paragraph
    3. Identify repeating pattern (e.g., A→B→C→A→B→C)
       - Use sliding window to find consistent pattern
       - Account for occasional anomalies
    4. Group parallel translations:
       - Paragraphs 0, 3, 6, 9 → Language A
       - Paragraphs 1, 4, 7, 10 → Language B
       - Paragraphs 2, 5, 8, 11 → Language C
    5. Combine all paragraphs of same language
    6. Return {language: full_text}
    """
```

**Pattern Detection:**
```python
def identify_language_pattern(language_sequence):
    """
    Find repeating pattern in language sequence
    
    Example: ['en', 'fr', 'en', 'fr', 'en', 'fr']
    Returns: ['en', 'fr']
    
    Example: ['en', 'fr', 'rw', 'en', 'fr', 'rw']
    Returns: ['en', 'fr', 'rw']
    """
    # Try pattern lengths from 2 to 5
    for pattern_length in range(2, 6):
        pattern = language_sequence[:pattern_length]
        if is_repeating_pattern(language_sequence, pattern):
            return pattern
    return None
```

#### For Section Block Layout:
```python
def extract_sections(self, pdf_path):
    """
    Extract large language sections
    
    Process:
    1. Extract text sequentially (preserve page order)
    2. Analyze language in sliding windows (e.g., 500 chars)
    3. Detect language boundaries:
       - Where language changes and stays changed
       - Ignore brief mixed sections
    4. Split document at language boundaries
    5. Return {language: full_text}
    """
```

**Boundary Detection:**
```python
def detect_language_boundaries(text_blocks):
    """
    Find where language switches occur
    
    Use sliding window analysis:
    - Window size: 3-5 paragraphs or 500+ characters
    - Detect stable language regions
    - Mark boundaries where language changes
    """
    boundaries = []
    current_language = None
    
    for i, block in enumerate(text_blocks):
        window_text = " ".join([b.text for b in text_blocks[i:i+3]])
        detected_lang = detect_language(window_text)
        
        if detected_lang != current_language and detected_lang confidence > 0.7:
            boundaries.append(i)
            current_language = detected_lang
    
    return boundaries
```

### 4. Markdown Formatting

Convert extracted text to well-structured, readable Markdown:

```python
class MarkdownFormatter:
    def format_as_markdown(self, text, metadata):
        """
        Convert extracted text to Markdown with proper structure
        
        Features:
        - Document header
        - Metadata block
        - Auto-detected headings
        - Preserved formatting
        - Page markers
        """
```

**Markdown Structure:**

```markdown
# [Document Title]

**Source PDF:** original_filename.pdf  
**Language:** English  
**Extracted:** 2025-10-15 14:32:05  
**Layout Pattern:** Side-by-side columns  
**Total Pages:** 47  
**Confidence:** 95%  

---

[Main content with proper formatting]
```

**Heading Detection:**

Automatically convert text to Markdown headings based on:
- **All caps text** → `## HEADING`
- **Text with larger font size** → `## Heading` or `### Heading`
- **Numbered sections** (1., 1.1, etc.) → `### Numbered Heading`
- **Bold text on its own line** → `#### Subheading`

**Content Preservation:**
- Maintain paragraph breaks (double newline)
- Preserve bullet points and numbered lists
- Keep line breaks where intentional
- Add page break markers: `<!-- Page 2 -->`
- Preserve emphasis (bold/italic) where detectable

**Text Cleaning:**
- Remove excessive whitespace
- Fix common OCR errors (if applicable)
- Normalize line endings
- Remove header/footer repetition

### 5. Batch Processing Engine

```python
class BatchProcessor:
    def process_files(self, file_list, output_dir, settings, callback):
        """
        Process multiple PDFs efficiently
        
        Features:
        - Parallel processing (configurable threads)
        - Progress tracking
        - Error handling per file
        - Detailed logging
        - Cancellation support
        """
```

**Processing Flow:**

For each PDF file:
1. **Pre-process**
   - Validate PDF (not corrupted)
   - Check if text-extractable or needs OCR
   - Estimate processing time

2. **Detect Layout**
   - Analyze document structure
   - Determine pattern type
   - Calculate confidence

3. **Extract Text**
   - Use appropriate extraction method
   - Handle errors gracefully
   - Track progress

4. **Detect Languages**
   - Identify each language
   - Verify expected languages
   - Flag unexpected results

5. **Format & Save**
   - Convert to Markdown
   - Generate proper filenames
   - Save to output directory
   - Update log

6. **Report**
   - Log success/failure
   - Report statistics
   - Update UI

**Error Recovery:**
- Continue processing even if one file fails
- Log detailed error messages
- Attempt fallback methods
- Save partial results when possible

## User Interface

### Main Window Layout

```
╔═══════════════════════════════════════════════════════════════════╗
║  LinguaSplit - Multi-Language PDF Extractor           [_][□][X]   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  📁 Input Folder:  [C:\Documents\PDFs\_________] [Browse]        ║
║  💾 Output Folder: [C:\Output\Markdown\________] [Browse]        ║
║                                                                   ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │ 📄 Files to Process                 [🔍 Search: _________]  │ ║
║  ├─────────────────────────────────────────────────────────────┤ ║
║  │  Filename                Size      Status      Actions      │ ║
║  ├─────────────────────────────────────────────────────────────┤ ║
║  │ ☑ document_001.pdf      2.3 MB    Ready       [👁️ Preview] │ ║
║  │ ☑ report_2024.pdf       1.8 MB    Ready       [👁️ Preview] │ ║
║  │ ☑ legal_doc.pdf         4.1 MB    Scanned(*)  [👁️ Preview] │ ║
║  │ ☐ draft_notes.pdf       890 KB    Ready       [👁️ Preview] │ ║
║  │ ☑ minutes_q4.pdf        3.2 MB    Ready       [👁️ Preview] │ ║
║  │ ...                                                          │ ║
║  │                                                              │ ║
║  │ (*) May require OCR                                         │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                                                                   ║
║  [✓ Select All] [✗ Clear] [🔄 Analyze Layouts]                  ║
║  [⚙️ Settings] [📊 Process Selected (5 files)] [❌ Cancel]       ║
║                                                                   ║
║  ┌─────────────────────────────────────────────────────────────┐ ║
║  │ 📋 Processing Log                           [Clear] [Export]│ ║
║  ├─────────────────────────────────────────────────────────────┤ ║
║  │ [14:32:05] Starting batch process (5 files)...              │ ║
║  │                                                              │ ║
║  │ ✓ document_001.pdf                                          │ ║
║  │   → Layout: Columns (3 detected, confidence: 95%)           │ ║
║  │   → Languages: English, French, Kinyarwanda                 │ ║
║  │   → Extracted: 28,453 | 27,387 | 28,401 characters         │ ║
║  │   ✅ Saved: document_001_english.md                          │ ║
║  │   ✅ Saved: document_001_french.md                           │ ║
║  │   ✅ Saved: document_001_kinyarwanda.md                      │ ║
║  │   ⏱️ Time: 3.2s                                              │ ║
║  │                                                              │ ║
║  │ ⚙️ report_2024.pdf (processing...)                          │ ║
║  │   → Layout: Sequential paragraphs (confidence: 88%)         │ ║
║  │   → Pattern detected: English → French (2 languages)        │ ║
║  │   → Processing page 5 of 23...                             │ ║
║  │                                                              │ ║
║  │ ⚠️ legal_doc.pdf                                            │ ║
║  │   → Warning: Low text content detected (scanned?)           │ ║
║  │   → OCR mode: Enabled                                       │ ║
║  │   → Applying OCR... (may take longer)                      │ ║
║  │                                                              │ ║
║  └─────────────────────────────────────────────────────────────┘ ║
║                                                                   ║
║  Progress: ████████████░░░░░░░░ 60% (3/5 files)                 ║
║  ⏱️ Elapsed: 00:08:34 | Remaining: ~00:05:42 | Avg: 2.8s/file   ║
║                                                                   ║
║  Status: Processing... [❌ Stop Processing]                      ║
║  [📁 Open Output Folder] [📊 View Summary] [🔄 New Batch]        ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Settings Dialog

```
┌──────────────────────────────────────────────┐
│  ⚙️ LinguaSplit Settings              [X]   │
├──────────────────────────────────────────────┤
│                                              │
│  🔍 Layout Detection                         │
│  ┌──────────────────────────────────────┐   │
│  │ ● Auto-detect layout (recommended)    │   │
│  │ ○ Force column extraction             │   │
│  │ ○ Force sequential paragraphs         │   │
│  │ ○ Force section blocks                │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  Column Gap Threshold:                       │
│  [──────●────] 50 pixels                     │
│  (Minimum space between columns)             │
│                                              │
│  🌍 Language Settings                        │
│  ┌──────────────────────────────────────┐   │
│  │ ☑ Enable automatic language detection│   │
│  │                                       │   │
│  │ Expected Languages (optional):        │   │
│  │ [English, French, Kinyarwanda____]   │   │
│  │                                       │   │
│  │ Minimum confidence: [60]%             │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  🖼️ OCR Settings                             │
│  ┌──────────────────────────────────────┐   │
│  │ ☑ Enable OCR for scanned documents   │   │
│  │                                       │   │
│  │ Tesseract Path:                       │   │
│  │ [C:\Program Files\Tesseract\____]    │   │
│  │ [Browse...]                           │   │
│  │                                       │   │
│  │ OCR Languages:                        │   │
│  │ [eng+fra+kin________________]        │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  📄 Output Settings                          │
│  ┌──────────────────────────────────────┐   │
│  │ Filename Pattern:                     │   │
│  │ ● {filename}_{language}.md            │   │
│  │ ○ {language}/{filename}.md            │   │
│  │ ○ {filename}-{language}.md            │   │
│  │                                       │   │
│  │ ☑ Add metadata header to files       │   │
│  │ ☑ Include page break markers         │   │
│  │ ☑ Auto-detect document titles        │   │
│  │ ☑ Preserve formatting hints          │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  ⚡ Performance                               │
│  ┌──────────────────────────────────────┐   │
│  │ Parallel Processing Threads: [4]     │   │
│  │ Memory Limit: [2048] MB               │   │
│  └──────────────────────────────────────┘   │
│                                              │
│     [💾 Save] [❌ Cancel] [↺ Reset Defaults] │
└──────────────────────────────────────────────┘
```

### Preview Dialog

When user clicks "Preview" on a file:

```
┌──────────────────────────────────────────────────────┐
│  👁️ Preview: document_001.pdf                   [X] │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Detected Layout: Columns (3)                        │
│  Confidence: 95%                                     │
│  Languages: English, French, Kinyarwanda             │
│                                                      │
│  Select Language: [English ▼]                        │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ # Document Title                               │ │
│  │                                                │ │
│  │ **Source PDF:** document_001.pdf              │ │
│  │ **Language:** English                         │ │
│  │                                                │ │
│  │ ---                                            │ │
│  │                                                │ │
│  │ ## THE PARLIAMENT:                            │ │
│  │                                                │ │
│  │ The Chamber of Deputies, in its session       │ │
│  │ of 25 October 2012;                           │ │
│  │                                                │ │
│  │ The Senate, in its session of 08 February     │ │
│  │ 2013;                                          │ │
│  │                                                │ │
│  │ Pursuant to the Constitution...                │ │
│  │                                                │ │
│  │ [Preview shows first ~500 words]              │ │
│  │                                                │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  [✅ Looks Good] [⚙️ Adjust Settings] [❌ Skip File] │
└──────────────────────────────────────────────────────┘
```

### Summary Report Dialog

After processing completes:

```
┌───────────────────────────────────────────────┐
│  📊 Processing Summary                   [X] │
├───────────────────────────────────────────────┤
│                                               │
│  ✅ Batch Complete!                           │
│                                               │
│  📈 Statistics:                               │
│  ├─ Total Files: 100                          │
│  ├─ Successful: 97                            │
│  ├─ Failed: 3                                 │
│  ├─ Total Time: 00:08:23                      │
│  └─ Avg Time/File: 5.0s                       │
│                                               │
│  📄 Files Created:                            │
│  ├─ English: 97 files                         │
│  ├─ French: 97 files                          │
│  ├─ Kinyarwanda: 89 files                     │
│  └─ Total: 283 markdown files                 │
│                                               │
│  🔍 Layout Breakdown:                         │
│  ├─ Columns: 78 files                         │
│  ├─ Sequential: 15 files                      │
│  ├─ Sections: 4 files                         │
│  └─ Mixed: 0 files                            │
│                                               │
│  ⚠️ Issues:                                   │
│  ├─ document_045.pdf: Corrupted               │
│  ├─ report_old.pdf: No text found             │
│  └─ memo_draft.pdf: Single language only      │
│                                               │
│  [📁 Open Output Folder]                      │
│  [📄 Export Detailed Report]                  │
│  [✓ OK]                                       │
└───────────────────────────────────────────────┘
```

### UI Features

1. **Responsive Design**
   - Processing runs in separate thread
   - UI remains responsive during batch operations
   - Real-time log updates
   - Smooth progress bar animation

2. **User Feedback**
   - Color-coded status indicators:
     - 🟢 Green: Success
     - 🟡 Yellow: Warning
     - 🔴 Red: Error
     - ⚪ Gray: Pending
   - Tooltips on hover
   - Status messages
   - Progress percentage

3. **Error Handling**
   - Clear error messages
   - Suggested solutions
   - Option to skip or retry
   - Detailed error log

4. **Keyboard Shortcuts**
   - Ctrl+O: Open input folder
   - Ctrl+P: Process selected
   - Ctrl+A: Select all
   - Ctrl+D: Deselect all
   - Escape: Cancel operation
   - F5: Refresh file list

5. **Drag & Drop** (optional but nice)
   - Drag PDF files into window
   - Auto-add to processing queue

## Technical Specifications

### Technology Stack

**Core Language:** Python 3.8+

**Required Libraries:**
```python
# PDF Processing
PyMuPDF==1.23.8              # Primary PDF text extraction
pdfplumber==0.10.0           # Backup PDF library

# OCR (Optional but recommended)
pytesseract==0.3.10          # Tesseract wrapper
pdf2image==1.16.3            # PDF to image conversion
Pillow==10.1.0               # Image processing

# Language Detection
langdetect==1.0.9            # Statistical language detection
polyglot==16.7.4             # Alternative language detector (optional)

# GUI
tkinter                      # Built-in (Python standard library)
ttkthemes==3.2.2             # Modern themes for tkinter

# Utilities
python-magic==0.4.27         # File type detection
chardet==5.2.0               # Character encoding detection
```

### Project Structure

```
linguasplit/
│
├── main.py                          # Application entry point
│
├── gui/
│   ├── __init__.py
│   ├── main_window.py               # Main application window
│   ├── settings_dialog.py           # Settings configuration
│   ├── preview_dialog.py            # Preview window
│   ├── summary_dialog.py            # Results summary
│   └── components/
│       ├── file_list.py             # File list widget
│       ├── progress_bar.py          # Custom progress bar
│       └── log_viewer.py            # Log display widget
│
├── core/
│   ├── __init__.py
│   ├── pdf_processor.py             # Main orchestrator
│   ├── layout_detector.py           # Layout pattern detection
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── column_extractor.py      # Column-based extraction
│   │   ├── paragraph_extractor.py   # Sequential extraction
│   │   ├── section_extractor.py     # Section-based extraction
│   │   └── base_extractor.py        # Abstract base class
│   ├── language_detector.py         # Language identification
│   └── batch_processor.py           # Batch processing engine
│
├── formatters/
│   ├── __init__.py
│   ├── markdown_formatter.py        # Markdown generation
│   └── text_cleaner.py              # Text preprocessing
│
├── utils/
│   ├── __init__.py
│   ├── ocr_helper.py                # OCR utilities
│   ├── file_helper.py               # File operations
│   ├── logger.py                    # Logging system
│   └── config_manager.py            # Settings persistence
│
├── tests/
│   ├── __init__.py
│   ├── test_layout_detection.py     # Unit tests
│   ├── test_extraction.py
│   ├── test_language_detection.py
│   └── sample_pdfs/                 # Test files
│       ├── columns_3lang.pdf
│       ├── sequential_2lang.pdf
│       └── sections_3lang.pdf
│
├── resources/
│   ├── icons/                       # Application icons
│   ├── themes/                      # UI themes
│   └── config.json                  # Default configuration
│
├── requirements.txt                 # Python dependencies
├── README.md                        # Documentation
├── LICENSE                          # Software license
└── setup.py                         # Installation script
```

### Key Algorithms & Implementation Details

#### 1. Layout Detection Algorithm

```python
class LayoutDetector:
    def detect_layout_type(self, pdf_path):
        """
        Multi-stage detection process
        """
        # Stage 1: Extract structural information
        pages_data = []
        for page in pdf:
            blocks = self.extract_text_blocks(page)
            pages_data.append({
                'blocks': blocks,
                'width': page.width,
                'height': page.height
            })
        
        # Stage 2: Spatial analysis
        spatial_score = self.analyze_spatial_distribution(pages_data)
        
        # Stage 3: Language pattern analysis
        language_score = self.analyze_language_patterns(pages_data)
        
        # Stage 4: Combine scores and decide
        layout_type = self.classify_layout(spatial_score, language_score)
        confidence = self.calculate_confidence(spatial_score, language_score)
        
        return {
            'type': layout_type,
            'confidence': confidence,
            'details': {
                'spatial_analysis': spatial_score,
                'language_analysis': language_score
            }
        }
    
    def analyze_spatial_distribution(self, pages_data):
        """
        Analyze x and y positions of text blocks
        """
        # Collect all x-positions
        x_positions = []
        for page in pages_data:
            for block in page['blocks']:
                x_positions.append(block['x'])
        
        # Cluster x-positions
        x_clusters = self.cluster_positions(x_positions, min_gap=50)
        
        # Determine if columns exist
        has_columns = len(x_clusters) >= 2
        
        # Check for y-axis alignment (parallel text)
        has_parallel = self.check_parallel_text(pages_data)
        
        return {
            'has_columns': has_columns,
            'num_clusters': len(x_clusters),
            'has_parallel': has_parallel,
            'cluster_details': x_clusters
        }
    
    def analyze_language_patterns(self, pages_data):
        """
        Analyze how languages are distributed
        """
        # Extract text samples and detect languages
        language_sequence = []
        for page in pages_data:
            for block in page['blocks']:
                lang = self.quick_language_check(block['text'])
                language_sequence.append((block['y'], lang))
        
        # Sort by y-position
        language_sequence.sort(key=lambda x: x[0])
        
        # Look for patterns
        pattern = self.find_repeating_pattern([l for _, l in language_sequence])
        
        # Check for language blocks
        blocks = self.find_language_blocks(language_sequence)
        
        return {
            'has_pattern': pattern is not None,
            'pattern': pattern,
            'has_blocks': len(blocks) > 1,
            'blocks': blocks
        }
    
    def cluster_positions(self, positions, min_gap):
        """
        Cluster positions using simple threshold method
        """
        if not positions:
            return []
        
        sorted_pos = sorted(positions)
        clusters = [[sorted_pos[0]]]
        
        for pos in sorted_pos[1:]:
            if pos - clusters[-1][-1] > min_gap:
                clusters.append([pos])
            else:
                clusters[-1].append(pos)
        
        # Return cluster centers
        return [sum(cluster) / len(cluster) for cluster in clusters]
```

#### 2. Column Extraction Algorithm

```python
class ColumnExtractor:
    def extract(self, pdf_path):
        """
        Extract text from columnar layout
        """
        doc = fitz.open(pdf_path)
        
        # Detect column boundaries (only once for consistency)
        first_page = doc[0]
        column_boundaries = self.detect_column_boundaries(first_page)
        
        # Extract text column by column
        columns_text = {i: [] for i in range(len(column_boundaries))}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get all text blocks with positions
            blocks = page.get_text("dict")["blocks"]
            
            # Sort by y-position (top to bottom)
            blocks.sort(key=lambda b: b["bbox"][1])
            
            # Assign each block to a column
            for block in blocks:
                if "lines" not in block:
                    continue
                
                block_x = block["bbox"][0]
                col_idx = self.assign_to_column(block_x, column_boundaries)
                
                # Extract text from block
                text = self.extract_block_text(block)
                if text.strip():
                    columns_text[col_idx].append(text)
        
        # Combine pages for each column
        result = {}
        for col_idx, texts in columns_text.items():
            combined_text = "\n\n".join(texts)
            language = self.detect_language(combined_text)
            result[language] = combined_text
        
        return result
    
    def detect_column_boundaries(self, page):
        """
        Detect where columns begin and end
        """
        blocks = page.get_text("dict")["blocks"]
        x_positions = []
        
        for block in blocks:
            if "lines" in block:
                x_positions.append(block["bbox"][0])
        
        # Cluster x-positions
        clusters = self.cluster_positions(x_positions, min_gap=50)
        
        # Calculate column boundaries
        page_width = page.rect.width
        num_columns = len(clusters)
        
        boundaries = []
        for i, cluster_x in enumerate(clusters):
            start_x = cluster_x - 20  # Some tolerance
            end_x = cluster_x + (page_width / num_columns) + 20
            boundaries.append((start_x, end_x, i))
        
        return boundaries
```

#### 3. Sequential Paragraph Extraction

```python
class ParagraphExtractor:
    def extract(self, pdf_path):
        """
        Extract alternating language paragraphs
        """
        # Extract all paragraphs in order
        paragraphs = self.extract_all_paragraphs(pdf_path)
        
        # Detect language of each paragraph
        lang_paragraphs = []
        for para in paragraphs:
            lang, confidence = self.detect_language(para)
            lang_paragraphs.append({
                'text': para,
                'language': lang,
                'confidence': confidence
            })
        
        # Identify repeating pattern
        language_sequence = [p['language'] for p in lang_paragraphs]
        pattern = self.identify_pattern(language_sequence)
        
        if pattern:
            # Group by pattern
            grouped = self.group_by_pattern(lang_paragraphs, pattern)
        else:
            # Fallback: group by language
            grouped = self.group_by_language(lang_paragraphs)
        
        # Combine paragraphs for each language
        result = {}
        for lang, paras in grouped.items():
            result[lang] = "\n\n".join([p['text'] for p in paras])
        
        return result
    
    def identify_pattern(self, sequence, max_pattern_length=5):
        """
        Find repeating pattern in language sequence
        
        Example: ['en', 'fr', 'en', 'fr'] -> ['en', 'fr']
        """
        for length in range(2, min(max_pattern_length + 1, len(sequence) // 2 + 1)):
            pattern = sequence[:length]
            
            # Check if pattern repeats
            is_pattern = True
            for i in range(length, len(sequence)):
                expected = pattern[i % length]
                if sequence[i] != expected:
                    # Allow some tolerance
                    if self.language_similarity(sequence[i], expected) < 0.8:
                        is_pattern = False
                        break
            
            if is_pattern:
                return pattern
        
        return None
    
    def group_by_pattern(self, lang_paragraphs, pattern):
        """
        Group paragraphs according to detected pattern
        """
        grouped = {lang: [] for lang in set(pattern)}
        
        for i, para in enumerate(lang_paragraphs):
            expected_lang = pattern[i % len(pattern)]
            
            # Allow for detection errors
            if para['language'] == expected_lang or para['confidence'] < 0.6:
                grouped[expected_lang].append(para)
            else:
                # Use detected language if high confidence
                if para['language'] not in grouped:
                    grouped[para['language']] = []
                grouped[para['language']].append(para)
        
        return grouped
```

#### 4. Robust Language Detection

```python
class LanguageDetector:
    def __init__(self):
        # Initialize detection methods
        self.langdetect_available = True
        try:
            from langdetect import detect, detect_langs
            self.detect = detect
            self.detect_langs = detect_langs
        except:
            self.langdetect_available = False
        
        # Keyword patterns (user can extend)
        self.keyword_patterns = {
            'kinyarwanda': {
                'keywords': ['mu', 'ku', 'kwa', 'rya', 'iya', 'n\'uko', 'umutwe', 
                             'kandi', 'nk\'uko', 'igihe', 'cyangwa'],
                'weight': 1.0
            },
            'french': {
                'keywords': ['le', 'la', 'les', 'des', 'du', 'de', 'que', 'est', 
                             'dans', 'pour', 'avec', 'par'],
                'weight': 0.8
            },
            'english': {
                'keywords': ['the', 'of', 'and', 'to', 'in', 'is', 'that', 'for', 
                             'with', 'on', 'as'],
                'weight': 0.8
            }
        }
    
    def detect_language(self, text, min_length=100):
        """
        Multi-method language detection
        
        Returns: (language, confidence)
        """
        if len(text.strip()) < min_length:
            return ('unknown', 0.0)
        
        results = []
        
        # Method 1: langdetect library (if available)
        if self.langdetect_available:
            try:
                lang_probs = self.detect_langs(text)
                if lang_probs:
                    primary = lang_probs[0]
                    results.append((primary.lang, primary.prob))
            except:
                pass
        
        # Method 2: Keyword pattern matching
        pattern_result = self.detect_by_patterns(text)
        if pattern_result:
            results.append(pattern_result)
        
        # Method 3: Character set analysis
        charset_result = self.detect_by_charset(text)
        if charset_result:
            results.append(charset_result)
        
        # Combine results
        if results:
            # Weighted average or majority vote
            return self.combine_detection_results(results)
        
        return ('unknown', 0.0)
    
    def detect_by_patterns(self, text):
        """
        Keyword-based detection
        """
        text_lower = text.lower()
        scores = {}
        
        for lang, config in self.keyword_patterns.items():
            count = 0
            for keyword in config['keywords']:
                # Count occurrences (with word boundaries)
                pattern = r'\b' + re.escape(keyword) + r'\b'
                count += len(re.findall(pattern, text_lower))
            
            if count > 0:
                scores[lang] = count * config['weight']
        
        if scores:
            best_lang = max(scores, key=scores.get)
            confidence = min(scores[best_lang] / 20, 1.0)  # Normalize
            return (best_lang, confidence)
        
        return None
    
    def detect_by_charset(self, text):
        """
        Character set analysis
        """
        # Count character types
        latin = sum(1 for c in text if '\u0000' <= c <= '\u007F')
        latin_ext = sum(1 for c in text if '\u0080' <= c <= '\u024F')
        cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        arabic = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        # ... more character ranges
        
        total = len([c for c in text if c.isalpha()])
        if total == 0:
            return None
        
        # Determine script family
        if latin + latin_ext > 0.9 * total:
            # Could be English, French, Kinyarwanda, etc.
            # Look for accent marks to differentiate
            has_french_accents = bool(re.search(r'[éèêëàâäôöùûüÿæœç]', text.lower()))
            if has_french_accents:
                return ('french', 0.7)
            return ('latin_script', 0.5)
        
        # More script analysis...
        
        return None
    
    def combine_detection_results(self, results):
        """
        Combine multiple detection results
        """
        # Weight by confidence
        weighted_scores = {}
        for lang, conf in results:
            if lang not in weighted_scores:
                weighted_scores[lang] = 0
            weighted_scores[lang] += conf
        
        if weighted_scores:
            best_lang = max(weighted_scores, key=weighted_scores.get)
            avg_confidence = weighted_scores[best_lang] / len(results)
            return (best_lang, avg_confidence)
        
        return ('unknown', 0.0)
```

#### 5. Markdown Formatting

```python
class MarkdownFormatter:
    def format(self, text, metadata):
        """
        Convert text to well-formatted Markdown
        """
        # Generate header
        header = self.generate_header(metadata)
        
        # Process content
        content = self.format_content(text)
        
        # Combine
        markdown = f"{header}\n\n---\n\n{content}"
        
        return markdown
    
    def generate_header(self, metadata):
        """
        Create document header with metadata
        """
        title = metadata.get('title', 'Document')
        
        header = f"# {title}\n\n"
        header += f"**Source PDF:** {metadata['source_file']}\n"
        header += f"**Language:** {metadata['language'].title()}\n"
        header += f"**Extracted:** {metadata['timestamp']}\n"
        header += f"**Layout Pattern:** {metadata['layout_type']}\n"
        header += f"**Total Pages:** {metadata['page_count']}\n"
        
        if 'confidence' in metadata:
            header += f"**Confidence:** {metadata['confidence']:.0%}\n"
        
        return header
    
    def format_content(self, text):
        """
        Format main content with proper structure
        """
        lines = text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                formatted_lines.append('')
                continue
            
            # Detect and format headings
            if self.is_heading(line):
                level = self.detect_heading_level(line)
                formatted_line = '#' * level + ' ' + line
                formatted_lines.append(formatted_line)
            else:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def is_heading(self, line):
        """
        Determine if a line is likely a heading
        """
        # Heuristics for heading detection
        
        # All caps (at least 3 words)
        if line.isupper() and len(line.split()) >= 3:
            return True
        
        # Numbered section (1., 1.1, etc.)
        if re.match(r'^\d+(\.\d+)*\.?\s+[A-Z]', line):
            return True
        
        # Short line followed by content (title-like)
        if len(line) < 100 and not line.endswith('.'):
            # Would need context to determine
            # For now, use simple heuristic
            pass
        
        return False
    
    def detect_heading_level(self, line):
        """
        Determine heading level (1-6)
        """
        # Level 2 for major sections (all caps)
        if line.isupper():
            return 2
        
        # Level 3 for numbered sections
        if re.match(r'^\d+\.', line):
            return 3
        
        # Level 4 for sub-sections
        if re.match(r'^\d+\.\d+', line):
            return 4
        
        return 2  # Default
```

### Error Handling & Recovery

```python
class ErrorHandler:
    """
    Centralized error handling
    """
    
    @staticmethod
    def handle_pdf_error(pdf_path, error, logger):
        """
        Handle PDF-related errors
        """
        error_type = type(error).__name__
        
        if "damaged" in str(error).lower() or "corrupted" in str(error).lower():
            logger.error(f"❌ {pdf_path}: PDF is corrupted or damaged")
            logger.info(f"   Suggestion: Try repairing with 'gs' or 'pdftk'")
            return 'corrupted'
        
        elif "password" in str(error).lower() or "encrypted" in str(error).lower():
            logger.error(f"❌ {pdf_path}: PDF is password-protected")
            logger.info(f"   Suggestion: Remove password protection first")
            return 'encrypted'
        
        elif "no text" in str(error).lower():
            logger.warning(f"⚠️ {pdf_path}: No text found (scanned document?)")
            logger.info(f"   Suggestion: Enable OCR in settings")
            return 'no_text'
        
        else:
            logger.error(f"❌ {pdf_path}: {error_type}: {str(error)}")
            return 'unknown_error'
    
    @staticmethod
    def attempt_recovery(pdf_path, error_type):
        """
        Attempt to recover from error
        """
        if error_type == 'no_text':
            # Try OCR
            return 'try_ocr'
        
        elif error_type == 'corrupted':
            # Try repair (if tools available)
            return 'try_repair'
        
        return 'skip'
```

## Configuration & Persistence

### Settings File (JSON)

```json
{
  "version": "1.0.0",
  "layout_detection": {
    "auto_detect": true,
    "force_mode": null,
    "column_gap_threshold": 50,
    "min_confidence": 0.6
  },
  "language_detection": {
    "auto_detect": true,
    "expected_languages": [],
    "min_confidence": 0.6,
    "custom_patterns": {}
  },
  "ocr": {
    "enabled": true,
    "tesseract_path": "",
    "languages": "eng+fra+kin",
    "fallback_to_ocr": true
  },
  "output": {
    "filename_pattern": "{filename}_{language}.md",
    "add_metadata": true,
    "include_page_breaks": true,
    "auto_detect_title": true,
    "preserve_formatting": true
  },
  "performance": {
    "parallel_threads": 4,
    "memory_limit_mb": 2048,
    "process_page_by_page": true
  },
  "ui": {
    "theme": "default",
    "show_preview_by_default": false,
    "auto_open_output_folder": false
  }
}
```

## Testing Strategy

### Unit Tests

```python
# tests/test_layout_detection.py
def test_column_detection():
    """Test column layout detection"""
    detector = LayoutDetector()
    result = detector.detect_layout('tests/sample_pdfs/columns_3lang.pdf')
    
    assert result['type'] == 'columns'
    assert result['confidence'] > 0.8
    assert result['details']['num_columns'] == 3

def test_sequential_detection():
    """Test sequential paragraph detection"""
    # Similar tests...

# tests/test_extraction.py
def test_column_extraction_accuracy():
    """Test extraction accuracy for column layout"""
    # Load known PDF
    # Extract text
    # Compare with ground truth
    # Assert accuracy > threshold

# tests/test_language_detection.py
def test_language_detection():
    """Test language detection accuracy"""
    detector = LanguageDetector()
    
    # Test samples
    assert detector.detect_language("This is English text")[0] == 'english'
    assert detector.detect_language("Ceci est du français")[0] == 'french'
    # More tests...
```

### Integration Tests

- Test end-to-end processing
- Test with real-world PDFs
- Test batch processing
- Test error handling

### Performance Tests

- Measure processing time for large batches
- Monitor memory usage
- Test with large PDFs (100+ pages)
- Verify no memory leaks

## Documentation Requirements

### README.md

Should include:

1. **Introduction**
   - What is LinguaSplit?
   - What problems does it solve?
   - Key features

2. **Installation**
   ```bash
   # Clone repository
   git clone https://github.com/yourusername/linguasplit.git
   cd linguasplit
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Optional: Install Tesseract for OCR
   # Windows: choco install tesseract
   # Mac: brew install tesseract
   # Linux: sudo apt-get install tesseract-ocr
   ```

3. **Quick Start**
   ```bash
   # Run the application
   python main.py
   ```
   - Step-by-step guide with screenshots
   - Example workflow

4. **Supported Document Types**
   - Examples of each layout pattern
   - Supported languages
   - Limitations

5. **Advanced Usage**
   - Settings explanation
   - Command-line mode (if implemented)
   - Customization options

6. **Troubleshooting**
   - Common issues
   - Error messages
   - FAQ

7. **Contributing**
   - How to contribute
   - Code standards
   - Testing requirements

8. **License**
   - Open source license (MIT recommended)

### User Guide (Separate Document)

- Detailed walkthrough
- Best practices
- Tips for different document types
- Examples and screenshots

## Deliverables Checklist

Please create a complete, production-ready application with:

### Core Functionality
- ✅ Automatic layout detection for all three patterns
- ✅ Robust language detection (extensible)
- ✅ Column extraction algorithm
- ✅ Sequential paragraph extraction
- ✅ Section block extraction
- ✅ Markdown formatting with metadata
- ✅ Batch processing engine

### User Interface
- ✅ Main window with file list
- ✅ Settings dialog
- ✅ Preview functionality
- ✅ Real-time progress tracking
- ✅ Detailed logging
- ✅ Summary report

### Quality & Reliability
- ✅ Comprehensive error handling
- ✅ Graceful failure recovery
- ✅ Input validation
- ✅ Memory-efficient processing
- ✅ Thread-safe operations

### Documentation
- ✅ README.md with installation & usage
- ✅ Code documentation (docstrings)
- ✅ Example files or test suite
- ✅ Troubleshooting guide

### Configuration
- ✅ Settings persistence (JSON config)
- ✅ User-customizable patterns
- ✅ Adjustable parameters

### Optional (Nice to Have)
- ⭐ Command-line interface mode
- ⭐ Drag-and-drop support
- ⭐ Export processing log to CSV
- ⭐ Dark mode theme
- ⭐ Multi-language UI (for app itself)
- ⭐ PDF repair functionality
- ⭐ Automatic updates check

## Success Criteria

The application is considered successful when it:

1. ✅ **Accurately detects** layout patterns with >85% confidence
2. ✅ **Correctly extracts** text from all three layout types
3. ✅ **Properly identifies** multiple languages automatically
4. ✅ **Generates clean** Markdown files with proper structure
5. ✅ **Processes batches** of 100+ files without crashes
6. ✅ **Handles errors** gracefully and provides helpful feedback
7. ✅ **Provides clear UI** that non-technical users can operate
8. ✅ **Performs efficiently** (process typical document in <5 seconds)
9. ✅ **Maintains quality** across different PDF types and sources
10. ✅ **Is well-documented** with clear instructions

## Important Notes

1. **Generality**: This tool must work with ANY multi-language PDF, not just specific document types
2. **Robustness**: Handle edge cases and unexpected layouts gracefully
3. **User Experience**: Prioritize clear feedback and error messages
4. **Performance**: Optimize for batch processing of large document sets
5. **Extensibility**: Allow users to add custom language patterns
6. **Quality**: Focus on accuracy over speed
7. **Documentation**: Provide comprehensive documentation

This application will be used to process important official documents, so **reliability and accuracy are critical**.

Please implement this application with clean, well-organized, maintainable code. Use proper object-oriented design principles, include comprehensive error handling, and write clear documentation.

Focus on creating a production-quality tool that users can trust with their important documents.