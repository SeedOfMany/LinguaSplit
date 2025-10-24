"""
Section-based text extraction for large language sections in PDFs.

Uses sliding window approach to detect language boundaries and split
documents into major language sections.
"""

from typing import Dict, List, Tuple, Optional
from .base_extractor import BaseExtractor


class SectionExtractor(BaseExtractor):
    """
    Extracts text from PDFs organized in large language sections.

    Uses a sliding window to detect where language changes occur,
    then splits the document at these boundaries. Ideal for documents
    with large continuous sections in each language.
    """

    def __init__(self, language_detector=None):
        """
        Initialize the section extractor.

        Args:
            language_detector: LanguageDetector instance
        """
        super().__init__(language_detector)

    def extract(self, pdf_path: str, **kwargs) -> Dict[str, str]:
        """
        Extract text from sectioned PDF.

        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters
                - window_size: Number of blocks for sliding window (default: 5)
                - min_section_size: Minimum blocks in a section (default: 3)
                - confidence_threshold: Minimum confidence for language detection (default: 0.6)

        Returns:
            Dictionary mapping language names to extracted text

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If extraction fails
        """
        window_size = kwargs.get('window_size', 5)
        min_section_size = kwargs.get('min_section_size', 3)
        confidence_threshold = kwargs.get('confidence_threshold', 0.6)

        try:
            doc = self._open_pdf(pdf_path)
            all_blocks = []

            # Extract all text blocks from all pages
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = self._extract_text_blocks(page)
                all_blocks.extend(blocks)

            doc.close()

            if not all_blocks:
                raise ValueError("No text blocks found in PDF")

            # Sort all blocks in reading order
            all_blocks = self._sort_blocks_reading_order(all_blocks)

            # Detect language boundaries using sliding window
            boundaries = self._detect_language_boundaries(
                all_blocks, window_size, confidence_threshold
            )

            # Split into sections based on boundaries
            sections = self._split_into_sections(all_blocks, boundaries)

            # Filter small sections
            sections = [s for s in sections if len(s['blocks']) >= min_section_size]

            if not sections:
                raise ValueError("No valid sections found")

            # Group sections by language
            result = self._group_sections_by_language(sections)

            if not self._validate_extraction_result(result):
                raise ValueError("Extraction produced no meaningful text")

            return result

        except Exception as e:
            raise ValueError(f"Section extraction failed: {str(e)}")

    def _detect_language_boundaries(self, blocks: List[Dict], window_size: int,
                                   confidence_threshold: float) -> List[int]:
        """
        Detect language change boundaries using sliding window.

        Args:
            blocks: List of text blocks in reading order
            window_size: Size of sliding window
            confidence_threshold: Minimum confidence for detection

        Returns:
            List of indices where language changes occur
        """
        if len(blocks) < window_size * 2:
            return []

        boundaries = []
        current_language = None

        for i in range(0, len(blocks) - window_size + 1):
            # Get window of blocks
            window = blocks[i:i + window_size]

            # Combine text from window
            window_text = ' '.join(b['text'] for b in window)

            # Detect language
            lang, confidence = self._detect_language_with_confidence(window_text)

            # Check if language changed with sufficient confidence
            if confidence >= confidence_threshold:
                if current_language is None:
                    current_language = lang
                elif lang != current_language and lang != 'unknown':
                    # Language boundary detected
                    boundaries.append(i)
                    current_language = lang

        return boundaries

    def _detect_language_with_confidence(self, text: str) -> Tuple[str, float]:
        """
        Detect language with confidence score.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (language, confidence)
        """
        if not self.language_detector:
            return ('unknown', 0.0)

        try:
            return self.language_detector.detect_language(text)
        except Exception:
            return ('unknown', 0.0)

    def _split_into_sections(self, blocks: List[Dict],
                            boundaries: List[int]) -> List[Dict]:
        """
        Split blocks into sections based on boundaries.

        Args:
            blocks: List of text blocks
            boundaries: List of boundary indices

        Returns:
            List of section dictionaries with 'blocks' and 'language'
        """
        sections = []
        start_idx = 0

        # Add boundaries including the end
        all_boundaries = boundaries + [len(blocks)]

        for boundary in all_boundaries:
            # Extract section blocks
            section_blocks = blocks[start_idx:boundary]

            if section_blocks:
                # Detect section language from combined text
                section_text = ' '.join(b['text'] for b in section_blocks)
                language, confidence = self._detect_language_with_confidence(section_text)

                sections.append({
                    'blocks': section_blocks,
                    'language': language,
                    'confidence': confidence,
                    'start_index': start_idx,
                    'end_index': boundary
                })

            start_idx = boundary

        return sections

    def _group_sections_by_language(self, sections: List[Dict]) -> Dict[str, str]:
        """
        Group sections by language and combine text.

        Args:
            sections: List of section dictionaries

        Returns:
            Dictionary mapping languages to combined text
        """
        grouped = {}

        for section in sections:
            lang = section['language']

            # Combine section text
            section_text = self._combine_text_blocks(section['blocks'])

            if lang not in grouped:
                grouped[lang] = []

            grouped[lang].append(section_text)

        # Combine all sections for each language
        result = {}
        for lang, texts in grouped.items():
            combined = '\n\n'.join(texts)
            result[lang] = self._clean_text(combined)

        return result

    def analyze_sections(self, pdf_path: str, window_size: int = 5) -> Dict:
        """
        Analyze document section structure.

        Useful for understanding the document layout before extraction.

        Args:
            pdf_path: Path to the PDF file
            window_size: Window size for boundary detection

        Returns:
            Dictionary with section analysis results
        """
        try:
            doc = self._open_pdf(pdf_path)
            all_blocks = []

            # Sample pages for analysis
            sample_pages = min(10, len(doc))
            for page_num in range(sample_pages):
                page = doc[page_num]
                blocks = self._extract_text_blocks(page)
                all_blocks.extend(blocks)

            doc.close()

            if not all_blocks:
                return {'error': 'No text blocks found'}

            # Sort blocks
            all_blocks = self._sort_blocks_reading_order(all_blocks)

            # Detect boundaries
            boundaries = self._detect_language_boundaries(all_blocks, window_size, 0.6)

            # Split into sections
            sections = self._split_into_sections(all_blocks, boundaries)

            # Analyze sections
            section_info = []
            for i, section in enumerate(sections):
                section_info.append({
                    'section_number': i + 1,
                    'language': section['language'],
                    'confidence': section['confidence'],
                    'num_blocks': len(section['blocks']),
                    'text_length': sum(len(b['text']) for b in section['blocks']),
                    'preview': section['blocks'][0]['text'][:100] if section['blocks'] else ''
                })

            # Count languages
            languages = [s['language'] for s in sections]
            unique_languages = list(set(languages))

            result = {
                'total_blocks': len(all_blocks),
                'num_boundaries': len(boundaries),
                'num_sections': len(sections),
                'unique_languages': unique_languages,
                'sections': section_info,
                'boundaries': boundaries[:10]  # First 10 boundaries
            }

            return result

        except Exception as e:
            return {'error': str(e)}

    def get_section_preview(self, pdf_path: str, section_index: int = 0,
                           max_chars: int = 500) -> Dict:
        """
        Get preview of a specific section.

        Args:
            pdf_path: Path to the PDF file
            section_index: Index of section to preview
            max_chars: Maximum characters to return

        Returns:
            Dictionary with section preview
        """
        try:
            doc = self._open_pdf(pdf_path)
            all_blocks = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = self._extract_text_blocks(page)
                all_blocks.extend(blocks)

            doc.close()

            all_blocks = self._sort_blocks_reading_order(all_blocks)
            boundaries = self._detect_language_boundaries(all_blocks, 5, 0.6)
            sections = self._split_into_sections(all_blocks, boundaries)

            if section_index >= len(sections):
                return {'error': f'Section {section_index} does not exist'}

            section = sections[section_index]
            text = self._combine_text_blocks(section['blocks'])

            return {
                'section_index': section_index,
                'language': section['language'],
                'confidence': section['confidence'],
                'total_length': len(text),
                'preview': text[:max_chars]
            }

        except Exception as e:
            return {'error': str(e)}

    def extract_by_page_ranges(self, pdf_path: str,
                              page_ranges: List[Tuple[int, int, str]]) -> Dict[str, str]:
        """
        Extract text from specific page ranges with known languages.

        Useful when language boundaries are already known.

        Args:
            pdf_path: Path to the PDF file
            page_ranges: List of (start_page, end_page, language) tuples
                        Pages are 0-indexed

        Returns:
            Dictionary mapping languages to extracted text

        Raises:
            ValueError: If extraction fails
        """
        try:
            doc = self._open_pdf(pdf_path)
            result = {}

            for start_page, end_page, language in page_ranges:
                # Validate page range
                start_page = max(0, start_page)
                end_page = min(len(doc) - 1, end_page)

                # Extract text from page range
                range_blocks = []
                for page_num in range(start_page, end_page + 1):
                    page = doc[page_num]
                    blocks = self._extract_text_blocks(page)
                    range_blocks.extend(blocks)

                # Sort and combine
                range_blocks = self._sort_blocks_reading_order(range_blocks)
                text = self._combine_text_blocks(range_blocks)
                text = self._clean_text(text)

                # Add to result
                if language in result:
                    result[language] += '\n\n' + text
                else:
                    result[language] = text

            doc.close()

            if not self._validate_extraction_result(result):
                raise ValueError("Extraction produced no meaningful text")

            return result

        except Exception as e:
            raise ValueError(f"Page range extraction failed: {str(e)}")
