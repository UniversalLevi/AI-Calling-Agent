"""
WebSocket-based Real-time Interruption System
============================================

This module implements a robust interruption system using WebSocket connections
for real-time bidirectional audio streaming with Twilio Media Streams.
"""

import asyncio
import websockets
import json
import base64
import numpy as np
import time
import logging
from typing import Optional, Callable, Dict, Any
import threading
import queue
from collections import deque

try:
    from .enhanced_hindi_tts import speak_mixed_enhanced
except ImportError:
    from enhanced_hindi_tts import speak_mixed_enhanced

# Simple VAD implementation without webrtcvad dependency
class SimpleVAD:
    """Simple Voice Activity Detection using energy-based method"""
    
    def __init__(self, threshold: float = 0.01):
        self.threshold = threshold
    
    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """Simple energy-based speech detection"""
        if len(audio_chunk) == 0:
            return False
        
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        return rms > self.threshold

logger = logging.getLogger(__name__)

class WebSocketInterruptionHandler:
    """
    Real-time interruption handler using WebSocket connections
    """
    
    def __init__(self, vad_threshold: float = 0.01):
        """Initialize the WebSocket interruption handler"""
        self.vad = SimpleVAD(threshold=vad_threshold)
        self.is_bot_speaking = False
        self.is_listening = True
        self.websocket = None
        self.call_sid = None
        
        # Audio buffers
        self.audio_buffer = deque(maxlen=50)  # ~1 second at 50 chunks/sec
        self.speech_buffer = deque(maxlen=20)  # ~0.4 seconds
        
        # Interruption detection
        self.interruption_threshold = 0.4  # 40% confidence
        self.min_speech_duration = 0.3  # 300ms minimum
        self.speech_start_time = None
        
        # Callbacks
        self.on_interruption: Optional[Callable] = None
        self.on_speech_detected: Optional[Callable] = None
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.processing_thread = None
        self.running = False
        
        logger.info("🎧 WebSocket interruption handler initialized")
    
    async def handle_websocket(self, websocket, path):
        """Handle incoming WebSocket connection from Twilio Media Streams"""
        self.websocket = websocket
        logger.info(f"🔗 WebSocket connected: {path}")
        
        try:
            async for message in websocket:
                await self._process_websocket_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            self.websocket = None
    
    async def _process_websocket_message(self, message: str):
        """Process incoming WebSocket message from Twilio"""
        try:
            data = json.loads(message)
            event = data.get('event')
            
            if event == 'connected':
                logger.info("📞 Media stream connected")
                
            elif event == 'start':
                self.call_sid = data.get('start', {}).get('callSid')
                logger.info(f"🚀 Media stream started for call: {self.call_sid}")
                self._start_audio_processing()
                
            elif event == 'media':
                # Process incoming audio
                media = data.get('media', {})
                payload = media.get('payload', '')
                
                if payload:
                    # Decode audio (μ-law format)
                    audio_data = base64.b64decode(payload)
                    await self._process_audio_chunk(audio_data)
                    
            elif event == 'stop':
                logger.info("🛑 Media stream stopped")
                self._stop_audio_processing()
                
        except Exception as e:
            logger.error(f"❌ Error processing WebSocket message: {e}")
    
    async def _process_audio_chunk(self, audio_data: bytes):
        """Process incoming audio chunk for interruption detection"""
        try:
            # Convert μ-law to linear PCM
            audio_array = self._mulaw_to_linear(audio_data)
            
            # Add to processing queue
            self.audio_queue.put(audio_array)
            
        except Exception as e:
            logger.error(f"❌ Error processing audio chunk: {e}")
    
    def _mulaw_to_linear(self, mulaw_data: bytes) -> np.ndarray:
        """Convert μ-law encoded audio to linear PCM"""
        # μ-law to linear conversion
        mulaw_array = np.frombuffer(mulaw_data, dtype=np.uint8)
        
        # Convert μ-law to 16-bit linear PCM
        linear = np.zeros(len(mulaw_array), dtype=np.int16)
        
        for i, mulaw_val in enumerate(mulaw_array):
            # μ-law decompression algorithm
            mulaw_val = ~mulaw_val
            sign = mulaw_val & 0x80
            exponent = (mulaw_val >> 4) & 0x07
            mantissa = mulaw_val & 0x0F
            
            sample = mantissa << (exponent + 3)
            if exponent > 0:
                sample += (1 << (exponent + 2))
            
            if sign:
                sample = -sample
                
            linear[i] = sample
        
        return linear.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
    
    def _start_audio_processing(self):
        """Start audio processing thread"""
        if not self.running:
            self.running = True
            self.processing_thread = threading.Thread(target=self._audio_processing_loop, daemon=True)
            self.processing_thread.start()
            logger.info("🎵 Audio processing started")
    
    def _stop_audio_processing(self):
        """Stop audio processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        logger.info("🛑 Audio processing stopped")
    
    def _audio_processing_loop(self):
        """Main audio processing loop"""
        while self.running:
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Process for speech detection
                self._detect_speech_and_interruption(audio_chunk)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"❌ Audio processing error: {e}")
    
    def _detect_speech_and_interruption(self, audio_chunk: np.ndarray):
        """Detect speech and check for interruption"""
        try:
            # Voice activity detection
            is_speech = self.vad.is_speech(audio_chunk)
            current_time = time.time()
            
            # Add to speech buffer
            self.speech_buffer.append({
                'timestamp': current_time,
                'is_speech': is_speech,
                'confidence': 1.0 if is_speech else 0.0
            })
            
            if is_speech:
                # Track speech start
                if self.speech_start_time is None:
                    self.speech_start_time = current_time
                    logger.debug("🎤 Speech started")
                
                # Calculate recent speech confidence
                recent_speech = [item for item in self.speech_buffer 
                               if current_time - item['timestamp'] <= 0.5]  # Last 500ms
                
                if recent_speech:
                    speech_confidence = sum(item['confidence'] for item in recent_speech) / len(recent_speech)
                    speech_duration = current_time - self.speech_start_time
                    
                    # Check for interruption
                    if (self.is_bot_speaking and 
                        speech_confidence >= self.interruption_threshold and
                        speech_duration >= self.min_speech_duration):
                        
                        logger.info(f"🛑 INTERRUPTION DETECTED! Confidence: {speech_confidence:.2f}, Duration: {speech_duration:.2f}s")
                        self._handle_interruption()
                        
                        # Callback for interruption
                        if self.on_interruption:
                            self.on_interruption({
                                'confidence': speech_confidence,
                                'duration': speech_duration,
                                'timestamp': current_time
                            })
            else:
                # Reset speech tracking if no speech for 200ms
                if (self.speech_start_time and 
                    current_time - self.speech_start_time > 0.2):
                    self.speech_start_time = None
                    
        except Exception as e:
            logger.error(f"❌ Speech detection error: {e}")
    
    def _handle_interruption(self):
        """Handle detected interruption"""
        if self.is_bot_speaking:
            self.is_bot_speaking = False
            logger.info("🛑 Bot speech interrupted")
            
            # Send stop signal to Twilio (stop current audio)
            if self.websocket:
                asyncio.create_task(self._send_clear_audio())
    
    async def _send_clear_audio(self):
        """Send clear audio command to Twilio to stop current playback"""
        try:
            if self.websocket:
                clear_message = {
                    "event": "clear",
                    "streamSid": self.call_sid
                }
                await self.websocket.send(json.dumps(clear_message))
                logger.info("🔇 Sent clear audio command")
        except Exception as e:
            logger.error(f"❌ Error sending clear audio: {e}")
    
    def start_bot_speaking(self):
        """Mark that bot has started speaking"""
        self.is_bot_speaking = True
        self.speech_start_time = None  # Reset speech detection
        logger.info("🤖 Bot started speaking")
    
    def stop_bot_speaking(self):
        """Mark that bot has stopped speaking"""
        self.is_bot_speaking = False
        logger.info("🤖 Bot stopped speaking")
    
    async def send_audio_to_twilio(self, audio_data: bytes):
        """Send audio data to Twilio for playback"""
        try:
            if self.websocket:
                # Convert audio to μ-law and base64 encode
                mulaw_data = self._linear_to_mulaw(audio_data)
                payload = base64.b64encode(mulaw_data).decode('utf-8')
                
                message = {
                    "event": "media",
                    "streamSid": self.call_sid,
                    "media": {
                        "payload": payload
                    }
                }
                
                await self.websocket.send(json.dumps(message))
                
        except Exception as e:
            logger.error(f"❌ Error sending audio to Twilio: {e}")
    
    def _linear_to_mulaw(self, linear_data: bytes) -> bytes:
        """Convert linear PCM to μ-law encoding"""
        # Convert bytes to numpy array
        linear_array = np.frombuffer(linear_data, dtype=np.int16)
        
        # μ-law compression
        mulaw_array = np.zeros(len(linear_array), dtype=np.uint8)
        
        for i, sample in enumerate(linear_array):
            # μ-law compression algorithm
            sample = int(sample)
            sign = 0x80 if sample < 0 else 0x00
            sample = abs(sample)
            
            if sample > 32635:
                sample = 32635
                
            sample += 132  # Bias
            
            exponent = 7
            for exp_lut in [0x1F80, 0x3F0, 0x1F8, 0x3F, 0x1F, 0x0F, 0x07, 0x03]:
                if sample >= exp_lut:
                    break
                exponent -= 1
            
            mantissa = (sample >> (exponent + 3)) & 0x0F
            mulaw_val = ~(sign | (exponent << 4) | mantissa)
            mulaw_array[i] = mulaw_val & 0xFF
        
        return mulaw_array.tobytes()


class WebSocketInterruptionServer:
    """WebSocket server for handling Twilio Media Streams"""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.handler = WebSocketInterruptionHandler()
        self.server = None
        
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(
                self.handler.handle_websocket,
                self.host,
                self.port
            )
            logger.info(f"🚀 WebSocket server started on ws://{self.host}:{self.port}")
            
            # Keep server running
            await self.server.wait_closed()
            
        except Exception as e:
            logger.error(f"❌ WebSocket server error: {e}")
    
    def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            logger.info("🛑 WebSocket server stopped")
    
    def set_interruption_callback(self, callback: Callable):
        """Set callback for interruption events"""
        self.handler.on_interruption = callback
    
    def set_speech_callback(self, callback: Callable):
        """Set callback for speech detection events"""
        self.handler.on_speech_detected = callback


# Global server instance
websocket_server = None

def start_websocket_interruption_server(host: str = "localhost", port: int = 8080):
    """Start the WebSocket interruption server"""
    global websocket_server
    
    if websocket_server is None:
        websocket_server = WebSocketInterruptionServer(host, port)
        
        # Run in separate thread
        def run_server():
            asyncio.run(websocket_server.start_server())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        logger.info(f"🎧 WebSocket interruption server starting on {host}:{port}")
        return websocket_server
    
    return websocket_server

def stop_websocket_interruption_server():
    """Stop the WebSocket interruption server"""
    global websocket_server
    
    if websocket_server:
        websocket_server.stop_server()
        websocket_server = None
        logger.info("🛑 WebSocket interruption server stopped")
