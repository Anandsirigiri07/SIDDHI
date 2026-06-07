# backend/translator.py
from typing import Dict, Any
from langdetect import detect
from backend.gemini_client import translate_kannada_to_english, translate_english_to_kannada

def detect_language(text: str) -> str:
    """
    Detects language of input text.
    Uses langdetect library and falls back to a Unicode block check for Kannada.
    Returns 'kn' (Kannada) or 'en' (English).
    """
    if not text or not text.strip():
        return 'en'
        
    # Check for Kannada Unicode range (U+0C80 to U+0CFF)
    # This acts as an extremely reliable, fast heuristic for Kannada text
    has_kannada_chars = any('\u0c80' <= char <= '\u0cff' for char in text)
    if has_kannada_chars:
        return 'kn'
        
    try:
        lang = detect(text)
        if lang == 'kn':
            return 'kn'
    except Exception:
        pass
        
    return 'en'

def translate_query_to_english(query: str, debug_data: Dict[str, Any] = None) -> tuple[str, str]:
    """
    Detects query language. If Kannada, translates to English.
    Returns: (translated_query, original_language)
    """
    lang = detect_language(query)
    if lang == 'kn':
        translated = translate_kannada_to_english(query, debug_data=debug_data)
        return translated, 'kn'
    return query, 'en'

def translate_response_to_lang(response_text: str, target_lang: str, debug_data: Dict[str, Any] = None) -> str:
    """
    Translates response text back to Kannada if target_lang is 'kn'.
    """
    if target_lang == 'kn':
        return translate_english_to_kannada(response_text, debug_data=debug_data)
    return response_text

