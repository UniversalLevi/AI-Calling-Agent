import os
import time
import asyncio
import logging
import json
from typing import Dict
from pathlib import Path

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    from .debug_logger import logger, debug_enabled
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    def debug_enabled():
        return os.getenv('DEBUG_MODE', 'false').lower() == 'true'


app = FastAPI(title="Sara AI Calling Bot - FastAPI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_start_time = time.time()


@app.get("/")
async def root():
    return {"message": "Sara AI Calling Bot - FastAPI Server", "status": "running"}


@app.get("/health")
async def health() -> Dict:
    return {
        "status": "OK",
        "uptime": round(time.time() - _start_time, 2),
        "debug": debug_enabled(),
    }


@app.post("/voice")
@app.get("/voice")
async def voice_webhook(request: Request):
    """Twilio voice webhook - handles incoming calls"""
    try:
        # Get query parameters
        query_params = dict(request.query_params)
        realtime = query_params.get('realtime', 'false').lower() == 'true'
        media_streams = query_params.get('media_streams', 'false').lower() == 'true'
        interruption = query_params.get('interruption', 'none')
        
        logger.info(f"Voice webhook called - realtime={realtime}, media_streams={media_streams}, interruption={interruption}")
        
        # Import here to avoid circular imports
        from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
        
        response = VoiceResponse()
        
        if media_streams:
            # Media Streams mode - real-time audio streaming
            # Get the ngrok hostname from the request
            host = request.headers.get('host', request.url.hostname)
            
            # Send greeting first, then connect to media stream
            response.say("Hello! I'm Sara, your AI assistant. How can I help you today?")
            response.pause(length=1)
            
            # Connect to media stream for two-way audio
            connect = Connect()
            stream = Stream(url=f'wss://{host}/media-stream')
            connect.append(stream)
            response.append(connect)
        elif realtime:
            # Real-time mode without media streams
            response.say("Hello! I'm Sara, your AI assistant. How can I help you today?")
            response.gather(
                input='speech',
                action='/process-speech',
                method='POST',
                speechTimeout='auto'
            )
        else:
            # Basic mode
            response.say("Hello! This is Sara AI calling bot.")
        
        return Response(content=str(response), media_type="application/xml")
    
    except Exception as e:
        logger.error(f"Error in voice webhook: {e}")
        response = VoiceResponse()
        response.say("Sorry, there was an error. Please try again later.")
        return Response(content=str(response), media_type="application/xml")


@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve audio files"""
    try:
        audio_path = Path("audio_files") / filename
        if audio_path.exists():
            return FileResponse(audio_path, media_type="audio/mpeg")
        else:
            return Response(content="Audio file not found", status_code=404)
    except Exception as e:
        logger.error(f"Error serving audio {filename}: {e}")
        return Response(content="Error serving audio", status_code=500)


@app.websocket("/media-stream")
async def media_stream_websocket(websocket: WebSocket):
    """Handle Twilio Media Streams WebSocket connection"""
    await websocket.accept()
    logger.info("WebSocket connection accepted for media stream")
    
    stream_sid = None
    call_sid = None
    audio_buffer = bytearray()
    last_speech_time = 0
    is_processing = False
    
    try:
        # Import AI components
        from .mixed_stt import MixedSTTEngine
        from .mixed_ai_brain import MixedAIBrain
        from .enhanced_hindi_tts import EnhancedHindiTTS
        import base64
        import audioop
        
        stt = MixedSTTEngine()
        
        # Initialize AI brain with phone-optimized system prompt
        ai_brain = MixedAIBrain()
        # Override system prompt for phone calls
        phone_prompt = """You are Sara, a friendly AI phone assistant. You are currently on a PHONE CALL with a customer.

IMPORTANT RULES:
1. Keep responses SHORT and CONVERSATIONAL (1-2 sentences max)
2. Speak naturally as if talking on the phone
3. Support BOTH Hindi and English - detect user's language and respond in the SAME language
4. If user speaks Hindi, respond in Hindi. If English, respond in English
5. NEVER say "you can write to me" - this is a VOICE call, not text chat
6. Ask ONE question at a time
7. Be warm, helpful, and professional
8. For Hindi: Use natural Hinglish or pure Hindi as appropriate

Remember: This is a LIVE PHONE CONVERSATION. Keep it natural and conversational!"""
        
        # Set the phone-optimized prompt
        if hasattr(ai_brain, 'provider') and hasattr(ai_brain.provider, 'conversation_history'):
            ai_brain.provider.conversation_history = [
                {"role": "system", "content": phone_prompt}
            ]
        
        tts = EnhancedHindiTTS()
        
        logger.info("AI components initialized for media stream")
        
        async def send_audio_to_twilio(ws: WebSocket, sid: str, audio_filename: str):
            """Convert MP3 to µ-law and send to Twilio via WebSocket"""
            try:
                audio_path = Path("audio_files") / audio_filename
                if not audio_path.exists():
                    logger.error(f"Audio file not found: {audio_filename}")
                    return
                
                logger.info(f"Converting and sending audio: {audio_filename}")
                
                # Convert MP3 to WAV using pydub
                from pydub import AudioSegment
                
                # Load MP3
                audio = AudioSegment.from_mp3(str(audio_path))
                logger.debug(f"Loaded MP3: {len(audio)}ms, {audio.frame_rate}Hz, {audio.channels} channels")
                
                # Convert to 8kHz mono (Twilio's format)
                audio = audio.set_frame_rate(8000).set_channels(1).set_sample_width(2)
                logger.debug(f"Converted to Twilio format: 8kHz mono 16-bit")
                
                # Export as raw PCM
                pcm_data = audio.raw_data
                
                # Convert PCM to µ-law
                mulaw_data = audioop.lin2ulaw(pcm_data, 2)  # 2 = 16-bit
                logger.info(f"Converted to µ-law: {len(mulaw_data)} bytes")
                
                # Send in chunks (20ms chunks = 160 bytes at 8kHz µ-law)
                chunk_size = 160
                chunks_sent = 0
                for i in range(0, len(mulaw_data), chunk_size):
                    chunk = mulaw_data[i:i + chunk_size]
                    
                    # Encode to base64
                    payload = base64.b64encode(chunk).decode('utf-8')
                    
                    # Send to Twilio
                    await ws.send_json({
                        "event": "media",
                        "streamSid": sid,
                        "media": {
                            "payload": payload
                        }
                    })
                    
                    chunks_sent += 1
                    
                    # Small delay to simulate real-time streaming (20ms per chunk)
                    await asyncio.sleep(0.02)
                
                logger.info(f"✅ Successfully sent {chunks_sent} chunks ({len(mulaw_data)} bytes) to Twilio")
                
                # Mark audio as sent
                return True
                
            except ImportError as e:
                logger.error(f"Missing dependency: {e}")
                logger.error("Install with: pip install pydub")
                logger.error("Also requires ffmpeg: https://ffmpeg.org/download.html")
            except Exception as e:
                # Ignore errors if WebSocket is already closed
                if "close message has been sent" not in str(e):
                    logger.error(f"Error sending audio to Twilio: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                return False
        
        async def process_speech():
            """Process accumulated audio buffer"""
            nonlocal audio_buffer, is_processing
            
            if len(audio_buffer) < 8000:  # Need at least 0.5 seconds of audio
                return
            
            is_processing = True
            
            try:
                # Convert PCM to WAV format for STT
                pcm_data = bytes(audio_buffer)
                
                # Save to temporary WAV file
                import wave
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
                    wav_path = tmp_wav.name
                    with wave.open(wav_path, 'wb') as wav_file:
                        wav_file.setnchannels(1)  # Mono
                        wav_file.setsampwidth(2)  # 16-bit
                        wav_file.setframerate(8000)  # 8kHz (Twilio rate)
                        wav_file.writeframes(pcm_data)
                
                logger.info(f"Processing {len(pcm_data)} bytes of audio")
                
                # Transcribe
                transcript = stt.transcribe(wav_path)
                
                # Clean up temp file
                import os
                try:
                    os.unlink(wav_path)
                except:
                    pass
                
                if transcript and transcript.strip():
                    logger.info(f"User said: {transcript}")
                    
                    # Detect language and get AI response
                    from .language_detector import detect_language
                    detected_lang = detect_language(transcript)
                    logger.info(f"Detected language: {detected_lang}")
                    
                    # Get AI response with language context
                    ai_response = ai_brain.ask(transcript, language=detected_lang)
                    logger.info(f"AI response: {ai_response}")
                    
                    # Generate TTS
                    audio_file = tts.speak_openai(ai_response)
                    
                    if audio_file:
                        logger.info(f"Generated TTS: {audio_file}")
                        
                        # Send audio back to user through WebSocket
                        await send_audio_to_twilio(websocket, stream_sid, audio_file)
                    
                    # Clear buffer after processing
                    audio_buffer.clear()
                else:
                    logger.debug("No speech detected in audio")
                
            except Exception as e:
                logger.error(f"Error processing speech: {e}")
                import traceback
                traceback.print_exc()
            finally:
                is_processing = False
        
        # Process incoming messages
        while True:
            try:
                # Receive message from Twilio
                message = await websocket.receive_text()
                data = json.loads(message)
                
                event = data.get("event")
                
                if event == "start":
                    stream_sid = data["start"].get("streamSid")
                    call_sid = data["start"].get("callSid")
                    logger.info(f"Stream started: {stream_sid}, Call: {call_sid}")
                    logger.info("Media stream ready - listening for user speech")
                
                elif event == "media":
                    # Process incoming audio (user speaking)
                    media_data = data.get("media", {})
                    payload = media_data.get("payload", "")
                    
                    if payload:
                        # Decode µ-law audio to PCM
                        mu_law_bytes = base64.b64decode(payload)
                        pcm_bytes = audioop.ulaw2lin(mu_law_bytes, 2)  # Convert to 16-bit PCM
                        
                        # Add to buffer
                        audio_buffer.extend(pcm_bytes)
                        last_speech_time = time.time()
                        
                        # Process when we have enough audio and there's a pause
                        # Wait for 1.5 seconds of silence or 8 seconds of continuous speech
                        if not is_processing:
                            buffer_duration = len(audio_buffer) / (8000 * 2)  # 8kHz, 16-bit
                            time_since_last = time.time() - last_speech_time
                            
                            # Only process if we have meaningful audio (>1.5s) and user paused (>1.5s silence)
                            # OR if buffer is getting too large (>8s)
                            if buffer_duration > 8.0 or (buffer_duration > 1.5 and time_since_last > 1.5):
                                logger.info(f"Processing speech ({buffer_duration:.1f}s of audio, {time_since_last:.1f}s since last frame)")
                                asyncio.create_task(process_speech())
                
                elif event == "stop":
                    logger.info("Stream stopped by Twilio")
                    # Process any remaining audio
                    if len(audio_buffer) > 0 and not is_processing:
                        await process_speech()
                    break
                
            except json.JSONDecodeError:
                logger.error("Invalid JSON received")
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()
                break
        
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in media stream: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info(f"Media stream connection closed (SID: {stream_sid})")


@app.post("/status")
async def call_status(request: Request):
    """Handle Twilio call status callbacks"""
    try:
        form_data = await request.form()
        call_sid = form_data.get('CallSid', 'Unknown')
        call_status = form_data.get('CallStatus', 'Unknown')
        
        logger.info(f"Call status update - SID: {call_sid}, Status: {call_status}")
        
        # Log to dashboard if available
        try:
            from .dashboard_integration import sales_dashboard
            if sales_dashboard and hasattr(sales_dashboard, 'log_call_end'):
                # Log call completion
                if call_status in ['completed', 'busy', 'failed', 'no-answer']:
                    sales_dashboard.log_call_end(call_sid, call_status)
        except Exception as e:
            logger.debug(f"Dashboard logging skipped: {e}")
        
        return Response(content="OK", status_code=200)
    
    except Exception as e:
        logger.error(f"Error in status callback: {e}")
        return Response(content="Error", status_code=500)


async def _warm_tts_cache_async():
    try:
        from .tts_cache import initialize_tts_cache
        from .enhanced_hindi_tts import EnhancedHindiTTS

        tts = EnhancedHindiTTS()

        def tts_func(text: str) -> str:
            # Returns generated file path (mp3)
            return tts.speak_openai(text) or ""

        initialize_tts_cache(tts_func)
        logger.info("TTS cache warmup completed")
    except Exception as e:
        logger.error(f"TTS cache warmup failed: {e}")


async def _start_health_monitor():
    try:
        from .health_monitor import start_health_monitor
        await start_health_monitor()
    except Exception as e:
        logger.error(f"Health monitor start failed: {e}")


@app.on_event("startup")
async def on_startup():
    if debug_enabled():
        asyncio.create_task(_warm_tts_cache_async())
        asyncio.create_task(_start_health_monitor())


def run(host: str = "0.0.0.0", port: int = 8000):
    """Run FastAPI server on port 8000 (default bot port)"""
    import uvicorn
    logger.info(f"Starting FastAPI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


