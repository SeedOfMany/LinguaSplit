"""
Main application window for LinguaSplit GUI.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from linguasplit.gui.components.file_list import FileListWidget
from linguasplit.gui.components.log_viewer import LogViewerWidget
from linguasplit.gui.components.progress_bar import ProgressBarWidget
from linguasplit.utils.config_manager import ConfigManager

# Try to import tkinterdnd2 for drag and drop support
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DRAG_DROP_AVAILABLE = True
except ImportError:
    DRAG_DROP_AVAILABLE = False


class LinguaSplitMainWindow:
    """
    Main application window for LinguaSplit.

    Features:
    - File selection and management
    - Batch processing with progress tracking
    - Real-time log viewer
    - Settings management
    - Preview and summary dialogs
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize main window.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("LinguaSplit - Multi-Language PDF Extractor")

        # Load configuration
        self.config = ConfigManager()

        # Set window size from config
        window_size = self.config.get('gui.window_size', [1000, 700])
        self.root.geometry(f"{window_size[0]}x{window_size[1]}")

        # Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.processing = False
        self.cancel_processing = False
        
        # Language selection variables
        self.extract_all_languages = tk.BooleanVar(value=True)
        self.selected_languages = {
            'english': tk.BooleanVar(value=False),
            'french': tk.BooleanVar(value=False),
            'kinyarwanda': tk.BooleanVar(value=False),
            'spanish': tk.BooleanVar(value=False),
            'german': tk.BooleanVar(value=False),
            'chinese': tk.BooleanVar(value=False),
            'arabic': tk.BooleanVar(value=False),
            'portuguese': tk.BooleanVar(value=False)
        }

        # Apply theme
        self._apply_theme()

        # Create UI
        self._create_menu_bar()
        self._create_widgets()
        self._create_status_bar()

        # Protocol handlers
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _apply_theme(self):
        """Apply visual theme to the application."""
        try:
            from ttkthemes import ThemedStyle
            theme_name = self.config.get('gui.theme', 'system')

            if theme_name == 'system':
                # Use default ttk theme
                style = ttk.Style()
                available_themes = style.theme_names()
                if 'aqua' in available_themes:
                    style.theme_use('aqua')
                elif 'clam' in available_themes:
                    style.theme_use('clam')
            elif theme_name != 'system':
                try:
                    style = ThemedStyle(self.root)
                    style.set_theme(theme_name)
                except:
                    pass
        except ImportError:
            pass

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Add Files...", command=self._add_files, accelerator="Cmd+O")
        file_menu.add_command(label="Add Folder...", command=self._add_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Clear All Files", command=self._clear_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing, accelerator="Cmd+Q")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Settings...", command=self._open_settings, accelerator="Cmd+,")

        # Process menu
        process_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Process", menu=process_menu)
        process_menu.add_command(label="Start Processing", command=self._start_processing, accelerator="Cmd+R")
        process_menu.add_command(label="Stop Processing", command=self._stop_processing, accelerator="Cmd+.")

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Preview Selected File", command=self._preview_file)
        view_menu.add_command(label="Clear Log", command=lambda: self.log_viewer.clear())

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About LinguaSplit", command=self._show_about)
        help_menu.add_command(label="Documentation", command=self._show_documentation)

        # Bind keyboard shortcuts
        self.root.bind("<Command-o>", lambda e: self._add_files())
        self.root.bind("<Command-comma>", lambda e: self._open_settings())
        self.root.bind("<Command-r>", lambda e: self._start_processing())
        self.root.bind("<Command-period>", lambda e: self._stop_processing())
        self.root.bind("<Command-q>", lambda e: self._on_closing())

    def _create_widgets(self):
        """Create the main UI widgets."""
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Top section: File selection and list
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=3)

        # Folder selection frame
        folder_frame = ttk.LabelFrame(top_frame, text="Folders", padding=10)
        folder_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Input folder
        ttk.Label(folder_frame, text="Input Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=50).grid(
            row=0, column=1, sticky=tk.EW, padx=5, pady=2
        )
        ttk.Button(folder_frame, text="Browse...", command=self._browse_input_folder).grid(
            row=0, column=2, padx=5, pady=2
        )

        # Output folder
        ttk.Label(folder_frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=50).grid(
            row=1, column=1, sticky=tk.EW, padx=5, pady=2
        )
        ttk.Button(folder_frame, text="Browse...", command=self._browse_output_folder).grid(
            row=1, column=2, padx=5, pady=2
        )

        folder_frame.columnconfigure(1, weight=1)

        # Language selection frame - PROMINENT
        lang_frame = ttk.LabelFrame(top_frame, text="🌍 Languages to Extract", padding=10)
        lang_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # All languages option
        all_lang_check = ttk.Checkbutton(
            lang_frame,
            text="Extract All Languages (default)",
            variable=self.extract_all_languages,
            command=self._toggle_language_selection
        )
        all_lang_check.grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))
        
        # Separator
        ttk.Separator(lang_frame, orient='horizontal').grid(row=1, column=0, columnspan=4, sticky=tk.EW, pady=5)
        
        # Individual language checkboxes
        ttk.Label(lang_frame, text="Or select specific languages:").grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(0, 5))
        
        # Create language checkboxes in a grid
        languages = [
            ('English', 'english'),
            ('French', 'french'),
            ('Kinyarwanda', 'kinyarwanda'),
            ('Spanish', 'spanish'),
            ('German', 'german'),
            ('Chinese', 'chinese'),
            ('Arabic', 'arabic'),
            ('Portuguese', 'portuguese')
        ]
        
        def on_language_selected():
            """When a specific language is selected, uncheck 'All Languages'"""
            if any(var.get() for var in self.selected_languages.values()):
                self.extract_all_languages.set(False)
            self._update_ui_state()
        
        row = 3
        col = 0
        for display_name, lang_key in languages:
            cb = ttk.Checkbutton(
                lang_frame,
                text=display_name,
                variable=self.selected_languages[lang_key],
                command=on_language_selected
            )
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
            col += 1
            if col > 3:  # 4 columns
                col = 0
                row += 1
        
        # Configure grid columns
        for i in range(4):
            lang_frame.columnconfigure(i, weight=1)

        # PROMINENT PROCESS BUTTON at top
        process_top_frame = ttk.Frame(top_frame)
        process_top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.process_button_top = ttk.Button(
            process_top_frame,
            text="▶ PROCESS FILES",
            command=self._start_processing,
            style="Accent.TButton"
        )
        self.process_button_top.pack(side=tk.RIGHT, ipadx=20, ipady=10)

        ttk.Label(
            process_top_frame,
            text="👉 Click to extract text from PDFs automatically",
            foreground='gray'
        ).pack(side=tk.RIGHT, padx=10)

        # File list frame with drag-and-drop support
        file_frame = ttk.LabelFrame(top_frame, text="Files to Process (Drag & Drop PDF files here)", padding=5)
        file_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.file_list = FileListWidget(file_frame, on_selection_change=self._update_ui_state)
        self.file_list.pack(fill=tk.BOTH, expand=True)

        # Control buttons frame
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            control_frame,
            text="Add Files",
            command=self._add_files,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            control_frame,
            text="Add Folder",
            command=self._add_folder,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            control_frame,
            text="Preview",
            command=self._preview_file,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        # Process button (prominent)
        self.process_button = ttk.Button(
            control_frame,
            text="Start Processing",
            command=self._start_processing,
            width=20
        )
        self.process_button.pack(side=tk.RIGHT, padx=2)

        ttk.Button(
            control_frame,
            text="Settings",
            command=self._open_settings,
            width=15
        ).pack(side=tk.RIGHT, padx=2)

        # Bottom section: Progress and logs
        bottom_frame = ttk.Frame(main_paned)
        main_paned.add(bottom_frame, weight=1)

        # Progress bar
        self.progress_bar = ProgressBarWidget(bottom_frame, on_cancel=self._stop_processing)
        # Start hidden
        self.progress_bar.pack_forget()

        # Log viewer
        log_frame = ttk.LabelFrame(bottom_frame, text="Processing Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log_viewer = LogViewerWidget(log_frame, height=10)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)

        # Setup drag and drop (after log_viewer is created)
        self._setup_drag_drop()

        # Initial log message
        self.log_viewer.info("LinguaSplit initialized. Ready to process files.")

    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(
            self.status_bar,
            text="Ready",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)

        # Add version info
        version = self.config.get('app.version', '1.0.0')
        ttk.Label(
            self.status_bar,
            text=f"v{version}",
            anchor=tk.E
        ).pack(side=tk.RIGHT, padx=5, pady=2)

    def _setup_drag_drop(self):
        """Setup drag and drop functionality for the file list."""
        if not DRAG_DROP_AVAILABLE:
            # Drag and drop not available, log info
            self.log_viewer.info("Drag & Drop: Install tkinterdnd2 to enable this feature")
            return

        # Enable drag and drop on the treeview widget
        tree = self.file_list.tree

        # Register the widget for drag and drop
        tree.drop_target_register(DND_FILES)
        tree.dnd_bind('<<Drop>>', self._on_drop)

    def _on_drop(self, event):
        """
        Handle file drop event.

        Args:
            event: Drop event containing file paths
        """
        try:
            # Get dropped files - format varies by platform
            files = event.data

            # Parse file paths (handle both single and multiple files)
            if isinstance(files, str):
                # macOS/Linux format: space-separated paths in curly braces
                import re
                # Remove curly braces and split by space (respecting quoted paths)
                files = files.strip('{}').split('} {')
                files = [f.strip('{}').strip() for f in files]

            # Filter for PDF files only
            pdf_files = []
            for file_path in files:
                path = Path(file_path)
                if path.is_file() and path.suffix.lower() == '.pdf':
                    pdf_files.append(str(path))
                elif path.is_dir():
                    # If a folder is dropped, add all PDFs from it
                    folder_pdfs = list(path.glob("*.pdf"))
                    pdf_files.extend([str(f) for f in folder_pdfs])

            if pdf_files:
                self.file_list.add_files(pdf_files)
                self.log_viewer.info(f"Dropped {len(pdf_files)} PDF file(s)")
            else:
                self.log_viewer.warning("No PDF files found in dropped items")

        except Exception as e:
            self.log_viewer.error(f"Error handling dropped files: {str(e)}")

    def _browse_input_folder(self):
        """Browse for input folder."""
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder.set(folder)
            # Auto-load PDF files from folder
            self._load_pdfs_from_folder(folder)

    def _browse_output_folder(self):
        """Browse for output folder."""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    def _add_files(self):
        """Add individual files from anywhere (can select from different folders)."""
        files = filedialog.askopenfilenames(
            title="Select PDF Files (you can select from multiple folders)",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialdir=self.input_folder.get() if self.input_folder.get() else None
        )
        if files:
            self.file_list.add_files(list(files))
            self.log_viewer.info(f"Added {len(files)} file(s)")

    def _add_folder(self):
        """Add all PDFs from a folder."""
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            self._load_pdfs_from_folder(folder)

    def _load_pdfs_from_folder(self, folder: str):
        """
        Load all PDF files from a folder.

        Args:
            folder: Folder path
        """
        pdf_files = list(Path(folder).glob("*.pdf"))
        if pdf_files:
            self.file_list.add_files([str(f) for f in pdf_files])
            self.log_viewer.info(f"Added {len(pdf_files)} PDF file(s) from folder")
        else:
            messagebox.showwarning("No PDFs Found", f"No PDF files found in:\n{folder}")

    def _clear_files(self):
        """Clear all files from the list."""
        if messagebox.askyesno("Clear Files", "Remove all files from the list?"):
            self.file_list.clear()
            self.log_viewer.info("File list cleared")

    def _preview_file(self):
        """Preview selected file."""
        selected_files = self.file_list.get_selected_files()

        if not selected_files:
            messagebox.showwarning("No Selection", "Please select a file to preview.")
            return

        # Preview first selected file
        file_path = selected_files[0]

        try:
            from linguasplit.gui.preview_dialog import PreviewDialog
            PreviewDialog(self.root, file_path, self.config)
        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to preview file:\n{str(e)}")
            self.log_viewer.error(f"Preview failed: {str(e)}")

    def _open_settings(self):
        """Open settings dialog."""
        try:
            from linguasplit.gui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.root, self.config)

            if dialog.result:
                self.log_viewer.info("Settings updated successfully")
                # Reapply theme if changed
                self._apply_theme()
        except Exception as e:
            messagebox.showerror("Settings Error", f"Failed to open settings:\n{str(e)}")

    def _start_processing(self):
        """Start batch processing."""
        # Validate inputs
        selected_files = self.file_list.get_selected_files()

        if not selected_files:
            messagebox.showwarning("No Files", "Please add and select files to process.")
            return

        output_folder = self.output_folder.get()
        if not output_folder:
            messagebox.showwarning("No Output Folder", "Please select an output folder.")
            return

        # Confirm start
        if not messagebox.askyesno(
            "Start Processing",
            f"Process {len(selected_files)} file(s)?\n\nOutput folder:\n{output_folder}"
        ):
            return

        # Start processing in background thread
        self.processing = True
        self.cancel_processing = False

        # Update UI
        self._set_processing_ui(True)

        # Create processing thread
        thread = threading.Thread(target=self._process_files, args=(selected_files, output_folder))
        thread.daemon = True
        thread.start()

    def _stop_processing(self):
        """Stop/cancel processing."""
        if self.processing:
            if messagebox.askyesno("Cancel Processing", "Are you sure you want to cancel processing?"):
                self.cancel_processing = True
                self.log_viewer.warning("Processing cancelled by user")

    def _process_files(self, file_paths: List[str], output_folder: str):
        """
        Process files in background thread.

        Args:
            file_paths: List of file paths to process
            output_folder: Output folder path
        """
        try:
            from linguasplit.core.batch_processor import BatchProcessor

            # Apply language filter from UI selection
            selected_langs = self._get_selected_languages_list()
            if selected_langs:
                # Set language filter in config (temporarily for this processing)
                lang_filter = ', '.join(selected_langs)
                self.config.set('language.extract_only', lang_filter, save=False)
                self.root.after(0, self.log_viewer.info, f"Language filter active: {lang_filter}")
            else:
                # Clear any existing filter
                self.config.set('language.extract_only', '', save=False)

            # Create batch processor
            processor = BatchProcessor(config=self.config)

            # Progress callback for UI updates
            def progress_callback(current, total, filename):
                self.root.after(0, self._update_progress, current - 1, total, f"Processing: {filename}")
                self.root.after(0, self.log_viewer.info, f"Processing: {filename}")

            # Process batch
            self.root.after(0, self.log_viewer.info, f"Starting batch processing of {len(file_paths)} files...")
            
            batch_result = processor.process_batch(
                pdf_files=file_paths,
                output_dir=output_folder,
                progress_callback=progress_callback
            )

            # Convert batch result to expected format
            results = {
                'success': [],
                'failed': [],
                'total': batch_result.get('total_files', len(file_paths))
            }

            # Update file statuses based on results
            for result in batch_result.get('results', []):
                file_path = result.get('pdf_path', '')
                if result.get('success', False):
                    results['success'].append(file_path)
                    self.root.after(0, self.file_list.update_file_status, file_path, "Success")
                    self.root.after(0, self.log_viewer.success, f"Completed: {Path(file_path).name}")
                else:
                    results['failed'].append(file_path)
                    self.root.after(0, self.file_list.update_file_status, file_path, "Error")
                    error_msg = result.get('error', 'Unknown error')
                    self.root.after(0, self.log_viewer.error, f"Failed: {Path(file_path).name} - {error_msg}")

            # Complete
            self.root.after(0, self._processing_complete, results)

        except Exception as e:
            self.root.after(0, self.log_viewer.error, f"Processing error: {str(e)}")
            self.root.after(0, messagebox.showerror, "Processing Error", f"An error occurred:\n{str(e)}")
            self.root.after(0, self._set_processing_ui, False)

    def _update_progress(self, current: int, total: int, status: str):
        """Update progress bar (called from main thread)."""
        self.progress_bar.set_progress(current + 1, total, status)

    def _processing_complete(self, results: Dict[str, Any]):
        """
        Handle processing completion.

        Args:
            results: Processing results dictionary
        """
        self._set_processing_ui(False)

        # Log summary
        success_count = len(results['success'])
        failed_count = len(results['failed'])
        total = results['total']

        self.log_viewer.info(f"Processing complete: {success_count}/{total} successful, {failed_count} failed")

        # Show summary dialog
        if self.config.get('batch.create_summary', True):
            try:
                from linguasplit.gui.summary_dialog import SummaryDialog
                SummaryDialog(self.root, results, self.output_folder.get())
            except Exception as e:
                self.log_viewer.error(f"Failed to show summary: {str(e)}")

        # Show completion message
        if failed_count == 0:
            messagebox.showinfo(
                "Processing Complete",
                f"Successfully processed {success_count} file(s)!\n\nOutput folder:\n{self.output_folder.get()}"
            )
        else:
            messagebox.showwarning(
                "Processing Complete with Errors",
                f"Processed: {success_count}/{total}\nFailed: {failed_count}\n\nCheck the log for details."
            )

    def _set_processing_ui(self, processing: bool):
        """
        Update UI for processing state.

        Args:
            processing: Whether processing is active
        """
        self.processing = processing

        if processing:
            # Show progress bar
            self.progress_bar.show()
            self.progress_bar.show_cancel_button(True)
            self.progress_bar.reset()

            # Update buttons
            self.process_button_top.config(text="⏸ Processing...", state=tk.DISABLED)
            self.process_button.config(text="Processing...", state=tk.DISABLED)

            # Update status
            self.status_label.config(text="Processing files...")

        else:
            # Hide progress bar
            self.progress_bar.hide()

            # Update buttons
            self.process_button_top.config(text="▶ PROCESS FILES", state=tk.NORMAL)
            self.process_button.config(text="Start Processing", state=tk.NORMAL)

            # Update status
            self.status_label.config(text="Ready")

    def _toggle_language_selection(self):
        """Toggle between all languages and specific language selection."""
        if self.extract_all_languages.get():
            # Uncheck all specific languages when "All Languages" is selected
            for lang_var in self.selected_languages.values():
                lang_var.set(False)
            self.log_viewer.info("Language selection: Extract all detected languages")
        else:
            self.log_viewer.info("Language selection: Extract only selected languages")
        self._update_ui_state()
    
    def _get_selected_languages_list(self):
        """
        Get list of selected languages for extraction.
        
        Returns:
            List of language names, or empty list for all languages
        """
        if self.extract_all_languages.get():
            return []  # Empty list means extract all
        
        selected = [lang for lang, var in self.selected_languages.items() if var.get()]
        return selected
    
    def _update_ui_state(self):
        """Update UI state based on current selections."""
        selected_count = len(self.file_list.get_selected_files())
        
        # Build status message
        status_parts = [f"{selected_count} file(s) selected"]
        
        # Add language filter info
        selected_langs = self._get_selected_languages_list()
        if selected_langs:
            if len(selected_langs) == 1:
                status_parts.append(f"extracting {selected_langs[0]} only")
            else:
                status_parts.append(f"extracting {len(selected_langs)} languages")
        else:
            status_parts.append("extracting all languages")
        
        self.status_label.config(text=f"Ready - {' | '.join(status_parts)}")

    def _show_about(self):
        """Show about dialog."""
        version = self.config.get('app.version', '1.0.0')
        messagebox.showinfo(
            "About LinguaSplit",
            f"LinguaSplit v{version}\n\n"
            "Multi-Language PDF Document Extractor\n\n"
            "Intelligently extracts and separates multilingual content from PDF documents.\n\n"
            "Features:\n"
            "- Automatic language detection\n"
            "- Layout-aware extraction (columns, sections, sequential)\n"
            "- Batch processing\n"
            "- Multiple output formats\n\n"
            "© 2024 LinguaSplit"
        )

    def _show_documentation(self):
        """Show documentation."""
        messagebox.showinfo(
            "Documentation",
            "For documentation and help, please visit:\n\n"
            "https://github.com/yourusername/linguasplit\n\n"
            "Or refer to the README.md file in the project directory."
        )

    def _on_closing(self):
        """Handle window close event."""
        if self.processing:
            if not messagebox.askyesno(
                "Processing in Progress",
                "Processing is still running. Are you sure you want to exit?"
            ):
                return

        # Save window size if auto-save is enabled
        if self.config.get('gui.auto_save_settings', True):
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            self.config.set('gui.window_size', [width, height])

        self.root.destroy()

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    root = tk.Tk()
    app = LinguaSplitMainWindow(root)
    app.run()


if __name__ == "__main__":
    main()
