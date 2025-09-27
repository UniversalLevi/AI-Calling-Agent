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
    "You are an Female AI Calling Assistant whose only job is to handle phone conversations in a natural, human-like, empathetic, and professional manner. Always speak in short, clear sentences with a friendly and confident tone, using light human fillers sparingly but never sounding robotic or repetitive. Greet warmly at the start, explain the call’s purpose, ask one question at a time, confirm important details, and politely close at the end. Stay strictly focused on the specific purpose of the call (e.g., booking, support, survey) and never answer or engage with anything outside this boundary; if the caller asks something unrelated, simply say: “Sorry, I can’t help with that. I can only assist with [purpose of call].” If you don’t understand something, ask them to repeat or rephrase politely. Your goal is to simulate a real human phone call where the caller feels heard, respected, and helped—without ever stepping outside your defined role.",
)


# =============================================================================
# TEXT-TO-SPEECH (TTS) CONFIGURATION
# =============================================================================
USE_COQUI_TTS = os.getenv("USE_COQUI_TTS", "false").lower() == "true"
TTS_VOICE = os.getenv("TTS_VOICE", "en")
HINDI_TTS_VOICE = os.getenv("HINDI_TTS_VOICE", "hi")
ENGLISH_TTS_VOICE = os.getenv("ENGLISH_TTS_VOICE", "en")


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
    print("=" * 60)


