"""
Language Detection Utility for Mixed Hindi-English Support
=========================================================

This module provides language detection capabilities for mixed Hindi-English conversations.
"""

import re
from typing import Optional, Tuple
from src.config import HINDI_BIAS_THRESHOLD, DEFAULT_LANGUAGE

def detect_language_with_phone_bias(text: str, phone_number: str = None) -> str:
    """
    Detect language with phone number country code bias and Hindi preference.
    
    Args:
        text: Input text to analyze
        phone_number: User's phone number for country detection
        
    Returns:
        Language code: 'hi', 'en', or 'mixed'
    """
    # Check phone number country code first
    if phone_number and phone_number.startswith('+91'):
        # For Indian numbers, default to Hindi unless clearly English
        basic_detection = detect_language(text)
        if basic_detection == 'en':
            # Double-check for Hindi indicators (both Devanagari and Latin script)
            hindi_indicators = ['मैं', 'आप', 'है', 'हैं', 'कर', 'करना', 'चाहिए', 'हो', 'होगा']
            hinglish_words = ['namaste', 'kaise', 'haan', 'nahi', 'aap', 'kya', 'theek', 'bilkul']
            
            if any(word in text for word in hindi_indicators) or any(word in text.lower() for word in hinglish_words):
                return 'hi'
        return basic_detection
    
    # For non-Indian numbers, use standard detection with Hindi bias
    # Get Hindi bias threshold from dashboard settings
    try:
        from .dashboard_integration import sales_dashboard
        settings = sales_dashboard.get_voice_settings()
        hindi_bias_threshold = settings.get('hindi_bias_threshold', HINDI_BIAS_THRESHOLD)
    except Exception:
        hindi_bias_threshold = HINDI_BIAS_THRESHOLD
    
    return detect_language_with_bias(text, hindi_bias_threshold)

def detect_language_with_bias(text: str, hindi_bias_threshold: float = HINDI_BIAS_THRESHOLD) -> str:
    """
    Detect language with Hindi bias threshold.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Language code: 'hi', 'en', or 'mixed'
    """
    basic_detection = detect_language(text)
    
    # Apply Hindi bias threshold
    if hindi_bias_threshold > 0.5:
        # More aggressive Hindi detection
        if basic_detection == 'mixed':
            return 'hi'  # Bias mixed toward Hindi
        elif basic_detection == 'en':
            # Check for Hindi indicators even in English text
            hindi_indicators = ['मैं', 'आप', 'है', 'हैं', 'कर', 'करना', 'चाहिए', 'हो', 'होगा']
            hinglish_words = ['namaste', 'kaise', 'haan', 'nahi', 'aap', 'kya', 'theek', 'bilkul']
            
            if any(word in text for word in hindi_indicators) or any(word in text.lower() for word in hinglish_words):
                return 'hi'
    
    return basic_detection

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
        # Pure Hindi transliterations
        'namaste', 'kaise', 'ho', 'hai', 'haan', 'nahi', 'kripya', 'dhanyavad',
        'madad', 'samay', 'tarikh', 'pata', 'bhai', 'didi', 'ji',
        'aap', 'hum', 'mera', 'meri', 'kya', 'kyu', 'kyon', 'kab', 'kahan', 'kidhar',
        'chahiye', 'chahiyeh', 'karna', 'hoga', 'krna', 'krunga', 'krungi',
        'mere', 'mujhe', 'tumhe', 'aapko', 'hamein', 'unhein',
        'dekh', 'dekho', 'bolo', 'batao', 'suno', 'samjho',
        'theek', 'bilkul', 'zaroor', 'shayad', 'kabhi',
        'mein', 'me', 'ko', 'se', 'par', 'ke', 'ki', 'ka',
        'accha', 'acha', 'badhiya', 'sahi', 'thik',
        'naam', 'umar', 'sheher', 'paisa',
        # Hindi-English mixed patterns
        'hotel book', 'room book', 'train book', 'flight book',
        'booking karo', 'booking karna', 'book karo', 'book karna'
    ]
    for kw in hinglish_keywords:
        if kw in lower_text:
            hinglish_hits += 1
    # Determine language based on thresholds and hints (Master Branch Logic)
    if hindi_percentage >= 60:
        return 'hi'
    elif english_percentage >= 80 and hinglish_hits == 0:
        return 'en'
    elif hinglish_hits >= 2 and english_percentage >= 30 and hindi_percentage < 15:
        return 'mixed'
    elif english_percentage >= 70 and hindi_percentage < 5 and hinglish_hits <= 1:
        return 'en'
    elif hindi_percentage >= 30:
        return 'hi'
    else:
        return 'mixed'

