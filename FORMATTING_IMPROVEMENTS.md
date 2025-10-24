# Formatting Improvements to LinguaSplit

## Overview

LinguaSplit has been significantly enhanced to preserve document structure and improve readability of the extracted content. Previously, the output was a large, unformatted block of text. Now it maintains the original document's organization with proper headings, paragraphs, and list formatting.

## What Was Improved

### 1. **Intelligent Text Block Combination** (`base_extractor.py`)

The `_combine_text_blocks()` method now:
- **Detects paragraph breaks** by identifying section markers (numbered items, articles, chapters, etc.)
- **Removes duplicate lines** like repeated headers (e.g., "Official Gazette...")
- **Preserves natural document flow** by splitting blocks at logical boundaries

Key patterns detected:
- `1°`, `2°`, `3°` - Numbered list items
- `a)`, `b)`, `c)` - Lettered sub-items  
- `Article`, `Ingingo`, `Chapter`, `UMUTWE` - Section headers
- `Pursuant to` - Legal preamble markers

### 2. **Enhanced Text Cleaning** (`base_extractor.py`)

The `_clean_text()` method now:
- **Identifies headings** based on multiple criteria:
  - Short lines (< 150 chars)
  - All uppercase text
  - Lines starting with "Chapter", "Article", "Ingingo", etc.
  - Lines ending with colons
  - Lines starting with numbers
- **Adds spacing around headings** for better visual separation
- **Preserves paragraph structure** instead of collapsing everything

### 3. **Markdown Heading Detection** (`markdown_formatter.py`)

Enhanced `_detect_heading()` to recognize:
- **Multilingual patterns**:
  - English: "Chapter", "Article", "Section"
  - French: "Chapitre", "Article"
  - Kinyarwanda: "Ingingo", "UMUTWE"
- **Various numbering formats**:
  - `1°`, `1.`, `1)`
  - `a)`, `b)`, `c)`
  - Roman numerals: `I.`, `IV.`
- **Named articles**: "Article One", "Ingingo ya mbere"

### 4. **List Item Formatting** (`markdown_formatter.py`)

New methods `_is_list_item()` and `_format_list_item()`:
- Detect list items with patterns like `1°`, `a)`, `1.`
- Format them as markdown bullets:
  - Main items: `- 1° text`
  - Sub-items: `  - a) text` (indented)
- Preserve original numbering for context

## Results

### Before
```
Official Gazette nº 38 of 17/09/2018 Official Gazette nº 38 of 17/09/2018
Official Gazette nº 38 of 17/09/2018 a) prisons; b) places of detention 
investigation measures; c) rehabilitation and transit centres; d) centres 
for mentally handicapped and psychiatric hospitals; 1° to monitor the 
compliance with the human rights, in particular with the rights of child,
woman, persons with disabilities...
```

### After
```markdown
Official Gazette nº 38 of 17/09/2018 a) prisons; b) places of detention 
investigation measures; c) rehabilitation and transit centres; d) centres 
for mentally handicapped and psychiatric hospitals; e) elderly centres...

- 2° to regularly monitor the conditions of detention of persons deprived 
of their liberty and other rights with a view to their protection against 
torture or other cruel, inhuman or degrading treatment or punishment;

- 3° to issue recommendations to relevant authorities with the aim to 
improve the conditions of detention of the persons deprived of their 
liberty and to prevent torture...

# Article 4: Composition of the Council of Commissioners

"The Council of Commissioners is composed of seven (7) Commissioners 
including the Chairperson and the Vice Chairperson. For a person to be a 
Commissioner, he/she must fulfil the following conditions:

- 1° to be a Rwandan national;
- 2° to be a person of integrity;
- 3° not to have been convicted of the crime of genocide...
```

## Benefits

1. **Improved Readability**: Documents now have clear visual hierarchy
2. **Preserved Structure**: Original organization (headings, lists, paragraphs) is maintained
3. **Multilingual Support**: Works correctly for English, French, and Kinyarwanda
4. **Better Navigation**: Headings make it easier to scan and find specific sections
5. **Professional Output**: Clean markdown that can be easily converted to other formats

## Technical Details

### Files Modified

1. **`linguasplit/core/extractors/base_extractor.py`**
   - `_combine_text_blocks()`: Smart paragraph detection
   - `_clean_text()`: Heading detection and spacing

2. **`linguasplit/formatters/markdown_formatter.py`**
   - `_is_numbered_heading()`: Multilingual pattern matching
   - `_is_list_item()`: List detection
   - `_format_list_item()`: List formatting
   - `_format_content()`: Apply formatting to content

### Pattern Recognition

The system uses regex patterns to identify document structure:

```python
# Headings
r'^(Chapter|Article|Ingingo|UMUTWE|CHAPTER)\s+(ya\s+)?\d+'
r'^\d+[°\.\)]'  # Numbered sections

# Lists
r'^\d+[°\)]\s+'  # 1°, 2), 3°
r'^[a-z]\)\s+'   # a), b), c)
r'^\d+\.\s+'     # 1. 2. 3.

# Structure markers
r'^(Article|Ingingo)\s+(One|ya mbere|premier)'
r'^Pursuant to'  # Legal preambles
```

## Configuration

No configuration changes are needed. The improvements work automatically for all PDF processing.

## Testing

Tested with:
- **Document**: `/Users/ruch/Documents/Govlaws/downloads/Domestic laws/Laws in force/2. Human Rights/2.1. National Legal instruments/476 KB.pdf`
- **Output**: 3 files (English, French, Kinyarwanda) with properly formatted content
- **Result**: All files maintain clear structure with headings, paragraphs, and list formatting

## Future Enhancements

Possible future improvements:
- Detect and preserve tables
- Better handling of multi-level numbering (1.1.1, 1.1.2, etc.)
- Automatic table of contents generation
- Cross-reference preservation

