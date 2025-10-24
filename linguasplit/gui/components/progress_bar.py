"""
Progress bar widget with percentage and status text.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class ProgressBarWidget(ttk.Frame):
    """
    Progress bar with percentage and status display.

    Features:
    - Determinate and indeterminate modes
    - Percentage display
    - Status text
    - Cancel button support
    """

    def __init__(self, parent, on_cancel: Optional[callable] = None):
        """
        Initialize progress bar widget.

        Args:
            parent: Parent widget
            on_cancel: Optional callback for cancel button
        """
        super().__init__(parent)

        self.on_cancel = on_cancel
        self._create_widgets()

    def _create_widgets(self):
        """Create the progress bar UI components."""
        # Progress bar
        self.progress = ttk.Progressbar(
            self,
            mode='determinate',
            length=400
        )
        self.progress.pack(fill=tk.X, padx=5, pady=(5, 2))

        # Info frame (percentage + status + cancel)
        info_frame = ttk.Frame(self)
        info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        # Percentage label
        self.percentage_label = ttk.Label(
            info_frame,
            text="0%",
            width=8
        )
        self.percentage_label.pack(side=tk.LEFT)

        # Status label
        self.status_label = ttk.Label(
            info_frame,
            text="Ready"
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Cancel button (hidden by default)
        self.cancel_button = ttk.Button(
            info_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            width=10
        )

        # Start hidden
        self.hide()

    def show(self):
        """Show the progress bar."""
        self.pack(fill=tk.X, padx=10, pady=5)

    def hide(self):
        """Hide the progress bar."""
        self.pack_forget()

    def set_progress(self, current: int, total: int, status: str = ""):
        """
        Update progress.

        Args:
            current: Current progress value
            total: Total value
            status: Status text to display
        """
        if total > 0:
            percentage = (current / total) * 100
            self.progress['value'] = percentage
            self.percentage_label.config(text=f"{percentage:.1f}%")

        if status:
            self.status_label.config(text=status)

    def set_indeterminate(self, active: bool = True):
        """
        Set indeterminate mode (for unknown duration tasks).

        Args:
            active: Whether to activate indeterminate mode
        """
        if active:
            self.progress['mode'] = 'indeterminate'
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress['mode'] = 'determinate'

    def set_status(self, status: str):
        """
        Set status text.

        Args:
            status: Status text
        """
        self.status_label.config(text=status)

    def show_cancel_button(self, show: bool = True):
        """
        Show or hide cancel button.

        Args:
            show: Whether to show the button
        """
        if show and self.on_cancel:
            self.cancel_button.pack(side=tk.RIGHT)
        else:
            self.cancel_button.pack_forget()

    def reset(self):
        """Reset progress to 0."""
        self.progress['value'] = 0
        self.percentage_label.config(text="0%")
        self.status_label.config(text="Ready")

    def complete(self):
        """Set progress to 100% complete."""
        self.progress['value'] = 100
        self.percentage_label.config(text="100%")
        self.status_label.config(text="Complete")

    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.on_cancel:
            self.on_cancel()
