import os
from typing import Optional

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import settings manager for dynamic configuration
try:
    from .settings_manager import settings_manager
    SETTINGS_MANAGER_AVAILABLE = True
except ImportError:
    SETTINGS_MANAGER_AVAILABLE = False
    settings_manager = None


# =============================================================================
# AUDIO CONFIGURATION
# =============================================================================
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "20000"))
CHANNELS = int(os.getenv("CHANNELS", "1"))
RECORD_SECONDS = float(os.getenv("RECORD_SECONDS", "4.0"))
DEVICE_INDEX_IN = os.getenv("DEVICE_INDEX_IN")
DEVICE_INDEX_OUT = os.getenv("DEVICE_INDEX_OUT")

# Convert device indices to integers if provided
if DEVICE_INDEX_IN:
    try:
        DEVICE_INDEX_IN = int(DEVICE_INDEX_IN)
    except ValueError:
        DEVICE_INDEX_IN = None

if DEVICE_INDEX_OUT:
    try:
        DEVICE_INDEX_OUT = int(DEVICE_INDEX_OUT)
    except ValueError:
        DEVICE_INDEX_OUT = None


# =============================================================================
# SPEECH-TO-TEXT (STT) CONFIGURATION
# =============================================================================
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
LANGUAGE = os.getenv("LANGUAGE", "en")
AUTO_DETECT_LANGUAGE = os.getenv("AUTO_DETECT_LANGUAGE", "true").lower() == "true"
SUPPORTED_LANGUAGES = ["en", "hi"]  # English and Hindi
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "hi")  # Default to Hindi


# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    """You are Sara, a friendly female AI assistant for phone calls.

LANGUAGE RULES (CRITICAL):
- If user speaks Hindi/Hinglish, respond in Romanized Hinglish (e.g., "Bilkul! Main aapki madad kar sakti hun")
- If user speaks English, respond in English
- NEVER respond in English when user speaks Hindi
- Use natural Hinglish mixing: "Aapko hotel book karna hai? Main help kar sakti hun"
- ALWAYS use Romanized Hindi (Latin script) for Hindi words, never Devanagari script
- Examples: "Namaste" not "नमस्ते", "Aapka naam kya hai?" not "आपका नाम क्या है?"

CONVERSATION STYLE:
- Short, clear sentences (10-15 words max)
- Warm and helpful tone
- Ask one question at a time
- Use natural fillers: "Haan", "Theek hai", "Bilkul", "Okay"

YOUR PURPOSE: Help with bookings, recommendations, and general assistance.

