"""
TTS Adapter for Media Streams
==============================

This module provides adapters to convert our existing TTS systems
to work with the Twilio Media Streams barge-in system.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Optional, Callable

try:
    from .enhanced_hindi_tts import speak_mixed_enhanced_bytes
except ImportError:
    from enhanced_hindi_tts import speak_mixed_enhanced_bytes


def create_tts_adapter() -> Callable[[str], bytes]:
    """
    Create a TTS adapter that returns WAV bytes for the Media Streams system
    
    Returns:
        Function that takes text and returns WAV bytes
    """
    
    def tts_provider(text: str) -> bytes:
        """
        TTS provider that returns WAV bytes
        
        Args:
            text: Text to convert to speech
            
        Returns:
            WAV bytes ready for Media Streams
        """
        try:
            # Generate WAV bytes directly using the enhanced TTS system
            wav_bytes = speak_mixed_enhanced_bytes(text)
            
            if not isinstance(wav_bytes, (bytes, bytearray)):
                raise RuntimeError("TTS provider must return WAV bytes")
            
            return wav_bytes
            
        except Exception as e:
            print(f"❌ TTS adapter error: {e}")
            # Return silence as fallback
            return _generate_silence_wav()
    
    return tts_provider


def _convert_mp3_to_wav(mp3_bytes: bytes) -> bytes:
    """Convert MP3 bytes to WAV bytes using ffmpeg"""
    try:
        import subprocess
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as mp3_file:
            mp3_file.write(mp3_bytes)
            mp3_path = mp3_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
        
        try:
            # Convert MP3 to WAV using ffmpeg
            process = subprocess.run([
                'ffmpeg',
                '-i', mp3_path,
                '-ar', '8000',  # 8kHz sample rate for Twilio
                '-ac', '1',     # Mono
                '-f', 'wav',
                wav_path
            ], capture_output=True, check=True)
            
            # Read the converted WAV file
            with open(wav_path, 'rb') as f:
                wav_bytes = f.read()
            
            return wav_bytes
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(mp3_path)
                os.unlink(wav_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ MP3 to WAV conversion error: {e}")
        # Return silence as fallback
        return _generate_silence_wav()


def _generate_silence_wav(duration_ms: int = 100) -> bytes:
    """Generate a short silence WAV file"""
    try:
        import subprocess
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_path = wav_file.name
        
        try:
            # Generate silence using ffmpeg
            process = subprocess.run([
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'anullsrc=duration={duration_ms}ms',
                '-ar', '8000',
                '-ac', '1',
                '-f', 'wav',
                wav_path
            ], capture_output=True, check=True)
            
            with open(wav_path, 'rb') as f:
                wav_bytes = f.read()
            
            return wav_bytes
            
        finally:
            try:
                os.unlink(wav_path)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Silence generation error: {e}")
        # Return minimal WAV header as last resort
        return _minimal_wav_header()


def _minimal_wav_header() -> bytes:
    """Generate minimal WAV header for silence"""
    # Minimal WAV header for 8kHz mono 16-bit PCM
    return bytes([
        # RIFF header
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # File size - 8
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        
        # fmt chunk
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Chunk size
        0x01, 0x00,              # Audio format (PCM)
        0x01, 0x00,              # Number of channels (mono)
        0x40, 0x1F, 0x00, 0x00,  # Sample rate (8000)
        0x80, 0x3E, 0x00, 0x00,  # Byte rate
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample
        
        # data chunk
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # Data size (0 for silence)
    ])


def create_stt_callback() -> Callable[[bytes], None]:
    """
    Create an STT callback for processing incoming audio
    
    Returns:
        Function that processes audio bytes for STT
    """
    
    def stt_callback(pcm_bytes: bytes):
        """
        STT callback to process incoming audio
        
        Args:
            pcm_bytes: PCM audio bytes from Media Streams
        """
        try:
            # This is where you would integrate with your STT system
            # For now, just log the audio length
            print(f"🎤 STT callback: {len(pcm_bytes)} bytes")
            
            # TODO: Integrate with Faster-Whisper or your STT system
            # - Buffer audio frames
            # - When enough audio accumulated (e.g., 600ms), call STT
            # - Process the transcription
            
        except Exception as e:
            print(f"❌ STT callback error: {e}")
    
    return stt_callback


# Convenience functions for easy integration
def get_tts_provider() -> Callable[[str], bytes]:
    """Get the configured TTS provider"""
    return create_tts_adapter()


def get_stt_callback() -> Callable[[bytes], None]:
    """Get the configured STT callback"""
    return create_stt_callback()
