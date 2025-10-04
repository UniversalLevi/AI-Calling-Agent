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

# Import Ultra-Simple Interruption system (actually works)
try:
    from src.ultra_simple_interruption import create_ultra_simple_response, handle_ultra_simple_timeout
    ULTRA_SIMPLE_INTERRUPTION_AVAILABLE = True
    print("✅ Ultra-simple interruption system available")
except ImportError as e:
    ULTRA_SIMPLE_INTERRUPTION_AVAILABLE = False
    print(f"⚠️ Ultra-simple interruption not available: {e}")

# Import Simple Interruption system (reliable fallback)
try:
    from src.simple_interruption import get_simple_interruption_handler, create_interruption_response
    SIMPLE_INTERRUPTION_AVAILABLE = True
    print("✅ Simple interruption system available")
except ImportError as e:
    SIMPLE_INTERRUPTION_AVAILABLE = False
    print(f"⚠️ Simple interruption not available: {e}")

# Import WebSocket Interruption system (advanced)
try:
    from src.websocket_interruption import start_websocket_interruption_server, WebSocketInterruptionHandler
    WEBSOCKET_INTERRUPTION_AVAILABLE = True
    print("✅ WebSocket interruption system available")
except ImportError as e:
    WEBSOCKET_INTERRUPTION_AVAILABLE = False
    print(f"⚠️ WebSocket interruption not available: {e}")

