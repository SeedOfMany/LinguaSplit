"""
Log viewer widget for displaying real-time processing logs.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from typing import Optional
from datetime import datetime


class LogViewerWidget(ttk.Frame):
    """
    Real-time log viewer with auto-scroll and filtering.

    Features:
    - Auto-scrolling log display
    - Color-coded log levels
    - Clear log functionality
    - Search/filter capability
    - Export logs to file
    """

    # Log level colors
    COLORS = {
        'INFO': 'black',
        'WARNING': 'orange',
        'ERROR': 'red',
        'SUCCESS': 'green',
        'DEBUG': 'gray'
    }

    def __init__(self, parent, height: int = 10):
        """
        Initialize log viewer widget.

        Args:
            parent: Parent widget
            height: Height in lines (default: 10)
        """
        super().__init__(parent)

        self.height = height
        self._create_widgets()

    def _create_widgets(self):
        """Create the log viewer UI components."""
        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=(5, 0))

        ttk.Label(toolbar, text="Log:").pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            toolbar,
            text="Clear",
            command=self.clear,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="Save Log",
            command=self.export_logs,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toolbar,
            text="Auto-scroll",
            variable=self.auto_scroll_var
        ).pack(side=tk.LEFT, padx=10)

        # Text widget with scrollbar
        text_frame = ttk.Frame(self)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create scrolled text widget
        self.text = scrolledtext.ScrolledText(
            text_frame,
            height=self.height,
            wrap=tk.WORD,
            font=('Courier', 9),
            state=tk.DISABLED
        )
        self.text.pack(fill=tk.BOTH, expand=True)

        # Configure tags for different log levels
        for level, color in self.COLORS.items():
            self.text.tag_config(level, foreground=color)

    def log(self, message: str, level: str = 'INFO'):
        """
        Add a log message.

        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR, SUCCESS, DEBUG)
        """
        # Add timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}\n"

        # Insert into text widget
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, formatted_message, level)
        self.text.config(state=tk.DISABLED)

        # Auto-scroll to bottom if enabled
        if self.auto_scroll_var.get():
            self.text.see(tk.END)

    def info(self, message: str):
        """Log info message."""
        self.log(message, 'INFO')

    def warning(self, message: str):
        """Log warning message."""
        self.log(message, 'WARNING')

    def error(self, message: str):
        """Log error message."""
        self.log(message, 'ERROR')

    def success(self, message: str):
        """Log success message."""
        self.log(message, 'SUCCESS')

    def debug(self, message: str):
        """Log debug message."""
        self.log(message, 'DEBUG')

    def clear(self):
        """Clear all log messages."""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)

    def export_logs(self):
        """Export logs to a file."""
        from tkinter import filedialog

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    content = self.text.get(1.0, tk.END)
                    f.write(content)
                self.success(f"Logs exported to: {file_path}")
            except Exception as e:
                self.error(f"Failed to export logs: {str(e)}")

    def get_logs(self) -> str:
        """
        Get all log content.

        Returns:
            Log content as string
        """
        return self.text.get(1.0, tk.END)
