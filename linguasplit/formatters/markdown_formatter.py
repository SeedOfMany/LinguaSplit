"""
Markdown formatting module for LinguaSplit.
Converts extracted text to well-formatted Markdown with metadata.
"""

import re
from datetime import datetime
from typing import Optional, Dict, List
from .text_cleaner import TextCleaner


class MarkdownFormatter:
    """
    Formats extracted text as Markdown with metadata and structure.

    Features:
    - Auto-detection of headings (all caps, numbered sections)
    - Preserve paragraph breaks
    - Add page markers
    - Generate document metadata header
    - Clean excessive whitespace
    """

    def __init__(self, include_metadata: bool = True, include_page_markers: bool = True):
        """
        Initialize markdown formatter.

        Args:
            include_metadata: Whether to include metadata header
            include_page_markers: Whether to add page number markers
        """
        self.include_metadata = include_metadata
        self.include_page_markers = include_page_markers
        self.text_cleaner = TextCleaner(preserve_structure=True)

    def format_document(
        self,
        text: str,
        metadata: Optional[Dict] = None,
        language: Optional[str] = None,
        page_breaks: Optional[List[int]] = None
    ) -> str:
        """
        Format document text as Markdown.

        Args:
            text: Document text to format
            metadata: Optional document metadata
            language: Detected language
            page_breaks: Optional list of character positions where pages break

        Returns:
            Formatted Markdown text
        """
        if not text:
            return ""

        # Clean the text first
        text = self.text_cleaner.clean_text(text)

        # Build markdown document
        markdown_parts = []

        # Add metadata header
        if self.include_metadata:
            header = self._generate_metadata_header(metadata, language)
            if header:
                markdown_parts.append(header)
                markdown_parts.append("")  # Blank line after metadata

        # Process text to detect and format structure
        formatted_text = self._format_content(text, page_breaks)
        markdown_parts.append(formatted_text)

        return "\n".join(markdown_parts)

    def _generate_metadata_header(
        self,
        metadata: Optional[Dict] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Generate YAML-style metadata header.

        Args:
            metadata: Document metadata
            language: Detected language

        Returns:
            Formatted metadata header
        """
        if not metadata and not language:
            return ""

        lines = ["---"]

        # Add provided metadata
        if metadata:
            if 'title' in metadata:
                lines.append(f"title: {metadata['title']}")
            if 'author' in metadata:
                lines.append(f"author: {metadata['author']}")
            if 'source' in metadata:
                lines.append(f"source: {metadata['source']}")
            if 'pages' in metadata:
                lines.append(f"pages: {metadata['pages']}")

        # Add language
        if language:
            lines.append(f"language: {language}")

        # Add generation date
        lines.append(f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"tool: LinguaSplit")

        lines.append("---")

        return "\n".join(lines)

    def _format_content(self, text: str, page_breaks: Optional[List[int]] = None) -> str:
        """
        Format content with proper markdown structure.
        - Detects titles and makes them headings
        - Formats numbered/lettered lists
        - Preserves paragraph structure

        Args:
            text: Text to format
            page_breaks: Optional list of page break positions

        Returns:
            Formatted markdown text
        """
        if not text:
            return ""
        
        import re
        
        # Split into paragraphs (double newlines)
        paragraphs = text.split('\n\n')
        formatted_paragraphs = []
        
        for para in paragraphs:
            if not para.strip():
                continue
            
            lines = para.split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect and format different types of content
                
                # 1. ALL CAPS titles (but not single words)
                if re.match(r'^[A-Z][A-Z\s]{10,}$', line) and len(line.split()) > 2:
                    formatted_lines.append(f"## {line}")
                    continue
                
                # 2. Article headings
                if re.match(r'^Article\s+\w+:', line, re.IGNORECASE):
                    formatted_lines.append(f"### {line}")
                    continue
                
                # 3. Ingingo headings (Kinyarwanda)
                if re.match(r'^Ingingo\s+\w+:', line, re.IGNORECASE):
                    formatted_lines.append(f"### {line}")
                    continue
                
                # 4. Numbered lists with degree symbol (1°, 2°, 3°)
                if re.match(r'^(\d+)°\s+', line):
                    # Extract number and content
                    match = re.match(r'^(\d+)°\s+(.*)', line)
                    if match:
                        num, content = match.groups()
                        formatted_lines.append(f"{num}. {content}")
                        continue
                
                # 5. Lettered lists (a), b), c))
                if re.match(r'^([a-z])\)\s+', line):
                    # Extract letter and content
                    match = re.match(r'^([a-z])\)\s+(.*)', line)
                    if match:
                        letter, content = match.groups()
                        # Convert letter to number (a=1, b=2, etc)
                        num = ord(letter) - ord('a') + 1
                        formatted_lines.append(f"   {num}. {content}")  # Indent sub-lists
                        continue
                
                # 6. Section headings (CHAPTER, Section, TABLE OF CONTENTS)
                if re.match(r'^(CHAPTER|Section|TABLE OF CONTENTS)', line, re.IGNORECASE):
                    formatted_lines.append(f"## {line}")
                    continue
                
                # 7. Law/decree references at start
                if re.match(r'^(LAW|DECREE|Presidential Order|Pursuant to)', line):
                    formatted_lines.append(f"**{line}**")
                    continue
                
                # 8. Regular text
                formatted_lines.append(line)
            
            if formatted_lines:
                formatted_paragraphs.append('\n'.join(formatted_lines))
        
        # Join paragraphs with double newline
        result = '\n\n'.join(formatted_paragraphs)
        
        return result

    def _detect_heading(self, line: str, line_idx: int, all_lines: List[str]) -> int:
        """
        Detect if a line is a heading and determine its level.

        Args:
            line: Line to check
            line_idx: Index of line in document
            all_lines: All lines in document

        Returns:
            Heading level (1-6), or 0 if not a heading
        """
        # Skip very long lines (unlikely to be headings)
        if len(line) > 150:
            return 0

        # Skip lines that are clearly list items (start with number + ° or letter + ))
        if re.match(r'^\d+[°\)]', line) or re.match(r'^[a-z]\)', line):
            return 0

        # Check for numbered section headings (e.g., "Article 1", "Chapter 1", "Ingingo ya 1")
        if self._is_numbered_heading(line):
            # Determine level based on numbering depth
            level = self._get_numbering_depth(line)
            return min(level, 6)

        # Check for ALL CAPS headings
        if self._is_all_caps_heading(line):
            # Top-level heading if short and all caps
            if len(line) < 50:
                return 1
            return 2

        # Check for title case headings (at start of document)
        if line_idx < 5 and self._is_title_case(line):
            return 1

        # Check for section markers
        if self._is_section_marker(line):
            return 2

        return 0

    def _is_numbered_heading(self, line: str) -> bool:
        """
        Check if line is a numbered heading (not a list item).

        Args:
            line: Line to check

        Returns:
            True if numbered heading
        """
        # Only match Article/Chapter/Section headings, not list items
        patterns = [
            r'^(Chapter|Section|Part|Article|Chapitre|Ingingo|UMUTWE)\s+(ya\s+)?(\d+|One|premier|ya mbere)',  # "Chapter 1", "Article 5", "Ingingo ya 1"
            r'^[IVXLCDM]+\.\s+[A-Z]',  # Roman numerals followed by text "I. Introduction"
            r'^(LAW|ITEGEKO|LOI)\s+N[°º]',  # "LAW N° 61/2018"
        ]

        for pattern in patterns:
            if re.match(pattern, line, re.IGNORECASE):
                return True

        return False

    def _get_numbering_depth(self, line: str) -> int:
        """
        Get depth level from numbered heading.

        Args:
            line: Numbered heading line

        Returns:
            Depth level (1-6)
        """
        # Count dots in numbering (e.g., "1.2.3" = depth 3)
        match = re.match(r'^(\d+(?:\.\d+)*)', line)
        if match:
            numbering = match.group(1)
            depth = numbering.count('.') + 1
            return depth

        # Default to level 1 for other patterns
        return 1

    def _is_all_caps_heading(self, line: str) -> bool:
        """
        Check if line is an all-caps heading.

        Args:
            line: Line to check

        Returns:
            True if all caps heading
        """
        # Must have at least some letters
        if not any(c.isalpha() for c in line):
            return False

        # Check if all letters are uppercase
        letters = [c for c in line if c.isalpha()]
        if not letters:
            return False

        uppercase_ratio = sum(1 for c in letters if c.isupper()) / len(letters)

        # At least 90% uppercase and not too long
        return uppercase_ratio >= 0.9 and len(line) <= 100

    def _is_title_case(self, line: str) -> bool:
        """
        Check if line is in title case.

        Args:
            line: Line to check

        Returns:
            True if title case
        """
        words = line.split()
        if len(words) < 2 or len(words) > 15:
            return False

        # Check if most words start with capital letter
        capitalized = sum(1 for word in words if word[0].isupper())
        ratio = capitalized / len(words)

        # Allow for articles and prepositions
        return ratio >= 0.6

    def _is_section_marker(self, line: str) -> bool:
        """
        Check if line is a section marker.

        Args:
            line: Line to check

        Returns:
            True if section marker
        """
        markers = [
            'introduction',
            'abstract',
            'summary',
            'conclusion',
            'references',
            'bibliography',
            'appendix',
            'annexe',
            'résumé',
        ]

        line_lower = line.lower().strip()
        return line_lower in markers

    def _is_list_item(self, line: str) -> bool:
        """
        Check if line is a list item.

        Args:
            line: Line to check

        Returns:
            True if list item
        """
        patterns = [
            r'^\d+[°\)]\s+',  # "1° ", "2) "
            r'^[a-z]\)\s+',   # "a) ", "b) "
            r'^\d+\.\s+',     # "1. ", "2. "
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        
        return False

    def _format_list_item(self, line: str) -> str:
        """
        Format a list item for markdown with proper line wrapping.

        Args:
            line: List item line

        Returns:
            Formatted list item with wrapping for readability
        """
        # Replace various list markers with markdown bullet or number
        # Keep the original numbering but add proper markdown formatting
        
        # Determine indent level and prefix
        indent = ""
        prefix = "- "
        
        # For numbered items like "1°", "2)", keep them as-is but ensure spacing
        if re.match(r'^\d+[°\)]', line):
            prefix = "- "
        # For lettered items like "a)", "b)", keep them as-is
        elif re.match(r'^[a-z]\)', line):
            indent = "  "  # Indent sub-items
            prefix = "- "
        # For regular numbered lists "1.", "2."
        elif re.match(r'^\d+\.', line):
            prefix = "- "
        
        formatted = f"{indent}{prefix}{line}"
        
        # If line is very long, consider adding line break hints (but keep as one line for markdown)
        # Markdown will wrap naturally, but we can ensure readability
        return formatted

    def add_table_of_contents(self, text: str) -> str:
        """
        Add table of contents based on headings.

        Args:
            text: Markdown text

        Returns:
            Text with table of contents added
        """
        lines = text.split('\n')
        headings = []

        # Extract headings
        for line in lines:
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2)
                anchor = self._create_anchor(title)
                headings.append((level, title, anchor))

        if not headings:
            return text

        # Build TOC
        toc_lines = ["## Table of Contents", ""]
        for level, title, anchor in headings:
            indent = "  " * (level - 1)
            toc_lines.append(f"{indent}- [{title}](#{anchor})")

        toc_lines.append("")

        # Find where to insert TOC (after metadata)
        insert_idx = 0
        in_metadata = False
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_metadata:
                    in_metadata = True
                else:
                    insert_idx = i + 1
                    break

        # Insert TOC
        result_lines = lines[:insert_idx] + toc_lines + lines[insert_idx:]
        return "\n".join(result_lines)

    def _create_anchor(self, title: str) -> str:
        """
        Create URL-safe anchor from heading title.

        Args:
            title: Heading title

        Returns:
            URL-safe anchor
        """
        # Convert to lowercase
        anchor = title.lower()

        # Remove special characters
        anchor = re.sub(r'[^\w\s-]', '', anchor)

        # Replace spaces with hyphens
        anchor = re.sub(r'[-\s]+', '-', anchor)

        # Remove leading/trailing hyphens
        anchor = anchor.strip('-')

        return anchor

    def format_with_columns(self, columns: List[str], metadata: Optional[Dict] = None) -> str:
        """
        Format multi-column text as Markdown.

        Args:
            columns: List of column texts
            metadata: Optional metadata

        Returns:
            Formatted Markdown
        """
        parts = []

        # Add metadata
        if self.include_metadata:
            header = self._generate_metadata_header(metadata)
            if header:
                parts.append(header)
                parts.append("")

        # Format each column
        for i, column_text in enumerate(columns, 1):
            if len(columns) > 1:
                parts.append(f"## Column {i}")
                parts.append("")

            formatted = self._format_content(column_text)
            parts.append(formatted)
            parts.append("")

        return "\n".join(parts)
