import os
from typing import Optional

from dotenv import load_dotenv


load_dotenv()


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
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")


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


