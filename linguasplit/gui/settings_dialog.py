"""
Settings dialog for LinguaSplit configuration.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from linguasplit.utils.config_manager import ConfigManager


class SettingsDialog:
    """
    Settings dialog with tab-based organization.

    Tabs:
    - Output: Output format and options
    - Language: Language detection settings
    - Layout: Layout detection parameters
    - Processing: Text processing options
    - OCR: OCR configuration
    - Batch: Batch processing settings
    - GUI: GUI preferences
    """

    def __init__(self, parent: tk.Tk, config: ConfigManager):
        """
        Initialize settings dialog.

        Args:
            parent: Parent window
            config: Configuration manager
        """
        self.parent = parent
        self.config = config
        self.result = False  # True if OK clicked

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)

        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Store original config for cancel
        self.original_config = config.get_all()

        # Variables for settings
        self.vars: Dict[str, Any] = {}

        # Create UI
        self._create_widgets()

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
        """Create the settings dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create tabs
        self._create_output_tab()
        self._create_language_tab()
        self._create_layout_tab()
        self._create_processing_tab()
        self._create_ocr_tab()
        self._create_batch_tab()
        self._create_gui_tab()

        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=self._reset_defaults,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=12
        ).pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            button_frame,
            text="OK",
            command=self._on_ok,
            width=12
        ).pack(side=tk.RIGHT, padx=2)

    def _create_output_tab(self):
        """Create output settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Output")

        # Output format
        ttk.Label(frame, text="Output Format:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.vars['output.format'] = tk.StringVar(value=self.config.get('output.format', 'markdown'))
        format_combo = ttk.Combobox(
            frame,
            textvariable=self.vars['output.format'],
            values=['markdown', 'text', 'json'],
            state='readonly',
            width=30
        )
        format_combo.grid(row=0, column=1, sticky=tk.W, pady=5)

        # Include metadata
        self.vars['output.include_metadata'] = tk.BooleanVar(
            value=self.config.get('output.include_metadata', True)
        )
        ttk.Checkbutton(
            frame,
            text="Include metadata in output",
            variable=self.vars['output.include_metadata']
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Include page markers
        self.vars['output.include_page_markers'] = tk.BooleanVar(
            value=self.config.get('output.include_page_markers', True)
        )
        ttk.Checkbutton(
            frame,
            text="Include page markers",
            variable=self.vars['output.include_page_markers']
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Preserve formatting
        self.vars['output.preserve_formatting'] = tk.BooleanVar(
            value=self.config.get('output.preserve_formatting', True)
        )
        ttk.Checkbutton(
            frame,
            text="Preserve text formatting",
            variable=self.vars['output.preserve_formatting']
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

    def _create_language_tab(self):
        """Create language detection settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Language")

        # Auto detect
        self.vars['language.auto_detect'] = tk.BooleanVar(
            value=self.config.get('language.auto_detect', True)
        )
        ttk.Checkbutton(
            frame,
            text="Automatically detect languages",
            variable=self.vars['language.auto_detect']
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Default language
        ttk.Label(frame, text="Default Language:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.vars['language.default_language'] = tk.StringVar(
            value=self.config.get('language.default_language', 'english')
        )
        lang_entry = ttk.Entry(frame, textvariable=self.vars['language.default_language'], width=30)
        lang_entry.grid(row=1, column=1, sticky=tk.W, pady=5)

        # Minimum confidence
        ttk.Label(frame, text="Minimum Confidence:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.vars['language.min_confidence'] = tk.DoubleVar(
            value=self.config.get('language.min_confidence', 0.5)
        )
        conf_spin = ttk.Spinbox(
            frame,
            from_=0.0,
            to=1.0,
            increment=0.1,
            textvariable=self.vars['language.min_confidence'],
            width=28
        )
        conf_spin.grid(row=2, column=1, sticky=tk.W, pady=5)

        ttk.Label(
            frame,
            text="(0.0 = accept all, 1.0 = only very confident)",
            font=('TkDefaultFont', 8),
            foreground='gray'
        ).grid(row=3, column=1, sticky=tk.W)

        # Separator
        ttk.Separator(frame, orient='horizontal').grid(row=4, column=0, columnspan=2, sticky=tk.EW, pady=15)

        # Language filter section - PROMINENT
        filter_frame = ttk.LabelFrame(frame, text="🎯 Language Selection Filter", padding=10)
        filter_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        frame.grid_columnconfigure(0, weight=1)

        # Instructions
        ttk.Label(
            filter_frame,
            text="Choose which languages to extract from your PDFs:",
            font=('TkDefaultFont', 9, 'bold'),
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 5))

        ttk.Label(
            filter_frame,
            text="• Leave EMPTY to extract ALL detected languages\n• Enter specific languages (comma-separated) to extract only those\n• Examples: 'english, french' or 'kinyarwanda' or 'english, french, kinyarwanda'",
            justify=tk.LEFT,
            foreground='#555'
        ).pack(anchor=tk.W, pady=(0, 8))

        # Language filter entry
        self.vars['language.extract_only'] = tk.StringVar(
            value=self.config.get('language.extract_only', '')
        )
        
        ttk.Label(
            filter_frame,
            text="Languages to extract:",
            font=('TkDefaultFont', 9)
        ).pack(anchor=tk.W, pady=(0, 2))
        
        filter_entry = ttk.Entry(filter_frame, textvariable=self.vars['language.extract_only'], width=60)
        filter_entry.pack(fill=tk.X, pady=(0, 5))
        
        # Common language buttons for quick selection
        common_frame = ttk.Frame(filter_frame)
        common_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(common_frame, text="Quick select:", foreground='gray').pack(side=tk.LEFT, padx=(0, 5))
        
        def add_language(lang):
            current = self.vars['language.extract_only'].get().strip()
            if current:
                if lang.lower() not in current.lower():
                    self.vars['language.extract_only'].set(current + ', ' + lang)
            else:
                self.vars['language.extract_only'].set(lang)
        
        def clear_languages():
            self.vars['language.extract_only'].set('')
        
        for lang in ['english', 'french', 'kinyarwanda', 'spanish']:
            ttk.Button(
                common_frame,
                text=lang.title(),
                command=lambda l=lang: add_language(l),
                width=10
            ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            common_frame,
            text="Clear",
            command=clear_languages,
            width=8
        ).pack(side=tk.LEFT, padx=(10, 0))

    def _create_layout_tab(self):
        """Create layout detection settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Layout")

        # Use region-based analysis (NEW - recommended)
        self.vars['layout.use_region_analysis'] = tk.BooleanVar(
            value=self.config.get('layout.use_region_analysis', True)
        )
        region_check = ttk.Checkbutton(
            frame,
            text="Use region-based analysis (RECOMMENDED for complex layouts)",
            variable=self.vars['layout.use_region_analysis']
        )
        region_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Help text for region analysis
        ttk.Label(
            frame,
            text="Analyzes each page section independently to handle mixed layouts\n(e.g., single-column header + multi-column body on same page)",
            font=('TkDefaultFont', 8),
            foreground='gray',
            justify=tk.LEFT
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=20)

        # Separator
        ttk.Separator(frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)

        # Detect columns
        self.vars['layout.detect_columns'] = tk.BooleanVar(
            value=self.config.get('layout.detect_columns', True)
        )
        ttk.Checkbutton(
            frame,
            text="Detect multi-column layouts",
            variable=self.vars['layout.detect_columns']
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Minimum column width
        ttk.Label(frame, text="Min Column Width (points):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.vars['layout.min_column_width'] = tk.IntVar(
            value=self.config.get('layout.min_column_width', 100)
        )
        ttk.Spinbox(
            frame,
            from_=50,
            to=500,
            increment=10,
            textvariable=self.vars['layout.min_column_width'],
            width=28
        ).grid(row=4, column=1, sticky=tk.W, pady=5)

        # Column gap threshold
        ttk.Label(frame, text="Column Gap Threshold:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.vars['layout.column_gap_threshold'] = tk.IntVar(
            value=self.config.get('layout.column_gap_threshold', 50)
        )
        ttk.Spinbox(
            frame,
            from_=20,
            to=200,
            increment=10,
            textvariable=self.vars['layout.column_gap_threshold'],
            width=28
        ).grid(row=5, column=1, sticky=tk.W, pady=5)

        # Detect tables
        self.vars['layout.detect_tables'] = tk.BooleanVar(
            value=self.config.get('layout.detect_tables', False)
        )
        ttk.Checkbutton(
            frame,
            text="Detect tables (experimental)",
            variable=self.vars['layout.detect_tables']
        ).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=5)

    def _create_processing_tab(self):
        """Create text processing settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Processing")

        # Clean text
        self.vars['processing.clean_text'] = tk.BooleanVar(
            value=self.config.get('processing.clean_text', True)
        )
        ttk.Checkbutton(
            frame,
            text="Clean extracted text",
            variable=self.vars['processing.clean_text']
        ).grid(row=0, column=0, sticky=tk.W, pady=2)

        # Remove headers/footers
        self.vars['processing.remove_headers_footers'] = tk.BooleanVar(
            value=self.config.get('processing.remove_headers_footers', True)
        )
        ttk.Checkbutton(
            frame,
            text="Remove headers and footers",
            variable=self.vars['processing.remove_headers_footers']
        ).grid(row=1, column=0, sticky=tk.W, pady=2)

        # Normalize whitespace
        self.vars['processing.normalize_whitespace'] = tk.BooleanVar(
            value=self.config.get('processing.normalize_whitespace', True)
        )
        ttk.Checkbutton(
            frame,
            text="Normalize whitespace",
            variable=self.vars['processing.normalize_whitespace']
        ).grid(row=2, column=0, sticky=tk.W, pady=2)

        # Fix hyphenation
        self.vars['processing.fix_hyphenation'] = tk.BooleanVar(
            value=self.config.get('processing.fix_hyphenation', True)
        )
        ttk.Checkbutton(
            frame,
            text="Fix line-break hyphenation",
            variable=self.vars['processing.fix_hyphenation']
        ).grid(row=3, column=0, sticky=tk.W, pady=2)

    def _create_ocr_tab(self):
        """Create OCR settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="OCR")

        # Enable OCR
        self.vars['ocr.enabled'] = tk.BooleanVar(
            value=self.config.get('ocr.enabled', False)
        )
        ttk.Checkbutton(
            frame,
            text="Enable OCR for scanned PDFs",
            variable=self.vars['ocr.enabled']
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # OCR engine
        ttk.Label(frame, text="OCR Engine:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.vars['ocr.engine'] = tk.StringVar(value=self.config.get('ocr.engine', 'tesseract'))
        engine_combo = ttk.Combobox(
            frame,
            textvariable=self.vars['ocr.engine'],
            values=['tesseract', 'easyocr'],
            state='readonly',
            width=30
        )
        engine_combo.grid(row=1, column=1, sticky=tk.W, pady=5)

        # OCR language
        ttk.Label(frame, text="OCR Language Code:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.vars['ocr.language'] = tk.StringVar(value=self.config.get('ocr.language', 'eng'))
        ttk.Entry(frame, textvariable=self.vars['ocr.language'], width=30).grid(
            row=2, column=1, sticky=tk.W, pady=5
        )

        ttk.Label(
            frame,
            text="(e.g., 'eng' for English, 'fra' for French)",
            font=('TkDefaultFont', 8),
            foreground='gray'
        ).grid(row=3, column=1, sticky=tk.W)

        # DPI
        ttk.Label(frame, text="Image DPI:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.vars['ocr.dpi'] = tk.IntVar(value=self.config.get('ocr.dpi', 300))
        ttk.Spinbox(
            frame,
            from_=150,
            to=600,
            increment=50,
            textvariable=self.vars['ocr.dpi'],
            width=28
        ).grid(row=4, column=1, sticky=tk.W, pady=5)

    def _create_batch_tab(self):
        """Create batch processing settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Batch")

        # Max workers
        ttk.Label(frame, text="Parallel Workers:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.vars['batch.max_workers'] = tk.IntVar(
            value=self.config.get('batch.max_workers', 4)
        )
        ttk.Spinbox(
            frame,
            from_=1,
            to=16,
            increment=1,
            textvariable=self.vars['batch.max_workers'],
            width=28
        ).grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(
            frame,
            text="(Number of files to process simultaneously)",
            font=('TkDefaultFont', 8),
            foreground='gray'
        ).grid(row=1, column=1, sticky=tk.W)

        # Continue on error
        self.vars['batch.continue_on_error'] = tk.BooleanVar(
            value=self.config.get('batch.continue_on_error', True)
        )
        ttk.Checkbutton(
            frame,
            text="Continue processing if a file fails",
            variable=self.vars['batch.continue_on_error']
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Create summary
        self.vars['batch.create_summary'] = tk.BooleanVar(
            value=self.config.get('batch.create_summary', True)
        )
        ttk.Checkbutton(
            frame,
            text="Create summary report after processing",
            variable=self.vars['batch.create_summary']
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

    def _create_gui_tab(self):
        """Create GUI preferences tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="GUI")

        # Theme
        ttk.Label(frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.vars['gui.theme'] = tk.StringVar(value=self.config.get('gui.theme', 'system'))
        theme_combo = ttk.Combobox(
            frame,
            textvariable=self.vars['gui.theme'],
            values=['system', 'light', 'dark', 'clam', 'alt', 'default'],
            state='readonly',
            width=30
        )
        theme_combo.grid(row=0, column=1, sticky=tk.W, pady=5)

        ttk.Label(
            frame,
            text="(Requires restart to take effect)",
            font=('TkDefaultFont', 8),
            foreground='gray'
        ).grid(row=1, column=1, sticky=tk.W)

        # Show preview
        self.vars['gui.show_preview'] = tk.BooleanVar(
            value=self.config.get('gui.show_preview', True)
        )
        ttk.Checkbutton(
            frame,
            text="Show preview dialog by default",
            variable=self.vars['gui.show_preview']
        ).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # Auto-save settings
        self.vars['gui.auto_save_settings'] = tk.BooleanVar(
            value=self.config.get('gui.auto_save_settings', True)
        )
        ttk.Checkbutton(
            frame,
            text="Auto-save window size and position",
            variable=self.vars['gui.auto_save_settings']
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)

        # Logging level
        ttk.Label(frame, text="Logging Level:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.vars['logging.level'] = tk.StringVar(
            value=self.config.get('logging.level', 'INFO')
        )
        log_combo = ttk.Combobox(
            frame,
            textvariable=self.vars['logging.level'],
            values=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            state='readonly',
            width=30
        )
        log_combo.grid(row=4, column=1, sticky=tk.W, pady=5)

        # Log to file
        self.vars['logging.log_to_file'] = tk.BooleanVar(
            value=self.config.get('logging.log_to_file', False)
        )
        ttk.Checkbutton(
            frame,
            text="Save logs to file",
            variable=self.vars['logging.log_to_file']
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)

    def _reset_defaults(self):
        """Reset all settings to default values."""
        if messagebox.askyesno(
            "Reset Settings",
            "Reset all settings to default values?\n\nThis cannot be undone."
        ):
            # Reset config
            self.config.reset(save=False)

            # Update all variables
            for key, var in self.vars.items():
                value = self.config.get(key)
                if isinstance(var, tk.BooleanVar):
                    var.set(bool(value))
                elif isinstance(var, tk.IntVar):
                    var.set(int(value))
                elif isinstance(var, tk.DoubleVar):
                    var.set(float(value))
                else:
                    var.set(str(value))

            messagebox.showinfo("Settings Reset", "All settings have been reset to defaults.")

    def _on_ok(self):
        """Handle OK button click."""
        try:
            # Apply all settings
            for key, var in self.vars.items():
                value = var.get()
                self.config.set(key, value, save=False)

            # Save configuration
            if self.config.save():
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror(
                    "Save Error",
                    "Failed to save configuration.\n\nPlease check file permissions."
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings:\n{str(e)}")

    def _on_cancel(self):
        """Handle Cancel button click."""
        # Restore original config
        self.config.update(self.original_config, save=False)
        self.result = False
        self.dialog.destroy()
