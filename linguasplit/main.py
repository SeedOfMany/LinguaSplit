"""
LinguaSplit - Multi-Language PDF Document Extractor

Main entry point for the application.
"""

import sys
import tkinter as tk
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from linguasplit.gui.main_window import LinguaSplitMainWindow


def main():
    """Launch the LinguaSplit GUI application."""
    # Create root window
    root = tk.Tk()
    
    # Create and run application
    app = LinguaSplitMainWindow(root)
    app.run()


if __name__ == "__main__":
    main()
