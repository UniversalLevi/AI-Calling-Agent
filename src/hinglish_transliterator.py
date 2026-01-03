"""
Enhanced Hinglish Transliterator for Sara AI Voice Bot
Advanced Devanagari to Latin transliteration with custom overrides for natural TTS pronunciation.

Features:
- Detects Devanagari vs Latin (handles mixed Hinglish)
- Custom Devanagari overrides (phrase-level replacements)
- Robust transliteration using indic-transliteration
- Post-transliteration overrides for natural pronunciation
- Preserves English words, numbers, punctuation
- Performance optimized with caching
- Comprehensive replacements dictionary for Indian context
"""

from functools import lru_cache
import json
import regex as re
from pathlib import Path
from indic_transliteration.sanscript import transliterate, DEVANAGARI, ITRANS

# -------------------------
# Enhanced replacements dictionary for Indian context
# -------------------------
ENHANCED_REPLACEMENTS = {
    # Basic pronouns and common words
    'नमस्ते': 'Namaste',
    'हैं': 'hain',
    'है': 'hai',
    'मैं': 'main',
    'आप': 'aap',
    'कैसे': 'kaise',
    'क्या': 'kya',
    'कहाँ': 'kahan',
    'कब': 'kab',
    'क्यों': 'kyun',
    'कितना': 'kitna',
    'कौन': 'kaun',
    'कौन सा': 'kaun sa',
    'कौन सी': 'kaun si',
    'कौन से': 'kaun se',
    'मुझे': 'mujhe',
    'तुम्हें': 'tumhe',
    'आपको': 'aapko',
    'हमें': 'hamein',
    'उन्हें': 'unhein',
    'इस': 'is',
    'उस': 'us',
    'यह': 'yah',
    'वह': 'vah',
    'ये': 'ye',
    'वे': 've',
    
    # Possessive pronouns
    'मेरा': 'mera',
    'मेरी': 'meri',
    'मेरे': 'mere',
    'आपका': 'aapka',
    'आपकी': 'aapki',
    'आपके': 'aapke',
    'हमारा': 'hamara',
    'हमारी': 'hamari',
    'हमारे': 'hamare',
    'उनका': 'unka',
    'उनकी': 'unki',
    'उनके': 'unke',
    
    # Common verbs
    'होना': 'hona',
    'करना': 'karna',
    'जाना': 'jana',
    'आना': 'aana',
    'देना': 'dena',
    'लेना': 'lena',
    'बोलना': 'bolna',
    'सुनना': 'sunna',
    'देखना': 'dekhna',
    'समझना': 'samajhna',
    'पसंद': 'pasand',
    'चाहिए': 'chahiye',
    'चाहता': 'chahta',
    'चाहती': 'chahti',
    
    # Time and place
    'आज': 'aaj',
    'कल': 'kal',
    'परसों': 'parson',
    'सुबह': 'subah',
    'दोपहर': 'dopahar',
    'शाम': 'shaam',
    'रात': 'raat',
    'यहाँ': 'yahan',
    'वहाँ': 'vahan',
    'घर': 'ghar',
    'ऑफिस': 'office',
    'स्कूल': 'school',
    'हॉस्पिटल': 'hospital',
    
    # Numbers (spoken form)
    'एक': 'ek',
    'दो': 'do',
    'तीन': 'teen',
    'चार': 'char',
    'पांच': 'paanch',
    'छह': 'chhah',
    'सात': 'saat',
    'आठ': 'aath',
    'नौ': 'nau',
    'दस': 'das',
    
    # Common adjectives
    'अच्छा': 'accha',
    'बुरा': 'bura',
    'बड़ा': 'bada',
    'छोटा': 'chhota',
    'नया': 'naya',
    'पुराना': 'purana',
    'साफ': 'saaf',
    'गंदा': 'ganda',
    'तेज़': 'tez',
    'धीमा': 'dheema',
    
    # Hotel and travel related
    'होटल': 'hotel',
    'बुकिंग': 'booking',
    'रूम': 'room',
    'कमरा': 'kamra',
    'चेक-इन': 'check-in',
    'चेक-आउट': 'check-out',
    'रिजर्वेशन': 'reservation',
    'टिकट': 'ticket',
    'यात्रा': 'yatra',
    'सफर': 'safar',
    
    # Technology and modern terms
    'वाई-फाई': 'WiFi',
    'इंटरनेट': 'internet',
    'मोबाइल': 'mobile',
    'फोन': 'phone',
    'कंप्यूटर': 'computer',
    'लैपटॉप': 'laptop',
    'एप': 'app',
    'वेबसाइट': 'website',
    'ईमेल': 'email',
    'पासवर्ड': 'password',
    
    # Food and dining
    'खाना': 'khana',
    'पानी': 'paani',
    'चाय': 'chai',
    'कॉफी': 'coffee',
    'दूध': 'doodh',
    'रोटी': 'roti',
    'चावल': 'chawal',
    'दाल': 'daal',
    'सब्जी': 'sabzi',
    'मिठाई': 'mithai',
    
    # Family and relationships
    'पापा': 'papa',
    'मम्मी': 'mummy',
    'भाई': 'bhai',
    'बहन': 'behen',
    'दोस्त': 'dost',
    'पति': 'pati',
    'पत्नी': 'patni',
    'बेटा': 'beta',
    'बेटी': 'beti',
    
    # Common phrases
    'धन्यवाद': 'dhanyawad',
    'शुक्रिया': 'shukriya',
    'माफ करें': 'maaf karein',
    'कृपया': 'kripya',
    'जी हाँ': ' haan',
    'जी नहीं': ' nahi',
    'ठीक है': 'theek hai',
    'कोई बात नहीं': 'koi baat nahi',
    'बहुत अच्छा': 'bahut accha',
    'मदद': 'madad',
    
    # Cities and places (common ones)
    'दिल्ली': 'Delhi',
    'मुंबई': 'Mumbai',
    'बैंगलोर': 'Bangalore',
    'चेन्नई': 'Chennai',
    'कोलकाता': 'Kolkata',
    'हैदराबाद': 'Hyderabad',
    'पुणे': 'Pune',
    'जयपुर': 'Jaipur',
    'अहमदाबाद': 'Ahmedabad',
    'सूरत': 'Surat',
    
    # Business and professional terms
    'मीटिंग': 'meeting',
    'प्रोजेक्ट': 'project',
    'काम': 'kaam',
    'कार्यालय': 'karyalay',
    'कंपनी': 'company',
    'बिजनेस': 'business',
    'क्लाइंट': 'client',
    'कस्टमर': 'customer',
    'सर्विस': 'service',
    'प्रोडक्ट': 'product',
    
    # Emergency and health
    'डॉक्टर': 'doctor',
    'हॉस्पिटल': 'hospital',
    'दवा': 'dawa',
    'बीमार': 'bimar',
    'स्वस्थ': 'swasth',
    'एमरजेंसी': 'emergency',
    'पुलिस': 'police',
    'फायर': 'fire',
    'एम्बुलेंस': 'ambulance',
    
    # Common English words that are often mixed
    'ओके': 'OK',
    'हैलो': 'hello',
    'हाय': 'hi',
    'बाय': 'bye',
    'यस': 'yes',
    'नो': 'no',
    'प्लीज़': 'please',
    'थैंक यू': 'thank you',
    'सॉरी': 'sorry',
    'एक्सक्यूज़ मी': 'excuse me'
}

