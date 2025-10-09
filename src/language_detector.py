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
        'namaste', 'kaise', 'ho', 'hai', 'haan', 'nahi', 'kripya', 'dhanyavad',
        'madad', 'samay', 'tarikh', 'booking', 'pata', 'number', 'bhai', 'didi', 'ji',
        'aap', 'hum', 'mera', 'meri', 'kya', 'kyu', 'kyon', 'kab', 'kahan', 'kidhar',
        'chahiye', 'chahiyeh', 'karna', 'hoga', 'krna', 'krunga', 'krungi',
        # Additional common Hindi transliterated words
        'mere', 'ko', 'mein', 'ke', 'ki', 'se', 'par', 'tak', 'bhi', 'toh',
        'book', 'kar', 'karne', 'karo', 'karen', 'karte', 'karta', 'karti',
        'restaurant', 'hotel', 'room', 'price', 'budget', 'date', 'time',
        'batao', 'batayen', 'samajh', 'samajhna', 'dekh', 'dekhna', 'sun', 'sunna',
        'accha', 'theek', 'sahi', 'bilkul', 'zaroor', 'pakka', 'yakin',
        'kal', 'aaj', 'parso', 'raat', 'din', 'subah', 'shaam',
        # Enhanced Hinglish patterns
        'book karo', 'book karna', 'book kar', 'booking karo', 'booking karna',
        'hotel book', 'restaurant book', 'travel book', 'trip book',
        'ghumne', 'ghumna', 'jane', 'jana', 'dekhne', 'dekhna',
        'suggest karo', 'suggest karna', 'help karo', 'help karna',
        'plan karo', 'plan karna', 'arrange karo', 'arrange karna',
        'han', 'hain', 'hai', 'ho', 'hoga', 'hogi', 'honge'
    ]
    for kw in hinglish_keywords:
        if kw in lower_text:
            hinglish_hits += 1
    # Determine language based on thresholds and hints
    if hindi_percentage >= 60:
        return 'hi'
    elif english_percentage >= 70 and hinglish_hits == 0:
        return 'en'
    elif hinglish_hits >= 1 and english_percentage >= 30 and hindi_percentage < 20:
        return 'mixed'  # More sensitive to Hinglish detection
    elif english_percentage >= 50 and hindi_percentage < 10 and hinglish_hits == 0:
        return 'en'
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
        'hi': """आप सारा हैं, एक दोस्ताना और मददगार महिला AI असिस्टेंट। आप रेस्टोरेंट बुकिंग, होटल रिजर्वेशन और सामान्य प्रश्नों में मदद कर सकती हैं। गर्मजोशी से और प्राकृतिक तरीके से बात करें। हिंदी में जवाब दें और अपने आप को 'मैं' कहें। अगर कोई अश्लील या अनुचित बात करे तो विनम्रता से मना करें और सहायता की पेशकश करें।""",
        
        'en': """You are Sara, a friendly and helpful female AI assistant. You can help with:
- Restaurant bookings and recommendations
- Hotel reservations and travel planning
- General questions and conversations
- Booking assistance and guidance

Be warm, friendly, and conversational. Speak naturally as a helpful female assistant. If someone uses inappropriate language or makes inappropriate requests, politely decline and offer to help with appropriate topics instead. Always maintain a professional and respectful tone.""",
        
        'mixed': """You are Sara, a friendly and helpful female AI assistant. You can help with:
- Restaurant bookings and recommendations
- Hotel reservations and travel planning
- General questions and conversations
- Booking assistance and guidance

Be warm, friendly, and conversational. Respond in the same language as the user (Hindi or English). Speak naturally as a helpful female assistant. If someone uses inappropriate language or makes inappropriate requests, politely decline and offer to help with appropriate topics instead. Always maintain a professional and respectful tone."""
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
        'hi': "मैं आपकी मदद करने के लिए यहाँ हूँ, लेकिन कृपया उचित भाषा का प्रयोग करें। मैं आपके साथ सम्मानजनक तरीके से बात करना चाहती हूँ। क्या मैं आपकी किसी अन्य तरीके से मदद कर सकती हूँ?",
        
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
