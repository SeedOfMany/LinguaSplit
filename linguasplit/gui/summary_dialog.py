"""
Summary dialog showing batch processing results.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import json


class SummaryDialog:
    """
    Results summary dialog for batch processing.

    Features:
    - Overall statistics (success/fail counts)
    - Layout breakdown
    - Files created per language
    - Errors and issues list
    - Export report functionality
    """

    def __init__(self, parent: tk.Tk, results: Dict[str, Any], output_dir: str):
        """
        Initialize summary dialog.

        Args:
            parent: Parent window
            results: Processing results dictionary
            output_dir: Output directory path
        """
        self.parent = parent
        self.results = results
        self.output_dir = output_dir

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Processing Summary")
        self.dialog.geometry("700x600")
        self.dialog.resizable(True, True)

        # Make modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Create UI
        self._create_widgets()
        self._populate_summary()

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
        """Create the summary dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with overall stats
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Success/Fail indicators
        stats_frame = ttk.Frame(header_frame)
        stats_frame.pack(fill=tk.X)

        self.total_label = ttk.Label(
            stats_frame,
            text="Total: 0",
            font=('TkDefaultFont', 12, 'bold')
        )
        self.total_label.pack(side=tk.LEFT, padx=10)

        self.success_label = ttk.Label(
            stats_frame,
            text="Success: 0",
            font=('TkDefaultFont', 12),
            foreground='green'
        )
        self.success_label.pack(side=tk.LEFT, padx=10)

        self.failed_label = ttk.Label(
            stats_frame,
            text="Failed: 0",
            font=('TkDefaultFont', 12),
            foreground='red'
        )
        self.failed_label.pack(side=tk.LEFT, padx=10)

        # Notebook for detailed sections
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create tabs
        self._create_overview_tab()
        self._create_files_tab()
        self._create_languages_tab()
        self._create_errors_tab()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="Export Report",
            command=self._export_report,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Open Output Folder",
            command=self._open_output_folder,
            width=18
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            width=12
        ).pack(side=tk.RIGHT, padx=2)

    def _create_overview_tab(self):
        """Create overview tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Overview")

        # Create text widget for overview
        self.overview_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            height=20,
            font=('Courier', 10),
            state=tk.DISABLED
        )
        self.overview_text.pack(fill=tk.BOTH, expand=True)

    def _create_files_tab(self):
        """Create files tab showing processed files."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Files")

        # Treeview for files
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        self.files_tree = ttk.Treeview(
            tree_frame,
            columns=("status", "languages", "outputs"),
            show="tree headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.files_tree.yview)
        hsb.config(command=self.files_tree.xview)

        # Layout
        self.files_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Configure columns
        self.files_tree.heading("#0", text="File", anchor=tk.W)
        self.files_tree.heading("status", text="Status", anchor=tk.W)
        self.files_tree.heading("languages", text="Languages", anchor=tk.W)
        self.files_tree.heading("outputs", text="Output Files", anchor=tk.W)

        self.files_tree.column("#0", width=200, minwidth=150)
        self.files_tree.column("status", width=100, minwidth=80)
        self.files_tree.column("languages", width=150, minwidth=100)
        self.files_tree.column("outputs", width=50, minwidth=50)

        # Tags for coloring
        self.files_tree.tag_configure("success", foreground="green")
        self.files_tree.tag_configure("error", foreground="red")

    def _create_languages_tab(self):
        """Create languages tab showing language breakdown."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Languages")

        # Treeview for languages
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")

        self.lang_tree = ttk.Treeview(
            tree_frame,
            columns=("count", "files"),
            show="tree headings",
            yscrollcommand=vsb.set
        )

        vsb.config(command=self.lang_tree.yview)

        # Layout
        self.lang_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure columns
        self.lang_tree.heading("#0", text="Language", anchor=tk.W)
        self.lang_tree.heading("count", text="Occurrences", anchor=tk.E)
        self.lang_tree.heading("files", text="Output Files", anchor=tk.E)

        self.lang_tree.column("#0", width=200, minwidth=150)
        self.lang_tree.column("count", width=120, minwidth=100, anchor=tk.E)
        self.lang_tree.column("files", width=120, minwidth=100, anchor=tk.E)

    def _create_errors_tab(self):
        """Create errors tab showing issues."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Errors")

        self.errors_text = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            height=20,
            font=('Courier', 9),
            state=tk.DISABLED
        )
        self.errors_text.pack(fill=tk.BOTH, expand=True)

        # Configure tag for errors
        self.errors_text.tag_config("error", foreground="red")

    def _populate_summary(self):
        """Populate summary with results data."""
        # Update header stats
        total = self.results.get('total', 0)
        success = len(self.results.get('success', []))
        failed = len(self.results.get('failed', []))

        self.total_label.config(text=f"Total: {total}")
        self.success_label.config(text=f"Success: {success}")
        self.failed_label.config(text=f"Failed: {failed}")

        # Populate overview
        self._populate_overview()

        # Populate files list
        self._populate_files()

        # Populate languages
        self._populate_languages()

        # Populate errors
        self._populate_errors()

    def _populate_overview(self):
        """Populate overview text."""
        overview_lines = []

        # Processing summary
        overview_lines.append("=" * 60)
        overview_lines.append("PROCESSING SUMMARY")
        overview_lines.append("=" * 60)
        overview_lines.append("")

        # Statistics
        total = self.results.get('total', 0)
        success = len(self.results.get('success', []))
        failed = len(self.results.get('failed', []))

        overview_lines.append(f"Total Files:      {total}")
        overview_lines.append(f"Successful:       {success}")
        overview_lines.append(f"Failed:           {failed}")

        if total > 0:
            success_rate = (success / total) * 100
            overview_lines.append(f"Success Rate:     {success_rate:.1f}%")

        overview_lines.append("")

        # Output directory
        overview_lines.append(f"Output Directory: {self.output_dir}")
        overview_lines.append("")

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        overview_lines.append(f"Generated:        {timestamp}")
        overview_lines.append("")

        # Layout breakdown (if available)
        overview_lines.append("-" * 60)
        overview_lines.append("LAYOUT BREAKDOWN")
        overview_lines.append("-" * 60)

        # Count layouts from successful results
        layout_counts = {}
        for file_path in self.results.get('success', []):
            # In real implementation, would get layout from detailed results
            # For now, placeholder
            layout_counts['columns'] = layout_counts.get('columns', 0) + 1

        if layout_counts:
            for layout_type, count in layout_counts.items():
                overview_lines.append(f"{layout_type.title():20s} {count:3d}")
        else:
            overview_lines.append("No layout information available")

        # Show in text widget
        self.overview_text.config(state=tk.NORMAL)
        self.overview_text.delete(1.0, tk.END)
        self.overview_text.insert(1.0, "\n".join(overview_lines))
        self.overview_text.config(state=tk.DISABLED)

    def _populate_files(self):
        """Populate files tree."""
        # Add successful files
        for file_path in self.results.get('success', []):
            filename = Path(file_path).name

            self.files_tree.insert(
                "",
                tk.END,
                text=filename,
                values=("Success", "multiple", "2+"),
                tags=("success",)
            )

        # Add failed files
        for file_path in self.results.get('failed', []):
            filename = Path(file_path).name

            self.files_tree.insert(
                "",
                tk.END,
                text=filename,
                values=("Failed", "-", "0"),
                tags=("error",)
            )

    def _populate_languages(self):
        """Populate languages tree."""
        # Count languages across all successful files
        language_counts = {}
        output_file_counts = {}

        for file_path in self.results.get('success', []):
            # In real implementation, would get actual language data
            # Placeholder: assume 2 languages per file
            for lang in ['English', 'French']:  # Placeholder
                language_counts[lang] = language_counts.get(lang, 0) + 1
                output_file_counts[lang] = output_file_counts.get(lang, 0) + 1

        # Add to tree
        for lang, count in sorted(language_counts.items()):
            files = output_file_counts.get(lang, 0)
            self.lang_tree.insert(
                "",
                tk.END,
                text=lang,
                values=(count, files)
            )

        if not language_counts:
            self.lang_tree.insert(
                "",
                tk.END,
                text="No language data available",
                values=("-", "-")
            )

    def _populate_errors(self):
        """Populate errors text."""
        failed_files = self.results.get('failed', [])

        if not failed_files:
            self.errors_text.config(state=tk.NORMAL)
            self.errors_text.insert(1.0, "No errors occurred during processing.")
            self.errors_text.config(state=tk.DISABLED)
            return

        # Build error list
        error_lines = []
        error_lines.append(f"Total Errors: {len(failed_files)}\n")
        error_lines.append("=" * 60 + "\n\n")

        for i, file_path in enumerate(failed_files, 1):
            filename = Path(file_path).name
            error_lines.append(f"{i}. {filename}\n")
            error_lines.append(f"   Path: {file_path}\n")
            error_lines.append(f"   Error: Unknown error\n")  # Placeholder
            error_lines.append("\n")

        # Show in text widget
        self.errors_text.config(state=tk.NORMAL)
        self.errors_text.delete(1.0, tk.END)
        for line in error_lines:
            if "Error:" in line:
                self.errors_text.insert(tk.END, line, "error")
            else:
                self.errors_text.insert(tk.END, line)
        self.errors_text.config(state=tk.DISABLED)

    def _export_report(self):
        """Export summary report to file."""
        # Ask for save location
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialfile=f"processing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )

        if not file_path:
            return

        try:
            if file_path.endswith('.json'):
                # Export as JSON
                report_data = {
                    'timestamp': datetime.now().isoformat(),
                    'output_directory': self.output_dir,
                    'results': {
                        'total': self.results.get('total', 0),
                        'success': len(self.results.get('success', [])),
                        'failed': len(self.results.get('failed', [])),
                        'success_files': self.results.get('success', []),
                        'failed_files': self.results.get('failed', [])
                    }
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2, ensure_ascii=False)

            else:
                # Export as text
                with open(file_path, 'w', encoding='utf-8') as f:
                    # Get overview text
                    overview = self.overview_text.get(1.0, tk.END)
                    f.write(overview)

                    f.write("\n\n")
                    f.write("=" * 60 + "\n")
                    f.write("PROCESSED FILES\n")
                    f.write("=" * 60 + "\n\n")

                    # List all files
                    for file_path in self.results.get('success', []):
                        f.write(f"[SUCCESS] {file_path}\n")

                    for file_path in self.results.get('failed', []):
                        f.write(f"[FAILED]  {file_path}\n")

            messagebox.showinfo("Report Exported", f"Summary report saved to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")

    def _open_output_folder(self):
        """Open output folder in file manager."""
        import platform
        import subprocess

        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.output_dir])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", self.output_dir])
            else:  # Linux
                subprocess.run(["xdg-open", self.output_dir])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{str(e)}")
