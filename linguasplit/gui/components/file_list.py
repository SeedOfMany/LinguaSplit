"""
File list widget with checkboxes, size, and status display.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import List, Dict, Callable, Optional


class FileListWidget(ttk.Frame):
    """
    File list widget with checkboxes and status tracking.

    Features:
    - Checkbox selection for each file
    - Display file name, size, and status
    - Select all/deselect all functionality
    - Sort by different columns
    - Context menu for file operations
    """

    def __init__(self, parent, on_selection_change: Optional[Callable] = None):
        """
        Initialize file list widget.

        Args:
            parent: Parent widget
            on_selection_change: Callback when selection changes
        """
        super().__init__(parent)

        self.on_selection_change = on_selection_change
        self.files: Dict[str, Dict] = {}  # file_path -> file_info

        self._create_widgets()

    def _create_widgets(self):
        """Create the file list UI components."""
        # Toolbar with select all/none buttons
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            toolbar,
            text="Select All",
            command=self.select_all,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="Deselect All",
            command=self.deselect_all,
            width=12
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar,
            text="Remove Selected",
            command=self.remove_selected,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        # File count label
        self.count_label = ttk.Label(toolbar, text="Files: 0")
        self.count_label.pack(side=tk.RIGHT, padx=5)

        # Treeview with scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("filename", "size", "status"),
            show="tree headings",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            selectmode="extended"
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Configure columns
        self.tree.heading("#0", text="✓", anchor=tk.W)
        self.tree.heading("filename", text="Filename", anchor=tk.W)
        self.tree.heading("size", text="Size", anchor=tk.E)
        self.tree.heading("status", text="Status", anchor=tk.W)

        self.tree.column("#0", width=30, minwidth=30, stretch=False)
        self.tree.column("filename", width=400, minwidth=200)
        self.tree.column("size", width=100, minwidth=80, anchor=tk.E)
        self.tree.column("status", width=150, minwidth=100)

        # Bind events
        self.tree.bind("<Button-1>", self._on_click)
        self.tree.bind("<Double-Button-1>", self._on_double_click)

        # Tags for styling
        self.tree.tag_configure("checked", foreground="black")
        self.tree.tag_configure("unchecked", foreground="gray")
        self.tree.tag_configure("success", foreground="green")
        self.tree.tag_configure("error", foreground="red")
        self.tree.tag_configure("processing", foreground="blue")

    def add_files(self, file_paths: List[str]):
        """
        Add files to the list.

        Args:
            file_paths: List of file paths to add
        """
        for file_path in file_paths:
            if file_path not in self.files:
                path = Path(file_path)

                # Get file size
                try:
                    size = path.stat().st_size
                    size_str = self._format_size(size)
                except:
                    size_str = "Unknown"

                # Add to tree
                item_id = self.tree.insert(
                    "",
                    tk.END,
                    text="☑",
                    values=(path.name, size_str, "Pending"),
                    tags=("checked",)
                )

                # Store file info
                self.files[file_path] = {
                    "item_id": item_id,
                    "checked": True,
                    "status": "Pending",
                    "path": file_path,
                    "filename": path.name,
                    "size": size_str
                }

        self._update_count()
        self._notify_selection_change()

    def remove_selected(self):
        """Remove selected files from the list."""
        selected_items = self.tree.selection()

        # Find and remove corresponding files
        files_to_remove = []
        for file_path, info in self.files.items():
            if info["item_id"] in selected_items:
                files_to_remove.append(file_path)

        for file_path in files_to_remove:
            item_id = self.files[file_path]["item_id"]
            self.tree.delete(item_id)
            del self.files[file_path]

        self._update_count()
        self._notify_selection_change()

    def clear(self):
        """Clear all files from the list."""
        self.tree.delete(*self.tree.get_children())
        self.files.clear()
        self._update_count()
        self._notify_selection_change()

    def select_all(self):
        """Check all files."""
        for file_path, info in self.files.items():
            if not info["checked"]:
                info["checked"] = True
                self.tree.item(info["item_id"], text="☑", tags=("checked",))

        self._notify_selection_change()

    def deselect_all(self):
        """Uncheck all files."""
        for file_path, info in self.files.items():
            if info["checked"]:
                info["checked"] = False
                self.tree.item(info["item_id"], text="☐", tags=("unchecked",))

        self._notify_selection_change()

    def get_selected_files(self) -> List[str]:
        """
        Get list of checked file paths.

        Returns:
            List of file paths that are checked
        """
        return [
            file_path
            for file_path, info in self.files.items()
            if info["checked"]
        ]

    def update_file_status(self, file_path: str, status: str):
        """
        Update the status of a file.

        Args:
            file_path: Path to the file
            status: New status (Pending, Processing, Success, Error)
        """
        if file_path in self.files:
            info = self.files[file_path]
            info["status"] = status

            # Determine tag based on status
            if status == "Success":
                tags = ("checked", "success")
            elif status == "Error":
                tags = ("checked", "error")
            elif status == "Processing":
                tags = ("checked", "processing")
            else:
                tags = ("checked",)

            self.tree.item(
                info["item_id"],
                values=(info["filename"], info["size"], status),
                tags=tags
            )

    def _on_click(self, event):
        """Handle click events on the tree."""
        region = self.tree.identify("region", event.x, event.y)

        if region == "tree":
            # Click on checkbox column
            item = self.tree.identify_row(event.y)
            if item:
                # Find the file
                for file_path, info in self.files.items():
                    if info["item_id"] == item:
                        # Toggle checkbox
                        info["checked"] = not info["checked"]
                        checkbox = "☑" if info["checked"] else "☐"
                        tags = ("checked",) if info["checked"] else ("unchecked",)
                        self.tree.item(item, text=checkbox, tags=tags)
                        self._notify_selection_change()
                        break

    def _on_double_click(self, event):
        """Handle double-click events."""
        # Could be used to preview file or show details
        pass

    def _format_size(self, size: int) -> str:
        """
        Format file size in human-readable format.

        Args:
            size: Size in bytes

        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def _update_count(self):
        """Update the file count label."""
        total = len(self.files)
        selected = sum(1 for info in self.files.values() if info["checked"])
        self.count_label.config(text=f"Files: {selected}/{total}")

    def _notify_selection_change(self):
        """Notify callback of selection change."""
        if self.on_selection_change:
            self.on_selection_change()
