"""
Column-based text extraction for side-by-side multilingual PDFs.

Uses x-position clustering to detect column boundaries and extract
parallel translations from side-by-side layouts.
"""

from typing import Dict, List, Optional
import numpy as np
from sklearn.cluster import KMeans
from .base_extractor import BaseExtractor


class ColumnExtractor(BaseExtractor):
    """
    Extracts text from side-by-side column layouts.

    Detects column boundaries using x-position clustering and sorts
    blocks within each column by reading order. Ideal for parallel
    translation documents.
    """

    def __init__(self, language_detector=None, num_columns: int = 2):
        """
        Initialize the column extractor.

        Args:
            language_detector: LanguageDetector instance
            num_columns: Expected number of columns (default: 2)
        """
        super().__init__(language_detector)
        self.num_columns = num_columns

    def extract(self, pdf_path: str, **kwargs) -> Dict[str, str]:
        """
        Extract text from multi-column PDF.

        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional parameters
                - num_columns: Override default number of columns
                - min_column_width: Minimum column width in points (default: 50)

        Returns:
            Dictionary mapping language names to extracted text

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If extraction fails
        """
        num_columns = kwargs.get('num_columns', self.num_columns)
        min_column_width = kwargs.get('min_column_width', 50)

        try:
            doc = self._open_pdf(pdf_path)
            all_columns = {i: [] for i in range(num_columns)}

            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = self._extract_text_blocks(page)

                if not blocks:
                    continue

                # Add page number to each block for proper sorting
                for block in blocks:
                    block['page_num'] = page_num

                # Detect columns and assign blocks
                column_assignments = self._detect_columns(blocks, num_columns, min_column_width)

                # Group blocks by column
                for block, column_id in zip(blocks, column_assignments):
                    all_columns[column_id].append(block)

            doc.close()

            # Sort blocks within each column and combine
            result = {}
            for column_id in range(num_columns):
                column_blocks = self._sort_blocks_reading_order(all_columns[column_id])

                if column_blocks:
                    # Combine text
                    column_text = self._combine_text_blocks(column_blocks)
                    column_text = self._clean_text(column_text)

                    # Detect language
                    language = self._detect_block_language(column_text, min_length=100)

                    # Skip if language is unknown or invalid
                    if language == 'unknown' or not language:
                        continue

                    # Add to result - merge if language already exists
                    if language in result:
                        # Same language detected in multiple columns - merge with separator
                        result[language] += "\n\n" + column_text
                    else:
                        result[language] = column_text

            if not self._validate_extraction_result(result):
                raise ValueError("Extraction produced no meaningful text")

            return result

        except Exception as e:
            raise ValueError(f"Column extraction failed: {str(e)}")

    def _detect_columns(self, blocks: List[Dict], num_columns: int,
                       min_column_width: float) -> List[int]:
        """
        Detect column boundaries and assign blocks to columns.

        Uses x-position clustering to identify column boundaries.

        Args:
            blocks: List of text block dictionaries
            num_columns: Number of columns to detect
            min_column_width: Minimum width for a valid column

        Returns:
            List of column IDs (0-indexed) for each block
        """
        if not blocks:
            return []

        if len(blocks) < num_columns:
            # Not enough blocks, assign sequentially
            return list(range(len(blocks)))

        # Extract x-center positions
        x_centers = np.array([(b['x0'] + b['x1']) / 2 for b in blocks]).reshape(-1, 1)

        # Cluster by x-position
        try:
            kmeans = KMeans(n_clusters=num_columns, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(x_centers)

            # Get cluster centers and sort them left to right
            centers = kmeans.cluster_centers_.flatten()
            sorted_cluster_ids = np.argsort(centers)

            # Create mapping from cluster label to column number
            cluster_to_column = {old_id: new_id for new_id, old_id in enumerate(sorted_cluster_ids)}

            # Map cluster labels to column IDs
            column_assignments = [cluster_to_column[label] for label in cluster_labels]

            # Validate column widths
            if not self._validate_columns(blocks, column_assignments, num_columns, min_column_width):
                # Fall back to simple division
                return self._simple_column_detection(blocks, num_columns)

            return column_assignments

        except Exception:
            # Fall back to simple division
            return self._simple_column_detection(blocks, num_columns)

    def _simple_column_detection(self, blocks: List[Dict], num_columns: int) -> List[int]:
        """
        Simple column detection by dividing page width.

        Args:
            blocks: List of text block dictionaries
            num_columns: Number of columns

        Returns:
            List of column IDs for each block
        """
        if not blocks:
            return []

        # Find page boundaries
        min_x = min(b['x0'] for b in blocks)
        max_x = max(b['x1'] for b in blocks)
        page_width = max_x - min_x

        # Calculate column width
        column_width = page_width / num_columns

        # Assign blocks based on x-position
        assignments = []
        for block in blocks:
            block_center = (block['x0'] + block['x1']) / 2
            column_id = int((block_center - min_x) / column_width)
            column_id = min(column_id, num_columns - 1)  # Ensure within bounds
            assignments.append(column_id)

        return assignments

    def _validate_columns(self, blocks: List[Dict], assignments: List[int],
                         num_columns: int, min_width: float) -> bool:
        """
        Validate that detected columns meet minimum width requirements.

        Args:
            blocks: List of text blocks
            assignments: Column assignments for each block
            num_columns: Expected number of columns
            min_width: Minimum column width

        Returns:
            True if columns are valid, False otherwise
        """
        # Group blocks by column
        column_blocks = {i: [] for i in range(num_columns)}
        for block, col_id in zip(blocks, assignments):
            column_blocks[col_id].append(block)

        # Check each column has content and reasonable width
        for col_id in range(num_columns):
            col_blocks = column_blocks[col_id]

            if not col_blocks:
                return False

            # Calculate column width
            min_x = min(b['x0'] for b in col_blocks)
            max_x = max(b['x1'] for b in col_blocks)
            width = max_x - min_x

            if width < min_width:
                return False

        return True

    def get_column_statistics(self, pdf_path: str) -> Dict:
        """
        Analyze PDF to get column statistics.

        Useful for determining optimal extraction parameters.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary with column statistics
        """
        try:
            doc = self._open_pdf(pdf_path)
            all_blocks = []

            # Collect all blocks from all pages
            for page_num in range(min(3, len(doc))):  # Sample first 3 pages
                page = doc[page_num]
                blocks = self._extract_text_blocks(page)
                all_blocks.extend(blocks)

            doc.close()

            if not all_blocks:
                return {'error': 'No text blocks found'}

            # Calculate x-position statistics
            x_centers = [(b['x0'] + b['x1']) / 2 for b in all_blocks]

            stats = {
                'num_blocks': len(all_blocks),
                'x_min': min(b['x0'] for b in all_blocks),
                'x_max': max(b['x1'] for b in all_blocks),
                'x_center_mean': np.mean(x_centers),
                'x_center_std': np.std(x_centers),
                'suggested_columns': self._suggest_column_count(all_blocks)
            }

            return stats

        except Exception as e:
            return {'error': str(e)}

    def _suggest_column_count(self, blocks: List[Dict]) -> int:
        """
        Suggest optimal number of columns based on x-position distribution.

        Args:
            blocks: List of text blocks

        Returns:
            Suggested number of columns
        """
        if not blocks:
            return 1

        x_centers = np.array([(b['x0'] + b['x1']) / 2 for b in blocks])

        # Try different column counts and measure clustering quality
        best_score = float('inf')
        best_k = 1

        for k in range(1, 5):  # Try 1-4 columns
            if len(blocks) < k:
                continue

            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                kmeans.fit(x_centers.reshape(-1, 1))
                score = kmeans.inertia_  # Within-cluster sum of squares

                # Penalize more clusters
                adjusted_score = score * (1 + 0.2 * k)

                if adjusted_score < best_score:
                    best_score = adjusted_score
                    best_k = k
            except Exception:
                continue

        return best_k
