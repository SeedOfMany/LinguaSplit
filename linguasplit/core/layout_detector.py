"""
Layout detection module for identifying document structure patterns.
Detects columns, sequential paragraphs, and section blocks using spatial and language analysis.
"""

import fitz  # PyMuPDF
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict


class LayoutDetector:
    """
    Detects document layout patterns using spatial distribution and language analysis.

    Supports three main layout types:
    - columns: Multi-column layouts (newspapers, academic papers)
    - sequential: Single-column sequential paragraphs (books, reports)
    - sections: Distinct sections with headers (manuals, guides)
    """

    # Layout type constants
    LAYOUT_COLUMNS = 'columns'
    LAYOUT_SEQUENTIAL = 'sequential'
    LAYOUT_SECTIONS = 'sections'

    # Detection thresholds
    COLUMN_MIN_GAP = 30  # Minimum gap in points to consider separate columns
    SPATIAL_THRESHOLD = 0.6  # Threshold for spatial score
    LANGUAGE_THRESHOLD = 0.5  # Threshold for language pattern score
    MIN_BLOCKS_FOR_ANALYSIS = 10  # Minimum text blocks needed

    def __init__(self, min_column_gap: int = None, spatial_threshold: float = None):
        """
        Initialize layout detector.

        Args:
            min_column_gap: Minimum gap in points between columns (default: 30)
            spatial_threshold: Threshold for spatial score (default: 0.6)
        """
        self.min_column_gap = min_column_gap or self.COLUMN_MIN_GAP
        self.spatial_threshold = spatial_threshold or self.SPATIAL_THRESHOLD

    def detect_layout(self, pdf_path: str) -> Dict[str, Any]:
        """
        Main detection method to analyze PDF layout.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with keys:
                - type: Layout type (columns/sequential/sections)
                - confidence: Overall confidence score (0-1)
                - details: Additional layout information
                - spatial_score: Spatial analysis score
                - language_score: Language pattern score
        """
        try:
            # Extract page data from PDF
            pages_data = self._extract_pages_data(pdf_path)

            if not pages_data:
                return {
                    'type': self.LAYOUT_SEQUENTIAL,
                    'confidence': 0.0,
                    'details': {'error': 'No text blocks found'},
                    'spatial_score': 0.0,
                    'language_score': 0.0
                }

            # Analyze spatial distribution
            spatial_result = self.analyze_spatial_distribution(pages_data)

            # Analyze language patterns
            language_result = self.analyze_language_patterns(pages_data)

            # Classify layout based on combined analysis
            layout_type, confidence, details = self.classify_layout(
                spatial_result,
                language_result
            )

            return {
                'type': layout_type,
                'confidence': confidence,
                'details': details,
                'spatial_score': spatial_result.get('score', 0.0),
                'language_score': language_result.get('score', 0.0)
            }

        except Exception as e:
            return {
                'type': self.LAYOUT_SEQUENTIAL,
                'confidence': 0.0,
                'details': {'error': str(e)},
                'spatial_score': 0.0,
                'language_score': 0.0
            }

    def _extract_pages_data(self, pdf_path: str) -> List[Dict]:
        """
        Extract text block data from PDF pages.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of page data dictionaries
        """
        pages_data = []

        try:
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = page.get_text("dict")["blocks"]

                page_data = {
                    'page_num': page_num,
                    'width': page.rect.width,
                    'height': page.rect.height,
                    'blocks': []
                }

                for block in blocks:
                    if block.get('type') == 0:  # Text block
                        block_data = {
                            'x0': block['bbox'][0],
                            'y0': block['bbox'][1],
                            'x1': block['bbox'][2],
                            'y1': block['bbox'][3],
                            'text': self._extract_block_text(block),
                            'lines': len(block.get('lines', []))
                        }

                        if block_data['text'].strip():
                            page_data['blocks'].append(block_data)

                if page_data['blocks']:
                    pages_data.append(page_data)

            doc.close()

        except Exception as e:
            raise Exception(f"Failed to extract PDF data: {str(e)}")

        return pages_data

    def _extract_block_text(self, block: Dict) -> str:
        """
        Extract text content from a text block.

        Args:
            block: Block dictionary from PyMuPDF

        Returns:
            Extracted text string
        """
        text_parts = []

        for line in block.get('lines', []):
            for span in line.get('spans', []):
                text_parts.append(span.get('text', ''))

        return ' '.join(text_parts)

    def analyze_spatial_distribution(self, pages_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze spatial distribution of text blocks.

        Args:
            pages_data: List of page data dictionaries

        Returns:
            Dictionary with spatial analysis results:
                - score: Confidence score for spatial pattern
                - column_count: Estimated number of columns
                - column_positions: X-positions of detected columns
                - y_distribution: Analysis of vertical spacing
        """
        if not pages_data:
            return {'score': 0.0, 'column_count': 1, 'column_positions': [], 'y_distribution': {}}

        # Collect all x-positions (left edges of blocks)
        all_x_positions = []
        all_y_positions = []
        block_widths = []

        for page_data in pages_data:
            for block in page_data['blocks']:
                all_x_positions.append(block['x0'])
                all_y_positions.append(block['y0'])
                block_widths.append(block['x1'] - block['x0'])

        if not all_x_positions:
            return {'score': 0.0, 'column_count': 1, 'column_positions': [], 'y_distribution': {}}

        # Cluster x-positions to detect columns
        column_positions = self.cluster_positions(all_x_positions, self.min_column_gap)
        column_count = len(column_positions)

        # Analyze y-distribution for sequential vs. sectioned layout
        y_distribution = self._analyze_y_distribution(all_y_positions)

        # Calculate spatial score
        # High score indicates strong column structure
        spatial_score = 0.0

        if column_count > 1:
            # Multi-column layout
            # Check consistency of column usage
            column_consistency = self._calculate_column_consistency(pages_data, column_positions)
            spatial_score = column_consistency * 0.9  # High score for columns
        else:
            # Single column - check for regular spacing
            if y_distribution['is_regular']:
                spatial_score = 0.4  # Medium score for sequential
            else:
                spatial_score = 0.2  # Low score, likely sections

        return {
            'score': spatial_score,
            'column_count': column_count,
            'column_positions': column_positions,
            'y_distribution': y_distribution,
            'avg_block_width': np.mean(block_widths) if block_widths else 0
        }

    def cluster_positions(self, positions: List[float], min_gap: float) -> List[float]:
        """
        Cluster positions to identify distinct columns or sections.

        Args:
            positions: List of x or y positions
            min_gap: Minimum gap to consider separate clusters

        Returns:
            List of cluster center positions
        """
        if not positions:
            return []

        # Sort positions
        sorted_positions = sorted(positions)

        # Simple clustering based on gaps
        clusters = []
        current_cluster = [sorted_positions[0]]

        for pos in sorted_positions[1:]:
            if pos - current_cluster[-1] < min_gap:
                current_cluster.append(pos)
            else:
                # New cluster
                clusters.append(current_cluster)
                current_cluster = [pos]

        # Add last cluster
        clusters.append(current_cluster)

        # Calculate cluster centers
        cluster_centers = [np.mean(cluster) for cluster in clusters]

        return cluster_centers

    def _analyze_y_distribution(self, y_positions: List[float]) -> Dict[str, Any]:
        """
        Analyze vertical distribution of text blocks.

        Args:
            y_positions: List of y-coordinates

        Returns:
            Dictionary with y-distribution analysis
        """
        if not y_positions:
            return {'is_regular': False, 'avg_gap': 0, 'gap_variance': 0}

        sorted_y = sorted(y_positions)
        gaps = [sorted_y[i+1] - sorted_y[i] for i in range(len(sorted_y) - 1)]

        if not gaps:
            return {'is_regular': False, 'avg_gap': 0, 'gap_variance': 0}

        avg_gap = np.mean(gaps)
        gap_variance = np.var(gaps)

        # Regular spacing indicates sequential layout
        # High variance indicates sections with breaks
        is_regular = gap_variance < (avg_gap * 0.5)

        return {
            'is_regular': is_regular,
            'avg_gap': avg_gap,
            'gap_variance': gap_variance
        }

    def _calculate_column_consistency(self, pages_data: List[Dict],
                                     column_positions: List[float]) -> float:
        """
        Calculate how consistently columns are used across pages.

        Args:
            pages_data: List of page data
            column_positions: Detected column x-positions

        Returns:
            Consistency score (0-1)
        """
        if len(column_positions) <= 1:
            return 0.5

        # Tolerance for matching column positions
        tolerance = self.min_column_gap / 2

        # Count blocks in each column across all pages
        column_usage = defaultdict(int)
        total_blocks = 0

        for page_data in pages_data:
            for block in page_data['blocks']:
                total_blocks += 1
                # Find which column this block belongs to
                for i, col_pos in enumerate(column_positions):
                    if abs(block['x0'] - col_pos) < tolerance:
                        column_usage[i] += 1
                        break

        if total_blocks == 0:
            return 0.0

        # Calculate balance across columns
        usage_values = list(column_usage.values())
        if not usage_values:
            return 0.0

        # Ideal would be equal distribution
        expected_per_column = total_blocks / len(column_positions)
        variance = np.var([usage - expected_per_column for usage in usage_values])

        # Normalize variance to 0-1 score (lower variance = higher score)
        consistency = 1.0 / (1.0 + variance / expected_per_column) if expected_per_column > 0 else 0.0

        return consistency

    def analyze_language_patterns(self, pages_data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze language mixing patterns in text blocks.

        Args:
            pages_data: List of page data dictionaries

        Returns:
            Dictionary with language pattern analysis:
                - score: Confidence score for language pattern
                - pattern_type: Type of language pattern detected
                - language_switches: Number of language switches detected
        """
        if not pages_data:
            return {'score': 0.0, 'pattern_type': 'unknown', 'language_switches': 0}

        # Collect text blocks with their positions
        blocks_info = []
        for page_data in pages_data:
            for block in page_data['blocks']:
                blocks_info.append({
                    'text': block['text'],
                    'x0': block['x0'],
                    'y0': block['y0'],
                    'page': page_data['page_num']
                })

        if len(blocks_info) < self.MIN_BLOCKS_FOR_ANALYSIS:
            return {'score': 0.0, 'pattern_type': 'insufficient_data', 'language_switches': 0}

        # Detect language for each block
        language_blocks = self._detect_block_languages(blocks_info)

        # Analyze patterns
        pattern_analysis = self._analyze_language_switching_pattern(language_blocks)

        # Calculate score based on pattern clarity
        score = pattern_analysis['confidence']

        return {
            'score': score,
            'pattern_type': pattern_analysis['type'],
            'language_switches': pattern_analysis['switches'],
            'details': pattern_analysis
        }

    def _detect_block_languages(self, blocks_info: List[Dict]) -> List[Dict]:
        """
        Detect language for each text block using simple heuristics.

        Args:
            blocks_info: List of block information dictionaries

        Returns:
            List of blocks with language information
        """
        # Simple language detection based on character patterns
        # This is a basic implementation - can be enhanced with langdetect

        language_blocks = []

        for block in blocks_info:
            text = block['text']

            # Basic language detection heuristic
            language = self._simple_language_detect(text)

            language_blocks.append({
                **block,
                'language': language
            })

        return language_blocks

    def _simple_language_detect(self, text: str) -> str:
        """
        Simple language detection based on character patterns.

        Args:
            text: Text to analyze

        Returns:
            Detected language code
        """
        if not text or len(text) < 10:
            return 'unknown'

        # Count different script types
        latin = sum(1 for c in text if '\u0000' <= c <= '\u007F')
        latin_ext = sum(1 for c in text if '\u0080' <= c <= '\u024F')
        cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        arabic = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        cjk = sum(1 for c in text if '\u4E00' <= c <= '\u9FFF')

        total = len([c for c in text if c.isalpha()])
        if total == 0:
            return 'unknown'

        # Determine dominant script
        if (latin + latin_ext) > 0.7 * total:
            return 'latin'
        elif cyrillic > 0.7 * total:
            return 'cyrillic'
        elif arabic > 0.7 * total:
            return 'arabic'
        elif cjk > 0.5 * total:
            return 'cjk'
        else:
            return 'mixed'

    def _analyze_language_switching_pattern(self, language_blocks: List[Dict]) -> Dict[str, Any]:
        """
        Analyze how languages switch in the document.

        Args:
            language_blocks: List of blocks with language information

        Returns:
            Dictionary with pattern analysis
        """
        if not language_blocks:
            return {'type': 'unknown', 'confidence': 0.0, 'switches': 0}

        # Count language switches
        switches = 0
        prev_lang = language_blocks[0]['language']

        # Track language distribution by position (x-coordinate)
        lang_by_x = defaultdict(list)

        for block in language_blocks:
            lang = block['language']

            if lang != prev_lang and lang != 'unknown' and prev_lang != 'unknown':
                switches += 1

            prev_lang = lang

            # Group by approximate x-position (for column detection)
            x_bucket = int(block['x0'] / 50) * 50  # Round to nearest 50
            lang_by_x[x_bucket].append(lang)

        # Analyze pattern type
        total_blocks = len(language_blocks)
        switch_rate = switches / max(total_blocks - 1, 1)

        # Check if languages are separated by columns
        column_separated = self._check_column_language_separation(lang_by_x)

        if column_separated:
            # Column layout with different languages per column
            return {
                'type': 'column_separated',
                'confidence': 0.9,
                'switches': switches,
                'switch_rate': switch_rate
            }
        elif switch_rate > 0.3:
            # High switching rate - likely sections
            return {
                'type': 'section_separated',
                'confidence': 0.7,
                'switches': switches,
                'switch_rate': switch_rate
            }
        else:
            # Low switching - sequential or single language
            return {
                'type': 'sequential',
                'confidence': 0.6,
                'switches': switches,
                'switch_rate': switch_rate
            }

    def _check_column_language_separation(self, lang_by_x: Dict[int, List[str]]) -> bool:
        """
        Check if different languages are separated by columns.

        Args:
            lang_by_x: Dictionary mapping x-positions to language lists

        Returns:
            True if languages appear to be column-separated
        """
        if len(lang_by_x) < 2:
            return False

        # Check if each x-position group has a dominant language
        # and different positions have different dominant languages
        dominant_langs = set()

        for x_pos, langs in lang_by_x.items():
            if not langs:
                continue

            # Find most common language at this x-position
            lang_counts = defaultdict(int)
            for lang in langs:
                if lang != 'unknown':
                    lang_counts[lang] += 1

            if lang_counts:
                dominant = max(lang_counts, key=lang_counts.get)
                dominant_langs.add(dominant)

        # If we have multiple different dominant languages, likely column-separated
        return len(dominant_langs) > 1

    def classify_layout(self, spatial_result: Dict, language_result: Dict) -> Tuple[str, float, Dict]:
        """
        Classify layout type based on spatial and language analysis.

        Args:
            spatial_result: Results from spatial analysis
            language_result: Results from language pattern analysis

        Returns:
            Tuple of (layout_type, confidence, details)
        """
        spatial_score = spatial_result.get('score', 0.0)
        language_score = language_result.get('score', 0.0)
        column_count = spatial_result.get('column_count', 1)

        # Decision logic
        details = {
            'spatial_analysis': spatial_result,
            'language_analysis': language_result
        }

        # Multi-column detection
        if column_count > 1 and spatial_score > self.spatial_threshold:
            confidence = (spatial_score + language_score) / 2
            return (self.LAYOUT_COLUMNS, confidence, {
                **details,
                'column_count': column_count,
                'column_positions': spatial_result.get('column_positions', [])
            })

        # Section-based layout detection
        y_dist = spatial_result.get('y_distribution', {})
        if not y_dist.get('is_regular', False) and language_result.get('pattern_type') == 'section_separated':
            confidence = (spatial_score * 0.4 + language_score * 0.6)
            return (self.LAYOUT_SECTIONS, confidence, {
                **details,
                'section_indicators': {
                    'irregular_spacing': True,
                    'language_switches': language_result.get('language_switches', 0)
                }
            })

        # Default to sequential layout
        confidence = max(0.3, (1.0 - spatial_score) * 0.5 + language_score * 0.5)
        return (self.LAYOUT_SEQUENTIAL, confidence, details)
