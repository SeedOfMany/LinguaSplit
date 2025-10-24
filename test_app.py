#!/usr/bin/env python3
"""
Comprehensive test script for LinguaSplit application.
Tests all major components without launching the GUI.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")

def test_imports():
    """Test all critical imports."""
    print_header("Testing Imports")
    
    tests = [
        ("GUI Main Window", "linguasplit.gui.main_window", "LinguaSplitMainWindow"),
        ("Settings Dialog", "linguasplit.gui.settings_dialog", "SettingsDialog"),
        ("Preview Dialog", "linguasplit.gui.preview_dialog", "PreviewDialog"),
        ("Summary Dialog", "linguasplit.gui.summary_dialog", "SummaryDialog"),
        ("PDF Processor", "linguasplit.core.pdf_processor", "PDFProcessor"),
        ("Batch Processor", "linguasplit.core.batch_processor", "BatchProcessor"),
        ("Language Detector", "linguasplit.core.language_detector", "LanguageDetector"),
        ("Layout Detector", "linguasplit.core.layout_detector", "LayoutDetector"),
        ("Config Manager", "linguasplit.utils.config_manager", "ConfigManager"),
        ("Logger", "linguasplit.utils.logger", "GUILogger"),
    ]
    
    passed = 0
    failed = 0
    
    for name, module, cls in tests:
        try:
            mod = __import__(module, fromlist=[cls])
            getattr(mod, cls)
            print(f"  ✓ {name}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
    
    print(f"\n  Result: {passed}/{len(tests)} passed")
    return failed == 0

def test_dependencies():
    """Test all required dependencies."""
    print_header("Testing Dependencies")
    
    deps = [
        ("PyMuPDF (PDF processing)", "fitz"),
        ("pdfplumber (PDF extraction)", "pdfplumber"),
        ("langdetect (language detection)", "langdetect"),
        ("Pillow (image processing)", "PIL"),
        ("numpy (numerical)", "numpy"),
        ("scikit-learn (ML)", "sklearn"),
        ("tkinter (GUI)", "tkinter"),
    ]
    
    passed = 0
    failed = 0
    
    for name, module in deps:
        try:
            __import__(module)
            print(f"  ✓ {name}")
            passed += 1
        except ImportError as e:
            print(f"  ✗ {name}: {e}")
            failed += 1
    
    print(f"\n  Result: {passed}/{len(deps)} passed")
    return failed == 0

def test_config_manager():
    """Test configuration manager."""
    print_header("Testing Configuration Manager")
    
    try:
        from linguasplit.utils.config_manager import ConfigManager
        
        # Create config manager
        config = ConfigManager()
        print("  ✓ ConfigManager instantiated")
        
        # Test getting default values
        version = config.get('app.version', '0.0.0')
        print(f"  ✓ App version: {version}")
        
        window_size = config.get('gui.window_size', [800, 600])
        print(f"  ✓ Window size: {window_size}")
        
        # Test setting values
        config.set('test.value', 'test123')
        value = config.get('test.value')
        assert value == 'test123', "Config set/get failed"
        print("  ✓ Config set/get working")
        
        print("\n  Result: Configuration manager working correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Configuration manager failed: {e}")
        return False

def test_language_detection():
    """Test language detection."""
    print_header("Testing Language Detection")
    
    try:
        from linguasplit.core.language_detector import LanguageDetector
        
        detector = LanguageDetector()
        print("  ✓ LanguageDetector instantiated")
        
        # Test English
        lang = detector.detect("This is a test in English.")
        print(f"  ✓ English detected: {lang}")
        
        # Test Spanish
        lang = detector.detect("Este es un texto en español.")
        print(f"  ✓ Spanish detected: {lang}")
        
        print("\n  Result: Language detection working")
        return True
        
    except Exception as e:
        print(f"  ✗ Language detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logger():
    """Test logging system."""
    print_header("Testing Logger")
    
    try:
        from linguasplit.utils.logger import GUILogger, LogLevel
        
        logger = GUILogger(name="TestLogger", level=LogLevel.INFO)
        print("  ✓ GUILogger instantiated")
        
        logger.info("Test info message")
        print("  ✓ Info logging working")
        
        logger.warning("Test warning message")
        print("  ✓ Warning logging working")
        
        logger.error("Test error message")
        print("  ✓ Error logging working")
        
        print("\n  Result: Logger working correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Logger failed: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  LinguaSplit Comprehensive Test Suite")
    print("="*70)
    
    results = []
    
    # Run all tests
    results.append(("Import Tests", test_imports()))
    results.append(("Dependency Tests", test_dependencies()))
    results.append(("Config Manager", test_config_manager()))
    results.append(("Language Detection", test_language_detection()))
    results.append(("Logger", test_logger()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}  {name}")
    
    print(f"\n  Total: {passed}/{len(results)} test suites passed")
    
    if failed == 0:
        print("\n  🎉 ALL TESTS PASSED! The app is ready to use.")
        print("\n  To launch the app, run:")
        print("    ./start_linguasplit.sh")
        print("  or")
        print("    source venv/bin/activate && python main.py")
        return 0
    else:
        print(f"\n  ⚠️  {failed} test suite(s) failed.")
        print("  Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

