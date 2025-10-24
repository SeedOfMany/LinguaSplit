"""
Main PDF processing orchestrator for LinguaSplit.

Coordinates layout detection, text extraction, language identification,
and markdown formatting to process multilingual PDFs.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime

from .layout_detector import LayoutDetector
from .extractors.column_extractor import ColumnExtractor
from .extractors.paragraph_extractor import ParagraphExtractor
from .extractors.section_extractor import SectionExtractor
from .language_detector import LanguageDetector
from .region_analyzer import RegionAnalyzer
from ..formatters.markdown_formatter import MarkdownFormatter
from ..utils.logger import GUILogger, LogLevel, get_logger
from ..utils.config_manager import ConfigManager
from ..utils.file_helper import FileHelper
import fitz  # PyMuPDF


class PDFProcessor:
    """
    Main orchestrator for processing multilingual PDFs.

    Workflow:
    1. Validate input PDF
    2. Detect document layout pattern (columns/sequential/sections)
    3. Route to appropriate extractor
    4. Detect languages in extracted text
    5. Format output as markdown
    6. Save results to output directory

    Features:
    - Automatic layout detection and routing
    - Multi-strategy text extraction
    - Language identification
    - Markdown formatting with metadata
    - Comprehensive error handling
    - Configurable settings
    """

    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        logger: Optional[GUILogger] = None
    ):
        """
        Initialize PDF processor.

        Args:
            config: Configuration manager instance (creates default if None)
            logger: Logger instance (creates default if None)
        """
        # Configuration
        self.config = config if config else ConfigManager()

        # Logging
        self.logger = logger if logger else get_logger()

        # Initialize components
        self._init_components()

        self.logger.info("PDFProcessor initialized")

    def _init_components(self):
        """Initialize processing components based on configuration."""
        # Layout detector
        min_column_gap = self.config.get('layout.column_gap_threshold', 50)
        self.layout_detector = LayoutDetector(min_column_gap=min_column_gap)

        # Region analyzer for page-level analysis
        self.region_analyzer = RegionAnalyzer(min_column_gap=min_column_gap)

        # Language detector
        self.language_detector = LanguageDetector()

        # Extractors (lazy initialization)
        self.column_extractor = None
        self.paragraph_extractor = None
        self.section_extractor = None

        # Markdown formatter
        include_metadata = self.config.get('output.include_metadata', True)
        include_page_markers = self.config.get('output.include_page_markers', True)
        self.markdown_formatter = MarkdownFormatter(
            include_metadata=include_metadata,
            include_page_markers=include_page_markers
        )

    def _get_extractor(self, layout_type: str):
        """
        Get or create extractor for given layout type.

        Args:
            layout_type: Layout type (columns/sequential/sections)

        Returns:
            Appropriate extractor instance
        """
        if layout_type == LayoutDetector.LAYOUT_COLUMNS:
            if not self.column_extractor:
                self.column_extractor = ColumnExtractor(
                    language_detector=self.language_detector
                )
            return self.column_extractor

        elif layout_type == LayoutDetector.LAYOUT_SEQUENTIAL:
            if not self.paragraph_extractor:
                self.paragraph_extractor = ParagraphExtractor(
                    language_detector=self.language_detector
                )
            return self.paragraph_extractor

        elif layout_type == LayoutDetector.LAYOUT_SECTIONS:
            if not self.section_extractor:
                self.section_extractor = SectionExtractor(
                    language_detector=self.language_detector
                )
            return self.section_extractor

        else:
            # Default to paragraph extractor
            if not self.paragraph_extractor:
                self.paragraph_extractor = ParagraphExtractor(
                    language_detector=self.language_detector
                )
            return self.paragraph_extractor

    def process_pdf(
        self,
        pdf_path: str,
        output_dir: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a PDF file and extract multilingual content.

        Args:
            pdf_path: Path to input PDF file
            output_dir: Directory for output files
            config: Optional processing configuration overrides
                - layout_type: Force specific layout type (columns/sequential/sections)
                - output_format: Output format (markdown/text/json)
                - language_hints: List of expected languages
                - save_separate: Save each language to separate file (default: True)
                - base_filename: Custom base filename for output

        Returns:
            Dictionary containing:
                - success: Boolean indicating success
                - pdf_path: Input PDF path
                - output_files: List of created output files
                - languages_found: List of detected languages
                - layout_type: Detected layout type
                - layout_confidence: Confidence score for layout detection
                - error: Error message (if success=False)
                - statistics: Processing statistics
                - timestamp: Processing timestamp

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If processing fails
        """
        start_time = datetime.now()
        self.logger.info(f"Processing PDF: {pdf_path}")

        result = {
            'success': False,
            'pdf_path': pdf_path,
            'output_files': [],
            'languages_found': [],
            'layout_type': None,
            'layout_confidence': 0.0,
            'error': None,
            'statistics': {},
            'timestamp': start_time.isoformat()
        }

        try:
            # Step 1: Validate input
            self.logger.debug("Validating input file")
            self._validate_input(pdf_path)

            # Step 2: Prepare output directory
            self.logger.debug("Preparing output directory")
            self._prepare_output_dir(output_dir)

            # Step 3: Detect layout
            self.logger.info("Detecting document layout")
            layout_info = self._detect_layout(pdf_path, config)
            result['layout_type'] = layout_info['type']
            result['layout_confidence'] = layout_info['confidence']

            # Step 4: Extract text using appropriate strategy
            # Check if multi-column layout was detected but not classified as columns
            if layout_info['type'] != LayoutDetector.LAYOUT_COLUMNS:
                column_count = layout_info.get('details', {}).get('spatial_analysis', {}).get('column_count', 1)
                if column_count >= 2:
                    # Override layout type to columns if multiple columns detected
                    self.logger.info(f"Detected {column_count} columns, using column extraction strategy")
                    layout_info['type'] = LayoutDetector.LAYOUT_COLUMNS
                    layout_info['column_count'] = column_count
            
            self.logger.info(f"Extracting text using {layout_info['type']} strategy")
            extracted_text = self._extract_text(pdf_path, layout_info, config)

            if not extracted_text:
                raise ValueError("No text extracted from PDF")
            
            # Post-process to split mixed-language lines (table-based PDFs)
            extracted_text = self._split_mixed_language_lines(extracted_text)

            result['languages_found'] = list(extracted_text.keys())

            # Step 5: Format and save output
            self.logger.info("Formatting and saving output")
            output_files = self._save_output(
                pdf_path,
                output_dir,
                extracted_text,
                layout_info,
                config
            )
            result['output_files'] = output_files

            # Step 6: Compile statistics
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            result['statistics'] = {
                'processing_time': processing_time,
                'num_languages': len(extracted_text),
                'total_characters': sum(len(text) for text in extracted_text.values()),
                'file_size': FileHelper.get_file_size(pdf_path)
            }

            result['success'] = True
            self.logger.info(f"Successfully processed {pdf_path} in {processing_time:.2f}s")

        except FileNotFoundError as e:
            error_msg = str(e)
            result['error'] = error_msg
            self.logger.error(f"File not found: {error_msg}")
            raise

        except ValueError as e:
            error_msg = str(e)
            result['error'] = error_msg
            self.logger.error(f"Processing error: {error_msg}")
            raise

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            result['error'] = error_msg
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        return result

    def _validate_input(self, pdf_path: str):
        """
        Validate input PDF file.

        Args:
            pdf_path: Path to PDF file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid PDF
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if not FileHelper.is_pdf(pdf_path):
            raise ValueError(f"File is not a PDF: {pdf_path}")

        # Check file size (warn if very large)
        file_size = FileHelper.get_file_size(pdf_path)
        if file_size and file_size > 100 * 1024 * 1024:  # 100MB
            self.logger.warning(f"Large PDF file ({FileHelper.format_file_size(file_size)}), processing may be slow")

    def _prepare_output_dir(self, output_dir: str):
        """
        Prepare output directory.

        Args:
            output_dir: Output directory path

        Raises:
            ValueError: If directory cannot be created
        """
        if not FileHelper.ensure_directory(output_dir):
            raise ValueError(f"Failed to create output directory: {output_dir}")

    def _detect_layout(
        self,
        pdf_path: str,
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect document layout pattern.

        Args:
            pdf_path: Path to PDF file
            config: Processing configuration

        Returns:
            Layout detection result
        """
        # Check if layout type is forced in config
        if config and 'layout_type' in config:
            forced_type = config['layout_type']
            self.logger.info(f"Using forced layout type: {forced_type}")
            return {
                'type': forced_type,
                'confidence': 1.0,
                'details': {'forced': True}
            }

        # Detect layout automatically
        try:
            layout_info = self.layout_detector.detect_layout(pdf_path)
            self.logger.debug(
                f"Layout detected: {layout_info['type']} "
                f"(confidence: {layout_info['confidence']:.2f})"
            )
            return layout_info
        except Exception as e:
            self.logger.warning(f"Layout detection failed: {e}, using default (sequential)")
            return {
                'type': LayoutDetector.LAYOUT_SEQUENTIAL,
                'confidence': 0.0,
                'details': {'error': str(e)}
            }

    def _extract_text(
        self,
        pdf_path: str,
        layout_info: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Extract text using appropriate strategy.

        Args:
            pdf_path: Path to PDF file
            layout_info: Layout detection result
            config: Processing configuration

        Returns:
            Dictionary mapping languages to extracted text

        Raises:
            ValueError: If extraction fails
        """
        layout_type = layout_info['type']

        # Get appropriate extractor
        extractor = self._get_extractor(layout_type)

        # Prepare extraction parameters
        extract_params = {}

        # Column extractor parameters
        if layout_type == LayoutDetector.LAYOUT_COLUMNS:
            # Use detected column count if available
            if 'column_count' in layout_info:
                extract_params['num_columns'] = layout_info['column_count']
            
            # Allow config to override
            if config:
                if 'num_columns' in config:
                    extract_params['num_columns'] = config['num_columns']
                if 'min_column_width' in config:
                    extract_params['min_column_width'] = config['min_column_width']
        
        # Paragraph extractor parameters
        elif layout_type == LayoutDetector.LAYOUT_SEQUENTIAL:
            if config:
                if 'min_paragraph_length' in config:
                    extract_params['min_paragraph_length'] = config['min_paragraph_length']
        
        # Section extractor parameters
        elif layout_type == LayoutDetector.LAYOUT_SECTIONS:
            if config:
                if 'window_size' in config:
                    extract_params['window_size'] = config['window_size']

        # Check if region-based analysis is enabled
        use_region_analysis = self.config.get('layout.use_region_analysis', True)

        if use_region_analysis:
            # Use region-based extraction (page-by-page, region-by-region)
            try:
                self.logger.info("Using region-based analysis (recommended for mixed layouts)")
                extracted_text = self._extract_text_by_regions(pdf_path, config)

                if extracted_text:
                    return extracted_text
                else:
                    self.logger.warning("Region-based extraction returned no text, falling back to standard extraction")
            except Exception as e:
                self.logger.warning(f"Region-based extraction failed: {e}, falling back to standard extraction")

        # Extract text using standard method
        try:
            extracted_text = extractor.extract(pdf_path, **extract_params)

            if not extracted_text:
                raise ValueError("Extractor returned empty result")

            return extracted_text

        except Exception as e:
            raise ValueError(f"Text extraction failed: {str(e)}")

    def _extract_text_by_regions(
        self,
        pdf_path: str,
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Extract text using region-based analysis.

        Analyzes each page region-by-region to handle mixed layouts
        (e.g., single-column header followed by multi-column content).

        Args:
            pdf_path: Path to PDF file
            config: Processing configuration

        Returns:
            Dictionary mapping languages to extracted text

        Raises:
            ValueError: If extraction fails
        """
        try:
            doc = fitz.open(pdf_path)
            all_languages = {}

            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                self.logger.debug(f"Analyzing page {page_num + 1} regions...")

                # Analyze page regions
                regions = self.region_analyzer.analyze_page(page)

                self.logger.debug(
                    f"Page {page_num + 1}: Found {len(regions)} regions"
                )

                # Extract text from each region
                for region_idx, region in enumerate(regions):
                    layout_type = region['layout_type']
                    num_columns = region['num_columns']

                    self.logger.debug(
                        f"  Region {region_idx + 1}: {layout_type} "
                        f"({num_columns} column{'s' if num_columns > 1 else ''})"
                    )

                    # Extract text from region
                    region_text = self.region_analyzer.extract_region_text(
                        region,
                        self.language_detector
                    )

                    # Merge with accumulated text
                    for language, text in region_text.items():
                        if language in all_languages:
                            all_languages[language] += '\n\n' + text
                        else:
                            all_languages[language] = text

            doc.close()

            if not all_languages:
                raise ValueError("No text extracted from any region")

            self.logger.info(
                f"Region-based extraction completed: "
                f"{len(all_languages)} language(s) found"
            )

            return all_languages

        except Exception as e:
            raise ValueError(f"Region-based extraction failed: {str(e)}")

    def _save_output(
        self,
        pdf_path: str,
        output_dir: str,
        extracted_text: Dict[str, str],
        layout_info: Dict[str, Any],
        config: Optional[Dict[str, Any]]
    ) -> List[str]:
        """
        Format and save extracted text to output files.

        Args:
            pdf_path: Input PDF path
            output_dir: Output directory
            extracted_text: Extracted text by language
            layout_info: Layout detection result
            config: Processing configuration

        Returns:
            List of created output file paths
        """
        output_files = []

        # Determine output format
        output_format = config.get('output_format', 'markdown') if config else 'markdown'
        output_format = self.config.get('output.format', output_format)

        # Determine if saving to separate files
        save_separate = config.get('save_separate', True) if config else True

        # Determine base filename
        if config and 'base_filename' in config:
            base_name = config['base_filename']
        else:
            base_name = Path(pdf_path).stem

        base_name = FileHelper.safe_filename(base_name)

        # Prepare metadata
        metadata = {
            'source': os.path.basename(pdf_path),
            'layout_type': layout_info['type'],
            'layout_confidence': f"{layout_info['confidence']:.2f}",
            'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        # Get language filter from config
        extract_only = self.config.get('language.extract_only', '')
        if isinstance(extract_only, str) and extract_only.strip():
            # Parse comma-separated language list
            allowed_languages = [lang.strip().lower() for lang in extract_only.split(',')]
            # Filter extracted text to only include selected languages
            filtered_text = {
                lang: text for lang, text in extracted_text.items()
                if lang.lower() in allowed_languages
            }
            if filtered_text:
                extracted_text = filtered_text
                self.logger.info(f"Filtered to extract only: {', '.join(filtered_text.keys())}")
            else:
                self.logger.warning(f"No languages matched filter '{extract_only}', extracting all")

        if save_separate:
            # Save each language to separate file
            for language, text in extracted_text.items():
                if output_format == 'markdown':
                    # Format as markdown
                    formatted_text = self.markdown_formatter.format_document(
                        text=text,
                        metadata=metadata,
                        language=language
                    )
                    extension = 'md'
                elif output_format == 'text':
                    formatted_text = text
                    extension = 'txt'
                elif output_format == 'json':
                    import json
                    formatted_text = json.dumps({
                        'language': language,
                        'text': text,
                        'metadata': metadata
                    }, indent=2, ensure_ascii=False)
                    extension = 'json'
                else:
                    # Default to text
                    formatted_text = text
                    extension = 'txt'

                # Create filename
                filename = f"{base_name}_{language}.{extension}"
                filepath = os.path.join(output_dir, filename)

                # Note: We overwrite existing files instead of creating duplicates
                # This ensures clean output when reprocessing PDFs

                # Write file
                if FileHelper.write_text_file(filepath, formatted_text):
                    output_files.append(filepath)
                    self.logger.debug(f"Saved {language} text to {filepath}")
                else:
                    self.logger.warning(f"Failed to save {language} text to {filepath}")

        else:
            # Save all languages to single file
            if output_format == 'markdown':
                # Combine all languages with separators
                parts = []
                for language, text in extracted_text.items():
                    formatted_text = self.markdown_formatter.format_document(
                        text=text,
                        metadata={**metadata, 'language': language},
                        language=language
                    )
                    parts.append(f"# {language.title()}\n\n{formatted_text}")

                combined_text = "\n\n---\n\n".join(parts)
                extension = 'md'

            elif output_format == 'json':
                import json
                combined_text = json.dumps({
                    'languages': extracted_text,
                    'metadata': metadata
                }, indent=2, ensure_ascii=False)
                extension = 'json'

            else:
                # Text format
                parts = []
                for language, text in extracted_text.items():
                    parts.append(f"=== {language.upper()} ===\n\n{text}")
                combined_text = "\n\n".join(parts)
                extension = 'txt'

            # Create filename
            filename = f"{base_name}_multilingual.{extension}"
            filepath = os.path.join(output_dir, filename)

            # Ensure unique filename
            if os.path.exists(filepath):
                filename = FileHelper.get_unique_filename(output_dir, filename)
                filepath = os.path.join(output_dir, filename)

            # Write file
            if FileHelper.write_text_file(filepath, combined_text):
                output_files.append(filepath)
                self.logger.debug(f"Saved combined text to {filepath}")
            else:
                self.logger.warning(f"Failed to save combined text to {filepath}")

        return output_files

    def _split_mixed_language_lines(self, extracted_text: Dict[str, str]) -> Dict[str, str]:
        """
        Split lines that contain multiple languages side-by-side (table-based PDFs).
        
        Detects patterns like:
        "Ingingo ya X: ... Article X: ... Article X: ..."
        
        Args:
            extracted_text: Dictionary of language -> text
            
        Returns:
            Dictionary with properly separated languages
        """
        import re
        
        # Patterns to detect language boundaries within a line
        patterns = {
            'kinyarwanda': [
                r'\b(Ingingo|UMUTWE|Icyiciro|Komisiyo|ubufatanye|abakozi|ry\'|by\'|cy\'|ya\s+\d+|bwa\s+)',
                r'(REPUBULIKA|PEREZIDA|MINISITIRI|ITEKA)',
            ],
            'english': [
                r'\b(Article|CHAPTER|Section|Commission|Commissioners|the|and|of|to|shall|for)\b',
                r'(pursuant\s+to|having\s+reviewed|adopted|enacted)',
            ],
            'french': [
                r'\b(Article|CHAPITRE|Section|Commission|Commissaires|la|le|de|du|des|pour)\b',
                r'(vu\s+la|ayant\s+revu|adopte)',
            ]
        }
        
        result = {lang: [] for lang in ['kinyarwanda', 'english', 'french']}
        
        # Process each language's text
        for lang, text in extracted_text.items():
            if not text:
                continue
                
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line contains multiple language markers (mixed line)
                kiny_match = any(re.search(p, line) for p in patterns['kinyarwanda'])
                eng_match = any(re.search(p, line) for p in patterns['english'])
                fr_match = any(re.search(p, line) for p in patterns['french'])
                
                mixed_count = sum([kiny_match, eng_match, fr_match])
                
                if mixed_count >= 2:
                    # This is a mixed line, try to split it
                    segments = self._split_line_by_language(line, patterns)
                    for seg_lang, seg_text in segments.items():
                        if seg_text:
                            result[seg_lang].append(seg_text)
                else:
                    # Not a mixed line - but still check if it's in the RIGHT language
                    detected_lang = self._detect_line_language(line, patterns)
                    
                    if detected_lang in result:
                        result[detected_lang].append(line)
                    elif lang in result:
                        # Only use the original language if detection failed
                        result[lang].append(line)
                    else:
                        # Fallback to english
                        result['english'].append(line)
        
        # Convert lists to strings
        final_result = {}
        for lang, lines in result.items():
            if lines:
                final_result[lang] = '\n\n'.join(lines)
        
        if final_result:
            self.logger.info(f"Split mixed-language lines: {list(final_result.keys())}")
        
        return final_result if final_result else extracted_text
    
    def _split_line_by_language(self, line: str, patterns: Dict) -> Dict[str, str]:
        """
        Split a single line that contains multiple languages.
        
        Strategy: Find language markers and split the line at those points.
        """
        import re
        
        # Find all marker positions
        markers = []
        for lang, lang_patterns in patterns.items():
            for pattern in lang_patterns:
                for match in re.finditer(pattern, line):
                    markers.append({
                        'position': match.start(),
                        'language': lang,
                        'text': match.group(0)
                    })
        
        # Sort markers by position
        markers.sort(key=lambda x: x['position'])
        
        if len(markers) < 2:
            # Can't split, return as-is
            return {}
        
        # Split line at marker boundaries
        segments = {}
        for i, marker in enumerate(markers):
            start = marker['position']
            end = markers[i + 1]['position'] if i + 1 < len(markers) else len(line)
            
            seg_text = line[start:end].strip()
            lang = marker['language']
            
            if lang not in segments:
                segments[lang] = []
            segments[lang].append(seg_text)
        
        # Join segments for each language
        return {lang: ' '.join(segs) for lang, segs in segments.items()}
    
    def _detect_line_language(self, line: str, patterns: Dict) -> str:
        """
        Detect which language a single line is in.
        """
        import re
        
        scores = {}
        for lang, lang_patterns in patterns.items():
            score = sum(1 for pattern in lang_patterns if re.search(pattern, line))
            if score > 0:
                scores[lang] = score
        
        if scores:
            return max(scores, key=scores.get)
        
        # Fallback: use language detector
        if self.language_detector and len(line) > 50:
            detected_lang, confidence = self.language_detector.detect_language(line)
            if confidence > 0.6:
                return detected_lang
        
        return 'english'  # Default fallback

    def get_supported_layouts(self) -> List[str]:
        """
        Get list of supported layout types.

        Returns:
            List of layout type names
        """
        return [
            LayoutDetector.LAYOUT_COLUMNS,
            LayoutDetector.LAYOUT_SEQUENTIAL,
            LayoutDetector.LAYOUT_SECTIONS
        ]

    def analyze_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze PDF structure without processing.

        Useful for previewing document structure before full processing.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with analysis results:
                - file_info: File information
                - layout_info: Layout detection result
                - suggested_extractor: Recommended extractor type
                - preview: Text preview from first page
        """
        self.logger.info(f"Analyzing PDF: {pdf_path}")

        try:
            # Get file info
            file_info = FileHelper.get_file_info(pdf_path)

            # Detect layout
            layout_info = self.layout_detector.detect_layout(pdf_path)

            # Get preview
            preview = self._get_preview(pdf_path)

            return {
                'file_info': file_info,
                'layout_info': layout_info,
                'suggested_extractor': layout_info['type'],
                'preview': preview
            }

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return {
                'error': str(e)
            }

    def _get_preview(self, pdf_path: str, max_chars: int = 500) -> str:
        """
        Get text preview from first page.

        Args:
            pdf_path: Path to PDF file
            max_chars: Maximum characters to return

        Returns:
            Preview text
        """
        try:
            import fitz
            doc = fitz.open(pdf_path)
            if len(doc) > 0:
                text = doc[0].get_text()
                doc.close()
                return text[:max_chars] + ('...' if len(text) > max_chars else '')
            doc.close()
            return ""
        except Exception:
            return ""