def get_language_prompt(language: str) -> str:
    """
    Get appropriate system prompt based on detected language for Sara.
    
    Args:
        language: Language code ('hi', 'en', 'mixed')
        
    Returns:
        System prompt text
    """
    prompts = {
        'hi': """You are Sara, a friendly female AI assistant.

CRITICAL: Respond in Romanized Hinglish (Hindi words in English script).
Examples:
- "Namaste! Main Sara hun, aapki madad kar sakti hun"
- "Aapko kis sheher mein hotel chahiye?"
- "Theek hai, main check karti hun"
- "Bilkul! Main aapki help kar sakti hun"
- "Aapka naam kya hai?"
- "Kitne din ke liye stay karna hai?"

Be warm, helpful, and conversational. Ask one question at a time.""",
        
        'en': """You are Sara, a friendly and helpful female AI assistant. You can help with:
- Restaurant bookings and recommendations
- Hotel reservations and travel planning
- General questions and conversations
- Booking assistance and guidance

Be warm, friendly, and conversational. Speak naturally as a helpful female assistant. If someone uses inappropriate language or makes inappropriate requests, politely decline and offer to help with appropriate topics instead. Always maintain a professional and respectful tone.""",
        
        'mixed': """You are Sara, a friendly female AI assistant.

CRITICAL: Respond in Romanized Hinglish (Hindi words in English script).
Examples:
- "Bilkul! Main aapki madad kar sakti hun"
- "Aapko kis sheher mein hotel chahiye?"
- "Theek hai, main check karti hun"
- "Perfect! Main aapki help kar sakti hun"
- "Aapka naam kya hai?"
- "Kitne din ke liye stay karna hai?"
- "Great! Main aapko best options deti hun"

Be warm, helpful, and conversational. Ask one question at a time."""
    }
    
    return prompts.get(language, prompts['en'])

def detect_inappropriate_content(text: str) -> bool:
    """
    Detect if text contains inappropriate or offensive content.
    
    Args:
        text: Input text to analyze
        
    Returns:
        True if inappropriate content detected, False otherwise
    """
    if not text or not text.strip():
        return False
    
    # Convert to lowercase for case-insensitive matching
    lower_text = text.lower().strip()
    
    # List of inappropriate words/phrases (both English and Hindi)
    inappropriate_words = [
        # English inappropriate words
        'fuck', 'shit', 'damn', 'bitch', 'asshole', 'bastard', 'piss', 'crap',
        'hell', 'bloody', 'stupid', 'idiot', 'moron', 'retard', 'gay', 'fag',
        'whore', 'slut', 'prostitute', 'sex', 'porn', 'nude', 'naked',
        'kill', 'murder', 'suicide', 'die', 'death', 'hate', 'violence',
        'drug', 'cocaine', 'heroin', 'marijuana', 'weed', 'alcohol',
        'rape', 'molest', 'abuse', 'harass', 'threat', 'blackmail',
        
        # Hindi inappropriate words (transliterated)
        'chutiya', 'bhosdike', 'madarchod', 'behenchod', 'lund', 'chut',
        'gaand', 'bhenchod', 'maa ki', 'teri maa', 'saala', 'saali',
        'randi', 'raand', 'kutiya', 'kutta', 'kamina', 'harami',
        'chakka', 'hijra', 'napunsak', 'murda', 'kutta', 'kutte',
        'machod', 'bhenchod', 'behenchod', 'madarchod', 'bhosdike',
        'chutiya', 'chut', 'lund', 'gaand', 'saala', 'saali'
    ]
    
    # Check for inappropriate words (exact word matches only)
    words_in_text = lower_text.split()
    inappropriate_found = False
    
    for word in inappropriate_words:
        if word in words_in_text:  # Only exact word matches
            inappropriate_found = True
            break
    
    return inappropriate_found

def get_appropriate_response(language: str) -> str:
    """
    Get appropriate response for inappropriate content based on language.
    
    Args:
        language: Language code ('hi', 'en', 'mixed')
        
    Returns:
        Appropriate response text
    """
    responses = {
        'hi': "Main aapki madad karne ke liye yahan hun, lekin kripya uchit bhasha ka prayog karein. Main aapke saath sammanjanak tareeke se baat karna chahti hun. Kya main aapki kisi aur tareeke se madad kar sakti hun?",
        
        'en': "I'm here to help you, but please use appropriate language. I'd like to have a respectful conversation with you. Is there something else I can help you with?",
        
        'mixed': "I'm here to help you, but please use appropriate language. I'd like to have a respectful conversation with you. Is there something else I can help you with?"
    }
    
    return responses.get(language, responses['en'])

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
        'hi': "Namaste! Main Sara hun, aapki madad kar sakti hun. Aaj main aapki kaise help kar sakti hun?",
        'en': "Hello! I'm Sara, your AI assistant. How can I help you today?",
        'mixed': "Hello! Namaste! Main Sara hun, aapki madad kar sakti hun. How can I help you today?"
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
        'hi': "Mujhe samajh nahi aaya. Kripya dobara kahiye.",
        'en': "I didn't catch that. Please try again.",
        'mixed': "I didn't catch that. Mujhe samajh nahi aaya. Please try again."
    }
    
    return messages.get(language, messages['en'])
