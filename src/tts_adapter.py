"""
TTS Adapter - Safe wrapper for existing enhanced_hindi_tts
===========================================================

This adapter provides byte-level output for systems that need it,
while preserving the robust multi-provider TTS system from master.

NO MODIFICATIONS to enhanced_hindi_tts.py are made.
"""

import os
from typing import Optional

try:
    from .enhanced_hindi_tts import EnhancedHindiTTS, speak_mixed_enhanced
except ImportError:
    from enhanced_hindi_tts import EnhancedHindiTTS, speak_mixed_enhanced


# Initialize global TTS instance
_tts_instance = None


def get_tts_instance() -> EnhancedHindiTTS:
    """Get or create TTS instance"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = EnhancedHindiTTS()
    return _tts_instance


def speak_mixed_enhanced_bytes(text: str) -> bytes:
    """
    Generate mixed language speech and return as WAV bytes
    
    This is a safe wrapper that uses the existing master TTS system
    with its robust multi-provider fallback (OpenAI → Google → Azure → gTTS).
    
    Args:
        text: Text to convert to speech
        
    Returns:
        WAV audio bytes (or MP3 bytes depending on provider)
    """
    try:
        # Generate audio file using existing TTS
        audio_filename = speak_mixed_enhanced(text)
        
        if not audio_filename:
            raise RuntimeError("TTS generation failed")
        
        # Read the generated audio file
        audio_path = os.path.join('audio_files', audio_filename)
        
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        
        return audio_bytes
        
    except Exception as e:
        print(f"⚠️ TTS adapter error: {e}")
        # Return minimal silence as fallback
        return b'\x00' * 1024


def speak_enhanced_hindi_bytes(text: str) -> bytes:
    """Alias for backwards compatibility"""
    return speak_mixed_enhanced_bytes(text)


# Export main function
__all__ = ['speak_mixed_enhanced_bytes', 'speak_enhanced_hindi_bytes', 'get_tts_instance']

