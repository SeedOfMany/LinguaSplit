"""
Batch processing engine for LinguaSplit.

Processes multiple PDFs with parallel execution, progress tracking,
error recovery, and comprehensive reporting.
"""

import os
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from .pdf_processor import PDFProcessor
from ..utils.logger import GUILogger, LogLevel, get_logger
from ..utils.config_manager import ConfigManager
from ..utils.file_helper import FileHelper


class BatchProcessor:
    """
    Batch processing engine for multiple PDFs.

    Features:
    - Parallel processing with configurable workers
    - Progress tracking and callbacks for GUI updates
    - Error recovery (continue on failure)
    - Detailed statistics and summary generation
    - Thread-safe logging
    - Cancellation support
    - Summary report generation

    Thread Safety:
    All public methods are thread-safe and can be called from GUI threads.
    """

    def __init__(
        self,
        config: Optional[ConfigManager] = None,
        logger: Optional[GUILogger] = None,
        max_workers: Optional[int] = None
    ):
        """
        Initialize batch processor.

        Args:
            config: Configuration manager instance (creates default if None)
            logger: Logger instance (creates default if None)
            max_workers: Maximum number of parallel workers (default: from config or 4)
        """
        # Configuration
        self.config = config if config else ConfigManager()

        # Logging
        self.logger = logger if logger else get_logger()

        # Thread safety
        self._lock = threading.Lock()
        self._cancel_flag = threading.Event()

        # Processing configuration
        if max_workers is not None:
            self.max_workers = max_workers
        else:
            self.max_workers = self.config.get('batch.max_workers', 4)

        self.continue_on_error = self.config.get('batch.continue_on_error', True)

        # Progress tracking
        self._current_progress = 0
        self._total_files = 0
        self._progress_callback: Optional[Callable] = None

        self.logger.info(f"BatchProcessor initialized with {self.max_workers} workers")

    def process_batch(
        self,
        pdf_files: List[str],
        output_dir: str,
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple PDF files in batch.

        Args:
            pdf_files: List of PDF file paths to process
            output_dir: Output directory for all processed files
            config: Optional processing configuration (passed to PDFProcessor)
            progress_callback: Optional callback function for progress updates
                Called with (current_count, total_count, current_file_name)

        Returns:
            Dictionary containing batch processing summary:
                - success: Boolean indicating overall success
                - total_files: Total number of files
                - processed: Number successfully processed
                - failed: Number of failures
                - skipped: Number of skipped files
                - output_directory: Output directory path
                - results: List of individual processing results
                - errors: List of errors encountered
                - statistics: Overall statistics
                - summary_file: Path to summary JSON file (if created)
                - start_time: Processing start timestamp
                - end_time: Processing end timestamp
                - duration: Total processing duration in seconds
                - cancelled: Whether processing was cancelled

        Example:
            >>> batch = BatchProcessor()
            >>> def update(current, total, filename):
            ...     print(f"Processing {current}/{total}: {filename}")
            >>> result = batch.process_batch(
            ...     pdf_files=['doc1.pdf', 'doc2.pdf'],
            ...     output_dir='./output',
            ...     progress_callback=update
            ... )
        """
        start_time = datetime.now()
        self.logger.info(f"Starting batch processing of {len(pdf_files)} files")

        # Reset cancellation flag
        self._cancel_flag.clear()

        # Set progress callback
        with self._lock:
            self._progress_callback = progress_callback
            self._total_files = len(pdf_files)
            self._current_progress = 0

        # Initialize result structure
        summary = {
            'success': False,
            'total_files': len(pdf_files),
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'output_directory': output_dir,
            'results': [],
            'errors': [],
            'statistics': {},
            'summary_file': None,
            'start_time': start_time.isoformat(),
            'end_time': None,
            'duration': 0.0,
            'cancelled': False
        }

        try:
            # Validate and prepare
            self.logger.debug("Validating input files and output directory")
            pdf_files, skipped = self._validate_and_filter_files(pdf_files)
            summary['skipped'] = skipped

            if not pdf_files:
                self.logger.warning("No valid PDF files to process")
                summary['success'] = True
                return summary

            # Ensure output directory exists
            if not FileHelper.ensure_directory(output_dir):
                raise ValueError(f"Failed to create output directory: {output_dir}")

            # Process files
            results = self._process_files_parallel(pdf_files, output_dir, config)

            # Compile results
            for result in results:
                summary['results'].append(result)

                if result.get('success'):
                    summary['processed'] += 1
                else:
                    summary['failed'] += 1
                    if result.get('error'):
                        summary['errors'].append({
                            'file': result.get('pdf_path'),
                            'error': result.get('error')
                        })

            # Check if cancelled
            if self._cancel_flag.is_set():
                summary['cancelled'] = True
                self.logger.warning("Batch processing was cancelled")

            # Calculate statistics
            summary['statistics'] = self._calculate_statistics(summary['results'])

            # Generate summary report
            if self.config.get('batch.create_summary', True):
                summary_file = self._create_summary_report(summary, output_dir)
                summary['summary_file'] = summary_file

            # Overall success if at least one file processed
            summary['success'] = summary['processed'] > 0

            end_time = datetime.now()
            summary['end_time'] = end_time.isoformat()
            summary['duration'] = (end_time - start_time).total_seconds()

            self.logger.info(
                f"Batch processing complete: {summary['processed']}/{summary['total_files']} "
                f"succeeded, {summary['failed']} failed in {summary['duration']:.2f}s"
            )

        except Exception as e:
            error_msg = f"Batch processing error: {str(e)}"
            self.logger.error(error_msg)
            summary['errors'].append({'error': error_msg})
            raise

        return summary

    def cancel(self):
        """
        Cancel ongoing batch processing.

        Can be called from any thread. Processing will stop after current
        file completes.
        """
        self.logger.warning("Cancellation requested")
        self._cancel_flag.set()

    def is_cancelled(self) -> bool:
        """
        Check if processing has been cancelled.

        Returns:
            True if cancelled
        """
        return self._cancel_flag.is_set()

    def _validate_and_filter_files(self, pdf_files: List[str]) -> tuple[List[str], int]:
        """
        Validate and filter PDF files.

        Args:
            pdf_files: List of PDF file paths

        Returns:
            Tuple of (valid_files, skipped_count)
        """
        valid_files = []
        skipped = 0

        for pdf_path in pdf_files:
            if not os.path.exists(pdf_path):
                self.logger.warning(f"File not found, skipping: {pdf_path}")
                skipped += 1
                continue

            if not FileHelper.is_pdf(pdf_path):
                self.logger.warning(f"Not a PDF file, skipping: {pdf_path}")
                skipped += 1
                continue

            valid_files.append(pdf_path)

        return valid_files, skipped

    def _process_files_parallel(
        self,
        pdf_files: List[str],
        output_dir: str,
        config: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Process files in parallel using thread pool.

        Args:
            pdf_files: List of valid PDF file paths
            output_dir: Output directory
            config: Processing configuration

        Returns:
            List of processing results
        """
        results = []

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self._process_single_file,
                    pdf_path,
                    output_dir,
                    config
                ): pdf_path
                for pdf_path in pdf_files
            }

            # Process completed tasks
            for future in as_completed(future_to_file):
                # Check for cancellation
                if self._cancel_flag.is_set():
                    # Cancel remaining futures
                    for f in future_to_file:
                        f.cancel()
                    break

                pdf_path = future_to_file[future]

                try:
                    result = future.result()
                    results.append(result)

                except Exception as e:
                    # Handle unexpected errors
                    error_result = {
                        'success': False,
                        'pdf_path': pdf_path,
                        'error': f"Unexpected error: {str(e)}",
                        'output_files': [],
                        'languages_found': []
                    }
                    results.append(error_result)
                    self.logger.error(f"Error processing {pdf_path}: {e}")

                    # Stop if not continuing on error
                    if not self.continue_on_error:
                        self._cancel_flag.set()
                        break

                # Update progress
                self._update_progress(pdf_path)

        return results

    def _process_single_file(
        self,
        pdf_path: str,
        output_dir: str,
        config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process a single PDF file.

        Args:
            pdf_path: Path to PDF file
            output_dir: Output directory
            config: Processing configuration

        Returns:
            Processing result dictionary
        """
        file_name = os.path.basename(pdf_path)
        self.logger.info(f"Processing file: {file_name}")

        try:
            # Create PDF processor for this file
            # Each thread gets its own processor instance
            processor = PDFProcessor(config=self.config, logger=self.logger)

            # Process the PDF
            result = processor.process_pdf(pdf_path, output_dir, config)

            return result

        except FileNotFoundError as e:
            return {
                'success': False,
                'pdf_path': pdf_path,
                'error': str(e),
                'output_files': [],
                'languages_found': []
            }

        except ValueError as e:
            return {
                'success': False,
                'pdf_path': pdf_path,
                'error': str(e),
                'output_files': [],
                'languages_found': []
            }

        except Exception as e:
            return {
                'success': False,
                'pdf_path': pdf_path,
                'error': f"Unexpected error: {str(e)}",
                'output_files': [],
                'languages_found': []
            }

    def _update_progress(self, current_file: str):
        """
        Update progress and call progress callback.

        Args:
            current_file: Currently processed file path
        """
        with self._lock:
            self._current_progress += 1

            if self._progress_callback:
                try:
                    file_name = os.path.basename(current_file)
                    self._progress_callback(
                        self._current_progress,
                        self._total_files,
                        file_name
                    )
                except Exception as e:
                    self.logger.error(f"Progress callback error: {e}")

    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate overall statistics from results.

        Args:
            results: List of processing results

        Returns:
            Statistics dictionary
        """
        stats = {
            'total_processing_time': 0.0,
            'average_processing_time': 0.0,
            'total_characters': 0,
            'total_output_files': 0,
            'languages_detected': set(),
            'layout_types': {},
            'file_sizes': {
                'total': 0,
                'average': 0,
                'min': float('inf'),
                'max': 0
            }
        }

        if not results:
            return stats

        successful_results = [r for r in results if r.get('success')]

        if not successful_results:
            return stats

        # Aggregate statistics
        for result in successful_results:
            # Processing time
            result_stats = result.get('statistics', {})
            proc_time = result_stats.get('processing_time', 0)
            stats['total_processing_time'] += proc_time

            # Characters
            chars = result_stats.get('total_characters', 0)
            stats['total_characters'] += chars

            # Output files
            stats['total_output_files'] += len(result.get('output_files', []))

            # Languages
            for lang in result.get('languages_found', []):
                stats['languages_detected'].add(lang)

            # Layout types
            layout_type = result.get('layout_type')
            if layout_type:
                stats['layout_types'][layout_type] = stats['layout_types'].get(layout_type, 0) + 1

            # File sizes
            file_size = result_stats.get('file_size', 0)
            if file_size:
                stats['file_sizes']['total'] += file_size
                stats['file_sizes']['min'] = min(stats['file_sizes']['min'], file_size)
                stats['file_sizes']['max'] = max(stats['file_sizes']['max'], file_size)

        # Calculate averages
        count = len(successful_results)
        stats['average_processing_time'] = stats['total_processing_time'] / count
        stats['file_sizes']['average'] = stats['file_sizes']['total'] / count

        # Convert set to list for JSON serialization
        stats['languages_detected'] = list(stats['languages_detected'])

        # Handle empty min
        if stats['file_sizes']['min'] == float('inf'):
            stats['file_sizes']['min'] = 0

        return stats

    def _create_summary_report(
        self,
        summary: Dict[str, Any],
        output_dir: str
    ) -> Optional[str]:
        """
        Create summary report as JSON file.

        Args:
            summary: Batch processing summary
            output_dir: Output directory

        Returns:
            Path to summary file or None on failure
        """
        try:
            # Create summary filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            summary_filename = f"batch_summary_{timestamp}.json"
            summary_path = os.path.join(output_dir, summary_filename)

            # Prepare summary for JSON (convert sets, etc.)
            json_summary = self._prepare_for_json(summary)

            # Write summary file
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(json_summary, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Summary report saved to: {summary_path}")
            return summary_path

        except Exception as e:
            self.logger.error(f"Failed to create summary report: {e}")
            return None

    def _prepare_for_json(self, obj: Any) -> Any:
        """
        Prepare object for JSON serialization.

        Args:
            obj: Object to prepare

        Returns:
            JSON-serializable object
        """
        if isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return {k: self._prepare_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._prepare_for_json(item) for item in obj]
        else:
            return obj

    def get_progress(self) -> Dict[str, int]:
        """
        Get current progress information.

        Thread-safe method for GUI updates.

        Returns:
            Dictionary with 'current' and 'total' counts
        """
        with self._lock:
            return {
                'current': self._current_progress,
                'total': self._total_files
            }

    def set_max_workers(self, max_workers: int):
        """
        Set maximum number of parallel workers.

        Args:
            max_workers: Number of workers (must be >= 1)
        """
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")

        with self._lock:
            self.max_workers = max_workers
            self.logger.info(f"Max workers set to: {max_workers}")

    def set_continue_on_error(self, continue_on_error: bool):
        """
        Set whether to continue processing on error.

        Args:
            continue_on_error: If True, continue processing other files on error
        """
        with self._lock:
            self.continue_on_error = continue_on_error
            self.logger.info(f"Continue on error: {continue_on_error}")

    def process_directory(
        self,
        input_dir: str,
        output_dir: str,
        recursive: bool = False,
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process all PDF files in a directory.

        Args:
            input_dir: Input directory containing PDF files
            output_dir: Output directory for processed files
            recursive: If True, search subdirectories recursively
            config: Optional processing configuration
            progress_callback: Optional progress callback

        Returns:
            Batch processing summary (same as process_batch)
        """
        self.logger.info(f"Processing directory: {input_dir} (recursive={recursive})")

        # Find all PDF files
        pattern = '*.pdf'
        pdf_files = FileHelper.list_files(input_dir, pattern, recursive)

        if not pdf_files:
            self.logger.warning(f"No PDF files found in {input_dir}")
            return {
                'success': True,
                'total_files': 0,
                'processed': 0,
                'failed': 0,
                'skipped': 0,
                'output_directory': output_dir,
                'results': [],
                'errors': [],
                'statistics': {}
            }

        self.logger.info(f"Found {len(pdf_files)} PDF files")

        # Process batch
        return self.process_batch(pdf_files, output_dir, config, progress_callback)