Stay focused on the call purpose. If asked unrelated questions, politely redirect.""",
)


# =============================================================================
# TEXT-TO-SPEECH (TTS) CONFIGURATION
# =============================================================================
USE_COQUI_TTS = os.getenv("USE_COQUI_TTS", "false").lower() == "true"
TTS_VOICE = os.getenv("TTS_VOICE", "en")
HINDI_TTS_VOICE = os.getenv("HINDI_TTS_VOICE", "hi")
ENGLISH_TTS_VOICE = os.getenv("ENGLISH_TTS_VOICE", "en")

# Human-like Features Configuration
ENABLE_NATURAL_PAUSES = os.getenv("ENABLE_NATURAL_PAUSES", "true").lower() == "true"
ENABLE_FILLER_WORDS = os.getenv("ENABLE_FILLER_WORDS", "true").lower() == "true"
FILLER_FREQUENCY = float(os.getenv("FILLER_FREQUENCY", "0.25"))  # 25% of responses
PAUSE_DURATION_MS = (200, 600)  # Random pause range

# Streaming Configuration
ENABLE_STREAMING_RESPONSES = os.getenv("ENABLE_STREAMING_RESPONSES", "true").lower() == "true"
STREAMING_CHUNK_SIZE = int(os.getenv("STREAMING_CHUNK_SIZE", "10"))  # Tokens per chunk

# TTS Cache Configuration
ENABLE_TTS_CACHE = os.getenv("ENABLE_TTS_CACHE", "true").lower() == "true"
TTS_CACHE_DIR = os.getenv("TTS_CACHE_DIR", "tts_cache")
PRE_GENERATE_COMMON_PHRASES = os.getenv("PRE_GENERATE_COMMON_PHRASES", "true").lower() == "true"

# OpenAI TTS Voices (mapping and fallback)
if SETTINGS_MANAGER_AVAILABLE and settings_manager:
    OPENAI_TTS_VOICE_ENGLISH = settings_manager.get_setting('tts_voice_english', 'nova')
    OPENAI_TTS_VOICE_HINDI = settings_manager.get_setting('tts_voice_hindi', 'shimmer')
    OPENAI_TTS_VOICE_FALLBACK = settings_manager.get_setting('tts_voice_fallback', 'alloy')
else:
    OPENAI_TTS_VOICE_ENGLISH = os.getenv("OPENAI_TTS_VOICE_ENGLISH", "nova")
    OPENAI_TTS_VOICE_HINDI = os.getenv("OPENAI_TTS_VOICE_HINDI", "shimmer")
    OPENAI_TTS_VOICE_FALLBACK = os.getenv("OPENAI_TTS_VOICE_FALLBACK", "alloy")


# =============================================================================
# SIP CONFIGURATION (PHASE 2)
# =============================================================================
SIP_SERVER_IP = os.getenv("SIP_SERVER_IP", "localhost")
SIP_USERNAME = os.getenv("SIP_USERNAME", "1001")
SIP_PASSWORD = os.getenv("SIP_PASSWORD", "botpass123")
SIP_TARGET_EXTENSION = os.getenv("SIP_TARGET_EXTENSION", "1002")


# =============================================================================
# USER EXPERIENCE SETTINGS
# =============================================================================
PRINT_TRANSCRIPTS = os.getenv("PRINT_TRANSCRIPTS", "true").lower() == "true"
PRINT_BOT_TEXT = os.getenv("PRINT_BOT_TEXT", "true").lower() == "true"


# =============================================================================
# ADVANCED SETTINGS
# =============================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
DEBUG_LOG_FILE = os.getenv("DEBUG_LOG_FILE", "debug.log")
MAX_HISTORY_LENGTH = int(os.getenv("MAX_HISTORY_LENGTH", "10"))
AUDIO_BUFFER_SIZE = int(os.getenv("AUDIO_BUFFER_SIZE", "1024"))
SIP_TIMEOUT = int(os.getenv("SIP_TIMEOUT", "30"))


# =============================================================================
# PRODUCTION SETTINGS
# =============================================================================
ENABLE_CALL_RECORDING = os.getenv("ENABLE_CALL_RECORDING", "false").lower() == "true"
CALL_RECORDING_DIR = os.getenv("CALL_RECORDING_DIR", "./recordings")
MAX_CALL_DURATION = int(os.getenv("MAX_CALL_DURATION", "30"))
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "false").lower() == "true"


# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SIP_USE_TLS = os.getenv("SIP_USE_TLS", "false").lower() == "true"
SIP_TLS_CERT_PATH = os.getenv("SIP_TLS_CERT_PATH", "")
SIP_TLS_KEY_PATH = os.getenv("SIP_TLS_KEY_PATH", "")


# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================
AUDIO_WORKER_THREADS = int(os.getenv("AUDIO_WORKER_THREADS", "2"))
ENABLE_AUDIO_COMPRESSION = os.getenv("ENABLE_AUDIO_COMPRESSION", "false").lower() == "true"
AUDIO_COMPRESSION_QUALITY = int(os.getenv("AUDIO_COMPRESSION_QUALITY", "5"))


# =============================================================================
# SALES AI CONFIGURATION
# =============================================================================
SALES_MODE_ENABLED = os.getenv("SALES_MODE_ENABLED", "true").lower() == "true"
ACTIVE_PRODUCT_ID = os.getenv("ACTIVE_PRODUCT_ID", "hotel_booking_service")
SALES_API_URL = os.getenv("SALES_API_URL", "http://localhost:5000")
QUALIFICATION_THRESHOLD = int(os.getenv("QUALIFICATION_THRESHOLD", "20"))
SENTIMENT_ANALYSIS_ENABLED = os.getenv("SENTIMENT_ANALYSIS_ENABLED", "true").lower() == "true"
TALK_LISTEN_TARGET_RATIO = float(os.getenv("TALK_LISTEN_TARGET_RATIO", "0.4"))
SALES_CACHE_DURATION = int(os.getenv("SALES_CACHE_DURATION", "300"))  # 5 minutes

# =============================================================================
# WHATSAPP BUSINESS API CONFIGURATION
# =============================================================================
# Feature Flags
ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "false").lower() == "true"
ENABLE_WHATSAPP_PAYMENT_LINKS = os.getenv("ENABLE_WHATSAPP_PAYMENT_LINKS", "false").lower() == "true"
ENABLE_WHATSAPP_FOLLOWUPS = os.getenv("ENABLE_WHATSAPP_FOLLOWUPS", "false").lower() == "true"

# WhatsApp Service Configuration
WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:8001")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")

# Razorpay Configuration
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_CALLBACK_URL = os.getenv("RAZORPAY_CALLBACK_URL", "")

# =============================================================================
# HUMANIZATION CONFIGURATION
# =============================================================================
if SETTINGS_MANAGER_AVAILABLE and settings_manager:
    HUMANIZED_MODE = settings_manager.get_setting('humanized_mode', False)
    HINDI_BIAS_THRESHOLD = settings_manager.get_setting('hindi_bias_threshold', 0.8)
    FILLER_FREQUENCY = settings_manager.get_setting('filler_frequency', 0.15)
    TTS_SPEED = settings_manager.get_setting('tts_speed', 1.0)
    EMOTION_DETECTION_MODE = settings_manager.get_setting('emotion_detection_mode', 'hybrid')
    ENABLE_SPOKEN_TONE_CONVERTER = settings_manager.get_setting('enable_spoken_tone_converter', True)
    ENABLE_MICRO_SENTENCES = settings_manager.get_setting('enable_micro_sentences', True)
    ENABLE_SEMANTIC_PACING = settings_manager.get_setting('enable_semantic_pacing', True)
else:
    HUMANIZED_MODE = os.getenv("HUMANIZED_MODE", "false").lower() == "true"
    HINDI_BIAS_THRESHOLD = float(os.getenv("HINDI_BIAS_THRESHOLD", "0.8"))  # 80% bias toward Hindi
    FILLER_FREQUENCY = float(os.getenv("FILLER_FREQUENCY", "0.15"))  # 15% of responses
    TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0"))  # Normal speech speed for better quality
    EMOTION_DETECTION_MODE = os.getenv("EMOTION_DETECTION_MODE", "hybrid")  # hybrid, keyword, gpt
    ENABLE_SPOKEN_TONE_CONVERTER = os.getenv("ENABLE_SPOKEN_TONE_CONVERTER", "true").lower() == "true"
    ENABLE_MICRO_SENTENCES = os.getenv("ENABLE_MICRO_SENTENCES", "true").lower() == "true"
    ENABLE_SEMANTIC_PACING = os.getenv("ENABLE_SEMANTIC_PACING", "true").lower() == "true"

# =============================================================================
# DEVELOPMENT SETTINGS
# =============================================================================
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
MOCK_SIP_SERVER = os.getenv("MOCK_SIP_SERVER", "false").lower() == "true"


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================
def validate_config() -> bool:
    """Validate the configuration and return True if valid, False otherwise."""
    errors = []
    
    # Check required settings
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-your-api-key-here":
        errors.append("OPENAI_API_KEY is required and must be set to a valid API key")
    
    # Validate numeric settings
    if SAMPLE_RATE not in [8000, 16000, 20000, 44100]:
        errors.append(f"SAMPLE_RATE must be one of [8000, 16000, 20000, 44100], got {SAMPLE_RATE}")
    
    if CHANNELS not in [1, 2]:
        errors.append(f"CHANNELS must be 1 or 2, got {CHANNELS}")
    
    if not (1.0 <= RECORD_SECONDS <= 10.0):
        errors.append(f"RECORD_SECONDS must be between 1.0 and 10.0, got {RECORD_SECONDS}")
    
    if WHISPER_MODEL_SIZE not in ["tiny", "small", "base", "medium", "large"]:
        errors.append(f"WHISPER_MODEL_SIZE must be one of [tiny, small, base, medium, large], got {WHISPER_MODEL_SIZE}")
    
    if AUDIO_COMPRESSION_QUALITY not in range(1, 10):
        errors.append(f"AUDIO_COMPRESSION_QUALITY must be between 1 and 9, got {AUDIO_COMPRESSION_QUALITY}")
    
    # Print errors if any
    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


def print_config_summary():
    """Print a summary of the current configuration."""
    print("=" * 60)
    print("AI CALLING BOT - CONFIGURATION SUMMARY")
    print("=" * 60)
    
    print(f"OpenAI Model: {OPENAI_MODEL}")
    print(f"Sample Rate: {SAMPLE_RATE} Hz")
    print(f"Channels: {CHANNELS}")
    print(f"Record Duration: {RECORD_SECONDS}s")
    print(f"Whisper Model: {WHISPER_MODEL_SIZE}")
    print(f"Language: {LANGUAGE}")
    print(f"TTS Engine: {'Coqui' if USE_COQUI_TTS else 'gTTS'}")
    print(f"SIP Server: {SIP_SERVER_IP}")
    print(f"SIP Username: {SIP_USERNAME}")
    print(f"Debug Mode: {DEBUG_MODE}")
    print(f"Test Mode: {TEST_MODE}")
    
    # Sales configuration
    if SALES_MODE_ENABLED:
        print("=" * 60)
        print("SALES AI CONFIGURATION")
        print("=" * 60)
        print(f"Sales Mode: ENABLED")
        print(f"Active Product ID: {ACTIVE_PRODUCT_ID}")
        print(f"Sales API URL: {SALES_API_URL}")
        print(f"Qualification Threshold: {QUALIFICATION_THRESHOLD}")
        print(f"Sentiment Analysis: {'ENABLED' if SENTIMENT_ANALYSIS_ENABLED else 'DISABLED'}")
        print(f"Talk-Listen Target Ratio: {TALK_LISTEN_TARGET_RATIO}")
    else:
        print("Sales Mode: DISABLED")
    
    print("=" * 60)


# =============================================================================
# FEATURE FLAG WRAPPER
# =============================================================================
def is_humanized_mode_enabled() -> bool:
    """Check if humanized mode is enabled via feature flag."""
    return HUMANIZED_MODE


def get_humanization_config() -> dict:
    """Get all humanization configuration settings."""
    return {
        'humanized_mode': HUMANIZED_MODE,
        'hindi_bias_threshold': HINDI_BIAS_THRESHOLD,
        'filler_frequency': FILLER_FREQUENCY,
        'tts_speed': TTS_SPEED,
        'emotion_detection_mode': EMOTION_DETECTION_MODE,
        'enable_spoken_tone_converter': ENABLE_SPOKEN_TONE_CONVERTER,
        'enable_micro_sentences': ENABLE_MICRO_SENTENCES,
        'enable_semantic_pacing': ENABLE_SEMANTIC_PACING,
        'default_language': DEFAULT_LANGUAGE
    }


# =============================================================================
# WHATSAPP FEATURE FLAG HELPERS
# =============================================================================
def is_whatsapp_enabled() -> bool:
    """Check if WhatsApp integration is enabled."""
    return ENABLE_WHATSAPP


def is_whatsapp_payment_links_enabled() -> bool:
    """Check if WhatsApp payment links feature is enabled."""
    return ENABLE_WHATSAPP and ENABLE_WHATSAPP_PAYMENT_LINKS


def is_whatsapp_followups_enabled() -> bool:
    """Check if WhatsApp followups feature is enabled."""
    return ENABLE_WHATSAPP and ENABLE_WHATSAPP_FOLLOWUPS


def is_whatsapp_configured() -> bool:
    """Check if WhatsApp credentials are properly configured."""
    return bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)


def is_razorpay_configured() -> bool:
    """Check if Razorpay credentials are properly configured."""
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def get_whatsapp_config() -> dict:
    """Get all WhatsApp configuration settings."""
    return {
        'enabled': ENABLE_WHATSAPP,
        'payment_links_enabled': ENABLE_WHATSAPP_PAYMENT_LINKS,
        'followups_enabled': ENABLE_WHATSAPP_FOLLOWUPS,
        'service_url': WHATSAPP_SERVICE_URL,
        'configured': is_whatsapp_configured(),
        'razorpay_configured': is_razorpay_configured()
    }


