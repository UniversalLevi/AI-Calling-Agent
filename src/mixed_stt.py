"""
Mixed Language STT Engine - Supports Hindi and English
=====================================================

This module provides speech-to-text capabilities for mixed Hindi-English conversations.
"""

from typing import Optional, Tuple
import numpy as np
import sounddevice as sd

# Conditional import to avoid startup errors
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: faster_whisper not available: {e}")
    WhisperModel = None
    FASTER_WHISPER_AVAILABLE = False

try:
    from .debug_logger import logger, log_timing
except Exception:
    class _Null:
        def __getattr__(self, *_):
            return lambda *a, **k: None
    logger = _Null()
    def log_timing(name):
        def _d(f):
            return f
        return _d

try:
    from .config import SAMPLE_RATE, CHANNELS, RECORD_SECONDS, DEVICE_INDEX_IN, AUTO_DETECT_LANGUAGE, SUPPORTED_LANGUAGES
    from .language_detector import detect_language
except ImportError:
    # Handle direct execution
    from config import SAMPLE_RATE, CHANNELS, RECORD_SECONDS, DEVICE_INDEX_IN, AUTO_DETECT_LANGUAGE, SUPPORTED_LANGUAGES
    from language_detector import detect_language


class MixedSTTEngine:
    """
    Mixed Language Speech-to-Text Engine supporting Hindi and English.
    """
    
    def __init__(self, model_size: str = "base") -> None:
        """
        Initialize the mixed language STT engine.
        
        Args:
            model_size: Whisper model size (tiny, small, base, medium, large)
        """
        if not FASTER_WHISPER_AVAILABLE:
            print("❌ Error: faster_whisper not available. STT functionality disabled.")
            self.model = None
            self.model_size = None
            return
            
        try:
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self.model_size = model_size
            print(f"🎤 Mixed STT Engine initialized with {model_size} model")
        except Exception as e:
            print(f"❌ Error initializing Whisper model: {e}")
            self.model = None
            self.model_size = None

    def record_audio(self) -> np.ndarray:
        """Record audio from microphone."""
        duration = RECORD_SECONDS
        device = int(DEVICE_INDEX_IN) if DEVICE_INDEX_IN else None
        audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="float32", device=device)
        sd.wait()
        return audio.flatten()

    @log_timing("STT transcription")
    def transcribe_with_language(self, audio: np.ndarray, language: str = None) -> Tuple[str, str]:
        """
        Transcribe audio with specified language or auto-detect.
        
        Args:
            audio: Audio data
            language: Language code ('hi', 'en', 'auto')
            
        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        if self.model is None:
            print("⚠️ STT model not available, returning empty result")
            return "", "en"
            
        if language == "auto" or language is None:
            # First transcribe without language constraint
            segments, _ = self.model.transcribe(audio, vad_filter=True)
            text_parts = [seg.text for seg in segments]
            initial_text = " ".join(part.strip() for part in text_parts).strip()
            
            if not initial_text:
                return "", "en"
            
            # Detect language from transcribed text
            detected_lang = detect_language(initial_text)
            
            # Re-transcribe with detected language for better accuracy
            if detected_lang in SUPPORTED_LANGUAGES:
                segments, _ = self.model.transcribe(audio, language=detected_lang, vad_filter=True)
                text_parts = [seg.text for seg in segments]
                final_text = " ".join(part.strip() for part in text_parts).strip()
                return final_text, detected_lang
            else:
                return initial_text, detected_lang
        else:
            # Transcribe with specified language
            segments, _ = self.model.transcribe(audio, language=language, vad_filter=True)
            text_parts = [seg.text for seg in segments]
            text = " ".join(part.strip() for part in text_parts).strip()
            return text, language

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcribe audio with automatic language detection.
        
        Args:
            audio: Audio data
            
        Returns:
            Transcribed text
        """
        if self.model is None:
            return ""
        text, _ = self.transcribe_with_language(audio, "auto")
        return text

    def transcribe_hindi(self, audio: np.ndarray) -> str:
        """
        Transcribe audio specifically in Hindi.
        
        Args:
            audio: Audio data
            
        Returns:
            Hindi transcribed text
        """
        if self.model is None:
            return ""
        text, _ = self.transcribe_with_language(audio, "hi")
        return text

    def transcribe_english(self, audio: np.ndarray) -> str:
        """
        Transcribe audio specifically in English.
        
        Args:
            audio: Audio data
            
        Returns:
            English transcribed text
        """
        if self.model is None:
            return ""
        text, _ = self.transcribe_with_language(audio, "en")
        return text


def capture_and_transcribe_mixed() -> Tuple[Optional[str], str]:
    """
    Capture audio and transcribe with mixed language support.
    
    Returns:
        Tuple of (transcribed_text, detected_language)
    """
    stt = MixedSTTEngine()
    audio = stt.record_audio()
    text, language = stt.transcribe_with_language(audio, "auto")
    return text if text else None, language


def capture_and_transcribe() -> Optional[str]:
    """
    Capture audio and transcribe with automatic language detection.
    
    Returns:
        Transcribed text or None if no speech detected
    """
    text, _ = capture_and_transcribe_mixed()
    return text


# Backward compatibility
class STTEngine(MixedSTTEngine):
    """Backward compatibility alias for existing code."""
    pass
