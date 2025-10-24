"""
Base extractor module providing abstract interface for all extraction strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import fitz  # PyMuPDF


class BaseExtractor(ABC):
    """
    Abstract base class for all PDF text extractors.

    Provides common functionality for text extraction and requires
    subclasses to implement specific extraction strategies.
    """

    def __init__(self, language_detector=None):
        """
        Initialize the base extractor.

        Args:
            language_detector: LanguageDetector instance for identifying languages
        """
        self.language_detector = language_detector

    @abstractmethod
    def extract(self, pdf_path: str, **kwargs) -> Dict[str, str]:
        """
        Extract text from PDF and organize by language.

        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional extraction parameters

        Returns:
            Dictionary mapping language names to extracted text

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If extraction fails
        """
        pass

    def _open_pdf(self, pdf_path: str) -> fitz.Document:
        """
        Safely open a PDF document.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Opened PyMuPDF document

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be opened
        """
        try:
            doc = fitz.open(pdf_path)
            return doc
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {str(e)}")

    def _extract_text_blocks(self, page: fitz.Page) -> List[Dict]:
        """
        Extract text blocks from a page preserving original line breaks.
        Merges lines that are at the same Y-coordinate (same visual line).

        Args:
            page: PyMuPDF page object

        Returns:
            List of dictionaries containing text blocks with position data
            Each dict has: 'text', 'x0', 'y0', 'x1', 'y1'
        """
        blocks = []

        # Get text blocks with position information
        text_dict = page.get_text("dict")

        for block in text_dict.get("blocks", []):
            # Skip image blocks
            if block.get("type") != 0:
                continue

            # Extract text from lines - merge lines at same Y-coordinate
            # and track empty lines for paragraph detection
            merged_lines = []
            current_y = None
            current_line_parts = []
            
            for line in block.get("lines", []):
                # Get Y coordinate of this line
                line_y = round(line['bbox'][1], 1)  # Round to 0.1 precision
                
                # Extract text from spans
                span_texts = []
                for span in line.get("spans", []):
                    span_texts.append(span.get("text", ""))
                line_text = "".join(span_texts)
                
                # If this line is at the same Y as previous, merge them
                if current_y is not None and abs(line_y - current_y) < 2:  # Within 2 points
                    # Same visual line - append to current with space
                    current_line_parts.append(line_text)
                else:
                    # Different Y - save previous line and start new one
                    if current_line_parts:
                        merged_text = " ".join(current_line_parts).strip()
                        # Keep empty lines as markers for paragraph breaks
                        if merged_text or len(merged_lines) > 0:  # Include empty lines between content
                            merged_lines.append(merged_text)
                    
                    # Start new line
                    current_y = line_y
                    current_line_parts = [line_text]
            
            # Don't forget the last line
            if current_line_parts:
                merged_text = " ".join(current_line_parts).strip()
                if merged_text:
                    merged_lines.append(merged_text)

            # Join lines with newline to preserve PDF structure
            text = "\n".join(merged_lines)

            if text:
                blocks.append({
                    'text': text,
                    'x0': block['bbox'][0],
                    'y0': block['bbox'][1],
                    'x1': block['bbox'][2],
                    'y1': block['bbox'][3]
                })

        return blocks

    def _sort_blocks_reading_order(self, blocks: List[Dict]) -> List[Dict]:
        """
        Sort text blocks in natural reading order (page, then top-to-bottom, then left-to-right).

        Args:
            blocks: List of text block dictionaries

        Returns:
            Sorted list of text blocks
        """
        # Sort primarily by page number (if available),
        # then by y-position (top to bottom),
        # then by x-position (left to right)
        return sorted(blocks, key=lambda b: (b.get('page_num', 0), b['y0'], b['x0']))

    def _detect_block_language(self, text: str, min_length: int = 50) -> str:
        """
        Detect the language of a text block.

        Args:
            text: Text to analyze
            min_length: Minimum text length for detection

        Returns:
            Detected language name or 'unknown'
        """
        if not self.language_detector:
            return 'unknown'

        if len(text.strip()) < min_length:
            return 'unknown'

        try:
            language, confidence = self.language_detector.detect_language(text)

            # Return language only if confidence is reasonable
            if confidence > 0.5:
                return language
        except Exception:
            pass

        return 'unknown'

    def _combine_text_blocks(self, blocks: List[Dict], separator: str = "\n\n") -> str:
        """
        Combine text blocks preserving original PDF layout.
        Filters out repeated headers, page numbers, and footers.

        Args:
            blocks: List of text block dictionaries
            separator: String to use between blocks (default: double newline)

        Returns:
            Combined text string with original layout preserved
        """
        import re
        
        combined_parts = []
        seen_short_blocks = {}  # Track short blocks (likely headers) and their count
        
        for block in blocks:
            if not block.get('text'):
                continue
            
            text = block['text'].strip()
            if not text:
                continue
            
            # Skip page numbers (single digit or small numbers, usually at bottom of page)
            # Check if block is very short and only contains numbers/spaces
            if len(text) <= 5 and re.match(r'^\d+$', text):
                continue
            
            # For short blocks (< 100 chars, likely headers), track occurrences
            if len(text) < 100:
                # Normalize for comparison (remove extra spaces)
                normalized = re.sub(r'\s+', ' ', text.lower())
                
                if normalized in seen_short_blocks:
                    seen_short_blocks[normalized] += 1
                    # Skip if we've seen this exact text more than once
                    # (repeated headers across pages)
                    if seen_short_blocks[normalized] > 1:
                        continue
                else:
                    seen_short_blocks[normalized] = 1
            
            combined_parts.append(text)
        
        # Join blocks with separator to maintain block boundaries
        return separator.join(combined_parts)

    def _clean_text(self, text: str) -> str:
        """
        Minimal cleaning that preserves original PDF layout.
        Only removes excessive spaces within lines, keeps all line breaks.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text with preserved structure
        """
        import re
        
        # Split into lines to preserve line breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Only clean excessive spaces within the line
            # Don't remove the line itself even if empty (preserves spacing)
            if line.strip():
                # Remove multiple spaces, but keep the content
                line = re.sub(r' +', ' ', line.strip())
                cleaned_lines.append(line)
            else:
                # Keep empty lines to preserve vertical spacing
                cleaned_lines.append('')
        
        # Join with original line breaks
        result = '\n'.join(cleaned_lines)
        
        # Only normalize excessive blank lines (3+ becomes 2)
        result = re.sub(r'\n\n\n+', '\n\n', result)
        
        return result.strip()

    def _validate_extraction_result(self, result: Dict[str, str]) -> bool:
        """
        Validate that extraction produced meaningful results.

        Args:
            result: Extraction result dictionary

        Returns:
            True if result is valid, False otherwise
        """
        if not result:
            return False

        # Check that we have at least some text
        total_text = ''.join(result.values())
        if len(total_text.strip()) < 10:
            return False

        return True
