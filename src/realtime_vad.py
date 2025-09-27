"""
Real-time Voice Activity Detection and Interruption Handling
===========================================================

This module provides real-time voice activity detection and interruption handling
for natural conversation flow, similar to ChatGPT's voice mode.
"""

import time
import threading
import queue
import collections
import logging
from typing import Optional, Callable, List
import numpy as np

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    print("⚠️ WebRTC VAD not available. Install with: pip install webrtcvad")

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️ Librosa not available. Install with: pip install librosa")

try:
    from .config import SAMPLE_RATE
except ImportError:
    from config import SAMPLE_RATE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """Real-time Voice Activity Detection for interruption handling"""
    
    def __init__(self, aggressiveness: int = 2, sample_rate: int = 16000):
        """
        Initialize VAD
        
        Args:
            aggressiveness: VAD aggressiveness level (0-3, higher = more aggressive)
            sample_rate: Audio sample rate (8000, 16000, 32000, or 48000)
        """
        self.sample_rate = sample_rate
        self.aggressiveness = aggressiveness
        self.vad = None
        
        if VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(aggressiveness)
            logger.info(f"🎤 VAD initialized with aggressiveness {aggressiveness}")
        else:
            logger.warning("🎤 VAD not available, using fallback detection")
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Detect if audio chunk contains speech
        
        Args:
            audio_chunk: Audio data as numpy array
            
        Returns:
            True if speech detected, False otherwise
        """
        if not self.vad:
            # Fallback: simple energy-based detection
            return self._energy_based_detection(audio_chunk)
        
        try:
            # Convert audio to format expected by WebRTC VAD
            if self.sample_rate != 16000:
                if LIBROSA_AVAILABLE:
                    audio_16k = librosa.resample(audio_chunk, orig_sr=self.sample_rate, target_sr=16000)
                else:
                    # Simple downsampling fallback
                    step = self.sample_rate // 16000
                    audio_16k = audio_chunk[::step]
            else:
                audio_16k = audio_chunk
            
            # Ensure proper format (16-bit PCM)
            audio_16k = np.clip(audio_16k, -1.0, 1.0)
            audio_bytes = (audio_16k * 32767).astype(np.int16).tobytes()
            
            # VAD expects specific frame sizes (10, 20, or 30ms)
            frame_duration = 30  # ms
            frame_size = int(16000 * frame_duration / 1000)  # samples
            
            if len(audio_bytes) >= frame_size * 2:  # 2 bytes per sample
                frame_bytes = audio_bytes[:frame_size * 2]
                return self.vad.is_speech(frame_bytes, 16000)
            
            return False
            
        except Exception as e:
            logger.error(f"VAD error: {e}")
            return self._energy_based_detection(audio_chunk)
    
    def _energy_based_detection(self, audio_chunk: np.ndarray) -> bool:
        """Fallback energy-based speech detection"""
        if len(audio_chunk) == 0:
            return False
        
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        # Simple threshold-based detection
        speech_threshold = 0.01  # Adjust based on your needs
        return rms > speech_threshold


class InterruptionHandler:
    """Handles interruption detection and bot speech control"""
    
    def __init__(self, vad: VoiceActivityDetector, speech_buffer_duration: float = 0.5):
        """
        Initialize interruption handler
        
        Args:
            vad: Voice activity detector instance
            speech_buffer_duration: Duration to buffer speech for interruption detection
        """
        self.vad = vad
        self.speech_buffer_duration = speech_buffer_duration
        self.is_bot_speaking = False
        self.is_listening = True
        self.current_tts_process = None
        
        # Speech detection buffer
        buffer_size = int(speech_buffer_duration * 10)  # 10 chunks per second
        self.speech_buffer = collections.deque(maxlen=buffer_size)
        
        # Callbacks
        self.on_interruption_detected: Optional[Callable] = None
        self.on_speech_started: Optional[Callable] = None
        self.on_speech_ended: Optional[Callable] = None
        
        logger.info("🔄 Interruption handler initialized")
    
    def process_audio_chunk(self, audio_chunk: np.ndarray) -> dict:
        """
        Process audio chunk for interruption detection
        
        Args:
            audio_chunk: Audio data
            
        Returns:
            Dictionary with detection results
        """
        is_speech = self.vad.is_speech(audio_chunk)
        current_time = time.time()
        
        # Add to speech buffer
        self.speech_buffer.append({
            'timestamp': current_time,
            'is_speech': is_speech,
            'audio': audio_chunk
        })
        
        result = {
            'is_speech': is_speech,
            'interruption_detected': False,
            'should_stop_bot': False,
            'confidence': 0.0
        }
        
        if is_speech:
            # Calculate speech confidence based on recent buffer
            recent_speech = sum(1 for item in self.speech_buffer if item['is_speech'])
            result['confidence'] = recent_speech / len(self.speech_buffer)
            
            # Check for interruption
            if self.is_bot_speaking and result['confidence'] > 0.3:
                result['interruption_detected'] = True
                result['should_stop_bot'] = True
                
                logger.info("🛑 Interruption detected - stopping bot speech")
                self._handle_interruption()
                
                if self.on_interruption_detected:
                    self.on_interruption_detected(audio_chunk)
        
        return result
    
    def start_bot_speaking(self, tts_process=None):
        """Indicate that bot has started speaking"""
        self.is_bot_speaking = True
        self.current_tts_process = tts_process
        logger.info("🤖 Bot started speaking")
    
    def stop_bot_speaking(self):
        """Stop bot from speaking"""
        if self.is_bot_speaking:
            self.is_bot_speaking = False
            
            # Stop current TTS process if available
            if self.current_tts_process:
                try:
                    if hasattr(self.current_tts_process, 'terminate'):
                        self.current_tts_process.terminate()
                    elif hasattr(self.current_tts_process, 'stop'):
                        self.current_tts_process.stop()
                except Exception as e:
                    logger.error(f"Error stopping TTS: {e}")
            
            self.current_tts_process = None
            logger.info("🛑 Bot stopped speaking")
    
    def _handle_interruption(self):
        """Internal interruption handling"""
        self.stop_bot_speaking()
        
        # Clear speech buffer to avoid false positives
        self.speech_buffer.clear()


class RealtimeConversationManager:
    """Manages real-time conversation flow with interruption handling"""
    
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 0.1):
        """
        Initialize conversation manager
        
        Args:
            sample_rate: Audio sample rate
            chunk_duration: Duration of each audio chunk in seconds
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # Initialize components
        self.vad = VoiceActivityDetector(sample_rate=sample_rate)
        self.interruption_handler = InterruptionHandler(self.vad)
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.is_running = False
        self.processing_thread = None
        
        # Callbacks
        self.on_speech_detected: Optional[Callable[[np.ndarray], None]] = None
        self.on_interruption: Optional[Callable] = None
        
        # Set up interruption callback
        self.interruption_handler.on_interruption_detected = self._on_interruption_callback
        
        logger.info("🎯 Realtime conversation manager initialized")
    
    def start(self):
        """Start real-time conversation processing"""
        if self.is_running:
            return
        
        self.is_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        logger.info("🚀 Realtime conversation manager started")
    
    def stop(self):
        """Stop real-time conversation processing"""
        self.is_running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        
        logger.info("🛑 Realtime conversation manager stopped")
    
    def add_audio_chunk(self, audio_chunk: np.ndarray):
        """Add audio chunk for processing"""
        if self.is_running:
            self.audio_queue.put(audio_chunk)
    
    def start_bot_response(self, tts_process=None):
        """Indicate bot started speaking"""
        self.interruption_handler.start_bot_speaking(tts_process)
    
    def stop_bot_response(self):
        """Stop bot from speaking"""
        self.interruption_handler.stop_bot_speaking()
    
    def _processing_loop(self):
        """Main processing loop for audio chunks"""
        logger.info("🔄 Audio processing loop started")
        
        speech_chunks = []
        silence_duration = 0
        max_silence = 1.0  # seconds of silence before processing speech
        
        while self.is_running:
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Process for interruption detection
                result = self.interruption_handler.process_audio_chunk(audio_chunk)
                
                # Accumulate speech chunks
                if result['is_speech'] and not self.interruption_handler.is_bot_speaking:
                    speech_chunks.append(audio_chunk)
                    silence_duration = 0
                else:
                    silence_duration += self.chunk_duration
                
                # Process accumulated speech if silence detected
                if speech_chunks and silence_duration >= max_silence:
                    combined_audio = np.concatenate(speech_chunks)
                    
                    if self.on_speech_detected:
                        self.on_speech_detected(combined_audio)
                    
                    # Clear accumulated speech
                    speech_chunks = []
                    silence_duration = 0
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
    
    def _on_interruption_callback(self, audio_chunk: np.ndarray):
        """Handle interruption callback"""
        if self.on_interruption:
            self.on_interruption()


# Utility functions
def create_realtime_conversation_manager(sample_rate: int = None) -> RealtimeConversationManager:
    """Create a configured realtime conversation manager"""
    if sample_rate is None:
        sample_rate = SAMPLE_RATE if SAMPLE_RATE in [8000, 16000, 32000, 48000] else 16000
    
    return RealtimeConversationManager(sample_rate=sample_rate)


def test_vad():
    """Test VAD functionality"""
    print("🧪 Testing Voice Activity Detection...")
    
    vad = VoiceActivityDetector()
    
    # Generate test audio
    duration = 1.0
    sample_rate = 16000
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Silent audio
    silent_audio = np.zeros_like(t)
    print(f"Silent audio: {vad.is_speech(silent_audio)}")
    
    # Noise audio
    noise_audio = np.random.normal(0, 0.1, len(t))
    print(f"Noise audio: {vad.is_speech(noise_audio)}")
    
    # Sine wave (simulating speech)
    sine_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
    print(f"Sine wave audio: {vad.is_speech(sine_audio)}")


if __name__ == "__main__":
    test_vad()
