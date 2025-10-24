"""
Region-based layout analyzer for complex PDF pages with mixed layouts.

Analyzes each page in horizontal regions/sections to detect layout
changes within a single page (e.g., full-width header, then multi-column body).
"""

import fitz  # PyMuPDF
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from sklearn.cluster import KMeans


class RegionAnalyzer:
    """
    Analyzes PDF pages in horizontal regions to detect layout changes.

    Unlike whole-document analysis, this works page-by-page and splits
    each page into horizontal regions, detecting the layout type for each region.

    Features:
    - Detects region boundaries based on vertical position clustering
    - Identifies layout type per region (single-column, multi-column, etc.)
    - Handles mixed layouts within single pages
    """

    # Layout type constants
    LAYOUT_SINGLE = 'single'
    LAYOUT_COLUMNS = 'columns'
    LAYOUT_MIXED = 'mixed'

    def __init__(self, min_region_height: int = 50, min_column_gap: int = 30):
        """
        Initialize region analyzer.

        Args:
            min_region_height: Minimum height for a valid region (points)
            min_column_gap: Minimum gap between columns (points)
        """
        self.min_region_height = min_region_height
        self.min_column_gap = min_column_gap

    def analyze_page(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """
        Analyze a single page and detect regions with their layouts.

        Args:
            page: PyMuPDF page object

        Returns:
            List of region dictionaries with keys:
                - y_start: Region start y-coordinate
                - y_end: Region end y-coordinate
                - blocks: Text blocks in this region
                - layout_type: Detected layout (single/columns)
                - num_columns: Number of columns (if multi-column)
        """
        # Extract text blocks
        blocks = self._extract_text_blocks(page)

        if not blocks:
            return []

        # Group blocks into horizontal regions
        regions = self._detect_regions(blocks, page.rect.height)

        # Analyze layout for each region
        for region in regions:
            region['layout_type'], region['num_columns'] = self._detect_region_layout(
                region['blocks']
            )

        return regions

    def _extract_text_blocks(self, page: fitz.Page) -> List[Dict]:
        """
        Extract text blocks from a page, with support for table-based layouts.
        
        For table-based PDFs, splits wide blocks that contain multiple languages
        on the same line into separate virtual blocks per language.

        Args:
            page: PyMuPDF page object

        Returns:
            List of block dictionaries
        """
        blocks = []
        page_dict = page.get_text("dict")
        page_width = page.rect.width

        for block in page_dict["blocks"]:
            if block.get('type') == 0:  # Text block
                # Extract text from lines
                text_lines = []
                for line in block.get('lines', []):
                    line_text = ""
                    for span in line.get('spans', []):
                        line_text += span.get('text', '')
                    if line_text.strip():
                        text_lines.append(line_text.strip())

                text = '\n'.join(text_lines)
                
                # Check if this is a wide block (likely table-based)
                block_width = block['bbox'][2] - block['bbox'][0]
                is_wide_block = block_width > (page_width * 0.5)  # >50% of page width
                
                if text.strip():
                    # Check if block contains mixed languages (table-based)
                    if is_wide_block and self._contains_multiple_languages(text):
                        # Split into virtual blocks by language, line-by-line
                        virtual_blocks = self._split_table_block_line_by_line(block, text_lines)
                        blocks.extend(virtual_blocks)
                    else:
                        # Regular block
                        blocks.append({
                            'x0': block['bbox'][0],
                            'y0': block['bbox'][1],
                            'x1': block['bbox'][2],
                            'y1': block['bbox'][3],
                            'text': text.strip(),
                            'width': block_width,
                            'height': block['bbox'][3] - block['bbox'][1],
                            'x_center': (block['bbox'][0] + block['bbox'][2]) / 2,
                            'y_center': (block['bbox'][1] + block['bbox'][3]) / 2
                        })

        return blocks
    
    def _contains_multiple_languages(self, text: str) -> bool:
        """
        Check if text contains multiple language markers indicating table-based layout.
        """
        import re
        
        # Check for presence of markers from different languages
        has_kinyarwanda = bool(re.search(r'(Ingingo ya|UMUTWE WA|Icyiciro cya|Komisiyo)', text))
        has_english = bool(re.search(r'(Article (?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+):|CHAPTER |Section (?:One|Two|Three|Four):|Commission)', text))
        has_french = bool(re.search(r'(Article (?:premier|deuxième):|CHAPITRE |Section (?:première|deuxième):|Commission)', text))
        
        # If we have markers from 2+ languages, it's likely table-based
        lang_count = sum([has_kinyarwanda, has_english, has_french])
        return lang_count >= 2
    
    def _split_table_block_line_by_line(self, block: Dict, text_lines: List[str]) -> List[Dict]:
        """
        Split table block by classifying EACH LINE individually by language.
        
        This handles PDFs where languages alternate line-by-line:
        Line 0: Kinyarwanda
        Line 1: English
        Line 2: French
        Line 3: Kinyarwanda...
        """
        import re
        
        x0, y0, x1, y1 = block['bbox']
        block_width = x1 - x0
        col_width = block_width / 3
        
        # Classify each line by language
        lang_lines = {'kinyarwanda': [], 'english': [], 'french': []}
        
        for line in text_lines:
            if not line.strip():
                continue
            
            # Check if line has all 3 languages separated by slashes (e.g., "Kiny/English/French")
            if '/' in line and line.count('/') >= 2:
                parts = [p.strip() for p in line.split('/')]
                if len(parts) >= 3:
                    # Assume order: Kinyarwanda / English / French
                    lang_lines['kinyarwanda'].append(parts[0])
                    lang_lines['english'].append(parts[1])
                    lang_lines['french'].append(parts[2])
                    continue
            
            # Detect language by checking for characteristic words
            line_lower = line.lower()
            
            # Count language-specific markers
            kiny_score = 0
            eng_score = 0
            fr_score = 0
            
            # Kinyarwanda markers (including title words)
            kiny_words = ['ingingo', 'umutwe', 'icyiciro', 'komisiyo', 'uburenganzira', 'bwa', 'ya', 'rya', 'cya', 'kwa', 'zihariye', 'rusange', 'ububasha', 'inshingano', 'itegeko', 'rigena', 'imiterere', 'imikorere', 'ibirimo', 'kuwa', 'ryo']
            kiny_score = sum(2 for word in kiny_words if word in line_lower)  # Higher weight per word
            
            # English markers  
            eng_words = ['article', 'chapter', 'section', 'commission', 'the', 'of', 'and', 'to', 'rights', 'powers', 'missions', 'special', 'ordinary']
            eng_score = sum(1 for word in eng_words if f' {word} ' in f' {line_lower} ' or line_lower.startswith(word) or line_lower.endswith(word))
            
            # French markers
            fr_words = ['article', 'chapitre', 'section', 'commission', 'la', 'le', 'de', 'et', 'des', 'droits', 'pouvoirs', 'missions', 'particulières', 'ordinaires']
            fr_score = sum(1 for word in fr_words if f' {word} ' in f' {line_lower} ' or line_lower.startswith(word) or line_lower.endswith(word))
            
            # Classify by highest score
            if kiny_score > eng_score and kiny_score > fr_score and kiny_score > 0:
                lang_lines['kinyarwanda'].append(line)
            elif fr_score > eng_score and fr_score > 0:
                # Distinguish French from English (both might have 'article', 'commission')
                has_fr_specific = any(word in line_lower for word in ['la ', 'le ', ' de ', ' des ', ' du ', 'particulières', 'particulière'])
                if has_fr_specific or 'personne' in line_lower:
                    lang_lines['french'].append(line)
                else:
                    lang_lines['english'].append(line)
            elif eng_score > 0:
                lang_lines['english'].append(line)
            else:
                # Fallback: detect by character patterns
                has_special_chars = any(c in line for c in ["'", "'"])  # Kinyarwanda apostrophes
                if has_special_chars:
                    lang_lines['kinyarwanda'].append(line)
                else:
                    lang_lines['english'].append(line)  # Default
        
        # Create virtual blocks for each language
        virtual_blocks = []
        for idx, lang in enumerate(['kinyarwanda', 'english', 'french']):
            if lang_lines[lang]:
                col_x0 = x0 + (idx * col_width)
                col_x1 = col_x0 + col_width
                
                virtual_blocks.append({
                    'x0': col_x0,
                    'y0': y0,
                    'x1': col_x1,
                    'y1': y1,
                    'text': '\n'.join(lang_lines[lang]),
                    'width': col_width,
                    'height': y1 - y0,
                    'x_center': (col_x0 + col_x1) / 2,
                    'y_center': (y0 + y1) / 2
                })
        
        return virtual_blocks if virtual_blocks else [{
            'x0': x0,
            'y0': y0,
            'x1': x1,
            'y1': y1,
            'text': '\n'.join(text_lines),
            'width': block_width,
            'height': y1 - y0,
            'x_center': (x0 + x1) / 2,
            'y_center': (y0 + y1) / 2
        }]
    
    def _split_table_block(self, block: Dict, text_lines: List[str]) -> List[Dict]:
        """
        Split a table-based block into virtual blocks for each language.
        
        For table-based PDFs where languages alternate line-by-line in the same block,
        categorize each line by language and create separate virtual blocks.
        """
        import re
        
        x0, y0, x1, y1 = block['bbox']
        block_width = x1 - x0
        col_width = block_width / 3
        
        # Language patterns for classification
        kiny_pattern = r'(Ingingo ya|UMUTWE WA|Icyiciro cya|Komisiyo|abakozi|ubufatanye|ry\'|by\'|cy\')'
        eng_pattern = r'(Article (?:One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+):|CHAPTER (?:I{1,3}|IV|V|VI{0,3}|IX|X|\d+)|Section (?:One|Two|Three|Four|Five):|the Commission|Commissioners)'
        fr_pattern = r'(Article (?:premier|première|deuxième|troisième|\d+):|CHAPITRE (?:I{1,3}|IV|V|VI{0,3}|IX|X|\d+)|Section (?:première|deuxième):|la Commission|Commissaires)'
        
        # Classify each line by language
        lang_texts = {'kinyarwanda': [], 'english': [], 'french': []}
        
        for line in text_lines:
            if not line.strip():
                continue
                
            line_stripped = line.strip()
            
            # Check if line contains markers from multiple languages (mixed line)
            has_kiny = bool(re.search(kiny_pattern, line, re.IGNORECASE))
            has_eng = bool(re.search(eng_pattern, line, re.IGNORECASE))
            has_fr = bool(re.search(fr_pattern, line, re.IGNORECASE))
            
            lang_count = sum([has_kiny, has_eng, has_fr])
            
            if lang_count >= 2:
                # Mixed line - split it
                markers = []
                for match in re.finditer(kiny_pattern, line, re.IGNORECASE):
                    markers.append(('kinyarwanda', match.start()))
                for match in re.finditer(eng_pattern, line, re.IGNORECASE):
                    markers.append(('english', match.start()))
                for match in re.finditer(fr_pattern, line, re.IGNORECASE):
                    markers.append(('french', match.start()))
                
                markers.sort(key=lambda x: x[1])
                
                # Split by markers
                for i, (lang, pos) in enumerate(markers):
                    start = pos
                    end = markers[i + 1][1] if i + 1 < len(markers) else len(line)
                    segment = line[start:end].strip()
                    if segment:
                        lang_texts[lang].append(segment)
            else:
                # Single language line - classify it
                if has_kiny:
                    lang_texts['kinyarwanda'].append(line_stripped)
                elif has_eng:
                    lang_texts['english'].append(line_stripped)
                elif has_fr:
                    lang_texts['french'].append(line_stripped)
                else:
                    # Fallback: try to detect by common words
                    line_lower = line_stripped.lower()
                    if any(word in line_lower for word in ['article', 'chapter', 'section', 'commission', 'the', 'and', 'of']):
                        lang_texts['english'].append(line_stripped)
                    elif any(word in line_lower for word in ['ingingo', 'umutwe', 'icyiciro', 'komisiyo', 'ya', 'na']):
                        lang_texts['kinyarwanda'].append(line_stripped)
                    elif any(word in line_lower for word in ['chapitre', 'commissaires', 'la', 'le', 'de', 'et']):
                        lang_texts['french'].append(line_stripped)
                    else:
                        # Default to english
                        lang_texts['english'].append(line_stripped)
        
        # Create virtual blocks for languages with content
        virtual_blocks = []
        for idx, (lang, lines) in enumerate([('kinyarwanda', lang_texts['kinyarwanda']), 
                                              ('english', lang_texts['english']), 
                                              ('french', lang_texts['french'])]):
            if lines:
                col_x0 = x0 + (idx * col_width)
                col_x1 = col_x0 + col_width
                
                virtual_blocks.append({
                    'x0': col_x0,
                    'y0': y0,
                    'x1': col_x1,
                    'y1': y1,
                    'text': '\n'.join(lines),
                    'width': col_width,
                    'height': y1 - y0,
                    'x_center': (col_x0 + col_x1) / 2,
                    'y_center': (y0 + y1) / 2
                })
        
        return virtual_blocks if virtual_blocks else [{
            'x0': x0,
            'y0': y0,
            'x1': x1,
            'y1': y1,
            'text': '\n'.join(text_lines),
            'width': block_width,
            'height': y1 - y0,
            'x_center': (x0 + x1) / 2,
            'y_center': (y0 + y1) / 2
        }]

    def _detect_regions(self, blocks: List[Dict], page_height: float) -> List[Dict]:
        """
        Detect horizontal regions on the page.

        Uses vertical position clustering to identify natural breaks in content.

        Args:
            blocks: List of text blocks
            page_height: Height of the page

        Returns:
            List of region dictionaries
        """
        if not blocks:
            return []

        # Sort blocks by vertical position
        sorted_blocks = sorted(blocks, key=lambda b: b['y0'])

        # Find vertical gaps to identify region boundaries
        regions = []
        current_region_blocks = []
        current_y_start = sorted_blocks[0]['y0']
        previous_y_end = sorted_blocks[0]['y0']

        for block in sorted_blocks:
            gap = block['y0'] - previous_y_end

            # If there's a significant gap, start a new region
            if gap > self.min_region_height and current_region_blocks:
                # Finalize current region
                regions.append({
                    'y_start': current_y_start,
                    'y_end': previous_y_end,
                    'blocks': current_region_blocks,
                    'height': previous_y_end - current_y_start
                })

                # Start new region
                current_region_blocks = [block]
                current_y_start = block['y0']
            else:
                current_region_blocks.append(block)

            previous_y_end = block['y1']

        # Add the last region
        if current_region_blocks:
            regions.append({
                'y_start': current_y_start,
                'y_end': previous_y_end,
                'blocks': current_region_blocks,
                'height': previous_y_end - current_y_start
            })

        return regions

    def _detect_region_layout(self, blocks: List[Dict]) -> Tuple[str, int]:
        """
        Detect layout type for a specific region.

        Args:
            blocks: Text blocks in the region

        Returns:
            Tuple of (layout_type, num_columns)
        """
        if not blocks:
            return self.LAYOUT_SINGLE, 1

        if len(blocks) < 2:
            return self.LAYOUT_SINGLE, 1

        # Analyze x-position distribution to detect columns
        x_centers = np.array([b['x_center'] for b in blocks])

        # Try to detect 2 columns first (most common)
        if len(blocks) >= 4:
            # Use K-means with k=2 to see if there are distinct columns
            kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
            labels = kmeans.fit_predict(x_centers.reshape(-1, 1))

            # Calculate cluster centers
            centers = kmeans.cluster_centers_.flatten()
            gap = abs(centers[0] - centers[1])

            # If gap is significant, we have columns
            if gap > self.min_column_gap * 2:
                # Check if blocks are roughly evenly distributed
                count0 = np.sum(labels == 0)
                count1 = np.sum(labels == 1)

                # If one column has significantly more blocks, might not be true columns
                ratio = min(count0, count1) / max(count0, count1)

                if ratio > 0.3:  # At least 30% balance
                    return self.LAYOUT_COLUMNS, 2

        # Try 3 columns (less common)
        if len(blocks) >= 6:
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            labels = kmeans.fit_predict(x_centers.reshape(-1, 1))

            # Check distribution balance
            counts = [np.sum(labels == i) for i in range(3)]
            min_count = min(counts)
            max_count = max(counts)

            if min_count / max_count > 0.25:  # Reasonable balance
                return self.LAYOUT_COLUMNS, 3

        # Default to single column
        return self.LAYOUT_SINGLE, 1

    def extract_region_text(
        self,
        region: Dict[str, Any],
        language_detector=None
    ) -> Dict[str, str]:
        """
        Extract text from a region based on its detected layout.

        Args:
            region: Region dictionary with blocks and layout info
            language_detector: LanguageDetector instance

        Returns:
            Dictionary mapping language names to extracted text
        """
        blocks = region['blocks']
        layout_type = region['layout_type']
        num_columns = region['num_columns']

        if layout_type == self.LAYOUT_SINGLE:
            # Single column - just combine all blocks
            blocks_sorted = sorted(blocks, key=lambda b: (b['y0'], b['x0']))
            text = '\n'.join(b['text'] for b in blocks_sorted)

            # Detect language
            if language_detector:
                language, _ = language_detector.detect_language(text)
            else:
                language = 'unknown'

            return {language: text}

        elif layout_type == self.LAYOUT_COLUMNS:
            # Multi-column - cluster by x-position
            x_centers = np.array([b['x_center'] for b in blocks]).reshape(-1, 1)

            kmeans = KMeans(n_clusters=num_columns, random_state=42, n_init=10)
            labels = kmeans.fit_predict(x_centers)

            # Sort cluster centers left to right
            centers = kmeans.cluster_centers_.flatten()
            sorted_cluster_ids = np.argsort(centers)

            # Map cluster labels to column IDs
            cluster_to_column = {old: new for new, old in enumerate(sorted_cluster_ids)}
            column_assignments = [cluster_to_column[label] for label in labels]

            # Group blocks by column
            columns = {i: [] for i in range(num_columns)}
            for block, col_id in zip(blocks, column_assignments):
                columns[col_id].append(block)

            # Extract text from each column
            result = {}
            for col_id in range(num_columns):
                if columns[col_id]:
                    col_blocks = sorted(columns[col_id], key=lambda b: (b['y0'], b['x0']))
                    col_text = '\n'.join(b['text'] for b in col_blocks)

                    # Detect language
                    if language_detector and col_text.strip():
                        language, confidence = language_detector.detect_language(col_text)
                        # Lower threshold - accept more results
                        if confidence > 0.3 or language != 'unknown':
                            if language in result:
                                result[language] += '\n\n' + col_text
                            else:
                                result[language] = col_text
                        else:
                            # Even if confidence is low, keep the text as 'unknown'
                            if 'unknown' in result:
                                result['unknown'] += '\n\n' + col_text
                            else:
                                result['unknown'] = col_text
                    elif col_text.strip():
                        # No detector, but we have text
                        if 'unknown' in result:
                            result['unknown'] += '\n\n' + col_text
                        else:
                            result['unknown'] = col_text

            return result if result else {'unknown': '\n\n'.join(b['text'] for b in blocks)}

        return {}
