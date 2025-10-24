"""
Paragraph-based text extraction for alternating multilingual PDFs.

Extracts sequential paragraphs and detects repeating language patterns
to group parallel translations (e.g., A->B->C->A->B->C pattern).
"""

from typing import Dict, List, Tuple, Optional
from collections import Counter
from .base_extractor import BaseExtractor


class ParagraphExtractor(BaseExtractor):
    """
    Extracts text from alternating paragraph layouts.

    Detects repeating language patterns in sequential paragraphs and
    groups parallel translations together. Ideal for documents where
    translations alternate paragraph by paragraph.
    """

    def __init__(self, language_detector=None):
        """
        Initialize the paragraph extractor.

        Args:
            language_detector: LanguageDetector instance
        """
        super().__init__(language_detector)

    def extract(self, pdf_path: str, **kwargs) -> Dict[str, str]:
        """
        Extract text from alternating paragraph PDF.

        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters
                - min_paragraph_length: Minimum paragraph length (default: 50)
                - pattern_window: Number of paragraphs to analyze for pattern (default: 12)

        Returns:
            Dictionary mapping language names to extracted text

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If extraction fails
        """
        min_paragraph_length = kwargs.get('min_paragraph_length', 50)
        pattern_window = kwargs.get('pattern_window', 12)

        try:
            doc = self._open_pdf(pdf_path)
            all_paragraphs = []

            # Extract all paragraphs from all pages
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = self._extract_text_blocks(page)

                # Sort blocks in reading order
                blocks = self._sort_blocks_reading_order(blocks)

                # Group into paragraphs (blocks close in y-position)
                paragraphs = self._group_into_paragraphs(blocks)
                all_paragraphs.extend(paragraphs)

            doc.close()

            if not all_paragraphs:
                raise ValueError("No paragraphs found in PDF")

            # Filter short paragraphs
            all_paragraphs = [p for p in all_paragraphs if len(p.strip()) >= min_paragraph_length]

            if not all_paragraphs:
                raise ValueError("No paragraphs meet minimum length requirement")

            # Detect language for each paragraph
            paragraph_languages = []
            for para in all_paragraphs:
                lang = self._detect_block_language(para, min_length=min_paragraph_length)
                paragraph_languages.append(lang)

            # Detect repeating pattern
            pattern = self._detect_language_pattern(paragraph_languages, pattern_window)

            if not pattern:
                # No pattern detected, group by language directly
                return self._group_by_language_simple(all_paragraphs, paragraph_languages)

            # Group paragraphs according to detected pattern
            result = self._group_by_pattern(all_paragraphs, paragraph_languages, pattern)

            if not self._validate_extraction_result(result):
                raise ValueError("Extraction produced no meaningful text")

            return result

        except Exception as e:
            raise ValueError(f"Paragraph extraction failed: {str(e)}")

    def _group_into_paragraphs(self, blocks: List[Dict]) -> List[str]:
        """
        Group text blocks into paragraphs.

        Blocks that are close together vertically are combined into
        the same paragraph.

        Args:
            blocks: List of text block dictionaries (already sorted)

        Returns:
            List of paragraph texts
        """
        if not blocks:
            return []

        paragraphs = []
        current_paragraph = []
        last_y1 = None

        # Threshold for paragraph separation (in points)
        paragraph_gap_threshold = 15

        for block in blocks:
            text = block['text'].strip()
            if not text:
                continue

            # Check if this starts a new paragraph
            if last_y1 is not None:
                gap = block['y0'] - last_y1
                if gap > paragraph_gap_threshold:
                    # New paragraph
                    if current_paragraph:
                        paragraphs.append(' '.join(current_paragraph))
                    current_paragraph = [text]
                else:
                    # Same paragraph
                    current_paragraph.append(text)
            else:
                current_paragraph.append(text)

            last_y1 = block['y1']

        # Add final paragraph
        if current_paragraph:
            paragraphs.append(' '.join(current_paragraph))

        return paragraphs

    def _detect_language_pattern(self, languages: List[str],
                                 window_size: int = 12) -> Optional[List[str]]:
        """
        Detect repeating language pattern in paragraph sequence.

        Analyzes the sequence of languages to find repeating patterns
        like [A, B, A, B, ...] or [A, B, C, A, B, C, ...].

        Args:
            languages: List of detected languages in order
            window_size: Number of elements to analyze for pattern

        Returns:
            Detected pattern as list of languages, or None if no pattern found
        """
        if len(languages) < 4:
            return None

        # Try different pattern lengths (2, 3, 4 languages)
        for pattern_length in range(2, min(5, len(languages) // 2 + 1)):
            pattern = self._try_pattern_length(languages, pattern_length, window_size)
            if pattern:
                return pattern

        return None

    def _try_pattern_length(self, languages: List[str], pattern_length: int,
                           window_size: int) -> Optional[List[str]]:
        """
        Try to detect a pattern of specific length.

        Args:
            languages: List of languages
            pattern_length: Length of pattern to try
            window_size: Number of elements to analyze

        Returns:
            Pattern if detected, None otherwise
        """
        analyze_count = min(window_size, len(languages))

        # Extract potential pattern from first N elements
        if analyze_count < pattern_length * 2:
            return None

        candidate_pattern = languages[:pattern_length]

        # Verify pattern repeats
        matches = 0
        total_checks = 0

        for i in range(pattern_length, analyze_count):
            expected_lang = candidate_pattern[i % pattern_length]
            actual_lang = languages[i]

            total_checks += 1
            if expected_lang == actual_lang:
                matches += 1

        # Pattern must match at least 70% of the time
        if total_checks > 0 and (matches / total_checks) >= 0.7:
            return candidate_pattern

        return None

    def _group_by_pattern(self, paragraphs: List[str], languages: List[str],
                         pattern: List[str]) -> Dict[str, str]:
        """
        Group paragraphs by detected language pattern.

        Args:
            paragraphs: List of paragraph texts
            languages: List of detected languages
            pattern: Detected language pattern

        Returns:
            Dictionary mapping languages to combined text
        """
        # Initialize storage for each language in pattern
        grouped = {lang: [] for lang in pattern}

        # Assign each paragraph to its language group
        for i, (para, lang) in enumerate(zip(paragraphs, languages)):
            if lang in grouped:
                grouped[lang].append(para)

        # Combine paragraphs for each language
        result = {}
        for lang, paras in grouped.items():
            if paras:
                combined = '\n\n'.join(paras)
                result[lang] = self._clean_text(combined)

        return result

    def _group_by_language_simple(self, paragraphs: List[str],
                                  languages: List[str]) -> Dict[str, str]:
        """
        Simple grouping by language without pattern detection.

        Args:
            paragraphs: List of paragraph texts
            languages: List of detected languages

        Returns:
            Dictionary mapping languages to combined text
        """
        grouped = {}

        for para, lang in zip(paragraphs, languages):
            if lang not in grouped:
                grouped[lang] = []
            grouped[lang].append(para)

        # Combine paragraphs for each language
        result = {}
        for lang, paras in grouped.items():
            if paras:
                combined = '\n\n'.join(paras)
                result[lang] = self._clean_text(combined)

        return result

    def analyze_pattern(self, pdf_path: str, num_paragraphs: int = 20) -> Dict:
        """
        Analyze paragraph language pattern in PDF.

        Useful for understanding the document structure before extraction.

        Args:
            pdf_path: Path to the PDF file
            num_paragraphs: Number of paragraphs to analyze

        Returns:
            Dictionary with pattern analysis results
        """
        try:
            doc = self._open_pdf(pdf_path)
            all_paragraphs = []

            # Extract paragraphs from first few pages
            for page_num in range(min(5, len(doc))):
                page = doc[page_num]
                blocks = self._extract_text_blocks(page)
                blocks = self._sort_blocks_reading_order(blocks)
                paragraphs = self._group_into_paragraphs(blocks)
                all_paragraphs.extend(paragraphs)

                if len(all_paragraphs) >= num_paragraphs:
                    break

            doc.close()

            # Limit to requested number
            all_paragraphs = all_paragraphs[:num_paragraphs]

            if not all_paragraphs:
                return {'error': 'No paragraphs found'}

            # Detect languages
            paragraph_languages = []
            for para in all_paragraphs:
                lang = self._detect_block_language(para)
                paragraph_languages.append(lang)

            # Detect pattern
            pattern = self._detect_language_pattern(paragraph_languages)

            # Count language frequencies
            lang_counts = Counter(paragraph_languages)

            result = {
                'num_paragraphs': len(all_paragraphs),
                'languages_found': list(lang_counts.keys()),
                'language_counts': dict(lang_counts),
                'language_sequence': paragraph_languages[:20],  # First 20
                'detected_pattern': pattern,
                'pattern_detected': pattern is not None
            }

            return result

        except Exception as e:
            return {'error': str(e)}

    def get_paragraph_details(self, pdf_path: str, max_paragraphs: int = 10) -> List[Dict]:
        """
        Get detailed information about paragraphs in PDF.

        Args:
            pdf_path: Path to the PDF file
            max_paragraphs: Maximum number of paragraphs to analyze

        Returns:
            List of dictionaries with paragraph details
        """
        try:
            doc = self._open_pdf(pdf_path)
            details = []

            paragraph_count = 0
            for page_num in range(len(doc)):
                if paragraph_count >= max_paragraphs:
                    break

                page = doc[page_num]
                blocks = self._extract_text_blocks(page)
                blocks = self._sort_blocks_reading_order(blocks)
                paragraphs = self._group_into_paragraphs(blocks)

                for para in paragraphs:
                    if paragraph_count >= max_paragraphs:
                        break

                    lang = self._detect_block_language(para)
                    details.append({
                        'index': paragraph_count,
                        'page': page_num + 1,
                        'language': lang,
                        'length': len(para),
                        'preview': para[:100] + '...' if len(para) > 100 else para
                    })
                    paragraph_count += 1

            doc.close()
            return details

        except Exception as e:
            return [{'error': str(e)}]
