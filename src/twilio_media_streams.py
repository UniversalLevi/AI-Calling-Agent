"""
Twilio Media Streams Barge-In System
====================================

This module implements a robust interruption system using Twilio Media Streams:
- Receives inbound µ-law audio frames from Twilio via WebSocket
- Runs server-side VAD on incoming audio
- Streams TTS to Twilio in small chunks for immediate interruption
- Sends 'clear' command to Twilio to stop buffered audio when user speaks

This solves the fundamental buffering problem by controlling Twilio's playback buffer directly.
"""

import asyncio
import base64
import json
import logging
try:
    from .debug_logger import logger, log_timing_async
except Exception:
    def log_timing_async(name):
        def _d(f):
            return f
        return _d
    logger = logging.getLogger(__name__)
import subprocess
import audioop
import time
from typing import Callable, Optional, Dict, Any
from pathlib import Path

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    print("⚠️ WebRTC VAD not available. Install with: pip install webrtcvad")

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    print("⚠️ WebSockets not available. Install with: pip install websockets")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwilioMediaStreamsServer:
    """Twilio Media Streams server with barge-in capability"""
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        tts_provider: Optional[Callable[[str], bytes]] = None,
        stt_callback: Optional[Callable[[bytes], None]] = None,
        vad_aggressiveness: int = 2,
        chunk_ms: int = 120
    ):
        """
        Initialize the Media Streams server
        
        Args:
            host: Host to bind to
            port: Port to listen on
            tts_provider: Function that takes text and returns WAV bytes
            stt_callback: Function to process incoming audio for STT
            vad_aggressiveness: VAD sensitivity (0-3, higher = more aggressive)
            chunk_ms: TTS chunk size in milliseconds
        """
        self.host = host
        self.port = port
        self.tts_provider = tts_provider or self._default_tts_provider
        self.stt_callback = stt_callback
        self.chunk_ms = chunk_ms
        self.sample_rate = 8000  # Twilio Media Streams use 8kHz µ-law
        
        # VAD setup
        if VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(vad_aggressiveness)
        else:
            self.vad = None
            logger.warning("VAD not available, using energy-based detection")
        
        # Connection state
        self._ws = None
        self._stream_sid = None
        self._is_playing = False
        self._play_lock = asyncio.Lock()
        self._play_cancel = asyncio.Event()
        
        # Audio buffering for STT
        self._audio_buffer = bytearray()
        self._last_audio_time = 0
        
        logger.info(f"🎤 Media Streams server initialized on {host}:{port}")
    
    async def start_server(self):
        """Start the WebSocket server"""
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("WebSockets not available. Install with: pip install websockets")
        
        logger.info(f"🚀 Starting Media Streams server on {self.host}:{self.port}")
        
        async with websockets.serve(self._handle_websocket, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    async def _handle_websocket(self, websocket, path):
        """Handle WebSocket connection from Twilio"""
        logger.info(f"🔗 New WebSocket connection: {path}")
        self._ws = websocket
        self._stream_sid = None
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    logger.debug("Non-JSON message ignored")
                    continue
                
                await self._process_message(data)
                
        except websockets.exceptions.ConnectionClosedOK:
            logger.info("🔌 WebSocket connection closed cleanly")
        except Exception as e:
            logger.error(f"❌ WebSocket error: {e}")
        finally:
            self._cleanup_connection()
    
    async def _process_message(self, data: Dict[str, Any]):
        """Process incoming WebSocket message from Twilio"""
        event = data.get("event")
        
        if event == "start":
            self._stream_sid = data["start"].get("streamSid")
            logger.info(f"🎬 Stream started: {self._stream_sid}")
            
        elif event == "media":
            await self._process_audio_data(data["media"])
            
        elif event == "stop":
            logger.info("🛑 Stream stopped by Twilio")
            self._cleanup_connection()
    
    @log_timing_async("Audio frame processing")
    async def _process_audio_data(self, media_data: Dict[str, Any]):
        """Process incoming audio data from Twilio"""
        try:
            # Decode base64 µ-law audio
            payload_b64 = media_data["payload"]
            mu_law_bytes = base64.b64decode(payload_b64)
            
            # Convert µ-law to 16-bit PCM
            pcm_bytes = audioop.ulaw2lin(mu_law_bytes, 2)
            
            # Buffer audio for STT processing
            self._audio_buffer.extend(pcm_bytes)
            self._last_audio_time = time.time()
            
            # Process audio for STT (non-blocking)
            if self.stt_callback:
                asyncio.create_task(self._process_stt_audio(pcm_bytes))
            
            # Check for speech using VAD
            is_speech = self._detect_speech(pcm_bytes)
            
            if is_speech and self._is_playing:
                logger.info("🛑 User speech detected while bot speaking - interrupting!")
                await self._handle_interruption()
                
        except Exception as e:
            logger.error(f"❌ Audio processing error: {e}")
    
    def _detect_speech(self, pcm_bytes: bytes) -> bool:
        """Detect speech in audio using VAD or energy-based detection"""
        if not pcm_bytes:
            return False
        
        # Try WebRTC VAD first
        if self.vad:
            try:
                return self.vad.is_speech(pcm_bytes, sample_rate=self.sample_rate)
            except Exception:
                pass
        
        # Fallback to energy-based detection
        return self._energy_based_detection(pcm_bytes)
    
    def _energy_based_detection(self, pcm_bytes: bytes) -> bool:
        """Fallback energy-based speech detection"""
        if len(pcm_bytes) < 2:
            return False
        
        # Convert bytes to samples (16-bit signed)
        import struct
        samples = struct.unpack(f'<{len(pcm_bytes)//2}h', pcm_bytes)
        
        # Calculate RMS energy
        energy = sum(sample * sample for sample in samples) / len(samples)
        rms = (energy ** 0.5) / 32768.0  # Normalize to 0-1
        
        # Simple threshold
        speech_threshold = 0.01
        return rms > speech_threshold
    
    async def _process_stt_audio(self, pcm_bytes: bytes):
        """Process audio for STT (non-blocking)"""
        try:
            if self.stt_callback:
                self.stt_callback(pcm_bytes)
        except Exception as e:
            logger.error(f"❌ STT processing error: {e}")
    
    async def _handle_interruption(self):
        """Handle user interruption"""
        # Cancel current playback
        self._play_cancel.set()
        
        # Send clear command to Twilio
        await self._send_clear()
        
        logger.info("✅ Interruption handled - bot stopped speaking")
    
    async def _send_clear(self):
        """Send clear command to Twilio to stop buffered audio"""
        if not self._ws or not self._stream_sid:
            return
        
        try:
            message = {
                "event": "clear",
                "streamSid": self._stream_sid
            }
            await self._ws.send(json.dumps(message))
            logger.info("📡 Sent clear command to Twilio")
        except Exception as e:
            logger.error(f"❌ Failed to send clear command: {e}")
    
    @log_timing_async("TTS streaming to Twilio")
    async def speak_text(self, text: str):
        """Speak text using TTS with chunked streaming for interruption"""
        if not self._ws or not self._stream_sid:
            raise RuntimeError("No active Twilio Media Stream connection")
        
        async with self._play_lock:
            self._is_playing = True
            self._play_cancel.clear()
            
            try:
                logger.info(f"🎵 Starting TTS: {text[:50]}...")
                
                # Generate TTS audio
                wav_bytes = self.tts_provider(text)
                if not isinstance(wav_bytes, (bytes, bytearray)):
                    raise RuntimeError("TTS provider must return WAV bytes")
                
                # Convert WAV to µ-law chunks
                mulaw_bytes = self._wav_to_mulaw(wav_bytes)
                
                # Stream in small chunks for immediate interruption
                chunk_size = int(self.sample_rate * self.chunk_ms / 1000)
                
                for i in range(0, len(mulaw_bytes), chunk_size):
                    if self._play_cancel.is_set():
                        logger.info("🛑 TTS interrupted by user")
                        break
                    
                    chunk = mulaw_bytes[i:i + chunk_size]
                    await self._send_audio_chunk(chunk)
                    
                    # Small delay to allow VAD checks
                    await asyncio.sleep(self.chunk_ms / 1000.0 * 0.5)
                
                logger.info("✅ TTS completed")
                
            except Exception as e:
                logger.error(f"❌ TTS error: {e}")
            finally:
                self._is_playing = False
                self._play_cancel.clear()
    
    async def _send_audio_chunk(self, mulaw_chunk: bytes):
        """Send audio chunk to Twilio"""
        if not self._ws or not self._stream_sid:
            return
        
        try:
            payload = base64.b64encode(mulaw_chunk).decode('ascii')
            message = {
                "event": "media",
                "streamSid": self._stream_sid,
                "media": {"payload": payload}
            }
            await self._ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Failed to send audio chunk: {e}")
    
    def _wav_to_mulaw(self, wav_bytes: bytes) -> bytes:
        """Convert WAV bytes to µ-law format using ffmpeg"""
        try:
            process = subprocess.Popen(
                [
                    "ffmpeg",
                    "-loglevel", "error",
                    "-i", "pipe:0",
                    "-ar", str(self.sample_rate),
                    "-ac", "1",
                    "-f", "mulaw",
                    "pipe:1"
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(input=wav_bytes)
            
            if process.returncode != 0:
                logger.error(f"❌ ffmpeg conversion failed: {stderr.decode()}")
                raise RuntimeError("ffmpeg conversion failed")
            
            return stdout
            
        except FileNotFoundError:
            logger.error("❌ ffmpeg not found. Please install ffmpeg and ensure it's in PATH")
            raise RuntimeError("ffmpeg not available")
        except Exception as e:
            logger.error(f"❌ Audio conversion error: {e}")
            raise
    
    def _cleanup_connection(self):
        """Clean up connection state"""
        self._ws = None
        self._stream_sid = None
        self._is_playing = False
        self._play_cancel.set()
        self._audio_buffer.clear()
        logger.info("🧹 Connection cleaned up")
    
    def _default_tts_provider(self, text: str) -> bytes:
        """Default TTS provider (placeholder)"""
        raise NotImplementedError(
            "No TTS provider configured. Please implement a TTS provider that returns WAV bytes."
        )


# Global server instance
_media_streams_server = None


async def start_media_streams_server(host: str = "0.0.0.0", port: int = 8765):
    """Start the Media Streams server"""
    global _media_streams_server
    
    if _media_streams_server:
        logger.warning("Media Streams server already running")
        return _media_streams_server
    
    _media_streams_server = TwilioMediaStreamsServer(host=host, port=port)
    
    # Start server in background
    asyncio.create_task(_media_streams_server.start_server())
    
    logger.info(f"🚀 Media Streams server started on {host}:{port}")
    return _media_streams_server


def get_media_streams_server() -> Optional[TwilioMediaStreamsServer]:
    """Get the current Media Streams server instance"""
    return _media_streams_server


async def speak_text_async(text: str):
    """Speak text using the Media Streams server"""
    server = get_media_streams_server()
    if not server:
        raise RuntimeError("Media Streams server not running")
    
    await server.speak_text(text)


if __name__ == "__main__":
    async def main():
        server = await start_media_streams_server()
        await asyncio.Future()  # Run forever
    
    asyncio.run(main())