# -------------------------
# Utilities: script detection & splitting
# -------------------------
def is_devanagari_char(ch: str) -> bool:
    """Check if character is Devanagari script."""
    return '\u0900' <= ch <= '\u097F'

def is_latin_char(ch: str) -> bool:
    """Check if character is Latin script."""
    return ('\u0041' <= ch <= '\u007A') or ('\u00C0' <= ch <= '\u024F')

def char_script(ch: str) -> str:
    """Determine the script type of a character."""
    if ch.isspace():
        return 'space'
    if is_devanagari_char(ch):
        return 'devanagari'
    if is_latin_char(ch) or ch.isascii():
        if ch.isalpha():
            return 'latin'
        if ch.isdigit():
            return 'digit'
        return 'other'
    return 'other'

def split_into_script_runs(text: str):
    """Split text into runs of same script-type."""
    if not text:
        return []
    runs = []
    current = text[0]
    current_script = char_script(text[0])
    for ch in text[1:]:
        s = char_script(ch)
        if s == current_script:
            current += ch
        else:
            runs.append((current_script, current))
            current = ch
            current_script = s
    runs.append((current_script, current))
    return runs

# -------------------------
# Replacement helpers
# -------------------------
def sort_keys_by_length_desc(keys):
    """Sort keys by length in descending order to avoid partial matches."""
    return sorted(keys, key=lambda k: len(k), reverse=True)

