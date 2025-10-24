# LinguaSplit

**Multi-Language PDF Document Extractor with Intelligent Layout Detection**

LinguaSplit is a powerful Python application designed to extract and organize text from multi-language PDF documents. It intelligently detects document layouts (single/multi-column), identifies language sections, and exports clean, well-formatted text with preserved structure.

## Features

- **Multi-Language Support**: Automatically detect and separate different languages within the same document
- **Intelligent Layout Detection**: Accurately identifies single-column, multi-column, and complex layouts
- **Column-Aware Extraction**: Properly extracts text from multi-column documents without mixing content
- **OCR Support**: Optional OCR for scanned documents using Tesseract or EasyOCR
- **Batch Processing**: Process multiple PDFs simultaneously with parallel processing
- **Multiple Output Formats**: Export to Markdown, plain text, or JSON
- **Text Cleaning**: Automatic removal of headers, footers, and formatting artifacts
- **Preview & Verification**: Built-in preview before saving extracted content
- **User-Friendly GUI**: Intuitive interface built with tkinter
- **Configurable**: Extensive configuration options for fine-tuning extraction

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Basic Installation

1. Clone or download this repository:
```bash
git clone https://github.com/yourusername/linguasplit.git
cd linguasplit
```

2. Install required Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Optional: OCR Support

For processing scanned PDFs, install Tesseract OCR:

**macOS** (using Homebrew):
```bash
brew install tesseract
```

**Ubuntu/Debian**:
```bash
sudo apt-get install tesseract-ocr
```

**Windows**:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

Install additional language packs as needed:
```bash
# Example for Spanish
brew install tesseract-lang  # macOS
sudo apt-get install tesseract-ocr-spa  # Ubuntu
```

## Quick Start

### GUI Mode (Recommended)

1. Launch the application:
```bash
python main.py
```

2. Click "Add Files" or drag and drop PDF files
3. Configure settings (optional) via the Settings button
4. Click "Start Processing"
5. Preview and save extracted text

### Command-Line Options

```bash
# Launch with debug logging
python main.py --debug

# Use custom configuration file
python main.py --config /path/to/config.json

# Reset configuration to defaults
python main.py --reset-config

# Show version
python main.py --version
```

## Usage Examples

### Basic Text Extraction

1. Add one or more PDF files to the file list
2. Click "Start Processing"
3. Review extracted text in the preview dialog
4. Save to your desired location

### Multi-Column Document Processing

LinguaSplit automatically detects multi-column layouts. For best results:

- Enable "Detect Columns" in Settings > Layout Detection
- Adjust "Column Gap Threshold" if columns are incorrectly merged (default: 50)
- Preview the output to verify proper column separation

### Multi-Language Document Processing

For documents containing multiple languages:

- Enable "Auto-detect Language" in Settings > Language Detection
- Each language section will be identified and marked
- Set "Minimum Confidence" to control detection sensitivity (default: 0.5)

### Batch Processing Configuration

Process multiple files efficiently:

```python
# Settings > Batch Processing
{
    "max_workers": 4,              # Parallel processing threads
    "continue_on_error": true,     # Don't stop on individual file errors
    "create_summary": true         # Generate processing summary
}
```

### OCR for Scanned PDFs

Enable OCR in Settings > OCR:

- Check "Enable OCR"
- Select OCR engine (Tesseract recommended)
- Set appropriate DPI (300 recommended for best quality)
- Choose OCR language (eng, spa, fra, etc.)

## Supported Document Types

### PDF Types
- Text-based PDFs (native text extraction)
- Scanned PDFs (with OCR enabled)
- Mixed content PDFs
- Password-protected PDFs (with correct password)

### Layouts
- Single-column documents
- Multi-column documents (2-3 columns)
- Mixed layout documents
- Academic papers and journals
- Magazines and newsletters
- Technical documentation

### Languages
LinguaSplit uses `langdetect` which supports 55+ languages including:
- English, Spanish, French, German, Italian
- Chinese, Japanese, Korean
- Arabic, Russian, Portuguese
- And many more

## Configuration

### Configuration File Location

- **Default**: `~/.linguasplit/config.json`
- **Custom**: Specify with `--config` flag

### Key Configuration Options

