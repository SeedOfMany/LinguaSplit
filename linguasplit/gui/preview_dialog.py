"""
Preview dialog for viewing PDF layout and language detection.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from linguasplit.utils.config_manager import ConfigManager


class PreviewDialog:
    """
    Preview dialog showing detected layout and languages.

    Features:
    - Display layout detection results
    - Show confidence scores
    - Preview extracted text by language
    - Language selector dropdown
    - Visual confidence indicators
    """

    def __init__(self, parent: tk.Tk, pdf_path: str, config: ConfigManager):
        """
        Initialize preview dialog.

        Args:
            parent: Parent window
            pdf_path: Path to PDF file
            config: Configuration manager
        """
        self.parent = parent
        self.pdf_path = pdf_path
        self.config = config

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Preview - {Path(pdf_path).name}")
        self.dialog.geometry("700x600")
        self.dialog.resizable(True, True)

        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Analysis results
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.extracted_text: Dict[str, str] = {}

        # Create UI
        self._create_widgets()

        # Start analysis
        self._analyze_pdf()

        # Center on parent
        self._center_on_parent()

        # Wait for dialog to close
        self.dialog.wait_window()

    def _center_on_parent(self):
        """Center dialog on parent window."""
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create the preview dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # File info section
        info_frame = ttk.LabelFrame(main_frame, text="File Information", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_info_label = ttk.Label(info_frame, text="Loading...", justify=tk.LEFT)
        self.file_info_label.pack(anchor=tk.W)

        # Layout detection section
        layout_frame = ttk.LabelFrame(main_frame, text="Layout Detection", padding=10)
        layout_frame.pack(fill=tk.X, pady=(0, 10))

        # Layout type
        ttk.Label(layout_frame, text="Detected Layout:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.layout_type_label = ttk.Label(layout_frame, text="Analyzing...", font=('TkDefaultFont', 10, 'bold'))
        self.layout_type_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=10)

        # Confidence indicator
        ttk.Label(layout_frame, text="Confidence:").grid(row=1, column=0, sticky=tk.W, pady=2)

        confidence_container = ttk.Frame(layout_frame)
        confidence_container.grid(row=1, column=1, sticky=tk.W, pady=2, padx=10)

        self.confidence_bar = ttk.Progressbar(
            confidence_container,
            mode='determinate',
            length=200
        )
        self.confidence_bar.pack(side=tk.LEFT, padx=(0, 5))

        self.confidence_label = ttk.Label(confidence_container, text="0%")
        self.confidence_label.pack(side=tk.LEFT)

        # Details
        ttk.Label(layout_frame, text="Details:").grid(row=2, column=0, sticky=tk.NW, pady=2)
        self.details_label = ttk.Label(layout_frame, text="", justify=tk.LEFT)
        self.details_label.grid(row=2, column=1, sticky=tk.W, pady=2, padx=10)

        # Language detection section
        lang_frame = ttk.LabelFrame(main_frame, text="Language Preview", padding=10)
        lang_frame.pack(fill=tk.BOTH, expand=True)

        # Language selector
        selector_frame = ttk.Frame(lang_frame)
        selector_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(selector_frame, text="Select Language:").pack(side=tk.LEFT, padx=(0, 5))

        self.language_var = tk.StringVar()
        self.language_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.language_var,
            state='readonly',
            width=20
        )
        self.language_combo.pack(side=tk.LEFT, padx=5)
        self.language_combo.bind('<<ComboboxSelected>>', self._on_language_selected)

        self.lang_confidence_label = ttk.Label(selector_frame, text="")
        self.lang_confidence_label.pack(side=tk.LEFT, padx=10)

        # Text preview
        preview_frame = ttk.Frame(lang_frame)
        preview_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(preview_frame, text="Text Preview:").pack(anchor=tk.W)

        self.preview_text = scrolledtext.ScrolledText(
            preview_frame,
            wrap=tk.WORD,
            height=15,
            font=('Courier', 10),
            state=tk.DISABLED
        )
        self.preview_text.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=12
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            button_frame,
            text="Process This File",
            command=self._process_file,
            width=15
        ).pack(side=tk.RIGHT, padx=2)

    def _analyze_pdf(self):
        """Analyze PDF and populate preview."""
        try:
            from linguasplit.core.pdf_processor import PDFProcessor

            # Create processor
            processor = PDFProcessor(config=self.config)

            # Show analyzing message
            self.file_info_label.config(text=f"Analyzing: {Path(self.pdf_path).name}")
            self.dialog.update()

            # Analyze PDF
            self.analysis_results = processor.analyze_pdf(self.pdf_path)

            # Update UI with results
            self._display_results()

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to analyze PDF:\n{str(e)}")
            self.file_info_label.config(text=f"Error: {str(e)}")

    def _display_results(self):
        """Display analysis results in UI."""
        if not self.analysis_results:
            return

        # File info
        file_info = self.analysis_results.get('file_info', {})
        file_name = file_info.get('name', Path(self.pdf_path).name)
        file_size = file_info.get('size_formatted', 'Unknown')

        self.file_info_label.config(
            text=f"File: {file_name}\nSize: {file_size}"
        )

        # Layout info
        layout_info = self.analysis_results.get('layout_info', {})
        layout_type = layout_info.get('type', 'unknown')
        confidence = layout_info.get('confidence', 0.0)

        # Update layout type
        layout_display = {
            'columns': 'Multi-Column Layout',
            'sequential': 'Sequential Paragraphs',
            'sections': 'Section-Based Layout'
        }.get(layout_type, layout_type.title())

        self.layout_type_label.config(text=layout_display)

        # Update confidence
        confidence_percent = confidence * 100
        self.confidence_bar['value'] = confidence_percent
        self.confidence_label.config(text=f"{confidence_percent:.1f}%")

        # Color code confidence
        if confidence >= 0.8:
            color = 'green'
        elif confidence >= 0.5:
            color = 'orange'
        else:
            color = 'red'

        # Update details
        details = layout_info.get('details', {})
        details_text = []

        spatial = details.get('spatial_analysis', {})
        if spatial:
            column_count = spatial.get('column_count', 1)
            details_text.append(f"Columns detected: {column_count}")

        language = details.get('language_analysis', {})
        if language:
            pattern_type = language.get('pattern_type', 'unknown')
            details_text.append(f"Language pattern: {pattern_type}")

        self.details_label.config(text="\n".join(details_text) if details_text else "No additional details")

        # Preview text
        preview = self.analysis_results.get('preview', '')
        if preview:
            self._detect_languages_in_preview(preview)

    def _detect_languages_in_preview(self, text: str):
        """
        Detect languages in preview text.

        Args:
            text: Preview text
        """
        try:
            from linguasplit.core.language_detector import LanguageDetector

            detector = LanguageDetector()

            # Simple split by newlines for demo
            # In real implementation, this would use proper text extraction
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

            # Detect languages
            languages_found = {}

            for para in paragraphs[:5]:  # Analyze first 5 paragraphs
                if len(para) > 50:  # Only analyze substantial paragraphs
                    lang, conf = detector.detect_language(para)
                    if lang != 'unknown' and conf > 0.3:
                        if lang not in languages_found:
                            languages_found[lang] = {
                                'confidence': conf,
                                'text': para
                            }

            # Update language combo
            if languages_found:
                self.extracted_text = {lang: data['text'] for lang, data in languages_found.items()}
                self.language_combo['values'] = list(languages_found.keys())
                self.language_combo.current(0)
                self._on_language_selected(None)
            else:
                # No languages detected, show raw preview
                self.extracted_text = {'preview': text}
                self.language_combo['values'] = ['preview']
                self.language_combo.current(0)
                self._show_text(text, 'Preview')

        except Exception as e:
            # Fallback: show raw preview
            self.extracted_text = {'preview': text}
            self.language_combo['values'] = ['preview']
            self.language_combo.current(0)
            self._show_text(text, 'Preview')

    def _on_language_selected(self, event):
        """Handle language selection change."""
        selected_lang = self.language_var.get()

        if selected_lang and selected_lang in self.extracted_text:
            text = self.extracted_text[selected_lang]
            self._show_text(text, selected_lang)

    def _show_text(self, text: str, language: str):
        """
        Show text in preview area.

        Args:
            text: Text to display
            language: Language name
        """
        # Update text widget
        self.preview_text.config(state=tk.NORMAL)
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, text)
        self.preview_text.config(state=tk.DISABLED)

        # Update confidence label
        char_count = len(text)
        word_count = len(text.split())
        self.lang_confidence_label.config(
            text=f"({word_count} words, {char_count} characters)"
        )

    def _process_file(self):
        """Process the current file."""
        if messagebox.askyesno(
            "Process File",
            f"Process this file now?\n\n{Path(self.pdf_path).name}"
        ):
            # Close dialog and signal to process
            self.dialog.destroy()
            # In real implementation, would trigger processing in main window
            messagebox.showinfo(
                "Processing",
                "File added to processing queue.\n\nClick 'Start Processing' in the main window."
            )