# Set interruption availability (prefer ultra-simple, then simple, then websocket)
INTERRUPTION_AVAILABLE = ULTRA_SIMPLE_INTERRUPTION_AVAILABLE or SIMPLE_INTERRUPTION_AVAILABLE or WEBSOCKET_INTERRUPTION_AVAILABLE

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
        
        # Enhanced logging for debugging_ok
        print(f"📞 Incoming call from: {caller}")
        print(f"📞 Call SID: {call_sid}")
        print(f"📞 Request args: {dict(request.args)}")
        print(f"📞 Request form: {dict(request.form)}")
        
        # Check for smart call features
        realtime_mode = request.args.get('realtime', 'false').lower() == 'true'
        interruption_mode = request.args.get('interruption', 'none').lower()
        media_streams_mode = request.args.get('media_streams', 'false').lower() == 'true'
        
        # Smart call mode - auto-detect and enable all features
        if realtime_mode or interruption_mode != 'none' or media_streams_mode:
            features = []
            if realtime_mode:
                features.append("⚡ Real-time")
            if interruption_mode != 'none':
                features.append(f"🎧 {interruption_mode.title()} interruption")
            if media_streams_mode:
                features.append("🎬 Media Streams")
            
            print(f"🚀 Smart call mode active: {', '.join(features)}")
        
        if REALTIME_AVAILABLE and realtime_mode:
            # Use enhanced real-time conversation with shorter timeouts
            print("🚀 Starting smart call mode")
            
            # Generate smooth, natural greeting
            greeting_text = "Hi there! I am Sara. How can I help you today?"
            
            # Use ultra-simple interruption if requested
            if interruption_mode == 'simple' and ULTRA_SIMPLE_INTERRUPTION_AVAILABLE:
                print("🎧 Using ultra-simple interruption system for greeting")
                try:
                    from src.ultra_simple_interruption import create_ultra_simple_response
                    response_twiml = create_ultra_simple_response(call_sid, greeting_text, 'en')
                    print(f"✅ Ultra-simple response created successfully")
                    print(f"📞 Response length: {len(str(response_twiml))} characters")
                    return str(response_twiml)
                except Exception as e:
                    print(f"❌ Ultra-simple interruption error: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to standard response
                    response.say("Hello! How can I help you?", voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
                    return str(response)
            elif interruption_mode == 'simple' and SIMPLE_INTERRUPTION_AVAILABLE:
                print("🎧 Using simple interruption system for greeting")
                try:
                    from src.simple_interruption import create_interruption_response
                    response_twiml = create_interruption_response(call_sid, greeting_text, 'en')
                    print(f"✅ Simple response created successfully")
                    print(f"📞 Response length: {len(str(response_twiml))} characters")
                    return str(response_twiml)
                except Exception as e:
                    print(f"❌ Simple interruption error: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to standard response
                    response.say("Hello! How can I help you?", voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
                    return str(response)
            else:
                # Standard real-time mode
                # Generate single smooth TTS for better quality
                audio_file = speak_mixed_enhanced(greeting_text)
                if audio_file:
                    response.play(f"/audio/{audio_file}")
                    print(f"🎵 Playing smooth greeting: {greeting_text}")
                else:
                    # Fallback to Twilio voice if TTS fails
                    twilio_voice_en = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
                    response.say(greeting_text, voice=twilio_voice_en, language='en-IN')
                    print("⚠️ Using Twilio fallback for greeting")
                
                # Very short pause after greeting
                response.pause(length=0.1)
            
            # Dynamic conversation system - adapt timeouts based on context
            def get_initial_timeout():
                """Get initial timeout for greeting with abuse prevention"""
                base_timeout = 12  # Give user time to think after greeting
                MIN_TIMEOUT = 8   # Minimum 8 seconds for greeting
                MAX_TIMEOUT = 15  # Maximum 15 seconds for greeting
                return max(MIN_TIMEOUT, min(MAX_TIMEOUT, base_timeout))
            
            # Start with greeting stage
            timeout = get_initial_timeout()
            
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=timeout,  # Dynamic timeout based on conversation context
                speech_timeout='auto',
                language='en-IN',  # Start with English, will switch based on detection
                enhanced='true',  # Use enhanced speech recognition
                profanity_filter='false',  # Don't filter speech
                num_digits=0,  # Don't expect digits
                finish_on_key='#'  # Allow finishing with # key
            )
            response.append(gather)
            
            print(f"🕐 Dynamic timeout set: {timeout} seconds for greeting stage")
            
            # Add a fallback message if no speech is detected
            twilio_voice_en = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
            response.say("I didn't hear anything. Please try again.", voice=twilio_voice_en, language='en-IN')
            
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
    
    @bot_app.route('/voice_websocket_interruption', methods=['POST'])
    def voice_websocket_interruption():
        """Handle incoming calls with WebSocket-based interruption"""
        print("🎧 WebSocket interruption call received")
        response = VoiceResponse()
        
        # Get ngrok URL for WebSocket connection
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            # Create WebSocket URL for Media Streams
            ws_url = ngrok_url.replace('http://', 'ws://').replace('https://', 'wss://')
            stream_url = f"{ws_url}/websocket_interruption"
            
            # Start Media Streams connection
            connect = response.connect()
            connect.stream(url=stream_url)
            
            print(f"🔗 Connecting to WebSocket interruption: {stream_url}")
        else:
            response.say("I'm sorry, the interruption service is not available right now.")
        
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
    
    # WebSocket handler for interruption
    if WEBSOCKET_INTERRUPTION_AVAILABLE:
        @bot_app.route('/websocket_interruption')
        def websocket_interruption():
            """WebSocket endpoint for real-time interruption"""
            # This will be handled by the WebSocket server
            return "WebSocket interruption endpoint", 200
    
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
                            twilio_voice_hi = os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi')
                            response.say(bot_response, voice=twilio_voice_hi)
                    except Exception as tts_error:
                        print(f"❌ Enhanced TTS failed: {tts_error}")
                        print(f"🗣️ Fallback to Twilio TTS (Hindi voice)")
                        twilio_voice_hi = os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi')
                        response.say(bot_response, voice=twilio_voice_hi)
                else:
                    # Use Twilio TTS for English
                    print(f"🗣️ Using Twilio TTS (English voice)")
                    twilio_voice_en = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
                    response.say(bot_response, voice=twilio_voice_en)
                
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
        response = VoiceResponse()
        speech_result = request.form.get('SpeechResult', '')
        caller = request.form.get('From', 'Unknown')
        call_sid = request.form.get('CallSid')
        
        # Enhanced logging for debugging
        print(f"⚡ Processing speech from: {caller}")
        print(f"⚡ Call SID: {call_sid}")
        print(f"⚡ Speech result: '{speech_result}'")
        print(f"⚡ Request args: {dict(request.args)}")
        print(f"⚡ Request form: {dict(request.form)}")
        
        # Check if simple interruption mode is active
        interruption_mode = request.args.get('interruption', 'none').lower()
        print(f"⚡ Interruption mode: {interruption_mode}")
        
        # Enhanced STT confidence check
        speech_confidence = float(request.form.get('Confidence', '0.0'))
        print(f"🎤 Speech confidence: {speech_confidence:.2f}")
        
        # If confidence is very low, try to improve the result
        if speech_confidence < 0.3 and speech_result:
            print(f"⚠️ Low confidence speech: '{speech_result}' - confidence: {speech_confidence}")
            # Try to clean up common STT errors
            cleaned_speech = speech_result.replace('hotel hotel', 'hotel').replace('booking booking', 'booking')
            if cleaned_speech != speech_result:
                print(f"🔧 Cleaned speech: '{cleaned_speech}'")
                speech_result = cleaned_speech
        
        # Check for hang-up phrases (enhanced for Hindi/mixed language)
        hangup_phrases = [
            # English
            'bye', 'goodbye', 'thank you', 'thanks', 'end call', 'hang up', 
            'call end', 'disconnect', 'close call', 'finish call',
            # Hindi
            'bye bye', 'tata', 'chalo bye', 'call khatam', 'call band', 
            'dhanyavad', 'shukriya', 'phone kat do', 'call cut', 'call band kar do',
            # Mixed language
            'thank you bye', 'bye thank you', 'thank you bye bye', 'bye bye thank you',
            'shukriya bye', 'bye shukriya', 'dhanyavad bye', 'bye dhanyavad',
            # Repetitive patterns (user frustration)
            'phone kat do phone kat do', 'call cut call cut', 'bye bye bye',
            # Common Hindi goodbye phrases
            'namaste', 'alvida', 'phir milenge', 'chalo bye bye'
        ]
        
        speech_lower = speech_result.lower().strip()
        if any(phrase in speech_lower for phrase in hangup_phrases):
            print(f"👋 User wants to end call: {speech_result}")
            response = VoiceResponse()
            
            # Detect language for appropriate goodbye message
            detected_language = detect_language(speech_result)
            
            if detected_language in ['hi', 'mixed']:
                goodbye_message = "Dhanyavad! Aapka din shubh ho. Phir milenge!"
                voice = os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi')
                language = 'hi-IN'
            else:
                goodbye_message = "Thank you for calling! Have a great day. Goodbye!"
                voice = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
                language = 'en-IN'
            
            response.say(goodbye_message, voice=voice, language=language)
            response.hangup()
            return str(response)
        
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
                # Enhanced language detection with confidence scoring
                detected_language = detect_language(speech_result)
                
                # Additional validation for mixed language detection
                if detected_language == 'mixed':
                    # Check if it's actually Hindi with some English words
                    hindi_words = ['मैं', 'आप', 'है', 'हैं', 'कर', 'करना', 'चाहिए', 'हो', 'होगा', 'करो', 'करना', 'बताओ', 'दो', 'लो', 'जाओ', 'आओ']
                    english_words = ['hotel', 'booking', 'book', 'room', 'price', 'budget', 'date', 'time', 'check', 'in', 'out']
                    
                    hindi_count = sum(1 for word in hindi_words if word in speech_result)
                    english_count = sum(1 for word in english_words if word.lower() in speech_result.lower())
                    
                    if hindi_count > english_count:
                        detected_language = 'hi'
                    elif english_count > hindi_count:
                        detected_language = 'en'
                
                print(f"🌐 Detected language: {detected_language} for: '{speech_result[:30]}...'")
                
                # Store language for this call
                if call_sid:
                    # Ensure proper dict structure for language storage
                    if call_sid not in bot_app.call_language:
                        bot_app.call_language[call_sid] = {}
                    elif not isinstance(bot_app.call_language[call_sid], dict):
                        # Convert string to dict if it was stored as language string
                        old_lang = bot_app.call_language[call_sid]
                        bot_app.call_language[call_sid] = {'language': old_lang}
                    
                    bot_app.call_language[call_sid]['language'] = detected_language
                
                # Dynamic conversation context detection and response generation
                # Analyze conversation context for dynamic behavior
                def analyze_conversation_context(user_input):
                    """Analyze user input to determine conversation stage and context"""
                    user_lower = user_input.lower()
                    
                    # Selection/Choice detection (highest priority)
                    if any(phrase in user_lower for phrase in [
                        'book kar do', 'book karo', 'select', 'choose', 'pick', 'take this', 'take that',
                        'इसको बुक कर', 'यह बुक कर', 'इसे बुक कर', 'चुनता हूं', 'लेता हूं', 'करूंगा',
                        'villa 243', 'option 1', 'option 2', 'first one', 'second one', 'पहला', 'दूसरा'
                    ]):
                        return "selection"
                    
                    # Greeting/Initial request detection
                    elif any(word in user_lower for word in ['hi', 'hello', 'namaste', 'hey', 'book', 'want', 'need', 'help']):
                        return "initial_request"
                    
                    # Detail providing stage
                    elif any(word in user_lower for word in ['budget', 'price', 'location', 'date', 'time', 'people', 'days', 'nights']):
                        return "details"
                    
                    # Confirmation/clarification stage
                    elif any(word in user_lower for word in ['yes', 'no', 'ok', 'sure', 'maybe', 'confirm', 'change']):
                        return "clarification"
                    
                    # Complex query stage
                    elif len(user_input.split()) > 10:
                        return "complex_query"
                    
                    else:
                        return "general"
                
                # Get conversation context and store memory
                conversation_stage = analyze_conversation_context(speech_result)
                # Initialize or ensure dict structure for call_sid
                if call_sid not in bot_app.call_language:
                    bot_app.call_language[call_sid] = {
                        'conversation_history': [],
                        'extracted_info': {},
                        'asked_questions': set()
                    }
                elif not isinstance(bot_app.call_language[call_sid], dict):
                    # Convert string to dict if it was stored as language string
                    old_lang = bot_app.call_language[call_sid]
                    bot_app.call_language[call_sid] = {
                        'language': old_lang,
                        'conversation_history': [],
                        'extracted_info': {},
                        'asked_questions': set()
                    }
                
                # Ensure all required keys exist
                if 'conversation_history' not in bot_app.call_language[call_sid]:
                    bot_app.call_language[call_sid]['conversation_history'] = []
                if 'extracted_info' not in bot_app.call_language[call_sid]:
                    bot_app.call_language[call_sid]['extracted_info'] = {}
                if 'asked_questions' not in bot_app.call_language[call_sid]:
                    bot_app.call_language[call_sid]['asked_questions'] = set()
                
                # Store conversation context
                bot_app.call_language[call_sid]['conversation_stage'] = conversation_stage
                bot_app.call_language[call_sid]['last_input_length'] = len(speech_result)
                
                # Add current user input to conversation history
                bot_app.call_language[call_sid]['conversation_history'].append({
                    'role': 'user',
                    'content': speech_result,
                    'timestamp': time.time(),
                    'stage': conversation_stage
                })
                
                if bot_app.gpt:
                    # Check for inappropriate content first
                    from src.language_detector import detect_inappropriate_content, get_appropriate_response
                    
                    if detect_inappropriate_content(speech_result):
                        print(f"⚠️ Inappropriate content detected from {caller}")
                        bot_response = get_appropriate_response(detected_language)
                    else:
                        # Extract information from user input and update memory
                        def extract_and_store_info(user_input, call_data):
                            """Extract key information from user input and store in memory"""
                            user_lower = user_input.lower()
                            extracted_info = call_data.get('extracted_info', {})
                            
                            # Extract location/destination (English and Hindi)
                            locations = {
                                'jaipur': 'Jaipur', 'जयपुर': 'Jaipur',
                                'delhi': 'Delhi', 'दिल्ली': 'Delhi',
                                'mumbai': 'Mumbai', 'मुंबई': 'Mumbai',
                                'bangalore': 'Bangalore', 'बैंगलोर': 'Bangalore',
                                'chennai': 'Chennai', 'चेन्नई': 'Chennai',
                                'kolkata': 'Kolkata', 'कोलकाता': 'Kolkata',
                                'hyderabad': 'Hyderabad', 'हैदराबाद': 'Hyderabad',
                                'pune': 'Pune', 'पुणे': 'Pune',
                                'ahmedabad': 'Ahmedabad', 'अहमदाबाद': 'Ahmedabad',
                                'goa': 'Goa', 'गोवा': 'Goa'
                            }
                            for location_key, location_value in locations.items():
                                if location_key in user_lower or location_key in user_input:
                                    extracted_info['destination'] = location_value
                                    break
                            
                            # Extract budget information
                            import re
                            budget_match = re.search(r'(\d+)\s*(?:rupees?|rs\.?|₹)', user_lower)
                            if budget_match:
                                extracted_info['budget'] = int(budget_match.group(1))
                            elif '5000' in user_input or 'five thousand' in user_lower:
                                extracted_info['budget'] = 5000
                            elif 'budget' in user_lower and 'friendly' in user_lower:
                                extracted_info['budget_type'] = 'budget-friendly'
                            
                            # Extract duration
                            duration_patterns = [
                                (r'(\d+)\s*(?:days?|nights?)', 'duration_days'),
                                (r'(?:one|two|three|four|five)\s*(?:days?|nights?)', 'duration_text')
                            ]
                            for pattern, key in duration_patterns:
                                match = re.search(pattern, user_lower)
                                if match:
                                    extracted_info[key] = match.group(0)
                                    break
                            
                            # Extract dates/timing
                            if 'today' in user_lower or 'आज' in user_input:
                                extracted_info['checkin'] = 'today'
                            elif 'tonight' in user_lower or 'रात' in user_input:
                                extracted_info['checkin'] = 'tonight'
                            elif 'tomorrow' in user_lower or 'कल' in user_input:
                                extracted_info['checkin'] = 'tomorrow'
                            
                            # Extract number of people
                            people_match = re.search(r'(\d+)\s*(?:people|person|व्यक्ति)', user_lower)
                            if people_match:
                                extracted_info['people'] = int(people_match.group(1))
                            
                            call_data['extracted_info'] = extracted_info
                            return extracted_info
                        
                        # Extract information and generate memory-aware response
                        current_info = extract_and_store_info(speech_result, bot_app.call_language[call_sid])
                        def get_memory_aware_prompt(stage, language, call_data):
                            # Improve language consistency
                            if language == 'hi':
                                base_prompt = "You are Sara, a helpful female AI assistant. Always respond in Hindi/Hinglish. Use Hindi words and phrases naturally. "
                            elif language == 'mixed':
                                base_prompt = "You are Sara, a helpful female AI assistant. Respond in Hinglish (mix of Hindi and English). Use Hindi words when natural. "
                            else:
                                base_prompt = f"You are Sara, a helpful female AI assistant. Respond naturally in {language}. "
                            
                            # Get conversation history and extracted info
                            history = call_data.get('conversation_history', [])
                            extracted_info = call_data.get('extracted_info', {})
                            asked_questions = call_data.get('asked_questions', set())
                            
                            # Build context from memory
                            context_parts = []
                            if extracted_info.get('destination'):
                                context_parts.append(f"Destination: {extracted_info['destination']}")
                            if extracted_info.get('budget'):
                                context_parts.append(f"Budget: ₹{extracted_info['budget']}")
                            elif extracted_info.get('budget_type'):
                                context_parts.append(f"Budget: {extracted_info['budget_type']}")
                            if extracted_info.get('duration_days') or extracted_info.get('duration_text'):
                                duration = extracted_info.get('duration_days') or extracted_info.get('duration_text')
                                context_parts.append(f"Duration: {duration}")
                            if extracted_info.get('checkin'):
                                context_parts.append(f"Check-in: {extracted_info['checkin']}")
                            if extracted_info.get('people'):
                                context_parts.append(f"People: {extracted_info['people']}")
                            
                            memory_context = ""
                            if context_parts:
                                memory_context = f"\n\nKnown information from conversation: {', '.join(context_parts)}"
                                memory_context += "\nDo NOT ask for information you already know. Build upon what you know."
                            
                            # Check if user is asking for options/suggestions
                            user_wants_options = any(word in speech_result.lower() for word in ['बताओ', 'options', 'suggest', 'recommend', 'show', 'list'])
                            
                            # Special handling for providing options/lists
                            if user_wants_options and extracted_info:
                                return base_prompt + f"The user wants you to provide specific options/suggestions based on their request. Give 2-3 relevant recommendations with details. Be complete in your response - don't cut off mid-sentence. You have all needed info: {', '.join(context_parts)}. Provide complete list with helpful details." + memory_context
                            
                            # Check if we have enough info to provide recommendations automatically
                            has_key_info = len(extracted_info) >= 2  # At least 2 pieces of information
                            
                            # Check if user is making a specific choice/selection
                            user_making_choice = any(phrase in speech_result.lower() for phrase in [
                                'book kar do', 'book karo', 'book this', 'book that', 'select', 'choose', 'pick',
                                'इसको बुक कर', 'यह बुक कर', 'इसे बुक कर', 'चुनता हूं', 'लेता हूं', 'करूंगा',
                                'villa 243', 'hotel', 'option 1', 'option 2', 'first one', 'second one',
                                'पहला', 'दूसरा', 'तीसरा', 'यह वाला', 'वो वाला'
                            ])
                            
                            # If user confirms details or says "yes" and we have enough info, provide recommendations
                            user_confirms = any(word in speech_result.lower() for word in ['yes', 'हाँ', 'हां', 'correct', 'right', 'okay', 'ok'])
                            
                            if user_making_choice:
                                return base_prompt + f"The user is making a specific choice or selection. Acknowledge their choice and proceed with booking/confirmation process. Don't provide more options - they've already decided. Focus on next steps like getting details or confirming the booking." + memory_context
                            elif user_confirms and has_key_info:
                                return base_prompt + f"The user has confirmed the details. You have enough information to provide specific recommendations based on their request. Give 2-3 relevant options with names, brief descriptions, and helpful details. Don't say you'll 'look' or 'search' - directly provide useful recommendations now. Ask if they'd like more details about any of these options." + memory_context
                            
                            # Stage-specific prompts with memory awareness
                            if stage == "selection":
                                return base_prompt + "The user is making a specific choice or selection. Acknowledge their choice positively and proceed with the next step (booking details, confirmation, etc.). Don't provide more options - they've decided. Be helpful and move forward." + memory_context
                            elif stage == "initial_request":
                                if not extracted_info:
                                    return base_prompt + "The user is making an initial request. Ask clarifying questions to understand their needs better. Keep it concise (max 2 sentences)." + memory_context
                                else:
                                    return base_prompt + "The user is making a request. You already have some information. Ask only for missing details needed. Keep it concise (max 2 sentences)." + memory_context
                            elif stage == "details":
                                return base_prompt + "The user is providing details. Acknowledge their information and ask for any missing details needed. Be specific but brief (max 3 sentences)." + memory_context
                            elif stage == "clarification":
                                return base_prompt + "The user is confirming or clarifying. Provide a clear, helpful response and next steps if needed (max 2 sentences)." + memory_context
                            elif stage == "complex_query":
                                return base_prompt + "The user has a complex question. Break down your response into clear points but keep it concise (max 4 sentences)." + memory_context
                            else:
                                # For general responses, if we have key info, be more proactive
                                if has_key_info:
                                    return base_prompt + f"You're helping the user with their request. Be helpful and continue the conversation. If you have enough details, provide specific recommendations instead of saying you'll 'look' or 'search'. Keep it conversational (max 3 sentences)." + memory_context
                                else:
                                    return base_prompt + "Respond helpfully and naturally. Keep it brief (max 2 sentences)." + memory_context
                        
                        # Generate response with memory-aware prompting (optimized for speed)
                        enhanced_prompt = get_memory_aware_prompt(conversation_stage, detected_language, bot_app.call_language[call_sid])
                        
                        # Optimize prompt for faster response
                        optimized_prompt = f"{enhanced_prompt}\n\nUser: {speech_result}\n\nRespond quickly and concisely:"
                        bot_response = bot_app.gpt.ask(optimized_prompt, detected_language)
                        
                        # Enforce response length limits based on context
                        def enforce_response_limits(response, stage):
                            """Enforce dynamic response length limits"""
                            
                            # Check if user is asking for options/lists - allow longer responses
                            user_wants_options = any(word in speech_result.lower() for word in ['बताओ', 'options', 'suggest', 'recommend', 'show', 'list'])
                            
                            # Also check if bot is providing recommendations (contains multiple options/names)
                            bot_providing_recommendations = (
                                'recommend' in response.lower() or 
                                'suggest' in response.lower() or
                                'option' in response.lower() or
                                'choice' in response.lower() or
                                'book' in response.lower() or
                                'hotel' in response.lower() or
                                'villa' in response.lower() or
                                '"' in response or  # Quoted names like "Heritage Villa"
                                response.count(',') >= 2 or  # Multiple items listed
                                'both of which' in response.lower() or
                                'either' in response.lower() and 'or' in response.lower() or
                                '1.' in response or '2.' in response or '3.' in response or  # Numbered lists
                                'first' in response.lower() and 'second' in response.lower()  # Multiple options
                            )
                            
                            if user_wants_options or bot_providing_recommendations:
                                # Allow much longer responses for lists/options/recommendations
                                max_length = 1200  # Increased to 1200 characters for complete recommendations
                            else:
                                max_lengths = {
                                    "initial_request": 300,  # Increased for better responses
                                    "details": 400,          # Increased for detailed responses
                                    "clarification": 250,    # Increased for clarifications
                                    "selection": 300,        # Increased for selection responses
                                    "complex_query": 500,    # Increased for complex queries
                                    "general": 300           # Increased for general responses
                                }
                                max_length = max_lengths.get(stage, 300)
                            
                            if len(response) > max_length:
                                # For recommendations/lists, try to keep complete items
                                if (user_wants_options or bot_providing_recommendations) and ('1.' in response or '2.' in response):
                                    # Try to keep complete list items
                                    lines = response.split('\n')
                                    truncated_lines = []
                                    current_length = 0
                                    
                                    for line in lines:
                                        if current_length + len(line) + 1 <= max_length:
                                            truncated_lines.append(line)
                                            current_length += len(line) + 1
                                        else:
                                            break
                                    
                                    if truncated_lines:
                                        return '\n'.join(truncated_lines).strip()
                                
                                # Fallback: truncate at sentence boundary
                                sentences = response.split('.')
                                truncated = ""
                                for sentence in sentences:
                                    if len(truncated + sentence + ".") <= max_length:
                                        truncated += sentence + "."
                                    else:
                                        break
                                
                                if truncated:
                                    return truncated.strip()
                                else:
                                    # For recommendations with quotes, try to preserve complete quoted names
                                    if bot_providing_recommendations and '"' in response:
                                        # Find the last complete quoted item that fits
                                        words = response.split()
                                        truncated_words = []
                                        current_length = 0
                                        
                                        for word in words:
                                            if current_length + len(word) + 1 <= max_length:
                                                truncated_words.append(word)
                                                current_length += len(word) + 1
                                            else:
                                                break
                                        
                                        if truncated_words:
                                            return ' '.join(truncated_words).strip()
                                    
                                    # Hard truncate if no sentence boundary found
                                    return response[:max_length].strip() + "..."
                            
                            return response
                        
                        # Apply length limits
                        original_length = len(bot_response)
                        bot_response = enforce_response_limits(bot_response, conversation_stage)
                        if len(bot_response) != original_length:
                            print(f"⚠️ Response truncated: {original_length} → {len(bot_response)} chars")
                        
                        # Check if booking is completed and user is satisfied
                        booking_completed = (
                            'booking' in bot_response.lower() and 
                            ('confirm' in bot_response.lower() or 'done' in bot_response.lower() or 'complete' in bot_response.lower())
                        )
                        
                        user_satisfied = any(word in speech_result.lower() for word in [
                            'thank you', 'thanks', 'shukriya', 'dhanyavad', 'perfect', 'good', 'accha', 'theek hai'
                        ])
                        
                        if booking_completed and user_satisfied:
                            print("✅ Booking completed and user satisfied - preparing to end call")
                            # Add a brief confirmation before ending
                            bot_response += " Have a great day!"
                        
                        # Store last bot response for smart timeout calculation
                        bot_app.call_language[call_sid]['last_bot_response'] = bot_response
                        
                        # Keep conversation history manageable (last 10 exchanges)
                        if len(bot_app.call_language[call_sid]['conversation_history']) > 20:
                            bot_app.call_language[call_sid]['conversation_history'] = bot_app.call_language[call_sid]['conversation_history'][-20:]
                        
                        print(f"🤖 Sara: {bot_response[:50]}{'...' if len(bot_response) > 50 else ''}")
                else:
                    # Quick fallback with context-aware responses
                    if conversation_stage == "initial_request":
                        if detected_language == 'hi':
                            bot_response = "हाँ, मैं आपकी मदद कर सकती हूँ। कृपया और बताएं।"
                        else:
                            bot_response = "Yes, I can help you with that. Please tell me more details."
                    else:
                        if detected_language == 'hi':
                            bot_response = f"मैं समझ गई। {speech_result[:50]}... के बारे में और बताएं।"
                        else:
                            bot_response = f"I understand. Please tell me more about {speech_result[:50]}..."
                
                # Ensure we have a valid response
                if not bot_response or bot_response.strip() == "":
                    if detected_language == 'hi':
                        bot_response = "मैं आपकी बात समझ गई हूँ। क्या मैं आपकी और मदद कर सकती हूँ?"
                    else:
                        bot_response = "I understand what you're saying. How else can I help you today?"
                
                # Use ultra-simple interruption if requested
                if interruption_mode == 'simple' and ULTRA_SIMPLE_INTERRUPTION_AVAILABLE:
                    print("🎧 Using ultra-simple interruption system for response")
                    from src.ultra_simple_interruption import create_ultra_simple_response
                    response_twiml = create_ultra_simple_response(call_sid, bot_response, detected_language)
                    
                    # Check if we should end the call after successful booking
                    if booking_completed and user_satisfied:
                        print("📞 Ending call after successful booking completion")
                        response = VoiceResponse()
                        if detected_language in ['hi', 'mixed']:
                            response.say("Dhanyavad! Aapka din shubh ho. Phir milenge!", voice=os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi'), language='hi-IN')
                        else:
                            response.say("Thank you! Have a great day. Goodbye!", voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
                        response.hangup()
                        return str(response)
                    
                    return str(response_twiml)
                elif interruption_mode == 'simple' and SIMPLE_INTERRUPTION_AVAILABLE:
                    print("🎧 Using simple interruption system for response")
                    from src.simple_interruption import create_interruption_response
                    return str(create_interruption_response(call_sid, bot_response, detected_language))
                else:
                    # Generate chunked response for better interruption handling
                    try:
                        # Generate and play response
                        audio_file = speak_mixed_enhanced(bot_response)
                        if audio_file:
                            response.play(f"/audio/{audio_file}")
                        else:
                            # Fallback to Twilio voice
                            if detected_language in ['hi', 'mixed']:
                                twilio_voice_hi = os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi')
                                response.say(bot_response, voice=twilio_voice_hi, language='hi-IN')
                            else:
                                twilio_voice_en = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
                                response.say(bot_response, voice=twilio_voice_en, language='en-IN')
                        
                    except Exception as e:
                        print(f"❌ Chunked TTS error: {e}")
                        # Fallback to single response
                        if detected_language in ['hi', 'mixed']:
                            twilio_voice_hi = os.getenv('TWILIO_VOICE_HI', 'Polly.Aditi')
                            response.say(bot_response, voice=twilio_voice_hi, language='hi-IN')
                        else:
                            twilio_voice_en = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
                            response.say(bot_response, voice=twilio_voice_en, language='en-IN')
                    
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
            
            # Smart timeout based on bot response length and conversation context
            call_data = bot_app.call_language.get(call_sid, {})
            if isinstance(call_data, dict):
                stored_stage = call_data.get('conversation_stage', 'general')
                last_input_length = call_data.get('last_input_length', 0)
                last_bot_response = call_data.get('last_bot_response', '')
            else:
                # Fallback if it's still a string
                stored_stage = 'general'
                last_input_length = 0
                last_bot_response = ''
            
            def get_smart_timeout(conversation_stage="general", user_input_length=0, bot_response_length=0):
                """Calculate smart timeout - responsive for short responses, longer for complex ones"""
                
                # Base timeout - start with shorter defaults for responsiveness
                base_timeout = 8  # Start with 8 seconds as base
                
                # Adjust based on conversation stage
                if conversation_stage == "initial_request":
                    base_timeout = 10  # Slightly more time for thinking
                elif conversation_stage == "details":
                    base_timeout = 15  # More time for detailed responses
                elif conversation_stage == "clarification":
                    base_timeout = 6   # Quick confirmations
                elif conversation_stage == "complex_query":
                    base_timeout = 12  # Moderate time for complex responses
                
                # If user just said something short (like "hi"), be more responsive
                if user_input_length <= 10:
                    base_timeout = max(6, base_timeout - 2)
                
                # If bot gave a long response, give user more time to process
                if bot_response_length > 150:
                    base_timeout += 3
                elif bot_response_length > 100:
                    base_timeout += 2
                
                # Apply limits - much more responsive
                MIN_TIMEOUT = 5   # Minimum 5 seconds
                MAX_TIMEOUT = 20  # Maximum 20 seconds (reduced from 35)
                
                final_timeout = max(MIN_TIMEOUT, min(MAX_TIMEOUT, base_timeout))
                return int(final_timeout)
            
            # Get smart timeout for next interaction
            last_bot_response_length = len(last_bot_response) if last_bot_response else 0
            next_timeout = get_smart_timeout(stored_stage, last_input_length, last_bot_response_length)
            
            # Continue with dynamic speech recognition
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=next_timeout,  # Dynamic timeout based on conversation context
                speech_timeout='auto',
                language='en-IN' if detected_language == 'en' else 'hi-IN',
                enhanced='true',  # Use enhanced speech recognition
                profanity_filter='false'  # Don't filter speech
            )
            response.append(gather)
            
            print(f"⏱️ Timeout: {next_timeout}s")
            
        else:
            # No speech detected - continue listening
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=8,  # Give user time to respond
                language='en-IN',
                enhanced='true',
                profanity_filter='false'
            )
            response.append(gather)
            
            # Fallback message if still no response
            twilio_voice_en = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
            response.say("I'm still here if you need help. What would you like to know?", voice=twilio_voice_en, language='en-IN')
        
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
                twilio_voice_en = os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna')
                response.say("", voice=twilio_voice_en)  # Empty say to stop current audio
                
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
    
    # Ultra-simple interruption timeout handler
    if ULTRA_SIMPLE_INTERRUPTION_AVAILABLE:
        @bot_app.route('/ultra_simple_interruption_timeout', methods=['POST'])
        def ultra_simple_interruption_timeout():
            """Handle timeout for ultra-simple interruption system"""
            call_sid = request.form.get('CallSid')
            caller = request.form.get('From', 'Unknown')
            print(f"⏰ Ultra-simple interruption timeout for call: {call_sid} from {caller}")
            print(f"📞 Timeout request form: {dict(request.form)}")
            
            try:
                from src.ultra_simple_interruption import handle_ultra_simple_timeout
                response_twiml = handle_ultra_simple_timeout(call_sid)
                print(f"✅ Ultra-simple timeout response created")
                return str(response_twiml)
            except Exception as e:
                print(f"❌ Ultra-simple timeout error: {e}")
                import traceback
                traceback.print_exc()
                response = VoiceResponse()
                response.say("I'm still here. How can I help you?", voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
                return str(response)
    
    # Simple interruption timeout handler
    if SIMPLE_INTERRUPTION_AVAILABLE:
        @bot_app.route('/simple_interruption_timeout', methods=['POST'])
        def simple_interruption_timeout():
            """Handle timeout for simple interruption system"""
            call_sid = request.form.get('CallSid')
            caller = request.form.get('From', 'Unknown')
            print(f"⏰ Simple interruption timeout for call: {call_sid} from {caller}")
            print(f"📞 Timeout request form: {dict(request.form)}")
            
            try:
                from src.simple_interruption import handle_interruption_timeout
                response_twiml = handle_interruption_timeout(call_sid)
                print(f"✅ Simple timeout response created")
                return str(response_twiml)
            except Exception as e:
                print(f"❌ Simple timeout error: {e}")
                import traceback
                traceback.print_exc()
                response = VoiceResponse()
                response.say("I'm still here. How can I help you?", voice=os.getenv('TWILIO_VOICE_EN', 'Polly.Joanna'), language='en-IN')
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

def make_websocket_interruption_call(phone_number: str):
    """Make a call with WebSocket-based interruption"""
    if not WEBSOCKET_INTERRUPTION_AVAILABLE:
        print("❌ WebSocket interruption not available")
        return
    
    print(f"🎧 Making WebSocket interruption call to: {phone_number}")
    
    # Start WebSocket interruption server
    try:
        print("🚀 Starting WebSocket interruption server...")
        start_websocket_interruption_server(host="0.0.0.0", port=8080)
        print("✅ WebSocket server started on port 8080")
    except Exception as e:
        print(f"❌ Failed to start WebSocket server: {e}")
        return
    
    # Update webhook to use WebSocket interruption endpoint
    ngrok_url = get_ngrok_url()
    if not ngrok_url:
        print("❌ Ngrok not available")
        return
    
    webhook_url = f"{ngrok_url}/voice_websocket_interruption"
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
        
        # Update webhook for WebSocket interruption
        incoming_numbers = client.incoming_phone_numbers.list(phone_number=twilio_phone)
        if incoming_numbers:
            incoming_numbers[0].update(voice_url=webhook_url)
            print("🔄 Updated webhook for WebSocket interruption mode")
        
        # Make the call
        call = client.calls.create(
            to=phone_number,
            from_=twilio_phone,
            url=webhook_url
        )
        
        print(f"✅ WebSocket interruption call initiated!")
        print(f"📞 SID: {call.sid}")
        print(f"🎯 Phone should ring!")
        print(f"🎧 WebSocket interruption active!")
        print(f"💬 Real-time audio streaming with interruption!")
        print(f"🔄 Bot can be interrupted immediately via WebSocket!")
        
    except Exception as e:
        print(f"❌ Error making WebSocket interruption call: {e}")

def make_smart_call(phone_number: str):
    """Make a smart call with all available features automatically enabled"""
    print(f"🤖 Making smart call to: {phone_number}")
    
    # Auto-detect best available features
    features = []
    webhook_params = []
    
    if REALTIME_AVAILABLE:
        features.append("⚡ Real-time conversation")
        webhook_params.append("realtime=true")
    
    if ULTRA_SIMPLE_INTERRUPTION_AVAILABLE:
        features.append("🎧 Ultra-simple interruption")
        webhook_params.append("interruption=simple")
    elif SIMPLE_INTERRUPTION_AVAILABLE:
        features.append("🎧 Simple interruption")
        webhook_params.append("interruption=simple")
    elif WEBSOCKET_INTERRUPTION_AVAILABLE:
        features.append("🎧 WebSocket interruption")
        webhook_params.append("interruption=websocket")
    
    if MEDIA_STREAMS_AVAILABLE:
        features.append("🎬 Media Streams barge-in")
        webhook_params.append("media_streams=true")
    
    print("🚀 Enabled features:")
    for feature in features:
        print(f"   {feature}")
    
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_phone]):
            print("❌ Twilio credentials not found")
            return
        
        ngrok_url = get_ngrok_url()
        if not ngrok_url:
            print("❌ Ngrok not available")
            return
        
        # Build webhook URL with all enabled features
        webhook_url = f"{ngrok_url}/voice?" + "&".join(webhook_params)
        print(f"🔗 Webhook URL: {webhook_url}")
        
        client = Client(account_sid, auth_token)
        
        # Update webhook for smart call
        incoming_numbers = client.incoming_phone_numbers.list(phone_number=twilio_phone)
        if incoming_numbers:
            incoming_numbers[0].update(voice_url=webhook_url)
            print("🔄 Updated webhook for smart call mode")
        
        # Make the call
        call = client.calls.create(
            to=phone_number,
            from_=twilio_phone,
            url=webhook_url
        )
        
        print(f"✅ Smart call initiated!")
        print(f"📞 SID: {call.sid}")
        print(f"🎯 Phone should ring!")
        print(f"💬 All features active - speak naturally!")
        print(f"🛑 Say 'bye' or 'thank you' to end call")
        
    except Exception as e:
        print(f"❌ Error making smart call: {e}")

def make_simple_interruption_call(phone_number: str):
    """Make a call with simple interruption system"""
    if not SIMPLE_INTERRUPTION_AVAILABLE:
        print("❌ Simple interruption not available")
        return
    
    print(f"🎧 Making simple interruption call to: {phone_number}")
    print("💡 This uses enhanced real-time mode with 2-second interruption detection")
    
    # Use the enhanced real-time mode which now includes simple interruption
    try:
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        if not all([account_sid, auth_token, twilio_phone]):
            print("❌ Twilio credentials not found")
            return
        
        ngrok_url = get_ngrok_url()
        if not ngrok_url:
            print("❌ Ngrok not available")
            return
        
        # Use the real-time endpoint with interruption enhancement
        webhook_url = f"{ngrok_url}/voice?realtime=true&interruption=simple"
        print(f"🔗 Webhook URL: {webhook_url}")
        
        client = Client(account_sid, auth_token)
        
        # Update webhook for simple interruption
        incoming_numbers = client.incoming_phone_numbers.list(phone_number=twilio_phone)
        if incoming_numbers:
            incoming_numbers[0].update(voice_url=webhook_url)
            print("🔄 Updated webhook for simple interruption mode")
        
        # Make the call
        call = client.calls.create(
            to=phone_number,
            from_=twilio_phone,
            url=webhook_url
        )
        
        print(f"✅ Simple interruption call initiated!")
        print(f"📞 SID: {call.sid}")
        print(f"🎯 Phone should ring!")
        print(f"🎧 Simple interruption active!")
        print(f"💬 Bot can be interrupted with 2-second detection!")
        print(f"⚡ Enhanced real-time conversation with interruption!")
        
    except Exception as e:
        print(f"❌ Error making simple interruption call: {e}")

def test_system():
    """Test all system components"""
    print("🧪 Testing AI Calling Bot System...")
    print("-" * 40)
    
    # Test 1: Environment Variables
    print("1. 🔧 Testing Environment Variables...")
    required_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER', 'OPENAI_API_KEY']
    env_ok = True
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Missing")
            env_ok = False
    
    if env_ok:
        print("   ✅ All environment variables set")
    else:
        print("   ❌ Some environment variables missing")
    
    # Test 2: Feature Availability
    print("\n2. 🚀 Testing Feature Availability...")
    features = []
    if REALTIME_AVAILABLE:
        features.append("Real-time")
        print("   ✅ Real-time conversation: Available")
    else:
        print("   ❌ Real-time conversation: Not available")
    
    if MEDIA_STREAMS_AVAILABLE:
        features.append("Media Streams")
        print("   ✅ Media Streams: Available")
    else:
        print("   ❌ Media Streams: Not available")
    
    if ULTRA_SIMPLE_INTERRUPTION_AVAILABLE:
        features.append("Ultra-Simple Interruption")
        print("   ✅ Ultra-Simple Interruption: Available")
    elif SIMPLE_INTERRUPTION_AVAILABLE:
        features.append("Simple Interruption")
        print("   ✅ Simple Interruption: Available")
    elif WEBSOCKET_INTERRUPTION_AVAILABLE:
        features.append("WebSocket Interruption")
        print("   ✅ WebSocket Interruption: Available")
    else:
        print("   ❌ Interruption: Not available")
    
    # Test 3: Ngrok
    print("\n3. 🌐 Testing Ngrok...")
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print(f"   ✅ Ngrok: {ngrok_url}")
    else:
        print("   ❌ Ngrok: Not available")
    
    # Test 4: TTS
    print("\n4. 🎵 Testing TTS...")
    try:
        from src.enhanced_hindi_tts import speak_mixed_enhanced
        test_audio = speak_mixed_enhanced("Test message")
        if test_audio:
            print("   ✅ TTS: Working")
        else:
            print("   ❌ TTS: Failed")
    except Exception as e:
        print(f"   ❌ TTS: Error - {e}")
    
    # Summary
    print("\n" + "=" * 40)
    if env_ok and features and ngrok_url:
        print("✅ System Status: READY")
        print(f"🚀 Available features: {', '.join(features)}")
        print("📞 Ready to make smart calls!")
    else:
        print("❌ System Status: ISSUES DETECTED")
        print("🔧 Please fix the issues above before making calls")
    
    print("=" * 40)

def main_menu():
    """Simplified main menu - single smart call option"""
    while True:
        clear_screen()
        print("🤖 AI CALLING BOT")
        print("🌐 Hindi + English Support")
        
        # Show available features
        features = []
        if REALTIME_AVAILABLE:
            features.append("⚡ Real-time")
        if MEDIA_STREAMS_AVAILABLE:
            features.append("🎬 Media Streams")
        if ULTRA_SIMPLE_INTERRUPTION_AVAILABLE:
            features.append("🎧 Ultra-Simple Interruption")
        elif SIMPLE_INTERRUPTION_AVAILABLE:
            features.append("🎧 Simple Interruption")
        elif WEBSOCKET_INTERRUPTION_AVAILABLE:
            features.append("🎧 WebSocket Interruption")
        
        if features:
            print(f"🚀 Available features: {', '.join(features)}")
        
        print("-" * 30)
        print("1. 📞 Make Smart Call")
        print("2. 🧪 Test System")
        print("3. 🔍 Status")
        print("4. ❌ Exit")
        print("-" * 30)
        
        choice = input("Choice (1-4): ").strip()
        
        if choice == "1":
            phone = input("📞 Enter phone number: ").strip()
            if phone:
                make_smart_call(phone)
                input("\nPress Enter to continue...")
        
        elif choice == "2":
            test_system()
            input("\nPress Enter to continue...")
        
        elif choice == "3":
            show_status()
            input("\nPress Enter to continue...")
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice (1-4)")
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