def compile_devanagari_prepattern(dev_keys):
    """Compile regex pattern for Devanagari key matching."""
    if not dev_keys:
        return None
    esc_keys = [re.escape(k) for k in sort_keys_by_length_desc(dev_keys)]
    pattern = r'(' + '|'.join(esc_keys) + r')'
    pattern = r'(?<![\p{Devanagari}])' + pattern + r'(?![\p{Devanagari}])'
    return re.compile(pattern)

def apply_pre_devanagari_overrides(text: str, replacements: dict) -> str:
    """Apply Devanagari phrase-level replacements."""
    if not replacements:
        return text
    pattern = compile_devanagari_prepattern(replacements.keys())
    if not pattern:
        return text

    def _repl(m):
        key = m.group(1)
        return replacements.get(key, key)

    return pattern.sub(_repl, text)

# -------------------------
# Transliteration (cached)
# -------------------------
@lru_cache(maxsize=8192)
def translit_devanagari_to_latin(dev_text: str) -> str:
    """Transliterate Devanagari to Latin with caching."""
    try:
        return transliterate(dev_text, DEVANAGARI, ITRANS)
    except Exception:
        return dev_text

# -------------------------
# Post-transliteration overrides
# -------------------------
def build_post_overrides_map(dev_replacements: dict) -> dict:
    """Build mapping from transliterated forms to desired pronunciations."""
    out = {}
    if not dev_replacements:
        return out
    for dev_key, desired in dev_replacements.items():
        translit_key = translit_devanagari_to_latin(dev_key)
        out[translit_key.lower()] = desired
    return out

def compile_post_pattern(post_map: dict):
    """Compile regex pattern for post-transliteration overrides."""
    if not post_map:
        return None
    esc_keys = [re.escape(k) for k in sort_keys_by_length_desc(post_map.keys())]
    pattern = r'\b(' + '|'.join(esc_keys) + r')\b'
    return re.compile(pattern, flags=re.IGNORECASE)

def apply_post_overrides(text: str, post_map: dict):
    """Apply post-transliteration overrides."""
    if not post_map:
        return text
    pattern = compile_post_pattern(post_map)
    if not pattern:
        return text
    def _repl(m):
        key = m.group(1).lower()
        return post_map.get(key, m.group(1))
    return pattern.sub(_repl, text)

# -------------------------
# Main pipeline function
# -------------------------
def transliterate_hinglish(text: str, replacements: dict = None, preserve_case: bool = True) -> str:
    """
    Complete Hinglish transliteration pipeline:
    1) Apply Devanagari pre-overrides (phrase-level)
    2) Split into script-runs and transliterate Devanagari runs
    3) Apply post-overrides (on transliterated Latin text)
    4) Normalize whitespace and case
    """
    if replacements is None:
        replacements = ENHANCED_REPLACEMENTS

    # 1) Pre-overrides on original text
    text_after_pre = apply_pre_devanagari_overrides(text, replacements)

    # 2) Split into script runs and transliterate only Devanagari runs
    runs = split_into_script_runs(text_after_pre)
    out_chunks = []
    for script, run in runs:
        if script == 'devanagari':
            out_chunks.append(translit_devanagari_to_latin(run))
        else:
            out_chunks.append(run)

    translit_text = ''.join(out_chunks)

    # 3) Post overrides
    post_map = build_post_overrides_map(replacements)
    translit_text = apply_post_overrides(translit_text, post_map)

    # 4) Normalization
    translit_text = re.sub(r'\s+', ' ', translit_text).strip()
    if not preserve_case:
        translit_text = translit_text.lower()

    # Optional: Capitalize sentence starts
    if preserve_case:
        translit_text = _sentence_capitalize(translit_text)

    return translit_text