```json
{
  "output": {
    "format": "markdown",              // markdown, text, json
    "include_metadata": true,          // Include document metadata
    "include_page_markers": true,      // Mark page boundaries
    "preserve_formatting": true        // Maintain text formatting
  },

  "language": {
    "auto_detect": true,               // Enable language detection
    "default_language": "english",     // Fallback language
    "min_confidence": 0.5              // Detection threshold
  },

  "layout": {
    "detect_columns": true,            // Enable column detection
    "min_column_width": 100,           // Minimum column width (points)
    "column_gap_threshold": 50,        // Gap for column separation
    "detect_tables": false             // Experimental: table detection
  },

  "processing": {
    "clean_text": true,                // Remove extra whitespace
    "remove_headers_footers": true,    // Strip headers/footers
    "normalize_whitespace": true,      // Normalize spaces/newlines
    "fix_hyphenation": true            // Rejoin hyphenated words
  },

  "ocr": {
    "enabled": false,                  // Enable OCR processing
    "engine": "tesseract",             // tesseract or easyocr
    "language": "eng",                 // OCR language code
    "dpi": 300                         // Image resolution for OCR
  }
}
```

## Troubleshooting

### Common Issues

**1. Text extraction is garbled or mixed up**
- Enable column detection in Settings
- Adjust column gap threshold (increase for wider gaps)
- Check document layout in preview

**2. Language detection is incorrect**
- Increase minimum confidence threshold
- Manually specify language in settings
- Ensure document has sufficient text for detection

**3. OCR not working**
- Verify Tesseract is installed: `tesseract --version`
- Check OCR language pack is installed
- Increase DPI setting for better quality (up to 600)

**4. Slow processing**
- Reduce number of parallel workers for memory-constrained systems
- Disable OCR if not needed
- Process files in smaller batches

**5. Headers/footers appearing in output**
- Enable "Remove Headers/Footers" in Processing settings
- Adjust detection sensitivity (may need manual editing)

**6. Application won't start**
- Verify Python version: `python --version` (3.8+ required)
- Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
- Check error logs in console or log file

### Getting Help

If you encounter issues:

1. Enable debug logging: `python main.py --debug`
2. Check the log file for detailed error messages
3. Verify all dependencies are installed correctly
4. Try resetting configuration: `python main.py --reset-config`

## Project Structure

```
LinguaSplit/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── LICENSE                      # MIT License
└── linguasplit/
    ├── __init__.py
    ├── main.py                  # Legacy entry (use root main.py)
    ├── core/                    # Core processing logic
    │   ├── pdf_processor.py     # PDF text extraction
    │   ├── batch_processor.py   # Batch processing
    │   ├── language_detector.py # Language identification
    │   ├── layout_detector.py   # Layout analysis
    │   └── extractors/          # Text extraction strategies
    ├── gui/                     # User interface
    │   ├── main_window.py       # Main application window
    │   ├── settings_dialog.py   # Settings configuration
    │   ├── preview_dialog.py    # Text preview
    │   └── components/          # Reusable UI components
    ├── formatters/              # Output formatters
    │   ├── text_cleaner.py      # Text cleaning utilities
    │   └── markdown_formatter.py # Markdown export
    ├── utils/                   # Utility modules
    │   ├── config_manager.py    # Configuration management
    │   ├── logger.py            # Logging system
    │   ├── ocr_helper.py        # OCR integration
    │   └── file_helper.py       # File operations
    └── resources/               # Application resources
        ├── config.json          # Default configuration
        ├── icons/               # UI icons
        └── themes/              # UI themes
```

## Development

### Running from Source

```bash
# Clone repository
git clone https://github.com/yourusername/linguasplit.git
cd linguasplit

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

### Running Tests

```bash
# Run test suite (if available)
python -m pytest linguasplit/tests/
```

## License

MIT License

Copyright (c) 2025 LinguaSplit Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- Built with [PyMuPDF](https://pymupdf.readthedocs.io/) for PDF processing
- Uses [langdetect](https://github.com/Mimino666/langdetect) for language identification
- OCR powered by [Tesseract](https://github.com/tesseract-ocr/tesseract)
- GUI built with Python's tkinter

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Roadmap

- [ ] Support for EPUB and DOCX formats
- [ ] Advanced table extraction
- [ ] Batch editing of detected sections
- [ ] Cloud storage integration
- [ ] Export to additional formats (HTML, RTF)
- [ ] Plugin system for custom processors

---

**Version**: 1.0.0
**Author**: LinguaSplit Contributors
**Website**: https://github.com/yourusername/linguasplit
