#!/usr/bin/env python3
"""
Diagnostic tool to analyze PDF language detection and content separation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from linguasplit.core.pdf_processor import PDFProcessor
from linguasplit.core.extractors.paragraph_extractor import ParagraphExtractor
from linguasplit.core.language_detector import LanguageDetector
from linguasplit.utils.config_manager import ConfigManager

def diagnose_pdf(pdf_path: str):
    """Diagnose language detection in a PDF."""
    print(f"\n{'='*70}")
    print(f"  Diagnosing: {Path(pdf_path).name}")
    print(f"{'='*70}\n")
    
    # Initialize components
    config = ConfigManager()
    detector = LanguageDetector()
    extractor = ParagraphExtractor(language_detector=detector)
    
    # Get paragraph details
    print("Analyzing first 15 paragraphs...")
    print(f"{'-'*70}\n")
    
    details = extractor.get_paragraph_details(pdf_path, max_paragraphs=15)
    
    for detail in details:
        if 'error' in detail:
            print(f"Error: {detail['error']}")
            return
        
        print(f"Paragraph #{detail['index']+1} (Page {detail['page']})")
        print(f"  Language: {detail['language']}")
        print(f"  Length: {detail['length']} characters")
        print(f"  Preview: {detail['preview'][:80]}...")
        print()
    
    # Analyze pattern
    print(f"\n{'-'*70}")
    print("Pattern Analysis:")
    print(f"{'-'*70}\n")
    
    pattern_info = extractor.analyze_pattern(pdf_path, num_paragraphs=20)
    
    if 'error' in pattern_info:
        print(f"Error: {pattern_info['error']}")
        return
    
    print(f"Total paragraphs analyzed: {pattern_info['num_paragraphs']}")
    print(f"Languages found: {', '.join(pattern_info['languages_found'])}")
    print(f"Pattern detected: {pattern_info['pattern_detected']}")
    
    if pattern_info['detected_pattern']:
        print(f"Pattern: {' -> '.join(pattern_info['detected_pattern'])}")
    
    print(f"\nLanguage distribution:")
    for lang, count in pattern_info['language_counts'].items():
        print(f"  {lang}: {count} paragraphs")
    
    print(f"\nLanguage sequence (first 20):")
    print(f"  {' -> '.join(pattern_info['language_sequence'])}")
    
    print(f"\n{'='*70}")
    print("Recommendations:")
    print(f"{'='*70}\n")
    
    # Provide recommendations
    if 'unknown' in pattern_info['languages_found']:
        unknown_count = pattern_info['language_counts'].get('unknown', 0)
        total = pattern_info['num_paragraphs']
        unknown_pct = (unknown_count / total) * 100 if total > 0 else 0
        
        print(f"⚠️  {unknown_pct:.1f}% of paragraphs couldn't be identified.")
        print(f"   This usually means:")
        print(f"   - Paragraphs are too short for reliable detection")
        print(f"   - Text contains mostly numbers/symbols")
        print(f"   - OCR quality is poor\n")
    
    if len(pattern_info['languages_found']) > 3:
        print(f"⚠️  Many languages detected ({len(pattern_info['languages_found'])})")
        print(f"   This might indicate:")
        print(f"   - False positives from short text chunks")
        print(f"   - Mixed language content")
        print(f"   - Language detection is too sensitive\n")
    
    if not pattern_info['pattern_detected']:
        print(f"ℹ️  No repeating pattern detected")
        print(f"   Content will be grouped by language directly")
        print(f"   (all paragraphs of same language together)\n")
    else:
        print(f"✓  Repeating pattern detected")
        print(f"   Content follows: {' -> '.join(pattern_info['detected_pattern'])}")
        print(f"   Perfect for multilingual parallel documents!\n")

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python diagnose_pdf.py <pdf_file>")
        print("\nThis tool analyzes how LinguaSplit detects languages in your PDF")
        return 1
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        return 1
    
    try:
        diagnose_pdf(pdf_path)
        return 0
    except Exception as e:
        print(f"\nError during diagnosis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

