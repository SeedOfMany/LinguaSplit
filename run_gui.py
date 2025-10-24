#!/usr/bin/env python3
"""
Quick launcher script for LinguaSplit GUI.
"""

import sys
from pathlib import Path

# Add linguasplit to path
sys.path.insert(0, str(Path(__file__).parent))

# Launch GUI
from linguasplit.gui import main

if __name__ == "__main__":
    main()
