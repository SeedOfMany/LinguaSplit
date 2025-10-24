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
        Extract text blocks from a page preserving BOTH position AND structure.
        For table-based PDFs, extracts individual spans as separate blocks.
        For regular PDFs, merges lines appropriately.

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

            # Extract text spans individually with their X positions preserved
            # This is critical for table-based PDFs where multiple languages
            # are side-by-side on the same line
            for line in block.get("lines", []):
                line_y = line['bbox'][1]

                for span in line.get("spans", []):
                    span_text = span.get("text", "").strip()
                    if not span_text:
                        continue

                    # Create a separate block for each span
                    # This preserves X-position for column detection
                    blocks.append({
                        'text': span_text,
                        'x0': span['bbox'][0],
                        'y0': span['bbox'][1],
                        'x1': span['bbox'][2],
                        'y1': span['bbox'][3]
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

    def _combine_text_blocks(self, blocks: List[Dict], separator: str = "\n") -> str:
        """
        Combine text blocks preserving reading order and paragraph structure.
        Intelligently merges blocks on the same line, filters repeated headers.

        Args:
            blocks: List of text block dictionaries (must be sorted in reading order)
            separator: String to use between paragraphs (default: single newline)

        Returns:
            Combined text string with proper paragraphs
        """
        import re

        if not blocks:
            return ""

        # Group blocks by Y-coordinate (same line) and merge them
        lines = []
        current_line = []
        current_y = None
        y_tolerance = 5  # Points tolerance for same line

        seen_short_text = {}  # Track repeated headers/footers

        for block in blocks:
            text = block.get('text', '').strip()
            if not text:
                continue

            # Skip standalone page numbers
            if len(text) <= 5 and re.match(r'^\d+$', text):
                continue

            # Track repeated short text (headers/footers)
            if len(text) < 50:
                normalized = re.sub(r'\s+', ' ', text.lower())
                if normalized in seen_short_text:
                    seen_short_text[normalized] += 1
                    # Skip if seen more than twice (repeated headers)
                    if seen_short_text[normalized] > 2:
                        continue
                else:
                    seen_short_text[normalized] = 1

            block_y = block.get('y0', 0)

            # Check if this block is on the same line as previous
            if current_y is not None and abs(block_y - current_y) < y_tolerance:
                # Same line - add with space
                current_line.append(text)
            else:
                # New line - save previous line if exists
                if current_line:
                    lines.append(' '.join(current_line))
                # Start new line
                current_line = [text]
                current_y = block_y

        # Don't forget the last line
        if current_line:
            lines.append(' '.join(current_line))

        # Join lines into paragraphs
        # Detect paragraph breaks (empty lines or major Y jumps)
        paragraphs = []
        current_paragraph = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line looks like a header/title (short, all caps, or ends with colon)
            is_header = (len(line) < 80 and
                        (line.isupper() or line.endswith(':') or
                         re.match(r'^(CHAPTER|ARTICLE|Section|Article)', line, re.I)))

            if is_header and current_paragraph:
                # Save current paragraph before header
                paragraphs.append(' '.join(current_paragraph))
                current_paragraph = []
                paragraphs.append(line)  # Header on its own line
            else:
                current_paragraph.append(line)

        # Add final paragraph
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))

        # Join paragraphs with double newline
        return '\n\n'.join(p for p in paragraphs if p.strip())

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
