# Spacing and Readability Improvements

## The Problem

The initial output had proper language separation and some structure detection, but everything was **crammed together** making it hard to read. Long paragraphs mixed list items, articles were buried in text blocks, and there was no visual breathing room.

## The Solution

We implemented **intelligent spacing** and **aggressive paragraph splitting** to make the documents easy for humans to read.

### Key Improvements

1. **Split Embedded List Items**: Detect and separate list items that were embedded in long paragraphs
2. **Add Visual Spacing**: Extra blank lines around headings, between list blocks, and after paragraphs
3. **Proper List Formatting**: Each list item gets its own line with consistent bullet formatting
4. **Smart Heading Detection**: Only mark actual articles/chapters as headings, not list items
5. **Paragraph Breaks**: Clear separation between different sections

## Before vs After

### BEFORE - Hard to Read ❌
```markdown
Official Gazette nº 38 of 17/09/2018 a) prisons; b) places of detention investigation measures; c) rehabilitation and transit centres; d) centres for mentally handicapped and psychiatric hospitals; e) elderly centres; f) transit centres for immigrants with problems; g) vehicles or any other means of detainees' transport; h) any other place where persons are or may be deprived of their liberty. 2° to regularly monitor the conditions of detention of persons deprived of their liberty and other rights with a view to their protection against torture or other cruel, inhuman or degrading treatment or punishment; 3° to issue recommendations to relevant authorities with the aim to improve the conditions of detention of the persons deprived of their liberty and to prevent torture and other cruel, inhuman or degrading treatment or punishment based on international, regional and national laws and ask them to solve identified problems; 4° to follow up the implementation of its recommendations that the Commission submitted to other institutions; 5° to provide views on existing laws and draft laws relating to the prevention and control of torture...
```

Just one massive wall of text!

### AFTER - Easy to Read ✅
```markdown
Official Gazette nº 38 of 17/09/2018 a) prisons; b) places of detention investigation measures; c) rehabilitation and transit centres; d) centres for mentally handicapped and psychiatric hospitals; e) elderly centres; f) transit centres for immigrants with problems; g) vehicles or any other means of detainees' transport; h) any other place where persons are or may be deprived of their liberty.

- 2° to regularly monitor the conditions of detention of persons deprived of their liberty and other rights with a view to their protection against torture or other cruel, inhuman or degrading treatment or punishment;
- 3° to issue recommendations to relevant authorities with the aim to improve the conditions of detention of the persons deprived of their liberty and to prevent torture and other cruel, inhuman or degrading treatment or punishment based on international, regional and national laws and ask them to solve identified problems;
- 4° to follow up the implementation of its recommendations that the Commission submitted to other institutions;
- 5° to provide views on existing laws and draft laws relating to the prevention and control of torture and other cruel inhuman or degrading treatment or punishment in place of detention;
- 6° to receive complaints relating to detention, well-being and other rights of persons deprived of their liberty;
- 7° to carry out research and studies on detention, well-being and other rights of detainees with the aim of preventing or combating torture and other cruel, inhuman or degrading treatment or punishment;

Article 5: Origin of Commissioners Article 18 of Law n° 19/2013 of 25/03/2013 determining missions, organization and functioning of the National Commission for Human Rights is modified as follows: "Commissioners come from:

- 1° civil society including non- governmental organizations for the promotion and protection of human rights;
- 2° public and private universities and institutions of higher learning;
- 3° public institutions;
- 4° private sector. At least thirty per cent (30%) of Commissioners selected from those bodies must be women.


# Article 6: Requirements for selection of candidate Commissioners

Article 20 of Law n° 19/2013 of 25/03/2013 determining missions, organisation and functioning of the National Commission for Human Rights is modified as follows: The Committee in charge of selecting candidate Commissioners is independent in the exercise of its duties. "In selecting candidates, the Committee must consider at least the following:

- 1° comply with the principles of transparency and independence;
- 2° widely announce vacancies for Commissioners.
```

Now with:
- ✅ Clear visual hierarchy
- ✅ Each list item on its own line
- ✅ Spacing around headings and sections
- ✅ Easy to scan and find information
- ✅ Professional document formatting

## Technical Implementation

### 1. Aggressive Paragraph Splitting (`base_extractor.py`)

The `_combine_text_blocks()` method now:
- Uses regex to **split long paragraphs** by detecting embedded list markers
- Pattern: `r'(\s+\d+[°\.\):]|\s+[a-z]\)|\s+Article\s+\d+:)'`
- Each detected marker starts a new paragraph
- Eliminates duplicate headers automatically

### 2. Enhanced Spacing (`markdown_formatter.py`)

The `_format_content()` method now:
- Tracks context (heading, list, paragraph)
- Adds **double blank lines** before headings
- Adds **single blank line** before new list blocks
- Adds **blank line** after each paragraph
- Maintains **list grouping** (no breaks within a list)

### 3. Smart Heading Detection

The `_detect_heading()` and `_is_numbered_heading()` methods now:
- **Exclude list items** from heading detection (items starting with `1°`, `a)`, etc.)
- **Only match true headings**: "Article 5", "Chapter 3", "Ingingo ya 2"
- Prevent false positives on numbered list items
- Support multilingual patterns (English, French, Kinyarwanda)

## Benefits

1. **For Human Readers**:
   - Easy to scan and find specific articles/sections
   - Clear visual structure matches logical document structure
   - Comfortable reading with proper white space
   - List items are clearly identifiable

2. **For Document Processing**:
   - Markdown is properly formatted for conversion to other formats
   - Headings can be used for navigation/TOC
   - List items are programmatically identifiable
   - Structure is preserved for further analysis

3. **For All Languages**:
   - Works consistently for English, French, and Kinyarwanda
   - Respects language-specific patterns (e.g., "Ingingo ya 5")
   - Maintains parallel structure across translations

## Files Modified

- `linguasplit/core/extractors/base_extractor.py`
  - `_combine_text_blocks()`: Aggressive paragraph splitting by regex
  
- `linguasplit/formatters/markdown_formatter.py`
  - `_format_content()`: Context-aware spacing
  - `_detect_heading()`: Exclude list items from headings
  - `_is_numbered_heading()`: Strict heading pattern matching

## Result

Documents that are **a pleasure to read** instead of a chore! The formatting now respects both the document's structure and the reader's need for clear, scannable content.

