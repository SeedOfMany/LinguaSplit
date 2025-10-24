"""
Text preprocessing and cleaning utilities for LinguaSplit.
Handles whitespace normalization, line break cleanup, and text preparation.
"""

import re
from typing import Optional


class TextCleaner:
    """
    Utilities for cleaning and preprocessing extracted text.

    Handles excessive whitespace, line breaks, special characters,
    and formatting artifacts from PDF extraction.
    """

    def __init__(self, preserve_structure: bool = True):
        """
        Initialize text cleaner.

        Args:
            preserve_structure: Whether to preserve document structure (paragraphs, etc.)
        """
        self.preserve_structure = preserve_structure

    def clean_text(self, text: str) -> str:
        """
        Clean text using all cleaning methods.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Apply cleaning steps in order
        text = self.normalize_whitespace(text)
        text = self.fix_line_breaks(text)
        text = self.remove_artifacts(text)
        text = self.normalize_quotes(text)

        return text.strip()

    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace while preserving document structure.

        Args:
            text: Text to normalize

        Returns:
            Text with normalized whitespace
        """
        if not text:
            return ""

        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        # Replace tabs with spaces
        text = text.replace('\t', ' ')

        # Normalize line breaks (preserve paragraph breaks)
        if self.preserve_structure:
            # Keep double line breaks (paragraph separators)
            text = re.sub(r'\n{3,}', '\n\n', text)
        else:
            # Collapse all multiple line breaks
            text = re.sub(r'\n{2,}', '\n', text)

        # Remove spaces at start/end of lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)

        return text

    def fix_line_breaks(self, text: str) -> str:
        """
        Fix line breaks using empty lines as paragraph markers.
        - Single newline = same paragraph, join with space
        - Double newline (blank line) = new paragraph, keep separate

        Args:
            text: Text to fix

        Returns:
            Text with improved line breaks
        """
        if not text:
            return ""

        # Only fix hyphenated words at line end (word broken across lines)
        text = re.sub(r'-\n(\w)', r'\1', text)

        # Split into paragraphs using double newlines (blank lines)
        paragraphs = re.split(r'\n\s*\n', text)
        result_paragraphs = []
        
        for para in paragraphs:
            lines = para.split('\n')
            para_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                
                # Check if this line should be joined with previous
                should_join = False
                
                if para_lines:
                    prev_line = para_lines[-1]
                    
                    # Don't join if this line starts a new item
                    starts_new_item = re.match(r'^(\d+°|[a-z]\)|Article\s+\d+:|Ingingo\s+)', line_stripped)
                    
                    # Don't join if previous line ends with punctuation
                    prev_ends_punct = re.search(r'[;:.]$', prev_line)
                    
                    # Join if it's a continuation (lowercase or continuation word)
                    starts_lowercase = line_stripped[0].islower()
                    starts_continuation = re.match(r'^(and|or|of|by|in|to|the|for|with|as|on|from)\s', line_stripped, re.IGNORECASE)
                    
                    if not starts_new_item and not prev_ends_punct and (starts_lowercase or starts_continuation):
                        should_join = True
                
                if should_join:
                    # Join with previous line
                    para_lines[-1] = para_lines[-1] + ' ' + line_stripped
                else:
                    # New line within paragraph
                    para_lines.append(line_stripped)
            
            if para_lines:
                result_paragraphs.append('\n'.join(para_lines))
        
        # Join paragraphs with double newline
        return '\n\n'.join(result_paragraphs)

    def remove_artifacts(self, text: str) -> str:
        """
        Remove common PDF extraction artifacts.

        Args:
            text: Text to clean

        Returns:
            Text without artifacts
        """
        if not text:
            return ""

        # Remove zero-width spaces and other invisible characters
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)

        # Remove form feed characters
        text = text.replace('\f', '\n\n')

        # Remove excessive punctuation artifacts (e.g., "......")
        text = re.sub(r'\.{4,}', '...', text)
        text = re.sub(r'-{3,}', '---', text)

        # Remove common OCR artifacts
        text = re.sub(r'\|(?=\s|$)', '', text)  # Stray vertical bars
        text = re.sub(r'(?<=\s)l(?=\s)', 'I', text)  # Lowercase L as I

        return text

    def normalize_quotes(self, text: str) -> str:
        """
        Normalize quotation marks to standard forms.

        Args:
            text: Text to normalize

        Returns:
            Text with normalized quotes
        """
        if not text:
            return ""

        # Replace smart quotes with straight quotes
        text = text.replace('\u201c', '"')  # Left double quote
        text = text.replace('\u201d', '"')  # Right double quote
        text = text.replace('\u2018', "'")  # Left single quote
        text = text.replace('\u2019', "'")  # Right single quote

        # Replace double prime with double quote
        text = text.replace('\u2033', '"')

        return text

    def remove_headers_footers(self, text: str, patterns: Optional[list] = None) -> str:
        """
        Remove common header/footer patterns.

        Args:
            text: Text to clean
            patterns: Optional list of regex patterns to remove

        Returns:
            Text without headers/footers
        """
        if not text:
            return ""

        lines = text.split('\n')
        cleaned_lines = []

        # Default patterns for headers/footers
        default_patterns = [
            r'^\d+$',  # Page numbers only
            r'^Page \d+',  # "Page X"
            r'^\d+ of \d+$',  # "X of Y"
            r'^-\s*\d+\s*-$',  # "- X -"
        ]

        patterns_to_use = patterns if patterns else default_patterns

        for line in lines:
            is_header_footer = False
            for pattern in patterns_to_use:
                if re.match(pattern, line.strip(), re.IGNORECASE):
                    is_header_footer = True
                    break

            if not is_header_footer:
                cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def clean_special_chars(self, text: str, allowed_chars: Optional[str] = None) -> str:
        """
        Remove or replace special characters.

        Args:
            text: Text to clean
            allowed_chars: String of allowed special characters (default: basic punctuation)

        Returns:
            Text with special characters cleaned
        """
        if not text:
            return ""

        # Default allowed: basic punctuation and common symbols
        if allowed_chars is None:
            allowed_chars = r'.,;:!?\'"()-\[\]{}/\\\n\r '

        # Build pattern for allowed characters
        pattern = r'[^a-zA-Z0-9' + re.escape(allowed_chars) + r']'

        # Replace disallowed characters with space
        text = re.sub(pattern, ' ', text)

        # Clean up resulting whitespace
        text = self.normalize_whitespace(text)

        return text

    def extract_sentences(self, text: str) -> list:
        """
        Split text into sentences.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        if not text:
            return []

        # Clean text first
        text = self.clean_text(text)

        # Split on sentence boundaries
        # Handle common abbreviations
        text = re.sub(r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr)\.', r'\1<PERIOD>', text)
        text = re.sub(r'\b([A-Z])\.\s', r'\1<PERIOD> ', text)  # Initials

        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!?]+\s+', text)

        # Restore periods in abbreviations
        sentences = [s.replace('<PERIOD>', '.') for s in sentences]

        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def clean_for_language_detection(self, text: str) -> str:
        """
        Clean text specifically for language detection.
        Removes numbers, URLs, emails while preserving linguistic features.

        Args:
            text: Text to clean

        Returns:
            Cleaned text suitable for language detection
        """
        if not text:
            return ""

        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ' ', text)

        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)

        # Remove standalone numbers
        text = re.sub(r'\b\d+\b', ' ', text)

        # Keep letters and basic punctuation only
        text = re.sub(r'[^a-zA-Z\u0080-\uFFFF\s.,!?;:\'-]', ' ', text)

        # Normalize whitespace
        text = self.normalize_whitespace(text)

        return text
