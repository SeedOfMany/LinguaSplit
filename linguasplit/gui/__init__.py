"""
LinguaSplit GUI package.

Provides graphical user interface components for PDF processing.
"""

from .main_window import LinguaSplitMainWindow, main
from .settings_dialog import SettingsDialog
from .preview_dialog import PreviewDialog
from .summary_dialog import SummaryDialog

__all__ = [
    'LinguaSplitMainWindow',
    'SettingsDialog',
    'PreviewDialog',
    'SummaryDialog',
    'main'
]
