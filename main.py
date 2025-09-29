#!/usr/bin/env python3
"""
AI Calling Bot - Complete Self-Contained Launcher
===============================================

This is the ONLY file you need to run. It handles everything:
- Audio server startup
- Voice bot server startup  
- Ngrok tunnel startup
- Clean menu system
- Mixed language support (Hindi + English)

Just run: python main.py
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path
import signal
import requests
import warnings
from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")
    print("⚠️ Environment variables not loaded from .env file")

# Clean up old audio files on startup
def cleanup_startup_audio():
    """Clean up old audio files on startup"""
    try:
        import time
        audio_dir = Path("audio_files")
        if not audio_dir.exists():
            return
        
        # Delete files older than 5 minutes (300 seconds)
        current_time = time.time()
        max_age = 300  # 5 minutes
        
        deleted_count = 0
        for file_path in audio_dir.glob("*.mp3"):
            if current_time - file_path.stat().st_mtime > max_age:
                file_path.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"🧹 Startup cleanup: Removed {deleted_count} old audio files (older than 5 minutes)")
        else:
            print("🧹 Startup cleanup: No old audio files to remove")
            
    except Exception as e:
        print(f"⚠️ Startup cleanup error: {e}")

# Run startup cleanup
cleanup_startup_audio()

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add src to path
sys.path.append('src')

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Import realtime voice bot components
try:
    from src.realtime_voice_bot import RealtimeVoiceBot, TwilioRealtimeIntegration
    REALTIME_AVAILABLE = True
    print("✅ Realtime voice capabilities available")
except ImportError as e:
    REALTIME_AVAILABLE = False
    print(f"⚠️ Realtime voice capabilities not available: {e}")

# Import Media Streams system
try:
    from src.twilio_media_streams import start_media_streams_server, get_media_streams_server, speak_text_async
    from src.tts_adapter import get_tts_provider, get_stt_callback
    MEDIA_STREAMS_AVAILABLE = True
    print("✅ Media Streams system available")
except ImportError as e:
    MEDIA_STREAMS_AVAILABLE = False
    print(f"⚠️ Media Streams not available: {e}")

# Global variables
voice_bot_app = None
audio_server_app = None
ngrok_process = None
running_services = {}
realtime_voice_bot = None
twilio_realtime_integration = None

# =============================================================================
# AUDIO SERVER (Built-in)
# =============================================================================
def create_audio_server():
    """Create the audio server Flask app"""
    audio_app = Flask(__name__, instance_relative_config=True)
    
    @audio_app.route('/health')
    def audio_health():
        return "Audio Server OK", 200
    
    @audio_app.route('/audio/<filename>')
    def serve_audio(filename):
        """Serve audio files"""
        audio_dir = Path("audio_files")
        file_path = audio_dir / filename
        
        if file_path.exists():
            print(f"🔊 Serving audio: {filename}")
            return send_file(file_path, mimetype='audio/mpeg')
        else:
            return "Audio file not found", 404
    
    return audio_app

# =============================================================================
# VOICE BOT SERVER (Built-in)
# =============================================================================
def create_voice_bot_server():
    """Create the voice bot server Flask app"""
    bot_app = Flask(__name__)
    bot_app.config['DEBUG'] = True  # Enable debug mode
    
    # Initialize AI components
    print("🤖 Initializing Enhanced AI components...")
    
    # Ensure audio files directory exists
    audio_dir = Path("audio_files")
    audio_dir.mkdir(exist_ok=True)
    print(f"📁 Audio directory ready: {audio_dir.absolute()}")
    
    try:
        from src.mixed_stt import MixedSTTEngine
        from src.mixed_ai_brain import MixedAIBrain
        from src.language_detector import detect_language
        from src.enhanced_hindi_tts import speak_mixed_enhanced
        
        stt = MixedSTTEngine()
        gpt = MixedAIBrain()
        print("✅ Enhanced AI components ready!")
        
        bot_app.stt = stt
        bot_app.gpt = gpt
        bot_app.enhanced_tts = speak_mixed_enhanced
        # Per-call language state (CallSid -> 'en' | 'hi' | 'mixed')
        bot_app.call_language = {}
        
    except Exception as e:
        print(f"❌ Error initializing AI components: {e}")
        bot_app.stt = None
        bot_app.gpt = None
        bot_app.enhanced_tts = None
    
    @bot_app.route('/health')
    def bot_health():
        return "Voice Bot Server OK", 200
    
    @bot_app.route('/audio/<filename>')
    def serve_bot_audio(filename):
        """Serve audio files to Twilio"""
        audio_dir = Path("audio_files")
        audio_dir.mkdir(exist_ok=True)  # Ensure directory exists
        file_path = audio_dir / filename
        
        if file_path.exists():
            print(f"🔊 Serving audio file: {filename}")
            # Determine mimetype based on extension
            if filename.endswith('.mp3'):
                return send_file(file_path, mimetype='audio/mpeg')
            elif filename.endswith('.wav'):
                return send_file(file_path, mimetype='audio/wav')
            else:
                return send_file(file_path, mimetype='audio/mpeg')
        else:
            print(f"❌ Audio file not found: {filename}")
            return "Audio file not found", 404
    
    @bot_app.route('/voice', methods=['POST'])
    def voice():
        response = VoiceResponse()
        
        caller = request.form.get('From', 'Unknown')
        call_sid = request.form.get('CallSid')
        print(f"📞 Incoming call from: {caller}")
        print(f"🔍 DEBUG: Request form data: {dict(request.form)}")
        print(f"🔍 DEBUG: Request args: {dict(request.args)}")
        
        # Check if realtime mode is available and requested
        realtime_mode = request.args.get('realtime', 'false').lower() == 'true'
        print(f"🔍 Realtime mode requested: {realtime_mode}")
        print(f"🔍 REALTIME_AVAILABLE: {REALTIME_AVAILABLE}")
        
        if REALTIME_AVAILABLE and realtime_mode:
            # Use enhanced real-time conversation with shorter timeouts
            print("🚀 Starting realtime conversation mode")
            
            # Send chunked greeting for better interruption handling
            greeting_parts = [
                "Hi there!",
                "I am Sara.",
                "How can I help you today?"
            ]
            
            # Play greeting in small chunks with pauses for interruption
            for i, part in enumerate(greeting_parts):
                response.say(part, voice='Polly.Joanna')
                # Add short pause between chunks (except for last part)
                if i < len(greeting_parts) - 1:
                    response.pause(length=0.2)
            
            print(f"🎵 Playing chunked greeting: {len(greeting_parts)} parts")
            
                # Add natural pause after greeting
            response.pause(length=0.2)
            
            # Use optimized gather settings for better speech recognition and interruption
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=1,  # Very short timeout for quick interruption detection
                speech_timeout='auto',
                language='en-IN',  # Start with English, will switch based on detection
                partial_result_callback='/partial_speech',
                enhanced='true',  # Use enhanced speech recognition
                profanity_filter='false',  # Don't filter speech
                num_digits=0,  # Don't expect digits
                finish_on_key='#'  # Allow finishing with # key
            )
            response.append(gather)
            
            # Add a fallback message if no speech is detected
            response.say("I didn't hear anything. Please try again.", voice='Polly.Joanna', language='en-IN')
            
            # Initialize realtime voice bot for this call
            global realtime_voice_bot, twilio_realtime_integration
            if not realtime_voice_bot:
                realtime_voice_bot = RealtimeVoiceBot()
                twilio_realtime_integration = TwilioRealtimeIntegration(realtime_voice_bot)
            
            return str(response)
        else:
            # Use traditional turn-based conversation
            print("📞 Starting traditional conversation mode")
        
        # Mixed language greeting
        greeting = "Hello! I'm your AI assistant. आज मैं आपकी कैसे मदद कर सकता हूं?"
        response.say(greeting)
        
        # Default to English-India initially; switch after first detection
        initial_language_code = 'en-IN'
        if call_sid and call_sid in bot_app.call_language:
            detected_lang = bot_app.call_language[call_sid]
            if detected_lang in ['hi', 'mixed']:
                initial_language_code = 'hi-IN'
        
        # Gather speech input
        gather = response.gather(
            input='speech',
            action='/process_speech',
            timeout=10,
            speech_timeout='auto',
            language=initial_language_code
        )
        response.append(gather)
        response.say("I didn't hear anything. Please try again.")
        
        return str(response)
    
    @bot_app.route('/voice_media_streams', methods=['POST'])
    def voice_media_streams():
        """Handle incoming calls with Media Streams barge-in"""
        print("🎬 Media Streams call received")
        
        response = VoiceResponse()
        
        # Connect to Media Streams WebSocket
        ngrok_url = get_ngrok_url()
        if ngrok_url and MEDIA_STREAMS_AVAILABLE:
            # Replace http with wss for WebSocket
            ws_url = ngrok_url.replace('http://', 'ws://').replace('https://', 'wss://')
            stream_url = f"{ws_url}/media_streams"
            
            response.connect().stream(url=stream_url)
            print(f"🔗 Connecting to Media Streams: {stream_url}")
        else:
            response.say("I'm sorry, the Media Streams service is not available right now.")
        
        return str(response)
    
    @bot_app.route('/process_speech', methods=['POST'])
    def process_speech():
        response = VoiceResponse()
        speech_result = request.form.get('SpeechResult', '')
        caller = request.form.get('From', 'Unknown')
        call_sid = request.form.get('CallSid')
        
        print(f"🎤 Caller {caller} said: {speech_result}")
        
        if speech_result:
            try:
                print(f"📝 Processing speech: '{speech_result}'")
                # Detect language
                detected_language = detect_language(speech_result)
                print(f"🌐 Detected language: {detected_language}")
                # Persist per-call language
                if call_sid:
                    bot_app.call_language[call_sid] = detected_language
                    print(f"💾 Saved language for call {call_sid}: {detected_language}")
                
                if bot_app.gpt:
                    print(f"🧠 Processing with Mixed Language AI...")
                    bot_response = bot_app.gpt.ask(speech_result, detected_language)
                    print(f"🤖 AI Bot response ({detected_language}): {bot_response}")
                else:
                    # Fallback response
                    if detected_language == 'hi':
                        bot_response = f"मैंने आपको कहते सुना: {speech_result}. यह आपके AI बॉट का टेस्ट रिस्पॉन्स है!"
                    else:
                        bot_response = f"I heard you say: {speech_result}. This is a test response from your AI bot!"
                    print(f"🤖 Fallback response ({detected_language}): {bot_response}")
                
                # Try enhanced Hindi TTS first
                if bot_app.enhanced_tts and detected_language in ['hi', 'mixed']:
                    try:
                        tts_result = bot_app.enhanced_tts(bot_response)
                        print(f"🔍 TTS result: '{tts_result}'")
                        
                        # If filename returned, build public URL via current host
                        if tts_result and (tts_result.endswith('.mp3') or tts_result.endswith('.wav')):
                            base = request.url_root.rstrip('/')
                            audio_url = f"{base}/audio/{tts_result}"
                            print(f"🎵 Using enhanced Hindi TTS: {audio_url}")
                            response.play(audio_url)
                        elif tts_result and tts_result.startswith('http'):
                            # Handle old URL format if returned
                            print(f"🎵 Using enhanced Hindi TTS (URL): {tts_result}")
                            response.play(tts_result)
                        else:
                            print(f"🗣️ Fallback to Twilio TTS (Hindi voice)")
                            response.say(bot_response, voice='Polly.Aditi')
                    except Exception as tts_error:
                        print(f"❌ Enhanced TTS failed: {tts_error}")
                        print(f"🗣️ Fallback to Twilio TTS (Hindi voice)")
                        response.say(bot_response, voice='Polly.Aditi')
                else:
                    # Use Twilio TTS for English
                    print(f"🗣️ Using Twilio TTS (English voice)")
                    response.say(bot_response, voice='Polly.Joanna')
                
            except Exception as e:
                print(f"❌ Error processing speech: {e}")
                response.say("I'm sorry, I encountered an error. Please try again.")
            
            # Ask for more input
            next_language_code = 'en-IN'
            if call_sid and bot_app.call_language.get(call_sid) in ['hi', 'mixed']:
                next_language_code = 'hi-IN'
            gather = response.gather(
                input='speech',
                action='/process_speech',
                timeout=10,
                speech_timeout='auto',
                language=next_language_code
            )
            response.append(gather)
            response.say("Is there anything else I can help you with?")
        else:
            response.say("I didn't hear anything. Please try again.")
            gather = response.gather(
                input='speech',
                action='/process_speech',
                timeout=10,
                language='en-IN'
            )
            response.append(gather)
        
        return str(response)
    
    @bot_app.route('/process_speech_realtime', methods=['POST'])
    def process_speech_realtime():
        """Enhanced real-time speech processing with interruption handling"""
        print(f"🔍 DEBUG: process_speech_realtime called")
        print(f"🔍 DEBUG: Request form data: {dict(request.form)}")
        print(f"🔍 DEBUG: Request args: {dict(request.args)}")
        response = VoiceResponse()
        speech_result = request.form.get('SpeechResult', '')
        caller = request.form.get('From', 'Unknown')
        call_sid = request.form.get('CallSid')
        
        print(f"⚡ Real-time caller {caller} said: {speech_result}")
        print(f"🔍 DEBUG: bot_app.gpt exists: {bot_app.gpt is not None}")
        
        # Check for interruption first
        interruption_detected = False
        interrupted_text = ""
        if call_sid and call_sid in bot_app.call_language:
            if isinstance(bot_app.call_language[call_sid], dict):
                interruption_detected = bot_app.call_language[call_sid].get('interruption_detected', False)
                interrupted_text = bot_app.call_language[call_sid].get('interrupted_text', '')
                # Reset interruption flags
                bot_app.call_language[call_sid]['interruption_detected'] = False
                bot_app.call_language[call_sid]['partial_speech_count'] = 0
                bot_app.call_language[call_sid]['interrupted_text'] = ''
        
        # Check for interrupted text from URL parameter (from redirect)
        interrupted_text_from_url = request.args.get('interrupted_text', '')
        if interrupted_text_from_url:
            print(f"🛑 Processing interrupted speech from URL: {interrupted_text_from_url}")
            speech_result = interrupted_text_from_url
            interruption_detected = False
            interrupted_text = ""
        
        # If interruption was detected, process the interrupted text instead
        elif interruption_detected and interrupted_text:
            print(f"🛑 Processing interrupted speech: {interrupted_text}")
            speech_result = interrupted_text
            # Reset interruption flags
            interruption_detected = False
            interrupted_text = ""
        
        if speech_result:
            try:
                # Fast language detection
                detected_language = detect_language(speech_result)
                print(f"🌐 Language: {detected_language}")
                
                # Initialize bot_response
                bot_response = ""
                
                # Store language for this call
                if call_sid:
                    if isinstance(bot_app.call_language.get(call_sid), dict):
                        bot_app.call_language[call_sid]['language'] = detected_language
                    else:
                        bot_app.call_language[call_sid] = detected_language
                
                # Fast AI processing with Sara's natural female responses
                print(f"🔍 DEBUG: About to check bot_app.gpt: {bot_app.gpt}")
                if bot_app.gpt:
                    # Check for inappropriate content first
                    from src.language_detector import detect_inappropriate_content, get_appropriate_response
                    
                    if detect_inappropriate_content(speech_result):
                        print(f"⚠️ Inappropriate content detected from {caller}")
                        bot_response = get_appropriate_response(detected_language)
                    else:
                        # Add context for Sara's natural female responses
                        enhanced_prompt = f"You are Sara, a helpful female AI assistant. Respond naturally and conversationally in {detected_language}. Be warm, friendly, and helpful. Keep responses concise but natural. Always maintain a professional and respectful tone."
                        print(f"🔍 Calling AI with prompt: {enhanced_prompt[:100]}...")
                        print(f"🔍 User input: {speech_result}")
                        bot_response = bot_app.gpt.ask(f"{enhanced_prompt}\n\nUser: {speech_result}", detected_language)
                        print(f"⚡ Sara's natural response ({detected_language}): '{bot_response}'")
                        print(f"🔍 Response type: {type(bot_response)}")
                        print(f"🔍 Response length: {len(bot_response) if bot_response else 0}")
                else:
                    # Quick fallback with Sara's responses
                    if detected_language == 'hi':
                        bot_response = f"हाँ, मैं समझ गई। {speech_result}"
                    else:
                        bot_response = f"Yes, I understand. {speech_result}"
                
                # Ensure we have a valid response (this runs regardless of AI provider)
                print(f"🔍 Validating response: '{bot_response}'")
                print(f"🔍 Validation check - not bot_response: {not bot_response}")
                print(f"🔍 Validation check - strip empty: {bot_response.strip() == '' if bot_response else 'N/A'}")
                if not bot_response or bot_response.strip() == "":
                    print(f"⚠️ Empty response detected, using fallback")
                    if detected_language == 'hi':
                        bot_response = "मैं आपकी बात समझ गई हूँ। क्या मैं आपकी और मदद कर सकती हूँ?"
                    else:
                        bot_response = "I understand what you're saying. How else can I help you today?"
                    print(f"✅ Fallback response set: '{bot_response}'")
                else:
                    print(f"✅ Response is valid: '{bot_response}'")
                
                # Generate chunked response for better interruption handling
                try:
                    # Mark bot as speaking for interruption detection
                    if call_sid:
                        bot_app.call_language[call_sid]['is_bot_speaking'] = True
                        print(f"🤖 Bot started speaking for call {call_sid}")
                    
                    # Split long responses into smaller chunks for better interruption
                    def split_response_into_chunks(text, max_chunk_length=50):
                        """Split text into smaller chunks for better interruption handling"""
                        words = text.split()
                        chunks = []
                        current_chunk = []
                        
                        for word in words:
                            if len(' '.join(current_chunk + [word])) <= max_chunk_length:
                                current_chunk.append(word)
                            else:
                                if current_chunk:
                                    chunks.append(' '.join(current_chunk))
                                current_chunk = [word]
                        
                        if current_chunk:
                            chunks.append(' '.join(current_chunk))
                        
                        return chunks
                    
                    # Split response into chunks
                    response_chunks = split_response_into_chunks(bot_response, max_chunk_length=40)
                    print(f"🔀 Split response into {len(response_chunks)} chunks")
                    
                    # Play each chunk with short pauses for interruption
                    for i, chunk in enumerate(response_chunks):
                        if detected_language in ['hi', 'mixed']:
                            response.say(chunk, voice='Polly.Aditi', language='hi-IN')
                        else:
                            response.say(chunk, voice='Polly.Joanna', language='en-IN')
                        
                        # Add short pause between chunks (except for last chunk)
                        if i < len(response_chunks) - 1:
                            response.pause(length=0.1)
                    
                    print(f"🎵 Playing chunked response: {len(response_chunks)} parts")
                    
                    # Mark bot as finished speaking
                    if call_sid:
                        bot_app.call_language[call_sid]['is_bot_speaking'] = False
                        print(f"🤖 Bot finished speaking for call {call_sid}")
                        
                except Exception as e:
                    print(f"❌ Chunked TTS error: {e}")
                    # Fallback to single response
                    if detected_language in ['hi', 'mixed']:
                        response.say(bot_response, voice='Polly.Aditi', language='hi-IN')
                    else:
                        response.say(bot_response, voice='Polly.Joanna', language='en-IN')
                    
                    # Mark bot as finished speaking even on error
                    if call_sid:
                        bot_app.call_language[call_sid]['is_bot_speaking'] = False
                
                # Add a brief pause after speaking for natural conversation flow
                response.pause(length=0.2)
                
            except Exception as e:
                print(f"❌ Real-time processing error: {e}")
                import traceback
                print("🔍 Full traceback:")
                traceback.print_exc()
                print("🔍 Request data:")
                print(f"   Speech Result: {request.form.get('SpeechResult', 'None')}")
                print(f"   Call SID: {request.form.get('CallSid', 'None')}")
                print(f"   From: {request.form.get('From', 'None')}")
                response.say("Sorry, there was an error. Please try again.")
            
            # Continue with optimized speech recognition and interruption
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=1,  # Very short timeout for immediate interruption detection
                speech_timeout='auto',
                language='en-IN' if detected_language == 'en' else 'hi-IN',
                partial_result_callback='/partial_speech',
                enhanced='true',  # Use enhanced speech recognition
                profanity_filter='false'  # Don't filter speech
            )
            response.append(gather)
            
        else:
            # No speech detected - optimized recovery with faster interruption
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=2,  # Very short timeout for faster interruption detection
                language='en-IN',
                partial_result_callback='/partial_speech',
                enhanced='true',  # Use enhanced speech recognition
                profanity_filter='false'  # Don't filter speech
            )
            response.append(gather)
        
        return str(response)
    
    @bot_app.route('/partial_speech', methods=['POST'])
    def partial_speech():
        """Handle partial speech results for interruption detection"""
        partial_result = request.form.get('UnstableSpeechResult', '')
        call_sid = request.form.get('CallSid')
        
        if partial_result and len(partial_result.strip()) > 0:
            print(f"🎤 Partial speech: {partial_result}")
            
            # Store partial speech for interruption detection
            if call_sid not in bot_app.call_language:
                bot_app.call_language[call_sid] = {}
            
            # Track partial speech confidence
            if 'partial_speech_count' not in bot_app.call_language[call_sid]:
                bot_app.call_language[call_sid]['partial_speech_count'] = 0
            
            bot_app.call_language[call_sid]['partial_speech_count'] += 1
            bot_app.call_language[call_sid]['last_partial'] = partial_result
            
            # Check if bot is currently speaking and user is interrupting
            is_bot_speaking = bot_app.call_language[call_sid].get('is_bot_speaking', False)
            
            if is_bot_speaking and bot_app.call_language[call_sid]['partial_speech_count'] >= 1:
                current_length = len(partial_result)
                last_length = len(bot_app.call_language[call_sid].get('last_partial', ''))
                
                # If speech is getting longer and more confident, it's an interruption
                if current_length > last_length and len(partial_result) > 1:
                    print(f"🛑 INTERRUPTION DETECTED! User said: {partial_result}")
                    # Mark for interruption handling
                    bot_app.call_language[call_sid]['interruption_detected'] = True
                    bot_app.call_language[call_sid]['interruption_text'] = partial_result
                    bot_app.call_language[call_sid]['is_bot_speaking'] = False  # Stop bot speaking
                    
                    # Store the interrupted text for processing
                    bot_app.call_language[call_sid]['interrupted_text'] = partial_result
                    print(f"🔄 Interruption stored: {partial_result}")
                    
                    # Trigger immediate interruption handling by returning a redirect response
                    # This will immediately stop the current audio and process the interruption
                    response = VoiceResponse()
                    ngrok_url = get_ngrok_url()
                    if ngrok_url:
                        response.redirect(f"{ngrok_url}/process_speech_realtime?interrupted_text={partial_result}")
                    else:
                        response.say("I'm sorry, there was an error processing your interruption.")
                    return str(response)
        
        return '', 200
    
    @bot_app.route('/interrupt', methods=['POST'])
    def handle_interruption():
        """Handle interruption by redirecting to process interrupted speech"""
        call_sid = request.form.get('CallSid')
        
        if call_sid and call_sid in bot_app.call_language:
            interrupted_text = bot_app.call_language[call_sid].get('interrupted_text', '')
            if interrupted_text:
                print(f"🛑 Handling interruption for call {call_sid}: {interrupted_text}")
                
                # Create a response that immediately processes the interrupted speech
                response = VoiceResponse()
                
                # Stop any current audio and immediately process the interruption
                response.say("", voice='Polly.Joanna')  # Empty say to stop current audio
                
                # Redirect to process the interrupted speech
                ngrok_url = get_ngrok_url()
                if ngrok_url:
                    response.redirect(f"{ngrok_url}/process_speech_realtime?interrupted_text={interrupted_text}")
                else:
                    response.say("I'm sorry, there was an error processing your interruption.")
                
                return str(response)
        
        # Fallback response
        response = VoiceResponse()
        response.say("I didn't catch that. Please try again.")
        return str(response)
    
    @bot_app.route('/audio/<filename>')
    def serve_audio(filename):
        """Serve generated audio files to Twilio"""
        try:
            from flask import send_from_directory, Response
            audio_dir = Path("audio_files")
            
            if not audio_dir.exists():
                print(f"❌ Audio directory not found: {audio_dir}")
                return "Audio directory not found", 404
                
            audio_file = audio_dir / filename
            if not audio_file.exists():
                print(f"❌ Audio file not found: {audio_file}")
                return "Audio file not found", 404
            
            print(f"🎵 Serving audio file: {filename}")
            return send_from_directory(str(audio_dir), filename, mimetype='audio/mpeg')
            
        except Exception as e:
            print(f"❌ Audio serving error: {e}")
            return Response("Error serving audio", status=500)
    
    @bot_app.route('/status', methods=['POST'])
    def status():
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        print(f"📊 Call {call_sid} status: {call_status}")
        return "OK"
    
    @bot_app.route('/media/<call_sid>', methods=['POST'])
    def handle_media_stream(call_sid):
        """Handle Twilio Media Streams for real-time audio processing"""
        try:
            media_data = request.get_json()
            
            if media_data and twilio_realtime_integration:
                twilio_realtime_integration.handle_media_stream(call_sid, media_data)
            
            return '', 200
            
        except Exception as e:
            print(f"❌ Error handling media stream: {e}")
            return '', 500
    
    @bot_app.route('/voice_realtime', methods=['POST'])
    def voice_realtime():
        """Enhanced voice endpoint with automatic realtime mode"""
        response = VoiceResponse()
        
        caller = request.form.get('From', 'Unknown')
        call_sid = request.form.get('CallSid')
        print(f"📞 Realtime call from: {caller}")
        
        if REALTIME_AVAILABLE:
            # Start Media Stream for real-time audio
            from twilio.twiml.voice_response import Connect, Stream
            connect = Connect()
            stream = Stream(url=f'{request.url_root.rstrip("/")}/media/{call_sid}')
            connect.append(stream)
            response.append(connect)
            
            # Initialize realtime voice bot for this call
            global realtime_voice_bot, twilio_realtime_integration
            if not realtime_voice_bot:
                realtime_voice_bot = RealtimeVoiceBot()
                twilio_realtime_integration = TwilioRealtimeIntegration(realtime_voice_bot)
            
            print("🚀 Realtime conversation mode activated")
        else:
            response.say("I'm sorry, realtime mode is not available. Please try again later.")
        
        return str(response)
    
    return bot_app

# =============================================================================
# SERVICE MANAGEMENT
# =============================================================================
def start_audio_server():
    """Start the audio server in a separate thread"""
    global audio_server_app
    
    if 'audio_server' in running_services:
        print("✅ Audio server already running!")
        return True
    
    try:
        audio_server_app = create_audio_server()
        
        def run_audio_server():
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            audio_server_app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
        
        audio_thread = threading.Thread(target=run_audio_server, daemon=True)
        audio_thread.start()
        
        # Wait for server to start
        for i in range(10):
            try:
                response = requests.get("http://localhost:5001/health", timeout=1)
                if response.status_code == 200:
                    running_services['audio_server'] = audio_thread
                    print("✅ Audio server started on port 5001!")
                    return True
            except:
                time.sleep(0.5)
        
        print("❌ Audio server failed to start")
        return False
        
    except Exception as e:
        print(f"❌ Error starting audio server: {e}")
        return False

def start_media_streams_server():
    """Start the Media Streams server for barge-in functionality"""
    if not MEDIA_STREAMS_AVAILABLE:
        print("❌ Media Streams not available")
        return False
    
    try:
        import asyncio
        import threading
        
        def run_media_streams_server():
            """Run Media Streams server in background thread"""
            try:
                # Create server with TTS and STT adapters
                from src.twilio_media_streams import TwilioMediaStreamsServer
                from src.tts_adapter import get_tts_provider, get_stt_callback
                
                server = TwilioMediaStreamsServer(
                    host="0.0.0.0",
                    port=8765,
                    tts_provider=get_tts_provider(),
                    stt_callback=get_stt_callback(),
                    vad_aggressiveness=2,
                    chunk_ms=120
                )
                
                # Run the server
                asyncio.run(server.start_server())
                
            except Exception as e:
                print(f"❌ Media Streams server error: {e}")
        
        # Start server in background thread
        media_thread = threading.Thread(target=run_media_streams_server, daemon=True)
        media_thread.start()
        
        print("✅ Media Streams server started on port 8765")
        return True
        
    except Exception as e:
        print(f"❌ Failed to start Media Streams server: {e}")
        return False

def start_voice_bot_server():
    """Start the voice bot server in a separate thread"""
    global voice_bot_app
    
    if 'voice_bot_server' in running_services:
        print("✅ Voice bot server already running!")
        return True
    
    try:
        voice_bot_app = create_voice_bot_server()
        
        def run_voice_bot_server():
            import logging
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            voice_bot_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
        bot_thread = threading.Thread(target=run_voice_bot_server, daemon=True)
        bot_thread.start()
        
        # Wait for server to start
        for i in range(15):
            try:
                response = requests.get("http://localhost:5000/health", timeout=1)
                if response.status_code == 200:
                    running_services['voice_bot_server'] = bot_thread
                    print("✅ Voice bot server started on port 5000!")
                    return True
            except:
                time.sleep(1)
        
        print("❌ Voice bot server failed to start")
        return False
        
    except Exception as e:
        print(f"❌ Error starting voice bot server: {e}")
        return False

def start_ngrok():
    """Start ngrok tunnel"""
    global ngrok_process
    
    if 'ngrok' in running_services:
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            print(f"✅ Ngrok already running: {ngrok_url}")
            return ngrok_url
    
    try:
        # Start ngrok
        ngrok_process = subprocess.Popen(['ngrok', 'http', '5000'], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
        
        # Wait for ngrok to start
        for i in range(15):
            time.sleep(1)
            ngrok_url = get_ngrok_url()
            if ngrok_url:
                running_services['ngrok'] = ngrok_process
                print(f"✅ Ngrok tunnel active: {ngrok_url}")
                return ngrok_url
            print(f"⏳ Waiting for ngrok... ({i+1}/15)")
        
        print("❌ Ngrok failed to start within 15 seconds")
        return None
        
    except Exception as e:
        print(f"❌ Error starting ngrok: {e}")
        return None

def get_ngrok_url():
    """Get the current ngrok URL"""
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
        if response.status_code == 200:
            tunnels = response.json()
            if tunnels.get('tunnels'):
                return tunnels['tunnels'][0]['public_url']
    except:
        pass
    return None

# =============================================================================
# PHONE CALL FUNCTIONALITY
# =============================================================================
def make_call(phone_number):
    """Make a call to the specified phone number"""
    print(f"\n📞 Calling: {phone_number}")
    
    try:
        from twilio.rest import Client
        
        # Get credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_number]):
            print("❌ Missing Twilio credentials")
            return False
        
        ngrok_url = get_ngrok_url()
        if not ngrok_url:
            print("❌ Ngrok not running")
            return False
        
        webhook_url = f"{ngrok_url}/voice"
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Update webhook
        print("🔄 Updating webhook...")
        incoming_phone_number = client.incoming_phone_numbers.list(
            phone_number=twilio_number
        )[0]
        incoming_phone_number.update(voice_url=webhook_url)
        
        # Make the call
        print("📞 Initiating call...")
        call = client.calls.create(
            to=phone_number,
            from_=twilio_number,
            url=webhook_url
        )
        
        print("✅ Call initiated!")
        print(f"📞 SID: {call.sid}")
        print("🎯 Phone should ring!")
        print("💬 Speak Hindi or English!")
        
        return True
        
    except Exception as e:
        print(f"❌ Call failed: {e}")
        return False

def make_realtime_call(phone_number):
    """Make a real-time call with interruption handling"""
    print(f"\n⚡ Making real-time call to: {phone_number}")
    
    try:
        from twilio.rest import Client
        
        # Get credentials
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_number]):
            print("❌ Missing Twilio credentials")
            return False
        
        ngrok_url = get_ngrok_url()
        if not ngrok_url:
            print("❌ Ngrok not running")
            return False
        
        # Use the regular voice endpoint with realtime parameter
        webhook_url = f"{ngrok_url}/voice?realtime=true"
        print(f"🔗 Webhook URL: {webhook_url}")
        
        # Initialize Twilio client
        client = Client(account_sid, auth_token)
        
        # Update webhook
        print("🔄 Updating webhook for real-time mode...")
        incoming_phone_number = client.incoming_phone_numbers.list(
            phone_number=twilio_number
        )[0]
        incoming_phone_number.update(voice_url=webhook_url)
        
        # Make the call
        print("📞 Initiating real-time call...")
        call = client.calls.create(
            to=phone_number,
            from_=twilio_number,
            url=webhook_url
        )
        
        print("✅ Real-time call initiated!")
        print(f"📞 SID: {call.sid}")
        print("🎯 Phone should ring!")
        print("⚡ Real-time conversation mode active!")
        print("💬 Speak naturally - you can interrupt the bot!")
        
        return True
        
    except Exception as e:
        print(f"❌ Real-time call failed: {e}")
        return False

# =============================================================================
# ENVIRONMENT CHECK
# =============================================================================
def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment setup...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'TWILIO_ACCOUNT_SID', 
        'TWILIO_AUTH_TOKEN',
        'TWILIO_PHONE_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == "REPLACE_ME":
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("📝 Please update your .env file with the required values.")
        return False
    
    print("✅ Environment variables configured!")
    return True

# =============================================================================
# MENU SYSTEM
# =============================================================================
def show_status():
    """Show system status"""
    print("\n🔍 SYSTEM STATUS")
    print("=" * 40)
    
    # Check services
    audio_ok = 'audio_server' in running_services
    bot_ok = 'voice_bot_server' in running_services
    ngrok_url = get_ngrok_url()
    
    print(f"Audio Server: {'✅ RUNNING' if audio_ok else '❌ STOPPED'}")
    print(f"Voice Bot Server: {'✅ RUNNING' if bot_ok else '❌ STOPPED'}")
    print(f"Ngrok Tunnel: {'✅ ACTIVE' if ngrok_url else '❌ STOPPED'}")
    
    if ngrok_url:
        print(f"Webhook URL: {ngrok_url}/voice")
    
    print(f"Running Services: {len(running_services)}")
    print("=" * 40)

def clear_screen():
    """Clear the screen for cleaner output"""
    os.system('cls' if os.name == 'nt' else 'clear')

def make_media_streams_call(phone_number: str):
    """Make a call with Media Streams barge-in functionality"""
    if not MEDIA_STREAMS_AVAILABLE:
        print("❌ Media Streams not available")
        return
    
    print(f"🎬 Making Media Streams call to: {phone_number}")
    
    # Start Media Streams server if not already running
    if not start_media_streams_server():
        print("❌ Failed to start Media Streams server")
        return
    
    # Update webhook to use Media Streams endpoint
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ Ngrok not available")
        return
    
    webhook_url = f"{ngrok_url}/voice_media_streams"
    print(f"🔗 Webhook URL: {webhook_url}")
    
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_phone]):
            print("❌ Twilio credentials not found")
            return
        
        client = Client(account_sid, auth_token)
        
        # Update webhook for Media Streams
        incoming_numbers = client.incoming_phone_numbers.list(phone_number=twilio_phone)
        if incoming_numbers:
            incoming_numbers[0].update(voice_url=webhook_url)
            print("🔄 Updated webhook for Media Streams mode")
        
        # Make the call
        call = client.calls.create(
            to=phone_number,
            from_=twilio_phone,
            url=webhook_url
        )
        
        print(f"✅ Media Streams call initiated!")
        print(f"📞 SID: {call.sid}")
        print(f"🎯 Phone should ring!")
        print(f"🎬 Media Streams barge-in active!")
        print(f"💬 Bot can be interrupted immediately!")
        
    except Exception as e:
        print(f"❌ Error making Media Streams call: {e}")

def main_menu():
    """Main menu system"""
    while True:
        clear_screen()
        print("🤖 AI CALLING BOT")
        print("🌐 Hindi + English Support")
        if REALTIME_AVAILABLE:
            print("⚡ Real-time Conversation Mode Available")
        if MEDIA_STREAMS_AVAILABLE:
            print("🎬 Media Streams Barge-In Available")
        print("-" * 30)
        print("1. 📞 Call a number")
        print("2. 📱 Call me")
        if REALTIME_AVAILABLE:
            print("3. ⚡ Call with real-time mode")
            print("4. 🎤 Test real-time locally")
            if MEDIA_STREAMS_AVAILABLE:
                print("5. 🎬 Call with Media Streams barge-in")
                print("6. 🔍 Status")
                print("7. 🧪 Test")
                print("8. 🎤 Voice bot")
                print("9. ❌ Exit")
            else:
                print("5. 🔍 Status")
                print("6. 🧪 Test")
                print("7. 🎤 Voice bot")
                print("8. ❌ Exit")
        else:
            if MEDIA_STREAMS_AVAILABLE:
                print("3. 🎬 Call with Media Streams barge-in")
                print("4. 🔍 Status")
                print("5. 🧪 Test")
                print("6. 🎤 Voice bot")
                print("7. ❌ Exit")
            else:
                print("3. 🔍 Status")
                print("4. 🧪 Test")
                print("5. 🎤 Voice bot")
                print("6. ❌ Exit")
        print("-" * 30)
        
        max_choice = 9 if REALTIME_AVAILABLE and MEDIA_STREAMS_AVAILABLE else (8 if REALTIME_AVAILABLE else (7 if MEDIA_STREAMS_AVAILABLE else 6))
        choice = input(f"Choice (1-{max_choice}): ").strip()
        
        if choice == "1":
            phone = input("📞 Phone number: ").strip()
            if phone:
                make_call(phone)
                input("\nPress Enter to continue...")
            
        elif choice == "2":
            # Replace with your own number for testing
            test_number = input("📞 Enter your phone number for testing: ").strip()
            if test_number:
                make_call(test_number)
            input("\nPress Enter to continue...")
            
        elif choice == "3" and REALTIME_AVAILABLE:
            phone = input("📞 Phone number for real-time call: ").strip()
            if phone:
                make_realtime_call(phone)
                input("\nPress Enter to continue...")
            
        elif choice == "4" and REALTIME_AVAILABLE:
            print("🎤 Starting real-time voice bot locally...")
            print("💡 Speak naturally - the bot will respond in real-time!")
            print("💡 You can interrupt the bot while it's speaking!")
            try:
                subprocess.run([sys.executable, "-m", "src.realtime_voice_bot"])
            except KeyboardInterrupt:
                print("\n🎤 Stopped.")
            input("\nPress Enter to continue...")
            
        elif choice == "5" and REALTIME_AVAILABLE and MEDIA_STREAMS_AVAILABLE:
            phone = input("📞 Phone number for Media Streams call: ").strip()
            if phone:
                make_media_streams_call(phone)
                input("\nPress Enter to continue...")
            
        elif choice == ("6" if REALTIME_AVAILABLE and MEDIA_STREAMS_AVAILABLE else ("5" if REALTIME_AVAILABLE else "3")):
            show_status()
            input("\nPress Enter to continue...")
            
        elif choice == ("7" if REALTIME_AVAILABLE and MEDIA_STREAMS_AVAILABLE else ("6" if REALTIME_AVAILABLE else "4")):
            print("🧪 Running tests...")
            try:
                subprocess.run([sys.executable, "test_mixed_language.py"], check=True)
            except:
                print("❌ Test failed")
            input("\nPress Enter to continue...")
            
        elif choice == ("8" if REALTIME_AVAILABLE and MEDIA_STREAMS_AVAILABLE else ("7" if REALTIME_AVAILABLE else "5")):
            print("🎤 Starting traditional voice bot...")
            print("💡 Speak Hindi or English!")
            try:
                subprocess.run([sys.executable, "-m", "src.voice_bot"])
            except KeyboardInterrupt:
                print("\n🎤 Stopped.")
            input("\nPress Enter to continue...")
            
        elif choice == ("9" if REALTIME_AVAILABLE and MEDIA_STREAMS_AVAILABLE else ("8" if REALTIME_AVAILABLE else "6")):
            print("👋 Goodbye!")
            break
            
        else:
            print(f"❌ Invalid choice (1-{max_choice})")
            time.sleep(1)

def show_project_info():
    """Show project information"""
    print("\n" + "=" * 60)
    print("📋 AI CALLING BOT - PROJECT INFORMATION")
    print("=" * 60)
    print("🤖 Complete AI Calling Bot with Mixed Language Support")
    print()
    print("✅ Features:")
    print("   • Phase 1: Core Bot Engine (STT → GPT → TTS)")
    print("   • Phase 2: SIP Integration (Asterisk)")
    print("   • Phase 3: Real Phone Calls (Twilio)")
    print("   • 🌐 Mixed Language: Hindi + English")
    print("   • 🤖 Automatic Language Detection")
    print("   • 🎤 Smart Voice Recognition")
    print("   • 🗣️ Natural Speech Synthesis")
    print()
    print("🔧 Components:")
    print("   • Speech-to-Text: Faster-Whisper (Hindi + English)")
    print("   • AI Brain: OpenAI GPT-4o-mini (Mixed Language)")
    print("   • Text-to-Speech: Twilio TTS (Hindi + English)")
    print("   • Phone Service: Twilio")
    print("   • Webhook Tunnel: ngrok")
    print("   • Language Detection: Automatic")
    print()
    print("📞 Usage Examples:")
    print("   • English: 'Hello, I need restaurant booking'")
    print("   • Hindi: 'नमस्ते, मुझे restaurant booking चाहिए'")
    print("   • Mixed: 'Hello नमस्ते, I need help'")
    print("=" * 60)

# =============================================================================
# MAIN FUNCTION
# =============================================================================
def cleanup_on_exit():
    """Cleanup function for graceful shutdown"""
    def signal_handler(signum, frame):
        print("\n🔄 Shutting down gracefully...")
        
        # Stop ngrok
        if ngrok_process:
            try:
                ngrok_process.terminate()
                print("✅ Ngrok stopped")
            except:
                pass
        
        print("✅ Cleanup complete. Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main function - the only entry point you need!"""
    clear_screen()
    print("🚀 AI CALLING BOT")
    print("🌐 Hindi + English Support")
    print("-" * 30)
    
    # Setup cleanup
    cleanup_on_exit()
    
    # Check environment
    print("🔍 Checking setup...")
    if not check_environment():
        print("❌ Setup incomplete!")
        print("📝 Configure your .env file")
        return
    
    # Start all services automatically
    print("🚀 Starting services...")
    
    # 1. Start audio server
    if not start_audio_server():
        print("❌ Audio server failed")
        return
    
    # 2. Start voice bot server  
    if not start_voice_bot_server():
        print("❌ Voice bot failed")
        return
    
    # 3. Start ngrok
    ngrok_url = start_ngrok()
    if not ngrok_url:
        print("❌ Ngrok failed")
        return
    
    print("✅ All services ready!")
    print(f"🌐 Webhook: {ngrok_url}/voice")
    time.sleep(2)
    
    # Show main menu
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()