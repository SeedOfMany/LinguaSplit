# 🚀 LinguaSplit Quick Start

## ✅ Status: READY TO USE

The app is fully installed and tested. All components are working!

---

## Launch the Application

### Option 1: Quick Launch (Recommended)
```bash
./start_linguasplit.sh
```

### Option 2: Manual Launch
```bash
source venv/bin/activate
python main.py
```

---

## What You Can Do

### 1. Extract Text from PDFs
- Drag and drop PDF files or click "Add Files"
- Select output folder
- Click "Start Processing"

### 2. Multi-Language Support
The app automatically detects and separates content in:
- English, Spanish, French, German, Italian
- Chinese, Japanese, Korean
- Arabic, Russian, Portuguese
- And 50+ more languages

### 3. Handle Complex Layouts
- **Single-column** documents
- **Multi-column** layouts (newspapers, academic papers)
- **Mixed layouts** (some pages with columns, some without)

### 4. Batch Processing
- Process multiple PDFs at once
- Parallel processing for speed
- Real-time progress tracking

### 5. Multiple Output Formats
- Markdown (default)
- Plain text
- JSON with metadata

---

## Quick Tutorial

1. **Launch the app**
   ```bash
   ./start_linguasplit.sh
   ```

2. **Add PDF files**
   - Click "Add Files" or "Add Folder"
   - Or use File → Add Files menu

3. **Select output folder**
   - Click "Browse..." next to Output Folder

4. **Adjust settings** (optional)
   - Click "Settings" button
   - Enable/disable language detection
   - Enable/disable column detection
   - Choose output format

5. **Start processing**
   - Click "Start Processing"
   - Watch real-time progress in the log viewer

6. **View results**
   - Check the output folder
   - Preview files before saving
   - View processing summary

---

## Command Line Options

```bash
# Show version
python main.py --version

# Enable debug logging
python main.py --debug

# Reset to default settings
python main.py --reset-config

# Use custom config file
python main.py --config /path/to/config.json
```

---

## Testing

Run the test suite to verify everything is working:
```bash
source venv/bin/activate
python test_app.py
```

Expected output: **5/5 test suites passed** ✅

---

## Troubleshooting

### App won't start
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Try running with debug mode
python main.py --debug
```

### No GUI appears
Check if tkinter is available:
```bash
python3 -c "import tkinter; print('OK')"
```

If not, reinstall tkinter support:
```bash
brew install python-tk@3.14
```

### PDF processing errors
- Ensure PDFs are not password-protected
- For scanned PDFs, install Tesseract: `brew install tesseract`

---

## Project Structure

```
LinguaSplit/
├── start_linguasplit.sh    # Quick launch script
├── main.py                 # Main entry point
├── test_app.py            # Test suite
├── requirements.txt        # Dependencies
├── venv/                  # Virtual environment
└── linguasplit/           # Application code
    ├── gui/               # User interface
    ├── core/              # Processing logic
    ├── formatters/        # Output formats
    └── utils/             # Utilities
```

---

## Need Help?

- **Documentation**: See `README.md` for detailed documentation
- **Setup Issues**: See `SETUP.md` for installation instructions
- **Status Report**: See `APP_STATUS.md` for component status

---

## What's Next?

Ready to process your first PDF? Let's go! 🎉

```bash
./start_linguasplit.sh
```

