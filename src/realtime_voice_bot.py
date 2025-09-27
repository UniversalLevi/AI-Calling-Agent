"""
Real-time Voice Bot with Interruption Handling
==============================================

This module provides a real-time voice bot that supports natural conversation
flow with interruption handling, similar to ChatGPT's voice mode.
"""

import os
import sys
import time
import threading
import queue
import asyncio
import json
import base64
import logging
from typing import Optional, Callable, Dict, Any
import numpy as np
import sounddevice as sd

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from .config import SAMPLE_RATE, CHANNELS, PRINT_TRANSCRIPTS, PRINT_BOT_TEXT
    from .mixed_ai_brain import MixedAIBrain
    from .mixed_stt import MixedSTTEngine
    from .enhanced_hindi_tts import speak_mixed_enhanced
    from .language_detector import detect_language
    from .realtime_vad import RealtimeConversationManager
except ImportError:
    from config import SAMPLE_RATE, CHANNELS, PRINT_TRANSCRIPTS, PRINT_BOT_TEXT
    from mixed_ai_brain import MixedAIBrain
    from mixed_stt import MixedSTTEngine
    from enhanced_hindi_tts import speak_mixed_enhanced
    from language_detector import detect_language
    from realtime_vad import RealtimeConversationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeVoiceBot:
    """Real-time voice bot with natural conversation flow and interruption handling"""
    
    def __init__(self):
        """Initialize the realtime voice bot"""
        self.sample_rate = SAMPLE_RATE if SAMPLE_RATE in [8000, 16000, 32000, 48000] else 16000
        self.channels = CHANNELS
        
        # Initialize AI components
        try:
            self.ai_brain = MixedAIBrain()
            self.stt_engine = MixedSTTEngine()
            logger.info("✅ AI components initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI components: {e}")
            raise
        
        # Initialize conversation manager
        self.conversation_manager = RealtimeConversationManager(sample_rate=self.sample_rate)
        self.conversation_manager.on_speech_detected = self._handle_user_speech
        self.conversation_manager.on_interruption = self._handle_interruption
        
        # Audio streaming
        self.input_stream = None
        self.output_stream = None
        self.is_active = False
        
        # TTS management
        self.current_tts_process = None
        self.tts_queue = queue.Queue()
        self.tts_thread = None
        
        # Conversation state
        self.conversation_history = []
        self.current_language = 'en'
        
        logger.info("🤖 Realtime voice bot initialized")
    
    def start(self):
        """Start the realtime voice bot"""
        if self.is_active:
            return
        
        try:
            self.is_active = True
            
            # Start conversation manager
            self.conversation_manager.start()
            
            # Start TTS processing thread
            self.tts_thread = threading.Thread(target=self._tts_processing_loop, daemon=True)
            self.tts_thread.start()
            
            # Start audio streams
            self._start_audio_streams()
            
            logger.info("🚀 Realtime voice bot started")
            
            # Send initial greeting
            self._send_greeting()
            
        except Exception as e:
            logger.error(f"❌ Failed to start realtime voice bot: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the realtime voice bot"""
        if not self.is_active:
            return
        
        self.is_active = False
        
        # Stop audio streams
        self._stop_audio_streams()
        
        # Stop conversation manager
        self.conversation_manager.stop()
        
        # Stop current TTS
        if self.current_tts_process:
            try:
                self.current_tts_process.terminate()
            except:
                pass
        
        logger.info("🛑 Realtime voice bot stopped")
    
    def _start_audio_streams(self):
        """Start audio input and output streams"""
        try:
            # Input stream for continuous listening
            self.input_stream = sd.InputStream(
                callback=self._audio_input_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * 0.1),  # 100ms chunks
                dtype='float32'
            )
            
            self.input_stream.start()
            logger.info(f"🎤 Audio input stream started ({self.sample_rate}Hz)")
            
        except Exception as e:
            logger.error(f"❌ Failed to start audio streams: {e}")
            raise
    
    def _stop_audio_streams(self):
        """Stop audio streams"""
        if self.input_stream:
            try:
                self.input_stream.stop()
                self.input_stream.close()
            except:
                pass
            self.input_stream = None
    
    def _audio_input_callback(self, indata, frames, time, status):
        """Process incoming audio in real-time"""
        if status:
            logger.warning(f"Audio input status: {status}")
        
        if self.is_active and len(indata) > 0:
            # Convert to mono if stereo
            if indata.shape[1] > 1:
                audio_data = np.mean(indata, axis=1)
            else:
                audio_data = indata.flatten()
            
            # Send to conversation manager for processing
            self.conversation_manager.add_audio_chunk(audio_data)
    
    def _handle_user_speech(self, audio_data: np.ndarray):
        """Handle detected user speech"""
        try:
            if PRINT_TRANSCRIPTS:
                logger.info("🎤 Processing user speech...")
            
            # Transcribe speech
            text, detected_language = self.stt_engine.transcribe_with_language(audio_data, "auto")
            
            if text and text.strip():
                self.current_language = detected_language
                
                if PRINT_TRANSCRIPTS:
                    print(f"👤 User ({detected_language}): {text}")
                
                # Generate AI response
                self._generate_ai_response(text, detected_language)
            
        except Exception as e:
            logger.error(f"❌ Error handling user speech: {e}")
    
    def _generate_ai_response(self, user_text: str, language: str):
        """Generate and queue AI response"""
        try:
            # Get AI response
            response = self.ai_brain.ask(user_text, language)
            
            if response and response.strip():
                if PRINT_BOT_TEXT:
                    print(f"🤖 Bot ({language}): {response}")
                
                # Queue for TTS
                self.tts_queue.put({
                    'text': response,
                    'language': language,
                    'timestamp': time.time()
                })
        
        except Exception as e:
            logger.error(f"❌ Error generating AI response: {e}")
    
    def _tts_processing_loop(self):
        """Process TTS queue in separate thread"""
        logger.info("🔊 TTS processing loop started")
        
        while self.is_active:
            try:
                # Get TTS request with timeout
                tts_request = self.tts_queue.get(timeout=0.1)
                
                # Check if we should still process this request
                if time.time() - tts_request['timestamp'] > 5.0:
                    logger.warning("⏰ Skipping old TTS request")
                    continue
                
                # Start speaking
                self.conversation_manager.start_bot_response()
                
                # Generate and play speech
                self._speak_response(tts_request['text'], tts_request['language'])
                
                # Finished speaking
                self.conversation_manager.stop_bot_response()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Error in TTS processing: {e}")
                self.conversation_manager.stop_bot_response()
    
    def _speak_response(self, text: str, language: str):
        """Speak the bot's response with interruption support"""
        try:
            # Use enhanced TTS for Hindi/mixed, otherwise use simple TTS
            if language in ['hi', 'mixed']:
                # Enhanced Hindi TTS returns filename
                result = speak_mixed_enhanced(text)
                if result and (result.endswith('.mp3') or result.endswith('.wav')):
                    self._play_audio_file(result)
                else:
                    # Fallback to text display
                    print(f"🔊 Bot: {text}")
            else:
                # For English, you could use a different TTS or the same enhanced one
                result = speak_mixed_enhanced(text)
                if result and (result.endswith('.mp3') or result.endswith('.wav')):
                    self._play_audio_file(result)
                else:
                    print(f"🔊 Bot: {text}")
        
        except Exception as e:
            logger.error(f"❌ Error speaking response: {e}")
            print(f"🔊 Bot: {text}")
    
    def _play_audio_file(self, filename: str):
        """Play audio file with interruption support"""
        try:
            import pygame
            pygame.mixer.init()
            
            # Store current process for interruption
            self.current_tts_process = pygame.mixer
            
            # Play audio
            audio_path = f"audio_files/{filename}"
            if os.path.exists(audio_path):
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                
                # Wait for playback to finish or be interrupted
                while pygame.mixer.music.get_busy() and self.conversation_manager.interruption_handler.is_bot_speaking:
                    time.sleep(0.1)
                
                pygame.mixer.music.stop()
            
            self.current_tts_process = None
            
        except Exception as e:
            logger.error(f"❌ Error playing audio file: {e}")
            # Fallback: just print the text
            self.current_tts_process = None
    
    def _handle_interruption(self):
        """Handle user interruption"""
        logger.info("🛑 User interrupted - stopping bot speech")
        
        # Stop current audio playback
        if self.current_tts_process:
            try:
                if hasattr(self.current_tts_process, 'music'):
                    self.current_tts_process.music.stop()
            except:
                pass
        
        # Clear TTS queue to avoid playing outdated responses
        while not self.tts_queue.empty():
            try:
                self.tts_queue.get_nowait()
            except queue.Empty:
                break
    
    def _send_greeting(self):
        """Send initial greeting"""
        greeting_text = "Hello! नमस्ते! I'm your AI assistant. How can I help you today?"
        greeting_language = detect_language(greeting_text)
        
        self.tts_queue.put({
            'text': greeting_text,
            'language': greeting_language,
            'timestamp': time.time()
        })
    
    def process_twilio_audio(self, audio_data: bytes, media_format: str = 'mulaw'):
        """Process audio from Twilio Media Streams"""
        try:
            # Convert Twilio audio format to numpy array
            if media_format == 'mulaw':
                # Decode μ-law to linear PCM
                import audioop
                linear_data = audioop.ulaw2lin(audio_data, 2)
                audio_array = np.frombuffer(linear_data, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                # Assume linear PCM
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Send to conversation manager
            self.conversation_manager.add_audio_chunk(audio_array)
            
        except Exception as e:
            logger.error(f"❌ Error processing Twilio audio: {e}")
    
    def get_bot_response_audio(self, text: str, language: str) -> Optional[bytes]:
        """Generate bot response audio for Twilio"""
        try:
            # Generate TTS
            if language in ['hi', 'mixed']:
                result = speak_mixed_enhanced(text)
            else:
                result = speak_mixed_enhanced(text)
            
            if result and os.path.exists(f"audio_files/{result}"):
                # Read audio file and convert to format expected by Twilio
                with open(f"audio_files/{result}", 'rb') as f:
                    audio_data = f.read()
                
                # Convert to μ-law format for Twilio
                # This is a simplified conversion - you might need more sophisticated audio processing
                return audio_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error generating bot response audio: {e}")
            return None


class TwilioRealtimeIntegration:
    """Integration between Realtime Voice Bot and Twilio Media Streams"""
    
    def __init__(self, voice_bot: RealtimeVoiceBot):
        self.voice_bot = voice_bot
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        logger.info("📞 Twilio realtime integration initialized")
    
    def handle_media_stream(self, call_sid: str, media_data: Dict[str, Any]):
        """Handle incoming media stream from Twilio"""
        try:
            event = media_data.get('event')
            
            if event == 'connected':
                logger.info(f"📞 Media stream connected for call {call_sid}")
                self.active_calls[call_sid] = {
                    'start_time': time.time(),
                    'stream_sid': media_data.get('streamSid')
                }
                
                # Start the voice bot if not already active
                if not self.voice_bot.is_active:
                    self.voice_bot.start()
            
            elif event == 'start':
                logger.info(f"📞 Media stream started for call {call_sid}")
            
            elif event == 'media':
                # Process incoming audio
                payload = media_data.get('media', {}).get('payload', '')
                if payload:
                    audio_data = base64.b64decode(payload)
                    self.voice_bot.process_twilio_audio(audio_data, 'mulaw')
            
            elif event == 'stop':
                logger.info(f"📞 Media stream stopped for call {call_sid}")
                if call_sid in self.active_calls:
                    del self.active_calls[call_sid]
                
                # Stop voice bot if no active calls
                if not self.active_calls:
                    self.voice_bot.stop()
        
        except Exception as e:
            logger.error(f"❌ Error handling media stream: {e}")
    
    def send_audio_to_twilio(self, call_sid: str, audio_data: bytes):
        """Send bot audio back to Twilio (placeholder)"""
        # This would need to be implemented with Twilio's WebSocket connection
        # for sending audio back to the caller
        pass


def main():
    """Test the realtime voice bot locally"""
    print("🎤 Starting Realtime Voice Bot Test")
    print("Press Ctrl+C to stop")
    
    bot = RealtimeVoiceBot()
    
    try:
        bot.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping realtime voice bot...")
        bot.stop()
    
    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
        bot.stop()


if __name__ == "__main__":
    main()