def _sentence_capitalize(text: str) -> str:
    """Capitalize first letter of sentences."""
    def cap_match(m):
        return m.group(1) + m.group(2).upper()
    text = re.sub(r'^(\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text, flags=re.IGNORECASE)
    text = re.sub(r'([.!?]\s+)([a-z])', cap_match, text, flags=re.IGNORECASE)
    return text

# -------------------------
# Load custom replacements from file
# -------------------------
def load_replacements_from_file(file_path: str) -> dict:
    """Load custom replacements from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load replacements from {file_path}: {e}")
        return ENHANCED_REPLACEMENTS

def save_replacements_to_file(replacements: dict, file_path: str):
    """Save replacements to JSON file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(replacements, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving replacements to {file_path}: {e}")

# -------------------------
# Integration with Sara's TTS system
# -------------------------
def optimize_text_for_sara_tts(text: str, language: str = 'mixed') -> str:
    """
    Optimize text specifically for Sara's TTS system.
    This function integrates with the existing TTS optimization.
    """
    if language in ['hi', 'mixed']:
        # Apply Hinglish transliteration for Hindi/mixed content
        optimized_text = transliterate_hinglish(text, ENHANCED_REPLACEMENTS)
        
        # Additional Sara-specific optimizations
        optimized_text = _apply_sara_specific_optimizations(optimized_text)
        
        return optimized_text
    else:
        # For English, apply basic optimizations
        return _apply_english_optimizations(text)

def _apply_sara_specific_optimizations(text: str) -> str:
    """Apply Sara-specific text optimizations for natural speech."""
    # Handle common contractions and natural speech patterns
    optimizations = {
        r'\bI am\b': "I'm",
        r'\byou are\b': "you're",
        r'\bwe are\b': "we're",
        r'\bthey are\b': "they're",
        r'\bit is\b': "it's",
        r'\bthat is\b': "that's",
        r'\bthere is\b': "there's",
        r'\bhere is\b': "here's",
        r'\bdo not\b': "don't",
        r'\bdoes not\b': "doesn't",
        r'\bwill not\b': "won't",
        r'\bcan not\b': "can't",
        r'\bcould not\b': "couldn't",
        r'\bshould not\b': "shouldn't",
        r'\bwould not\b': "wouldn't",
        r'\bhave not\b': "haven't",
        r'\bhas not\b': "hasn't",
        r'\bhad not\b': "hadn't",
    }
    
    for pattern, replacement in optimizations.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def _apply_english_optimizations(text: str) -> str:
    """Apply basic English text optimizations."""
    # Remove extra spaces and normalize punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([.!?,:;])', r'\1', text)
    return text.strip()

# -------------------------
# Testing and examples
# -------------------------
def run_sara_tests():
    """Run comprehensive tests for Sara's transliteration system."""
    test_cases = [
        # Basic Hindi
        ("नमस्ते आप कैसे हैं", "Namaste aap kaise hain"),
        ("मैं ठीक हूँ", "Main theek hoon"),
        
        # Mixed Hinglish
        ("आज meeting है", "Aaj meeting hai"),
        ("kal tum office aaoge?", "Kal tum office aaoge?"),
        ("आज का meeting important है", "Aaj ka meeting important hai"),
        
        # Hotel booking context
        ("होटल book करना है", "Hotel book karna hai"),
        ("तीन लोगों के लिए room चाहिए", "Teen logon ke liye room chahiye"),
        ("WiFi और AC चाहिए", "WiFi aur AC chahiye"),
        
        # Business context
        ("project complete करना है", "Project complete karna hai"),
        ("client से meeting है", "Client se meeting hai"),
        ("deadline tomorrow है", "Deadline tomorrow hai"),
        
        # Common phrases
        ("कोई बात नहीं", "Koi baat nahi"),
        ("बहुत अच्छा", "Bahut accha"),
        ("धन्यवाद", "Dhanyawad"),
        
        # Numbers and dates
        ("पांच दिन के लिए", "Paanch din ke liye"),
        ("दो हज़ार रुपए", "Do hazaar rupaye"),
        
        # Cities
        ("दिल्ली से मुंबई", "Delhi se Mumbai"),
        ("जयपुर में hotel", "Jaipur mein hotel"),
    ]
    
    print("🧪 Running Sara's Hinglish Transliteration Tests\n")
    
    for i, (input_text, expected_hint) in enumerate(test_cases, 1):
        result = transliterate_hinglish(input_text)
        print(f"Test {i}:")
        print(f"  Input:    {input_text}")
        print(f"  Output:   {result}")
        print(f"  Expected: {expected_hint}")
        print()

if __name__ == '__main__':
    # Run tests when executed directly
    run_sara_tests()
