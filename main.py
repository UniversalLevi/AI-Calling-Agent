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
from datetime import datetime

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

# Import product-aware conversation components
try:
    from src.product_service import get_product_service
    from src.dynamic_prompt_builder import get_prompt_builder
    PRODUCT_AWARE = True
    print("✅ Product-aware conversation capabilities available")
except ImportError as e:
    PRODUCT_AWARE = False
    print(f"⚠️ Product-aware conversation not available: {e}")

# Global variables
voice_bot_app = None
audio_server_app = None
ngrok_process = None
running_services = {}
realtime_voice_bot = None
twilio_realtime_integration = None
product_service = None
prompt_builder = None
call_sessions = {}  # Store product and conversation data per call_sid

# Dashboard integration
DASHBOARD_API_URL = "http://localhost:5000/api"

def log_call_to_dashboard(call_data):
    """Log call to dashboard backend"""
    try:
        response = requests.post(
            f"{DASHBOARD_API_URL}/calls",
            json=call_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            print(f"✅ Call logged to dashboard: {call_data.get('callId', 'Unknown')}")
            return response.json()
        else:
            print(f"⚠️ Dashboard logging failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Dashboard logging error: {e}")
        return None

def update_call_in_dashboard(call_id, update_data):
    """Update call in dashboard backend"""
    try:
        response = requests.patch(
            f"{DASHBOARD_API_URL}/calls/{call_id}",
            json=update_data,
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Call updated in dashboard: {call_id}")
            return response.json()
        else:
            print(f"⚠️ Dashboard update failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Dashboard update error: {e}")
        return None

def update_call_transcript(call_id, transcript_text):
    """Update call transcript in dashboard backend"""
    try:
        response = requests.patch(
            f"{DASHBOARD_API_URL}/calls/{call_id}/transcript",
            json={'transcript': transcript_text},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️ Transcript update failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Transcript update error: {e}")
        return None

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
        
        # Initialize product-aware conversation components
        if PRODUCT_AWARE:
            try:
                global product_service, prompt_builder
                product_service = get_product_service()
                prompt_builder = get_prompt_builder()
                bot_app.product_service = product_service
                bot_app.prompt_builder = prompt_builder
                print("✅ Product-aware conversation system initialized")
            except Exception as pe:
                print(f"⚠️ Product service initialization error: {pe}")
                bot_app.product_service = None
                bot_app.prompt_builder = None
        
    except Exception as e:
        print(f"❌ Error initializing AI components: {e}")
        bot_app.stt = None
        bot_app.gpt = None
        bot_app.enhanced_tts = None
        bot_app.product_service = None
        bot_app.prompt_builder = None
    
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
        
        from_number = request.form.get('From', 'Unknown')
        to_number = request.form.get('To', 'Unknown')
        call_sid = request.form.get('CallSid')
        print(f"📞 Incoming call from: {from_number} to {to_number}")
        print(f"🔍 DEBUG: Request form data: {dict(request.form)}")
        print(f"🔍 DEBUG: Request args: {dict(request.args)}")
        
        # Check if realtime mode is available and requested
        realtime_mode = request.args.get('realtime', 'false').lower() == 'true'
        print(f"🔍 Realtime mode requested: {realtime_mode}")
        print(f"🔍 REALTIME_AVAILABLE: {REALTIME_AVAILABLE}")
        
        if REALTIME_AVAILABLE and realtime_mode:
            # Use enhanced real-time conversation with shorter timeouts
            print("🚀 Starting realtime conversation mode")
            
            # Fetch active product for product-aware conversation
            active_product = None
            if PRODUCT_AWARE and hasattr(bot_app, 'product_service') and bot_app.product_service:
                try:
                    active_product = bot_app.product_service.get_active_product()
                    print(f"🛍️ Active product: {active_product.get('name') if active_product else 'None'}")
                except Exception as e:
                    print(f"⚠️ Error fetching active product: {e}")
            
            # Store product in call session
            if call_sid:
                global call_sessions
                call_sessions[call_sid] = {
                    'product': active_product,
                    'messages': [],
                    'redirect_count': 0
                }
            
            # Log call start to dashboard with product metadata
            call_data = {
                'callId': call_sid,
                'type': 'outbound',  # Bot is calling the user
                'caller': from_number,  # Twilio number
                'receiver': to_number,  # User's number
                'status': 'in-progress',
                'startTime': datetime.utcnow().isoformat() + 'Z',
                'language': 'mixed',
                'metadata': {}
            }
            
            # Add product context if available
            if active_product:
                call_data['metadata']['product_name'] = active_product.get('name', 'Unknown')
                call_data['metadata']['product_id'] = active_product.get('product_id', '')
                call_data['metadata']['product_category'] = active_product.get('category', '')
                print(f"📊 Call logged with product: {active_product.get('name')}")
            
            log_call_to_dashboard(call_data)
            
            # Generate product-specific greeting
            if active_product:
                greeting = active_product.get('greeting') or f"Namaste! Main Sara hun. Aapko {active_product.get('name', 'our product')} mein madad chahiye?"
                print(f"🎯 Using product-specific greeting for: {active_product.get('name')}")
            else:
                greeting = "Hi there!, I am Sara. How can I help you today?"
                print("📢 Using generic greeting (no active product)")
            
            try:
                from src.enhanced_hindi_tts import speak_mixed_enhanced
                
                # Generate greeting audio using available TTS providers
                audio_file = speak_mixed_enhanced(greeting)
                
                if audio_file and audio_file.endswith('.mp3'):
                    # Play the generated audio file
                    ngrok_url = get_ngrok_url()
                    if ngrok_url:
                        response.play(f"{ngrok_url}/audio/{audio_file}")
                        print(f"🎵 Playing TTS greeting: {audio_file}")
                    else:
                        print("❌ Ngrok URL not available, using Twilio fallback")
                        response.say(greeting, voice='Polly.Aditi', language='hi-IN')
                else:
                    # Fallback to Twilio voice
                    response.say(greeting, voice='Polly.Aditi', language='hi-IN')
                    print("⚠️ Using Twilio fallback for greeting")
                    
            except Exception as e:
                print(f"❌ TTS greeting error: {e}")
                # Fallback to Twilio voice
                response.say(greeting, voice='Polly.Aditi', language='hi-IN')
            
                # Add natural pause after greeting
                response.pause(length=0.2)
            
            # Use optimized gather settings for better speech recognition and interruption
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=5,  # Increased timeout to allow more time for speech
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
        from_number = request.form.get('From', 'Unknown')
        call_sid = request.form.get('CallSid')
        
        print(f"⚡ Real-time caller {from_number} said: {speech_result}")
        print(f"🔍 DEBUG: bot_app.gpt exists: {bot_app.gpt is not None}")
        
        # Update transcript in dashboard
        if call_sid and speech_result:
            timestamp = datetime.utcnow().strftime('%H:%M:%S')
            transcript_text = f"\n[{timestamp}] User: {speech_result}"
            update_call_transcript(call_sid, transcript_text)
        
        # Check for interruption
        interruption_detected = False
        if call_sid and call_sid in bot_app.call_language:
            if isinstance(bot_app.call_language[call_sid], dict):
                interruption_detected = bot_app.call_language[call_sid].get('interruption_detected', False)
                # Reset interruption flag
                bot_app.call_language[call_sid]['interruption_detected'] = False
                bot_app.call_language[call_sid]['partial_speech_count'] = 0
        
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
                        print(f"⚠️ Inappropriate content detected from {from_number}")
                        bot_response = get_appropriate_response(detected_language)
                    else:
                        # Get product and conversation context from session
                        session = call_sessions.get(call_sid, {})
                        active_product = session.get('product')
                        conversation_history = session.get('messages', [])
                        
                        # Build dynamic prompt with product context
                        if PRODUCT_AWARE and hasattr(bot_app, 'prompt_builder') and bot_app.prompt_builder:
                            try:
                                enhanced_prompt = bot_app.prompt_builder.build_prompt(
                                    product=active_product,
                                    conversation_history=conversation_history,
                                    detected_language=detected_language
                                )
                                print(f"🔍 Using product-aware dynamic prompt (product: {active_product.get('name') if active_product else 'generic'})")
                            except Exception as e:
                                print(f"⚠️ Prompt builder error: {e}")
                                enhanced_prompt = f"You are Sara, a helpful female AI assistant. Respond naturally and conversationally in {detected_language}. Be warm, friendly, and helpful. Keep responses concise but natural. Always maintain a professional and respectful tone."
                        else:
                            enhanced_prompt = f"You are Sara, a helpful female AI assistant. Respond naturally and conversationally in {detected_language}. Be warm, friendly, and helpful. Keep responses concise but natural. Always maintain a professional and respectful tone."
                        
                        print(f"🔍 Calling AI with prompt: {enhanced_prompt[:100]}...")
                        print(f"🔍 User input: {speech_result}")
                        bot_response = bot_app.gpt.ask(f"{enhanced_prompt}\n\nUser: {speech_result}", detected_language)
                        print(f"⚡ Sara's natural response ({detected_language}): '{bot_response}'")
                        print(f"🔍 Response type: {type(bot_response)}")
                        print(f"🔍 Response length: {len(bot_response) if bot_response else 0}")
                        
                        # Update conversation history in session
                        if call_sid and call_sid in call_sessions:
                            call_sessions[call_sid]['messages'].append({
                                'role': 'user',
                                'content': speech_result
                            })
                            if bot_response:
                                call_sessions[call_sid]['messages'].append({
                                    'role': 'assistant',
                                    'content': bot_response
                                })
                        
                        # Log bot response to transcript
                        if call_sid and bot_response:
                            timestamp = datetime.utcnow().strftime('%H:%M:%S')
                            transcript_text = f"\n[{timestamp}] Sara ({detected_language}): {bot_response}"
                            update_call_transcript(call_sid, transcript_text)
                else:
                    # Quick fallback with Sara's responses
                    if detected_language == 'hi':
                        bot_response = f"हाँ, मैं समझ गई। {speech_result}"
                    else:
                        bot_response = f"Yes, I understand. {speech_result}"
                
                # Check for hangup/goodbye keywords BEFORE playing audio
                hangup_keywords = {
                    'en': ['bye', 'goodbye', 'good bye', 'bye bye', 'end call', 'hang up', 'hangup', 'disconnect', 'thank you bye', 'thanks bye'],
                    'hi': ['बाय', 'बाय बाय', 'अलविदा', 'धन्यवाद', 'ठीक है बाय', 'रखती हूं', 'रखता हूं', 'चलता हूं', 'चलती हूं', 'फोन रख दो', 'रख दो'],
                    'mixed': ['bye', 'बाय', 'बाय बाय', 'bye bye', 'alvida', 'chalta hu', 'chalti hu', 'phone rakh do']
                }
                
                # Check if user wants to end call
                speech_lower = speech_result.lower() if speech_result else ''
                should_hangup = False
                
                for lang in ['en', 'hi', 'mixed']:
                    if any(keyword in speech_lower or keyword in speech_result for keyword in hangup_keywords.get(lang, [])):
                        should_hangup = True
                        print(f"🔚 Hangup keyword detected: '{speech_result}'")
                        break
                
                # Also check if bot response contains goodbye indicators
                if bot_response:
                    bot_lower = bot_response.lower()
                    if any(word in bot_lower for word in ['bye', 'goodbye', 'alvida', 'शुभ', 'धन्यवाद']) and any(word in speech_lower for word in ['bye', 'बाय', 'नहीं']):
                        should_hangup = True
                        print(f"🔚 Conversation ending detected in bot response")
                
                if should_hangup:
                    print("📞 Ending call gracefully...")
                    response.hangup()
                    return str(response)
                
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
                
                # Use enhanced TTS with consistent voice and interruption support
                try:
                    from src.enhanced_hindi_tts import speak_mixed_enhanced
                    
                    # Generate audio file using available TTS providers
                    audio_file = speak_mixed_enhanced(bot_response)
                    
                    # Create gather with barge-in BEFORE playing audio (enables interruption)
                    gather = response.gather(
                        input='speech',
                        action='/process_speech_realtime',
                        timeout=3,
                        speech_timeout='auto',
                        language='en-IN' if detected_language == 'en' else 'hi-IN',
                        partial_result_callback='/partial_speech',
                        enhanced='true',
                        profanity_filter='false'
                    )
                    
                    if audio_file and audio_file.endswith('.mp3'):
                        # Play audio INSIDE gather with barge-in enabled
                        ngrok_url = get_ngrok_url()
                        if ngrok_url:
                            gather.play(f"{ngrok_url}/audio/{audio_file}")
                            print(f"🎵 Playing TTS audio: {audio_file} (interruption enabled)")
                        else:
                            print("❌ Ngrok URL not available, using Twilio fallback")
                            if detected_language in ['hi', 'mixed']:
                                gather.say(bot_response, voice='Polly.Aditi', language='hi-IN')
                            else:
                                gather.say(bot_response, voice='Polly.Joanna', language='en-IN')
                    else:
                        # Fallback to Twilio voices inside gather
                        if detected_language in ['hi', 'mixed']:
                            gather.say(bot_response, voice='Polly.Aditi', language='hi-IN')
                        else:
                            gather.say(bot_response, voice='Polly.Joanna', language='en-IN')
                        
                        print("⚠️ Using Twilio fallback voices")
                    
                    # Add brief pause after speaking
                    gather.pause(length=0.2)
                    
                    response.append(gather)
                        
                except Exception as e:
                    print(f"❌ TTS error: {e}")
                    # Fallback to Twilio voices
                    if detected_language in ['hi', 'mixed']:
                        response.say(bot_response, voice='Polly.Aditi', language='hi-IN')
                    else:
                        response.say(bot_response, voice='Polly.Joanna', language='en-IN')
                    
                    # Add gather after error fallback
                    gather = response.gather(
                        input='speech',
                        action='/process_speech_realtime',
                        timeout=3,
                        speech_timeout='auto',
                        language='en-IN' if detected_language == 'en' else 'hi-IN',
                        partial_result_callback='/partial_speech',
                        enhanced='true',
                        profanity_filter='false'
                    )
                    response.append(gather)
                
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
                
                # Add gather after error
                gather = response.gather(
                    input='speech',
                    action='/process_speech_realtime',
                    timeout=3,
                    speech_timeout='auto',
                    language='en-IN',
                    partial_result_callback='/partial_speech',
                    enhanced='true',
                    profanity_filter='false'
                )
                response.append(gather)
            
        else:
            # No speech detected - optimized recovery with faster interruption
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=3,  # Shorter timeout for faster interruption detection
                language='en-IN',
                partial_result_callback='/partial_speech',
                enhanced='true',  # Use enhanced speech recognition
                profanity_filter='false'  # Don't filter speech
            )
            response.append(gather)
        
        return str(response)
    
    @bot_app.route('/partial_speech', methods=['POST'])
    def partial_speech():
        """Handle partial speech results for faster interruption detection"""
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
            
            # Interruption detection - if user speaks 3+ words, mark as interruption
            word_count = len(partial_result.strip().split())
            if word_count >= 3 or bot_app.call_language[call_sid]['partial_speech_count'] >= 3:
                print(f"🔔 Interruption detected! User speaking during bot response")
                bot_app.call_language[call_sid]['interruption_detected'] = True
            
            # Faster interruption detection - trigger after just 2 partial results
            if bot_app.call_language[call_sid]['partial_speech_count'] >= 2:
                current_length = len(partial_result)
                last_length = len(bot_app.call_language[call_sid].get('last_partial', ''))
                
                # If speech is getting longer and more confident, it's an interruption
                if current_length > last_length and len(partial_result) > 2:
                    print(f"🛑 Interruption detected! User said: {partial_result}")
                    # Mark for interruption handling
                    bot_app.call_language[call_sid]['interruption_detected'] = True
                    bot_app.call_language[call_sid]['interruption_text'] = partial_result
        
        return '', 200
    
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
        
        # Update call in dashboard when completed
        # Map Twilio status to our model status
        status_mapping = {
            'completed': 'success',
            'busy': 'failed',
            'failed': 'failed',
            'no-answer': 'missed',
            'canceled': 'failed'
        }
        
        if call_status in status_mapping:
            update_data = {
                'status': status_mapping[call_status],
                'endTime': datetime.utcnow().isoformat() + 'Z'
            }
            update_call_in_dashboard(call_sid, update_data)
        
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
            voice_bot_app.run(host='0.0.0.0', port=8000, debug=False, use_reloader=False)
        
        bot_thread = threading.Thread(target=run_voice_bot_server, daemon=True)
        bot_thread.start()
        
        # Wait for server to start
        for i in range(15):
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    running_services['voice_bot_server'] = bot_thread
                    print("✅ Voice bot server started on port 8000!")
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
        ngrok_process = subprocess.Popen(['ngrok', 'http', '8000'], 
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
        
        # Make the call with status callback
        status_callback_url = f"{ngrok_url}/status"
        print("📞 Initiating call...")
        call = client.calls.create(
            to=phone_number,
            from_=twilio_number,
            url=webhook_url,
            status_callback=status_callback_url,
            status_callback_event=['completed', 'busy', 'failed', 'no-answer', 'canceled']
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
        
        # Make the call with status callback
        status_callback_url = f"{ngrok_url}/status"
        print("📞 Initiating real-time call...")
        call = client.calls.create(
            to=phone_number,
            from_=twilio_number,
            url=webhook_url,
            status_callback=status_callback_url,
            status_callback_event=['completed', 'busy', 'failed', 'no-answer', 'canceled']
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

def main_menu():
    """Main menu system"""
    while True:
        clear_screen()
        print("🤖 AI CALLING BOT")
        print("🌐 Hindi + English Support")
        if REALTIME_AVAILABLE:
            print("⚡ Real-time Conversation Mode Available")
        print("-" * 30)
        print("1. 📞 Call a number")
        print("2. 📱 Call me")
        if REALTIME_AVAILABLE:
            print("3. ⚡ Call with real-time mode")
            print("4. 🎤 Test real-time locally")
            print("5. 🔍 Status")
            print("6. 🧪 Test")
            print("7. 🎤 Voice bot")
            print("8. ❌ Exit")
        else:
            print("3. 🔍 Status")
            print("4. 🧪 Test")
            print("5. 🎤 Voice bot")
            print("6. ❌ Exit")
        print("-" * 30)
        
        max_choice = 8 if REALTIME_AVAILABLE else 6
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
            
        elif choice == ("5" if REALTIME_AVAILABLE else "3"):
            show_status()
            input("\nPress Enter to continue...")
            
        elif choice == ("6" if REALTIME_AVAILABLE else "4"):
            print("🧪 Running tests...")
            try:
                subprocess.run([sys.executable, "test_mixed_language.py"], check=True)
            except:
                print("❌ Test failed")
            input("\nPress Enter to continue...")
            
        elif choice == ("7" if REALTIME_AVAILABLE else "5"):
            print("🎤 Starting traditional voice bot...")
            print("💡 Speak Hindi or English!")
            try:
                subprocess.run([sys.executable, "-m", "src.voice_bot"])
            except KeyboardInterrupt:
                print("\n🎤 Stopped.")
            input("\nPress Enter to continue...")
            
        elif choice == ("8" if REALTIME_AVAILABLE else "6"):
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