# LinguaSplit Setup Guide

## Quick Start (macOS)

### 1. Install tkinter support
```bash
brew install python-tk@3.14
```

### 2. Create virtual environment with system site packages
```bash
python3 -m venv --system-site-packages venv
```

### 3. Activate virtual environment and install dependencies
```bash
source venv/bin/activate
pip install PyMuPDF pdfplumber pytesseract pdf2image Pillow langdetect python-magic chardet numpy scikit-learn
```

### 4. Run the application

**Option A: Using the startup script**
```bash
./start_linguasplit.sh
```

**Option B: Manual activation**
```bash
source venv/bin/activate
python main.py
```

## Troubleshooting

### tkinter not available
If you get `ModuleNotFoundError: No module named '_tkinter'`:
- Make sure you installed `python-tk@3.14` via Homebrew
- Recreate the virtual environment with `--system-site-packages` flag

### ttkthemes installation fails
This is a known issue with Python 3.14. The app works fine without it - it will just use the default system theme instead of fancy themes.

### OCR not working
For OCR functionality, install Tesseract:
```bash
brew install tesseract
```

## Command Line Options

```bash
# Show version
python main.py --version

# Enable debug logging
python main.py --debug

# Use custom config file
python main.py --config /path/to/config.json

# Reset configuration to defaults
python main.py --reset-config
```

## System Requirements

- Python 3.8 or higher (tested with 3.14)
- macOS with Homebrew
- tkinter support (via python-tk)
- ~100MB disk space for dependencies

