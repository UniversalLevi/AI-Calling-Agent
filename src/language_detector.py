"""
Language Detection Utility for Mixed Hindi-English Support
=========================================================

This module provides language detection capabilities for mixed Hindi-English conversations.
"""

import re
from typing import Optional, Tuple

def detect_language(text: str) -> str:
    """
    Detect if text is primarily Hindi, English, or mixed.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Language code: 'hi', 'en', or 'mixed'
    """
    if not text or not text.strip():
        return 'en'  # Default to English
    
    # Clean the text
    text = text.strip()
    
    # Count Devanagari characters (Hindi script)
    devanagari_pattern = r'[\u0900-\u097F]'
    hindi_chars = len(re.findall(devanagari_pattern, text))
    
    # Count Latin characters (English script)
    latin_pattern = r'[a-zA-Z]'
    english_chars = len(re.findall(latin_pattern, text))
    
    # Count total meaningful characters
    total_chars = hindi_chars + english_chars
    
    if total_chars == 0:
        return 'en'  # Default to English if no recognizable characters
    
    # Calculate percentages
    hindi_percentage = (hindi_chars / total_chars) * 100
    english_percentage = (english_chars / total_chars) * 100
    
    # Quick Hinglish heuristic: Latin script but contains common Hindi words transliterated
    lower_text = text.lower()
    hinglish_hits = 0
    hinglish_keywords = [
        'namaste', 'kaise', 'ho', 'hai', 'haan', 'nahi', 'kripya', 'kripya', 'dhanyavad',
        'madad', 'samay', 'tarikh', 'booking', 'pata', 'number', 'bhai', 'didi', 'ji',
        'aap', 'hum', 'mera', 'meri', 'kya', 'kyu', 'kyon', 'kab', 'kahan', 'kidhar',
        'chahiye', 'chahiyeh', 'karna', 'hoga', 'krna', 'krunga', 'krungi'
    ]
    for kw in hinglish_keywords:
        if kw in lower_text:
            hinglish_hits += 1
    # Determine language based on thresholds and hints
    if hindi_percentage >= 60:
        return 'hi'
    elif english_percentage >= 70 and hinglish_hits == 0:
        return 'en'
    elif hinglish_hits >= 2 and english_percentage >= 40 and hindi_percentage < 10:
        return 'mixed'
    elif english_percentage >= 50 and hindi_percentage < 10 and hinglish_hits <= 1:
        return 'en'
    else:
        return 'mixed'

def get_language_prompt(language: str) -> str:
    """
    Get appropriate system prompt based on detected language.
    
    Args:
        language: Language code ('hi', 'en', 'mixed')
        
    Returns:
        System prompt text
    """
    prompts = {
        'hi': """आप एक सहायक AI असिस्टेंट हैं जो रेस्टोरेंट बुकिंग, होटल रिजर्वेशन और सामान्य प्रश्नों में मदद कर सकते हैं। दोस्ताना और सहायक बनें। हिंदी में जवाब दें।""",
        
        'en': """You are a helpful AI assistant that can help with:
- Restaurant bookings and recommendations
- Hotel reservations and travel planning
- General questions and conversations
- Booking assistance and guidance

Be friendly, helpful, and conversational. If you can't make direct bookings, guide users on how to do it themselves.""",
        
        'mixed': """You are a helpful AI assistant that can help with:
- Restaurant bookings and recommendations
- Hotel reservations and travel planning
- General questions and conversations
- Booking assistance and guidance

Be friendly, helpful, and conversational. Respond in the same language as the user (Hindi or English). If you can't make direct bookings, guide users on how to do it themselves."""
    }
    
    return prompts.get(language, prompts['en'])

def get_tts_voice(language: str) -> str:
    """
    Get appropriate TTS voice based on detected language.
    
    Args:
        language: Language code ('hi', 'en', 'mixed')
        
    Returns:
        TTS voice code
    """
    voices = {
        'hi': 'hi',      # Hindi
        'en': 'en',      # English
        'mixed': 'en'    # Default to English for mixed
    }
    
    return voices.get(language, 'en')

def is_hindi_text(text: str) -> bool:
    """
    Check if text contains Hindi characters.
    
    Args:
        text: Input text
        
    Returns:
        True if text contains Hindi characters
    """
    devanagari_pattern = r'[\u0900-\u097F]'
    return bool(re.search(devanagari_pattern, text))

def is_english_text(text: str) -> bool:
    """
    Check if text contains English characters.
    
    Args:
        text: Input text
        
    Returns:
        True if text contains English characters
    """
    latin_pattern = r'[a-zA-Z]'
    return bool(re.search(latin_pattern, text))

def get_greeting(language: str) -> str:
    """
    Get appropriate greeting based on detected language.
    
    Args:
        language: Language code ('hi', 'en', 'mixed')
        
    Returns:
        Greeting text
    """
    greetings = {
        'hi': "नमस्ते! मैं आपका AI असिस्टेंट हूं। आज मैं आपकी कैसे मदद कर सकता हूं?",
        'en': "Hello! I'm your AI assistant. How can I help you today?",
        'mixed': "Hello! नमस्ते! I'm your AI assistant. How can I help you today?"
    }
    
    return greetings.get(language, greetings['en'])

def get_fallback_message(language: str) -> str:
    """
    Get appropriate fallback message based on detected language.
    
    Args:
        language: Language code ('hi', 'en', 'mixed')
        
    Returns:
        Fallback message text
    """
    messages = {
        'hi': "मुझे समझ नहीं आया। कृपया दोबारा कहें।",
        'en': "I didn't catch that. Please try again.",
        'mixed': "I didn't catch that. मुझे समझ नहीं आया। Please try again."
    }
    
    return messages.get(language, messages['en'])
