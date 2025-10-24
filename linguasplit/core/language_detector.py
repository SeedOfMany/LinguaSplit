"""
Language detection module with multi-strategy approach.
Supports flexible, extensible language detection for any language.
"""

import re
from typing import Tuple, Dict, List, Optional


class LanguageDetector:
    """
    Multi-strategy language detector supporting any language.

    Uses statistical detection, keyword patterns, and character set analysis
    to identify languages with high accuracy.
    """

    def __init__(self, custom_patterns: Optional[Dict] = None):
        """
        Initialize language detector.

        Args:
            custom_patterns: Optional dictionary of custom language keyword patterns
        """
        # Try to import langdetect
        self.langdetect_available = True
        try:
            from langdetect import detect, detect_langs
            self.detect = detect
            self.detect_langs = detect_langs
        except ImportError:
            self.langdetect_available = False

        # Default keyword patterns for common languages
        self.keyword_patterns = {
            'kinyarwanda': {
                'keywords': ['ingingo', 'komite', 'perezida', 'iteka', 'umutwe', 'umunyarwanda',
                             'ry\'', 'cy\'', 'n\'', 'by\'', 'kwa', 'rya', 'iya', 'kandi', 
                             'igihe', 'cyangwa', 'uko', 'umuntu', 'ugize', 'aho', 'bya',
                             'minisitiri', 'abagize', 'kugira', 'ngo', 'republika'],
                'weight': 1.5
            },
            'french': {
                'keywords': ['le', 'la', 'les', 'des', 'du', 'de', 'que', 'est',
                             'dans', 'pour', 'avec', 'par', 'cette', 'sont'],
                'weight': 0.8
            },
            'english': {
                'keywords': ['the', 'of', 'and', 'to', 'in', 'is', 'that', 'for',
                             'with', 'on', 'as', 'this', 'are', 'by'],
                'weight': 0.8
            },
            'spanish': {
                'keywords': ['el', 'la', 'de', 'que', 'y', 'en', 'los', 'del',
                             'las', 'por', 'con', 'para', 'una', 'este'],
                'weight': 0.8
            }
        }

        # Merge custom patterns if provided
        if custom_patterns:
            self.keyword_patterns.update(custom_patterns)

    def detect_language(self, text: str, min_length: int = 100) -> Tuple[str, float]:
        """
        Detect language using multiple methods.

        Args:
            text: Text to analyze
            min_length: Minimum text length for reliable detection

        Returns:
            Tuple of (language_name, confidence_score)
        """
        if not text or len(text.strip()) < min_length:
            return ('unknown', 0.0)

        results = []

        # Method 1: langdetect library (if available)
        if self.langdetect_available:
            lang_result = self._detect_with_langdetect(text)
            if lang_result:
                results.append(lang_result)

        # Method 2: Keyword pattern matching
        pattern_result = self._detect_by_patterns(text)
        if pattern_result:
            results.append(pattern_result)

        # Method 3: Character set analysis
        charset_result = self._detect_by_charset(text)
        if charset_result:
            results.append(charset_result)

        # Combine results
        if results:
            return self._combine_detection_results(results)

        return ('unknown', 0.0)

    def _detect_with_langdetect(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Detect language using langdetect library.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (language, confidence) or None
        """
        try:
            lang_probs = self.detect_langs(text)
            if lang_probs:
                primary = lang_probs[0]
                
                # Handle Catalan misdetection - often confuses French with Catalan
                if primary.lang == 'ca':
                    # Check if it's actually French
                    french_keywords = ['le', 'la', 'de', 'et', 'est', 'que', 'des', 'les',
                                      'dans', 'pour', 'son', 'une', 'par', 'du', 'commission']
                    text_lower = text.lower()
                    french_count = sum(1 for keyword in french_keywords if f' {keyword} ' in f' {text_lower} ')
                    
                    # If we find many French keywords, it's likely French
                    if french_count >= 5:
                        return ('french', 0.9)  # High confidence for French
                
                # Handle Swahili misdetection - often confuses Kinyarwanda with Swahili
                if primary.lang == 'sw':
                    # Check if it's actually Kinyarwanda
                    kiny_keywords = ['ingingo', 'komisiyo', 'abakomiseri', 'perezida', 'repubulika',
                                    'itegeko', 'umutwe', 'umukomiseri', 'umwanya', 'abakozi',
                                    'rwandaise', 'kigali', 'mu rwanda', 'ry\'u rwanda']
                    text_lower = text.lower()
                    kiny_count = sum(1 for keyword in kiny_keywords if keyword in text_lower)
                    
                    # If we find many Kinyarwanda keywords, it's likely Kinyarwanda
                    if kiny_count >= 3:
                        return ('kinyarwanda', 0.95)  # Very high confidence for Kinyarwanda
                
                # Convert ISO 639-1 code to full name
                lang_name = self._iso_to_name(primary.lang)
                return (lang_name, primary.prob)
        except Exception:
            pass
        return None

    def _detect_by_patterns(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Detect language using keyword pattern matching.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (language, confidence) or None
        """
        text_lower = text.lower()
        scores = {}

        for lang, config in self.keyword_patterns.items():
            count = 0
            total_words = len(text.split())

            for keyword in config['keywords']:
                # Count occurrences with word boundaries
                pattern = r'\b' + re.escape(keyword) + r'\b'
                count += len(re.findall(pattern, text_lower))

            if count > 0:
                # Normalize by text length and apply weight
                normalized_score = (count / max(total_words, 1)) * config['weight'] * 100
                scores[lang] = normalized_score

        if scores:
            best_lang = max(scores, key=scores.get)
            # Normalize confidence to 0-1 range
            confidence = min(scores[best_lang] / 10, 1.0)
            return (best_lang, confidence)

        return None

    def _detect_by_charset(self, text: str) -> Optional[Tuple[str, float]]:
        """
        Detect language family using character set analysis.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (language_family, confidence) or None
        """
        # Count character types
        latin = sum(1 for c in text if '\u0000' <= c <= '\u007F')
        latin_ext = sum(1 for c in text if '\u0080' <= c <= '\u024F')
        cyrillic = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
        arabic = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        cjk = sum(1 for c in text if '\u4E00' <= c <= '\u9FFF')
        devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')

        total = len([c for c in text if c.isalpha()])
        if total == 0:
            return None

        # Determine script family with confidence
        if (latin + latin_ext) > 0.9 * total:
            # Check for French-specific accents
            has_french_accents = bool(re.search(r'[éèêëàâäôöùûüÿæœç]', text.lower()))
            if has_french_accents:
                return ('french', 0.7)
            # Default to English for Latin script
            return ('english', 0.5)

        elif cyrillic > 0.9 * total:
            return ('russian', 0.6)

        elif arabic > 0.9 * total:
            return ('arabic', 0.6)

        elif cjk > 0.5 * total:
            return ('chinese', 0.6)

        elif devanagari > 0.9 * total:
            return ('hindi', 0.6)

        return None

    def _combine_detection_results(self, results: List[Tuple[str, float]]) -> Tuple[str, float]:
        """
        Combine multiple detection results using weighted scoring.

        Args:
            results: List of (language, confidence) tuples

        Returns:
            Best (language, confidence) result
        """
        # Weight by confidence
        weighted_scores = {}
        for lang, conf in results:
            if lang not in weighted_scores:
                weighted_scores[lang] = []
            weighted_scores[lang].append(conf)

        # Calculate average confidence for each language
        avg_scores = {}
        for lang, confs in weighted_scores.items():
            avg_scores[lang] = sum(confs) / len(confs)

        if avg_scores:
            best_lang = max(avg_scores, key=avg_scores.get)
            # Boost confidence if multiple methods agree
            boost = 1.0 + (len(weighted_scores[best_lang]) - 1) * 0.1
            final_confidence = min(avg_scores[best_lang] * boost, 1.0)
            return (best_lang, final_confidence)

        return ('unknown', 0.0)

    def _iso_to_name(self, iso_code: str) -> str:
        """
        Convert ISO 639-1 language code to full name.

        Args:
            iso_code: Two-letter ISO language code

        Returns:
            Full language name
        """
        iso_map = {
            'en': 'english',
            'fr': 'french',
            'es': 'spanish',
            'de': 'german',
            'it': 'italian',
            'pt': 'portuguese',
            'ru': 'russian',
            'ar': 'arabic',
            'zh': 'chinese',
            'ja': 'japanese',
            'ko': 'korean',
            'hi': 'hindi',
            'rw': 'kinyarwanda',
            'sw': 'swahili',
            'nl': 'dutch',
            'pl': 'polish',
            'tr': 'turkish',
            'vi': 'vietnamese',
            'th': 'thai',
            'el': 'greek'
        }
        return iso_map.get(iso_code, iso_code)

    def add_custom_pattern(self, language: str, keywords: List[str], weight: float = 1.0):
        """
        Add or update a custom language pattern.

        Args:
            language: Language name
            keywords: List of characteristic keywords
            weight: Pattern weight (default 1.0)
        """
        self.keyword_patterns[language.lower()] = {
            'keywords': keywords,
            'weight': weight
        }
