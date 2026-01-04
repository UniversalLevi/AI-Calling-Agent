"""
AI Calling Bot - Complete Self-Contained Launcher
===============================================

This is the ONLY file you need to run. It handles everything:
- Auto-checks and installs dependencies
- Audio server startup
- Voice bot server startup  
- Ngrok tunnel startup
- Clean menu system
- Mixed language support (Hindi + English)
- Product-aware conversations
- Dashboard integration
- Voice interruptions

Just run: python main.py
"""

# First, check and install dependencies
print("\n" + "="*60)
print("🤖 SARA AI CALLING BOT - Initializing...")
print("="*60)

import sys

# Check dependencies before importing other modules
print("\n🔧 Checking system dependencies...")
try:
    from dependency_checker import run_full_check
    
    # Run dependency check with minimal output during imports
    if not run_full_check(auto_install=True, verbose=False):
        print("\n❌ Some dependencies failed to install.")
        print("   Attempting to continue anyway...")
        print("   You may encounter errors. Consider running: pip install -r requirements.txt\n")
except ImportError:
    print("⚠️  Dependency checker not available. Continuing...")
except Exception as e:
    print(f"⚠️  Dependency check warning: {e}")
    print("   Continuing anyway...\n")

# Now import remaining modules
import os
import time
import threading
import subprocess
from pathlib import Path
import signal
import requests
import warnings
from flask import Flask, request, send_file, Response
from twilio.twiml.voice_response import VoiceResponse
from datetime import datetime, timezone

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

# Import WhatsApp integration
try:
    from src.whatsapp_integration import (
        trigger_payment_link,
        trigger_followup,
        detect_payment_link_intent,
        detect_payment_confirmation_intent,
        detect_number_confirmation,
        extract_phone_from_text,
        is_whatsapp_enabled,
        is_payment_links_enabled,
        get_whatsapp_status
    )
    WHATSAPP_AVAILABLE = True
    if is_whatsapp_enabled():
        print("✅ WhatsApp integration available and ENABLED")
    else:
        print("⚠️ WhatsApp integration available but DISABLED (set ENABLE_WHATSAPP=true to enable)")
except ImportError as e:
    WHATSAPP_AVAILABLE = False
    print(f"⚠️ WhatsApp integration not available: {e}")

# Import Direct WhatsApp integration (simplified, production-ready)
try:
    from src.whatsapp_direct import (
        send_payment_link_sync,
        send_message_sync,
        get_whatsapp_greeting_prompt,
        should_send_payment_link,
        mark_payment_link_sent,
        is_configured as is_whatsapp_direct_configured,
        is_payment_enabled as is_direct_payment_enabled,
        get_status as get_direct_whatsapp_status,
        WHATSAPP_BUSINESS_NUMBER
    )
    WHATSAPP_DIRECT_AVAILABLE = True
    if is_whatsapp_direct_configured():
        print("✅ WhatsApp Direct integration READY")
    else:
        print("⚠️ WhatsApp Direct available but not configured")
except ImportError as e:
    WHATSAPP_DIRECT_AVAILABLE = False
    WHATSAPP_BUSINESS_NUMBER = "+91 91791 77847"
    print(f"⚠️ WhatsApp Direct not available: {e}")

# Import SMS service for WhatsApp opt-in (disabled for India due to carrier blocking)
try:
    from src.services.sms_service import (
        send_whatsapp_optin_sms,
        send_payment_link_sms,
        has_optin_sms_been_sent,
        ENABLE_WHATSAPP_OPTIN_SMS
    )
    SMS_SERVICE_AVAILABLE = True
    # SMS to India is blocked by carriers, so we disable by default
    if ENABLE_WHATSAPP_OPTIN_SMS:
        print("⚠️ SMS service enabled (may not work for Indian numbers)")
    else:
        print("📱 SMS opt-in disabled (using verbal prompt instead)")
except ImportError as e:
    SMS_SERVICE_AVAILABLE = False
    ENABLE_WHATSAPP_OPTIN_SMS = False
    print(f"⚠️ SMS service not available: {e}")

# Production mode detection
PRODUCTION_MODE = os.getenv('FLASK_ENV', 'development') == 'production'
BASE_URL = os.getenv('BASE_URL', '')  # Set this in production (e.g., https://yourdomain.com)

if PRODUCTION_MODE:
    print("🏭 Running in PRODUCTION mode")
    if BASE_URL:
        print(f"🌐 Base URL: {BASE_URL}")
    else:
        print("⚠️ BASE_URL not set! Set BASE_URL environment variable for production")
else:
    print("🔧 Running in DEVELOPMENT mode (ngrok required)")

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

def cleanup_old_sessions():
    """Clean up old call sessions (older than 1 hour)"""
    try:
        from datetime import datetime, timezone, timedelta
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=1)
        
        sessions_to_remove = []
        for call_sid, session in call_sessions.items():
            # Check if session has a timestamp
            created_at = session.get('created_at')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        session_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        session_time = created_at
                    
                    if session_time < cutoff_time:
                        sessions_to_remove.append(call_sid)
                except:
                    pass
        
        for call_sid in sessions_to_remove:
            del call_sessions[call_sid]
            print(f"🧹 Cleaned up old session: {call_sid}")
        
        if sessions_to_remove:
            print(f"🧹 Cleaned up {len(sessions_to_remove)} old session(s)")
    except Exception as e:
        print(f"⚠️ Session cleanup error: {e}")

# Dashboard integration
DASHBOARD_API_URL = os.environ.get("DASHBOARD_API_URL", "http://localhost:5016/api")

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

def log_payment_to_dashboard(payment_data):
    """Log payment link to dashboard backend"""
    try:
        response = requests.post(
            f"{DASHBOARD_API_URL}/payments",
            json=payment_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            print(f"✅ Payment logged to dashboard: {payment_data.get('razorpayLinkId', 'Unknown')}")
            return response.json()
        else:
            print(f"⚠️ Payment logging failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ Payment logging error: {e}")
        return None

def log_whatsapp_message_to_dashboard(message_data):
    """Log WhatsApp message to dashboard backend"""
    try:
        response = requests.post(
            f"{DASHBOARD_API_URL}/whatsapp/messages",
            json=message_data,
            timeout=5
        )
        if response.status_code in [200, 201]:
            print(f"✅ WhatsApp message logged to dashboard: {message_data.get('messageId', 'Unknown')}")
            return response.json()
        else:
            print(f"⚠️ WhatsApp logging failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ WhatsApp logging error: {e}")
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
        """Serve audio files with proper headers for streaming"""
        audio_dir = Path("audio_files")
        file_path = audio_dir / filename
        
        if not file_path.exists():
            print(f"❌ Audio file not found: {filename}")
            return "Audio file not found", 404
        
        try:
            # Get file size for Content-Length header
            file_size = file_path.stat().st_size
            
            # Determine MIME type based on extension
            if filename.endswith('.mp3'):
                mimetype = 'audio/mpeg'
            elif filename.endswith('.wav'):
                mimetype = 'audio/wav'
            elif filename.endswith('.ogg'):
                mimetype = 'audio/ogg'
            else:
                mimetype = 'audio/mpeg'  # Default
            
            # Check for Range header (for partial content support)
            range_header = request.headers.get('Range', None)
            
            if range_header:
                # Parse range header
                import re
                match = re.search(r'bytes=(\d+)-(\d*)', range_header)
                if match:
                    start = int(match.group(1))
                    end = int(match.group(2)) if match.group(2) else file_size - 1
                    length = end - start + 1
                    
                    # Read partial content
                    with open(file_path, 'rb') as f:
                        f.seek(start)
                        data = f.read(length)
                    
                    response = Response(
                        data,
                        206,  # Partial Content
                        mimetype=mimetype,
                        headers={
                            'Content-Range': f'bytes {start}-{end}/{file_size}',
                            'Accept-Ranges': 'bytes',
                            'Content-Length': str(length),
                            'Cache-Control': 'public, max-age=3600'
                        },
                        direct_passthrough=True
                    )
                    return response
            
            # Full file response
            print(f"🔊 Serving audio: {filename} ({file_size} bytes)")
            response = send_file(
                file_path,
                mimetype=mimetype,
                as_attachment=False
            )
            
            # Add headers for better streaming
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Content-Length'] = str(file_size)
            response.headers['Cache-Control'] = 'public, max-age=3600'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            return response
            
        except Exception as e:
            print(f"❌ Error serving audio {filename}: {e}")
            return f"Error serving audio: {str(e)}", 500
    
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
                    if active_product:
                        print(f"🛍️ Active product: {active_product.get('name')}")
                        print(f"💰 Product price: {active_product.get('price')} (type: {type(active_product.get('price')).__name__})")
                    else:
                        print(f"🛍️ No active product found")
                except Exception as e:
                    print(f"⚠️ Error fetching active product: {e}")
            
            # Store product in call session along with caller's phone number
            if call_sid:
                global call_sessions
                from datetime import datetime, timezone
                call_sessions[call_sid] = {
                    'product': active_product,
                    'messages': [],
                    'redirect_count': 0,
                    'caller_phone': to_number,  # User's phone number (we called them)
                    'customer_name': None,  # Will be extracted from conversation
                    'payment_link_sent': False,
                    'awaiting_number_confirmation': False,  # For payment link flow
                    'created_at': datetime.now(timezone.utc).isoformat()  # Track creation time for cleanup
                }
                print(f"📱 Caller phone stored: {to_number[:6]}****{to_number[-4:] if len(to_number) > 10 else to_number}")
            
            # SMS opt-in disabled - Indian carriers block international SMS (Error 30044)
            # WhatsApp works directly if user has messaged the business number before
            # The WhatsApp integration sends messages directly without SMS opt-in
            
            # Log call start to dashboard with product metadata
            call_data = {
                'callId': call_sid,
                'type': 'outbound',  # Bot is calling the user
                'caller': from_number,  # Twilio number
                'receiver': to_number,  # User's number
                'status': 'in-progress',
                'startTime': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
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
            
            # Generate product-specific greeting (casual, human, not robotic)
            # Always use fresh natural greeting, ignore old stored greetings
            if active_product:
                product_name = active_product.get('name', 'product')
                # Use natural, conversational greeting - ignore stored greeting as it may be outdated
                base_greeting = f"Hey! Sara here. {product_name} ke baare mein call kiya – suna hai aap interested ho?"
                print(f"🎯 Using product-specific greeting for: {product_name}")
            else:
                base_greeting = "Hey! Sara here. Kaise ho? Bataiye kya help kar sakti hun aaj?"
                print("📢 Using generic greeting (no active product)")
            
            # Use simple greeting (SMS handles WhatsApp opt-in)
            greeting = base_greeting
            
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
                timeout=8,  # Generous timeout for natural conversation
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
                timeout=8,
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
                timeout=8,
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
        
        # Reset no-response counter since user spoke
        if call_sid and call_sid in bot_app.call_language:
            if isinstance(bot_app.call_language[call_sid], dict):
                bot_app.call_language[call_sid]['no_response_count'] = 0
        
        # Update transcript in dashboard
        if call_sid and speech_result:
            timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
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
                        
                        # Build dynamic prompt with product context and call state
                        if PRODUCT_AWARE and hasattr(bot_app, 'prompt_builder') and bot_app.prompt_builder:
                            try:
                                # Build call state for prompt context
                                call_state = {
                                    'payment_link_success': session.get('payment_link_success', False),
                                    'whatsapp_needs_optin': session.get('whatsapp_needs_optin', False),
                                    'asked_if_done': session.get('asked_if_done', False),
                                    'customer_name': session.get('customer_name', '')
                                }
                                
                                enhanced_prompt = bot_app.prompt_builder.build_prompt(
                                    product=active_product,
                                    conversation_history=conversation_history,
                                    detected_language=detected_language,
                                    call_state=call_state
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
                            
                            # Try to extract customer name from user's speech
                            # Common patterns: "mera naam X hai", "my name is X", "I am X"
                            if not call_sessions[call_sid].get('customer_name'):
                                import re
                                name_patterns = [
                                    r'(?:my name is|i am|this is|naam hai|mera naam|naam)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
                                    r'^([A-Z][a-z]+)(?:\s+(?:here|speaking|hai|hun|hoon))?$',
                                ]
                                for pattern in name_patterns:
                                    match = re.search(pattern, speech_result, re.IGNORECASE)
                                    if match:
                                        name = match.group(1).strip().title()
                                        if len(name) > 2 and name.lower() not in ['yes', 'no', 'hello', 'hi', 'haan', 'nahi']:
                                            call_sessions[call_sid]['customer_name'] = name
                                            print(f"👤 Customer name extracted: {name}")
                                            break
                        
                        # Log bot response to transcript
                        if call_sid and bot_response:
                            timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
                            transcript_text = f"\n[{timestamp}] Sara ({detected_language}): {bot_response}"
                            update_call_transcript(call_sid, transcript_text)
                        
                        # =====================================================
                        # WHATSAPP PAYMENT LINK - Smart Flow with Retry
                        # Gathers customer details first, then sends link
                        # =====================================================
                        whatsapp_ready = (WHATSAPP_DIRECT_AVAILABLE and is_whatsapp_direct_configured()) or (WHATSAPP_AVAILABLE and is_payment_links_enabled())
                        
                        if whatsapp_ready:
                            try:
                                session = call_sessions.get(call_sid, {})
                                caller_phone = session.get('caller_phone') or request.form.get('To', '')
                                
                                # Check if we should send payment link
                                intent_detected = detect_payment_link_intent(speech_result, detected_language)
                                confirmation_detected = detect_payment_confirmation_intent(speech_result, detected_language)
                                
                                # Count payment link attempts (allow retries)
                                link_attempts = session.get('payment_link_attempts', 0)
                                link_sent_successfully = session.get('payment_link_success', False)
                                
                                # Get customer name from session (handle None safely)
                                customer_name = session.get('customer_name') or ''
                                customer_name = customer_name.strip() if customer_name else ''
                                has_customer_name = bool(customer_name) and customer_name.lower() not in ['customer', '']
                                
                                # Only send if: we have customer name OR they explicitly ask for link
                                # "खरीदना है" alone should NOT trigger - bot should ask for name first
                                should_try_send = False
                                if not link_sent_successfully and caller_phone:
                                    if intent_detected:  # Explicit "send me link" request
                                        should_try_send = True
                                    elif confirmation_detected and has_customer_name:
                                        # Only auto-send on confirmation if we already have their name
                                        should_try_send = True
                                
                                if should_try_send:
                                    intent_type = "explicit request" if intent_detected else "payment confirmation"
                                    print(f"📱 WhatsApp: Detected {intent_type} (attempt {link_attempts + 1})")
                                    
                                    # Get product info from session (fetched from dashboard)
                                    active_product = session.get('product', {}) or {}
                                    product_name = active_product.get('name', 'Service') or 'Service'
                                    
                                    # Get price from product (dashboard stores in rupees)
                                    raw_price = active_product.get('price')
                                    
                                    # Convert price to paise (integer)
                                    # Dashboard stores prices in RUPEES (e.g., 2000 for ₹2000)
                                    try:
                                        if raw_price is None:
                                            product_price = 200000  # Default ₹2000
                                        elif isinstance(raw_price, str):
                                            # Remove currency symbols and convert
                                            clean_price = raw_price.replace('₹', '').replace(',', '').strip()
                                            try:
                                                rupees = float(clean_price)
                                                product_price = int(rupees * 100)  # Convert rupees to paise
                                            except ValueError:
                                                product_price = 200000  # Default if string like "Contact us"
                                        elif isinstance(raw_price, (int, float)):
                                            # Dashboard stores in rupees, so always multiply by 100
                                            product_price = int(raw_price * 100)
                                        else:
                                            product_price = 200000  # Default ₹2000
                                    except (ValueError, TypeError):
                                        product_price = 200000  # Default ₹2000
                                    
                                    # Minimum ₹1 (100 paise)
                                    if product_price < 100:
                                        product_price = 100
                                    
                                    # Use extracted customer_name, fallback to 'Customer'
                                    display_name = customer_name if has_customer_name else 'Customer'
                                    
                                    print(f"📱 WhatsApp: Sending to {caller_phone[:6]}****{caller_phone[-4:]}")
                                    print(f"📱 WhatsApp: Raw price from product: {raw_price} (type: {type(raw_price).__name__ if raw_price else 'None'})")
                                    print(f"📱 WhatsApp: Converted price: {product_price} paise (₹{product_price/100:.0f})")
                                    print(f"📱 WhatsApp: Product={product_name}, Price=₹{product_price/100:.0f}, Customer={display_name}")
                                    
                                    # Send payment link synchronously to check result
                                    try:
                                        if WHATSAPP_DIRECT_AVAILABLE and is_whatsapp_direct_configured():
                                            print(f"📱 WhatsApp: Attempting to send payment link...")
                                            result = send_payment_link_sync(
                                                phone=caller_phone,
                                                amount=product_price,
                                                customer_name=display_name or 'Customer',
                                                product_name=product_name or 'Service',
                                                call_id=call_sid,
                                                language=detected_language if detected_language != 'mixed' else 'hi',
                                                fire_and_forget=False  # Wait for result
                                            )
                                            if result and result.get('success'):
                                                if call_sid in call_sessions:
                                                    call_sessions[call_sid]['payment_link_success'] = True
                                                    call_sessions[call_sid]['payment_link_url'] = result.get('payment_link')
                                                    call_sessions[call_sid]['whatsapp_needs_optin'] = False
                                                msg_id = result.get('message_id', 'N/A')
                                                payment_link = result.get('payment_link', 'N/A')
                                                razorpay_id = result.get('razorpay_link_id', '')
                                                print(f"✅ WhatsApp: Payment link sent successfully!")
                                                print(f"📱 Message ID: {msg_id}")
                                                print(f"🔗 Payment Link: {payment_link}")
                                                print(f"📞 Phone: {caller_phone}")
                                                
                                                # Log payment to dashboard
                                                log_payment_to_dashboard({
                                                    'razorpayLinkId': razorpay_id or f"link_{call_sid}_{int(time.time())}",
                                                    'callId': call_sid,
                                                    'phone': caller_phone,
                                                    'customerName': display_name or 'Customer',
                                                    'amount': product_price * 100 if product_price < 1000 else product_price,  # Convert to paise if needed
                                                    'amountDisplay': product_price / 100 if product_price > 10000 else product_price,
                                                    'productName': product_name or 'Service',
                                                    'shortUrl': payment_link,
                                                    'whatsappMessageId': msg_id,
                                                    'status': 'sent'
                                                })
                                                
                                                # Log WhatsApp message to dashboard
                                                log_whatsapp_message_to_dashboard({
                                                    'messageId': msg_id,
                                                    'callId': call_sid,
                                                    'phone': caller_phone,
                                                    'customerName': display_name or 'Customer',
                                                    'direction': 'outbound',
                                                    'type': 'payment_link',
                                                    'content': f"Payment link for {product_name}: {payment_link}",
                                                    'paymentLinkUrl': payment_link,
                                                    'status': 'sent'
                                                })
                                                
                                                # Override bot response to confirm link was sent
                                                name_part = f"{display_name} , " if display_name and display_name.lower() != 'customer' else ""
                                                bot_response = f"Done! {name_part}Payment link bhej diya hai aapke WhatsApp pe. Check kar lijiye! Kuch aur help chahiye?"
                                                # Mark that we just sent the link THIS turn - don't override with satisfied check
                                                call_sessions[call_sid]['payment_link_just_sent'] = True
                                                print(f"📱 Set payment_link_just_sent=True for call {call_sid}")
                                            elif result and result.get('needs_optin'):
                                                # User hasn't opted in - need to guide them
                                                business_number = result.get('business_number', '')
                                                if call_sid in call_sessions:
                                                    call_sessions[call_sid]['whatsapp_needs_optin'] = True
                                                    call_sessions[call_sid]['whatsapp_business_number'] = business_number
                                                    call_sessions[call_sid]['pending_payment_link'] = {
                                                        'amount': product_price,
                                                        'product_name': product_name,
                                                        'customer_name': display_name
                                                    }
                                                print(f"⚠️ WhatsApp: User needs opt-in. Business number: {business_number}")
                                            else:
                                                error = result.get('error', 'Unknown') if result else 'No response'
                                                error_code = result.get('error_code', 'N/A') if result else 'N/A'
                                                needs_optin = result.get('needs_optin', False) if result else False
                                                print(f"❌ WhatsApp: Payment link failed - {error}")
                                                print(f"📋 Error code: {error_code}")
                                                print(f"📋 Needs opt-in: {needs_optin}")
                                                if needs_optin:
                                                    print(f"⚠️ User needs to send 'Hi' to WhatsApp business number first!")
                                        elif WHATSAPP_AVAILABLE:
                                            trigger_payment_link(
                                                phone=caller_phone,
                                                amount=product_price,
                                                customer_name=display_name,
                                                product_name=product_name,
                                                call_id=call_sid,
                                                language=detected_language,
                                                fire_and_forget=True
                                            )
                                    except Exception as e:
                                        print(f"❌ WhatsApp send error: {e}")
                                    
                                    # Track attempt
                                    if call_sid in call_sessions:
                                        call_sessions[call_sid]['payment_link_attempts'] = link_attempts + 1
                                        call_sessions[call_sid]['payment_link_sent_at'] = datetime.now(timezone.utc).isoformat()
                                        call_sessions[call_sid]['payment_link_phone'] = caller_phone
                                
                                # Check if user needs to opt-in and modify response
                                if session.get('whatsapp_needs_optin') and not session.get('payment_link_success'):
                                    business_number = session.get('whatsapp_business_number', '')
                                    if business_number and bot_response:
                                        # Append opt-in instruction to bot's response
                                        optin_prompt = f" Ek kaam kariye – {business_number} par WhatsApp pe 'Hi' bhej dijiye, phir main link bhej dungi!"
                                        bot_response = bot_response.rstrip('.!?') + "." + optin_prompt
                                        print(f"📱 WhatsApp: Added opt-in prompt to response")
                                
                                # Check if user confirms they sent the message (retry logic)
                                optin_confirmations = ['bhej diya', 'send kar diya', 'done', 'ho gaya', 'kar diya', 'sent', 'message bheja', 'hi bhej diya']
                                if session.get('whatsapp_needs_optin') and any(kw in speech_result.lower() for kw in optin_confirmations):
                                    print(f"📱 WhatsApp: User confirmed opt-in, retrying payment link...")
                                    pending = session.get('pending_payment_link', {})
                                    if pending:
                                        try:
                                            # Use pending values with safe defaults
                                            retry_result = send_payment_link_sync(
                                                phone=caller_phone,
                                                amount=pending.get('amount', 200000),  # Default ₹2000
                                                customer_name=pending.get('customer_name') or 'Customer',
                                                product_name=pending.get('product_name') or 'Service',
                                                call_id=call_sid,
                                                language=detected_language if detected_language != 'mixed' else 'hi',
                                                fire_and_forget=False
                                            )
                                            if retry_result and retry_result.get('success'):
                                                call_sessions[call_sid]['payment_link_success'] = True
                                                call_sessions[call_sid]['payment_link_url'] = retry_result.get('payment_link')
                                                call_sessions[call_sid]['whatsapp_needs_optin'] = False
                                                call_sessions[call_sid]['payment_link_just_sent'] = True
                                                print(f"✅ WhatsApp: Retry successful! Payment link sent.")
                                                # Modify response to confirm - warm and respectful
                                                bot_response = "Done! Link bhej diya hai WhatsApp pe. Check kar lijiye! Kuch aur help chahiye?"
                                            else:
                                                print(f"❌ WhatsApp: Retry failed")
                                        except Exception as retry_err:
                                            print(f"❌ WhatsApp retry error: {retry_err}")
                                
                                # Check if user says link didn't come - offer to resend
                                # Define speech_lower here for use in this scope
                                speech_lower_check = speech_result.lower() if speech_result else ''
                                
                                link_not_received_phrases = ['link nahi aayi', 'लिंक नहीं आई', 'link nahi aaya', 'लिंक नहीं आया',
                                                             'link nahi mila', 'लिंक नहीं मिला', 'link nahi mili', 'लिंक नहीं मिली',
                                                             'payment link nahi', 'पेमेंट लिंक नहीं', 'link nahi aayi hai', 'लिंक नहीं आई है',
                                                             'vaapas bhej', 'वापस भेज', 'phir se bhej', 'फिर से भेज', 'dobara bhej', 'दोबारा भेज',
                                                             'resend', 'link nahi aaya', 'लिंक नहीं आया', 'payment link nahi aaya', 'पेमेंट लिंक नहीं आया']
                                
                                # Also check for explicit resend requests (even if link was sent)
                                resend_request_phrases = ['vaapas bhej do', 'वापस भेज दो', 'phir se bhej do', 'फिर से भेज दो', 
                                                          'dobara bhej do', 'दोबारा भेज दो', 'bhej do', 'भेज दो', 'vaapas', 'वापस',
                                                          'phir se', 'फिर से', 'resend kar do', 'resend karo']
                                
                                # Check if user says link didn't come OR explicitly asks to resend
                                # BUT only if we didn't just send it this turn (give it a moment to arrive)
                                payment_just_sent_this_turn = session.get('payment_link_just_sent', False)
                                resend_attempts = session.get('resend_attempts', 0)
                                
                                link_not_received = session.get('payment_link_success') and not payment_just_sent_this_turn and any(phrase in speech_lower_check or phrase in speech_result for phrase in link_not_received_phrases)
                                explicit_resend = not payment_just_sent_this_turn and any(phrase in speech_lower_check or phrase in speech_result for phrase in resend_request_phrases)
                                
                                # Limit resend attempts to prevent spam (max 2 resends)
                                if (link_not_received or explicit_resend) and resend_attempts < 2:
                                    print(f"📱 WhatsApp: User says link didn't come, offering to resend... (attempt {resend_attempts + 1}/2)")
                                    # Get product info for resend
                                    active_product = session.get('product', {}) or {}
                                    product_name = active_product.get('name', 'Service') or 'Service'
                                    raw_price = active_product.get('price')
                                    try:
                                        if raw_price is None:
                                            product_price = 200000
                                        elif isinstance(raw_price, str):
                                            clean_price = raw_price.replace('₹', '').replace(',', '').strip()
                                            try:
                                                rupees = float(clean_price)
                                                product_price = int(rupees * 100)
                                            except ValueError:
                                                product_price = 200000
                                        elif isinstance(raw_price, (int, float)):
                                            product_price = int(raw_price * 100)
                                        else:
                                            product_price = 200000
                                    except:
                                        product_price = 200000
                                    
                                    if product_price < 100:
                                        product_price = 100
                                    
                                    # Resend the link
                                    try:
                                        if WHATSAPP_DIRECT_AVAILABLE and is_whatsapp_direct_configured():
                                            resend_result = send_payment_link_sync(
                                                phone=caller_phone,
                                                amount=product_price,
                                                customer_name=customer_name or 'Customer',
                                                product_name=product_name,
                                                call_id=call_sid,
                                                language=detected_language if detected_language != 'mixed' else 'hi',
                                                fire_and_forget=False
                                            )
                                            if resend_result and resend_result.get('success'):
                                                call_sessions[call_sid]['payment_link_just_sent'] = True
                                                call_sessions[call_sid]['resend_attempts'] = resend_attempts + 1
                                                msg_id = resend_result.get('message_id', 'N/A')
                                                payment_link = resend_result.get('payment_link', 'N/A')
                                                razorpay_id = resend_result.get('razorpay_link_id', '')
                                                print(f"✅ WhatsApp: Link resent successfully!")
                                                print(f"📱 Message ID: {msg_id}")
                                                print(f"🔗 Payment Link: {payment_link}")
                                                print(f"📞 Phone: {caller_phone}")
                                                
                                                # Log resent payment to dashboard
                                                log_payment_to_dashboard({
                                                    'razorpayLinkId': razorpay_id or f"link_{call_sid}_{int(time.time())}",
                                                    'callId': call_sid,
                                                    'phone': caller_phone,
                                                    'customerName': customer_name or 'Customer',
                                                    'amount': product_price * 100 if product_price < 1000 else product_price,
                                                    'amountDisplay': product_price / 100 if product_price > 10000 else product_price,
                                                    'productName': product_name,
                                                    'shortUrl': payment_link,
                                                    'whatsappMessageId': msg_id,
                                                    'status': 'sent',
                                                    'metadata': {'isResend': True, 'resendAttempt': resend_attempts + 1}
                                                })
                                                
                                                # Log resent WhatsApp message
                                                log_whatsapp_message_to_dashboard({
                                                    'messageId': msg_id,
                                                    'callId': call_sid,
                                                    'phone': caller_phone,
                                                    'customerName': customer_name or 'Customer',
                                                    'direction': 'outbound',
                                                    'type': 'payment_link',
                                                    'content': f"Payment link resend ({resend_attempts + 1}) for {product_name}: {payment_link}",
                                                    'paymentLinkUrl': payment_link,
                                                    'status': 'sent',
                                                    'metadata': {'isResend': True}
                                                })
                                                
                                                bot_response = "Theek hai ! Maine phir se link bhej diya hai WhatsApp pe. Ab check kar lijiye, mil jayega!"
                                            elif resend_result and resend_result.get('needs_optin'):
                                                # Still needs opt-in - this is the real issue!
                                                call_sessions[call_sid]['resend_attempts'] = resend_attempts + 1
                                                call_sessions[call_sid]['whatsapp_needs_optin'] = True
                                                business_number = resend_result.get('business_number', '')
                                                error_msg = resend_result.get('error', '24-hour messaging window closed')
                                                print(f"⚠️ WhatsApp: Opt-in required! Error: {error_msg}")
                                                print(f"📱 Business number: {business_number}")
                                                if business_number:
                                                    bot_response = f"Sorry , WhatsApp pe 'Hi' bhejna padega pehle {business_number} par. Phir main link bhej dungi!"
                                                else:
                                                    bot_response = "Sorry , WhatsApp pe pehle 'Hi' message bhejna padega. Phir main link bhej sakti hun."
                                            else:
                                                call_sessions[call_sid]['resend_attempts'] = resend_attempts + 1
                                                error = resend_result.get('error', 'Unknown') if resend_result else 'No response'
                                                error_code = resend_result.get('error_code', 'N/A') if resend_result else 'N/A'
                                                print(f"❌ WhatsApp resend failed: {error} (code: {error_code})")
                                                bot_response = "Sorry , kuch technical issue ho raha hai. Thodi der mein phir se try karte hain?"
                                    except Exception as resend_err:
                                        call_sessions[call_sid]['resend_attempts'] = resend_attempts + 1
                                        print(f"❌ WhatsApp resend error: {resend_err}")
                                        bot_response = "Sorry , abhi technical issue ho raha hai. Thodi der baad phir try karein?"
                                elif resend_attempts >= 2:
                                    # Already tried resending 2 times - don't keep trying
                                    print(f"⚠️ WhatsApp: Max resend attempts reached ({resend_attempts}), not resending again")
                                    if session.get('whatsapp_needs_optin'):
                                        business_number = session.get('whatsapp_business_number', '')
                                        if business_number:
                                            bot_response = f"Sorry , link nahi ja raha. Kya aapne {business_number} par WhatsApp pe 'Hi' bheja hai? Pehle woh karna padega."
                                        else:
                                            bot_response = "Sorry , link delivery mein issue ho raha hai. Kya aap WhatsApp pe pehle 'Hi' message bhej sakte hain?"
                                    else:
                                        bot_response = "Sorry , link delivery mein technical issue ho raha hai. Aap WhatsApp support se contact kar sakte hain."
                                        
                            except Exception as wa_error:
                                print(f"⚠️ WhatsApp error (non-blocking): {wa_error}")
                        # =====================================================
                else:
                    # Quick fallback with Sara's responses
                    if detected_language == 'hi':
                        bot_response = f"हाँ, मैं समझ गई। {speech_result}"
                    else:
                        bot_response = f"Yes, I understand. {speech_result}"
                
                # Check for hangup/goodbye keywords BEFORE playing audio
                hangup_keywords = {
                    'en': ['bye', 'goodbye', 'good bye', 'bye bye', 'end call', 'hang up', 'hangup', 'disconnect', 'thank you bye', 'thanks bye', 'end the call', 'end it'],
                    'hi': ['बाय', 'बाय बाय', 'अलविदा', 'धन्यवाद', 'ठीक है बाय', 'रखती हूं', 'रखता हूं', 'चलता हूं', 'चलती हूं', 'फोन रख दो', 'रख दो', 'इन कर दो', 'end kar do', 'end kar'],
                    'mixed': ['bye', 'बाय', 'बाय बाय', 'bye bye', 'alvida', 'chalta hu', 'chalti hu', 'phone rakh do', 'end kar do', 'इन कर दो']
                }
                
                # Keywords that indicate user is done/satisfied (context-aware)
                # IMPORTANT: "nahi" alone is NOT done - only when clearly answering "do you need help?"
                done_keywords_phrases = ['bas itna', 'बस इतना', 'itna hi', 'इतना ही', 'no thanks', 'no need', 'nahi chahiye', 'नहीं चाहिए', 'kuch nahi chahiye', 'कुछ नहीं चाहिए', 'bas itna hi', 'बस इतना ही']
                confirm_done_keywords = ['bas yahi', 'बस यही', 'itna hi tha', 'इतना ही था', 'bas itna hi tha', 'बस इतना ही था', 'nothing else', 'kuch nahi', 'कुछ नहीं', 'that\'s all', 'bas itna tha', 'बस इतना था']
                
                # Phrases that indicate user is reporting a problem (NOT done)
                problem_phrases = ['nahi aayi', 'नहीं आई', 'nahi aaya', 'नहीं आया', 'nahi mila', 'नहीं मिला', 'nahi mili', 'नहीं मिली', 
                                  'nahi aaya hai', 'नहीं आया है', 'nahi aayi hai', 'नहीं आई है', 'link nahi', 'लिंक नहीं',
                                  'bhej do', 'भेज दो', 'resend', 'vaapas', 'वापस', 'phir se', 'फिर से']
                
                # Check if user wants to end call
                speech_lower = speech_result.lower() if speech_result else ''
                should_hangup = False
                
                # Check explicit hangup keywords
                for lang in ['en', 'hi', 'mixed']:
                    if any(keyword in speech_lower or keyword in speech_result for keyword in hangup_keywords.get(lang, [])):
                        should_hangup = True
                        print(f"🔚 Hangup keyword detected: '{speech_result}'")
                        break
                
                # Get session state
                session_check = call_sessions.get(call_sid, {})
                payment_sent = session_check.get('payment_link_success', False)
                payment_just_sent = session_check.get('payment_link_just_sent', False)
                asked_if_done = session_check.get('asked_if_done', False)
                
                # Clear the "just sent" flag for next turn
                if call_sid in call_sessions and payment_just_sent:
                    call_sessions[call_sid]['payment_link_just_sent'] = False
                
                # Check if user is reporting a problem (link didn't come, etc.) - NOT done!
                user_has_problem = any(phrase in speech_lower or phrase in speech_result for phrase in problem_phrases)
                
                # Only check for conversation end if payment was sent in a PREVIOUS turn (not just now)
                # Debug current state
                print(f"📊 State: payment_sent={payment_sent}, just_sent={payment_just_sent}, asked_done={asked_if_done}, has_problem={user_has_problem}")
                
                if payment_sent and not payment_just_sent and not should_hangup and not user_has_problem:
                    # Check if user is saying they're done (only if NOT reporting a problem)
                    user_says_done = any(kw in speech_lower or kw in speech_result for kw in done_keywords_phrases)
                    user_confirms_done = any(kw in speech_lower or kw in speech_result for kw in confirm_done_keywords)
                    
                    # Strong signals: "thank you" + "bas itna" = definitely done
                    has_thank_you = any(phrase in speech_lower or phrase in speech_result for phrase in ['thank you', 'thanks', 'धन्यवाद', 'शुक्रिया', 'thank'])
                    has_bas_itna = any(phrase in speech_lower or phrase in speech_result for phrase in ['bas itna', 'बस इतना', 'itna hi', 'इतना ही'])
                    if has_thank_you and has_bas_itna:
                        user_confirms_done = True
                        print(f"📊 Strong done signal: thank you + bas itna")
                    
                    # Special case: standalone "nahi" or "नहीं" ONLY if we asked "aur help chahiye?"
                    # AND it's not part of a problem phrase
                    is_standalone_nahi = False
                    if asked_if_done and ('nahi' in speech_lower or 'नहीं' in speech_result):
                        # Check if it's a standalone "nahi" (not "nahi aayi", etc.)
                        is_standalone_nahi = True
                        for problem in ['aayi', 'आई', 'aaya', 'आया', 'mila', 'मिला', 'mili', 'मिली', 'link', 'लिंक']:
                            if problem in speech_lower or problem in speech_result:
                                is_standalone_nahi = False
                                break
                        if is_standalone_nahi:
                            user_confirms_done = True
                    
                    print(f"📊 Checking done: says_done={user_says_done}, confirms_done={user_confirms_done}")
                    
                    if asked_if_done:
                        # We already asked if they're done - any confirmation means end call
                        if user_confirms_done or is_standalone_nahi:
                            should_hangup = True
                            bot_response = "Theek hai ! Apna khayal rakhiyega, koi issue ho toh batana. Take care, bye!"
                            print(f"🔚 User confirmed done, ending call")
                    elif user_says_done or user_confirms_done:
                        # If user says "bas itna hi tha" (with or without thank you), end immediately
                        if user_confirms_done:
                            should_hangup = True
                            bot_response = "Theek hai ! Apna khayal rakhiyega, koi issue ho toh batana. Take care, bye!"
                            print(f"🔚 User clearly done (bas itna hi tha), ending call")
                        else:
                            # First time saying done - ask for confirmation
                            bot_response = "Achha! Kuch aur help chahiye ya call end karein?"
                            if call_sid in call_sessions:
                                call_sessions[call_sid]['asked_if_done'] = True
                            print(f"📞 User seems done, asking for confirmation")
                
                # Also check if bot response contains goodbye indicators
                if bot_response and not should_hangup:
                    bot_lower = bot_response.lower()
                    if any(word in bot_lower for word in ['bye', 'goodbye', 'alvida']) and any(word in speech_lower for word in ['bye', 'बाय']):
                        should_hangup = True
                        print(f"🔚 Conversation ending detected in bot response")
                
                if should_hangup:
                    print("📞 Ending call gracefully...")
                    
                    # =====================================================
                    # WHATSAPP INTEGRATION - Send call followup
                    # =====================================================
                    if WHATSAPP_AVAILABLE and is_whatsapp_enabled():
                        try:
                            from src.config import ENABLE_WHATSAPP_FOLLOWUPS
                            if ENABLE_WHATSAPP_FOLLOWUPS:
                                session = call_sessions.get(call_sid, {})
                                conversation = session.get('messages', [])
                                
                                # Generate call summary from conversation
                                if conversation:
                                    # Simple summary from last few messages
                                    summary_parts = []
                                    for msg in conversation[-4:]:  # Last 4 messages
                                        if msg['role'] == 'assistant':
                                            summary_parts.append(msg['content'][:100])
                                    call_summary = " ".join(summary_parts)[:200] if summary_parts else "Thank you for speaking with us."
                                else:
                                    call_summary = "Thank you for speaking with us today."
                                
                                trigger_followup(
                                    phone=request.form.get('To', ''),
                                    customer_name=session.get('customer_name', 'Customer'),
                                    call_summary=call_summary,
                                    call_id=call_sid,
                                    language=detected_language,
                                    fire_and_forget=True
                                )
                                print(f"📱 WhatsApp: Followup triggered for call {call_sid}")
                        except Exception as wa_error:
                            print(f"⚠️ WhatsApp followup error (non-blocking): {wa_error}")
                    # =====================================================
                    
                    # Say goodbye if we have a custom message, otherwise use default
                    goodbye_msg = bot_response if (bot_response and 'bye' in bot_response.lower()) else "Achha theek hai! Apna khayal rakhiyega. Bye, take care!"
                    try:
                        from src.enhanced_hindi_tts import speak_mixed_enhanced
                        audio_file = speak_mixed_enhanced(goodbye_msg)
                        if audio_file:
                            ngrok_url = get_ngrok_url()
                            if ngrok_url:
                                response.play(f"{ngrok_url}/audio/{audio_file}")
                            else:
                                response.say(goodbye_msg, voice='Polly.Aditi')
                        else:
                            response.say(goodbye_msg, voice='Polly.Aditi')
                    except:
                        response.say(goodbye_msg, voice='Polly.Aditi')
                    
                    response.hangup()
                    return str(response)
                
                # Ensure we have a valid response (this runs regardless of AI provider)
                print(f"🔍 Validating response: '{bot_response}'")
                print(f"🔍 Validation check - not bot_response: {not bot_response}")
                print(f"🔍 Validation check - strip empty: {bot_response.strip() == '' if bot_response else 'N/A'}")
                if not bot_response or bot_response.strip() == "":
                    print(f"⚠️ Empty response detected, using fallback")
                    if detected_language == 'hi':
                        bot_response = "Haan , samajh gayi. Aur kuch help chahiye?"
                    else:
                        bot_response = "Got it! Anything else I can help with?"
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
                        timeout=8,
                        speech_timeout='auto',
                        language='en-IN' if detected_language == 'en' else 'hi-IN',
                        partial_result_callback='/partial_speech',
                        enhanced='true',
                        profanity_filter='false'
                    )
                    
                    if audio_file and audio_file.endswith('.mp3'):
                        # Verify audio file exists and is readable before playing
                        audio_path = Path("audio_files") / audio_file
                        if audio_path.exists():
                            # Check file size to ensure it's not empty/corrupted
                            file_size = audio_path.stat().st_size
                            if file_size > 1000:  # At least 1KB (reasonable minimum for audio)
                                # Play audio INSIDE gather with barge-in enabled
                                ngrok_url = get_ngrok_url()
                                if ngrok_url:
                                    gather.play(f"{ngrok_url}/audio/{audio_file}")
                                    print(f"🎵 Playing TTS audio: {audio_file} ({file_size} bytes, interruption enabled)")
                                else:
                                    print("❌ Ngrok URL not available, using Twilio fallback")
                                    if detected_language in ['hi', 'mixed']:
                                        gather.say(bot_response, voice='Polly.Aditi', language='hi-IN')
                                    else:
                                        gather.say(bot_response, voice='Polly.Joanna', language='en-IN')
                            else:
                                print(f"⚠️ Audio file too small ({file_size} bytes), using Twilio fallback")
                                if detected_language in ['hi', 'mixed']:
                                    gather.say(bot_response, voice='Polly.Aditi', language='hi-IN')
                                else:
                                    gather.say(bot_response, voice='Polly.Joanna', language='en-IN')
                        else:
                            print(f"⚠️ Audio file not found: {audio_file}, using Twilio fallback")
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
                        timeout=8,
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
                    timeout=8,
                    speech_timeout='auto',
                    language='en-IN',
                    partial_result_callback='/partial_speech',
                    enhanced='true',
                    profanity_filter='false'
                )
                response.append(gather)
            
        else:
            # No speech detected - prompt user to check if still there
            print("⚠️ No speech detected, prompting user")
            
            # Track no-response count for this call
            if call_sid:
                if call_sid not in bot_app.call_language:
                    bot_app.call_language[call_sid] = {}
                
                no_response_count = bot_app.call_language[call_sid].get('no_response_count', 0)
                bot_app.call_language[call_sid]['no_response_count'] = no_response_count + 1
                
                # After 2 no-responses, end the call gracefully
                if no_response_count >= 2:
                    print("📞 Ending call after multiple no-responses")
                    response.say("Lagta hai aap busy hain. Koi baat nahi, baad mein baat karte hain. Take care!", voice='Polly.Aditi', language='hi-IN')
                    response.hangup()
                    return str(response)
            
            # First no-response: prompt user
            gather = response.gather(
                input='speech',
                action='/process_speech_realtime',
                timeout=8,  # Give more time for user to respond
                language='en-IN',
                partial_result_callback='/partial_speech',
                enhanced='true',
                profanity_filter='false'
            )
            
            # Add a friendly check-in
            gather.say("Hello? Aap sun rahe hain? Kuch boliye please!", voice='Polly.Aditi', language='hi-IN')
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
                'endTime': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
            update_call_in_dashboard(call_sid, update_data)
            
            # Clean up session when call ends
            if call_sid in call_sessions:
                del call_sessions[call_sid]
                print(f"🧹 Cleaned up session for completed call: {call_sid}")
        
        # Periodic cleanup of old sessions (every 10th status update)
        import random
        if random.random() < 0.1:  # 10% chance to run cleanup
            cleanup_old_sessions()
        
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
            voice_bot_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5015)), debug=False, use_reloader=False)
        
        bot_thread = threading.Thread(target=run_voice_bot_server, daemon=True)
        bot_thread.start()
        
        # Wait for server to start
        bot_port = int(os.environ.get('PORT', 5015))
        for i in range(15):
            try:
                response = requests.get(f"http://localhost:{bot_port}/health", timeout=1)
                if response.status_code == 200:
                    running_services['voice_bot_server'] = bot_thread
                    print(f"✅ Voice bot server started on port {bot_port}!")
                    return True
            except:
                time.sleep(1)
        
        print("❌ Voice bot server failed to start")
        return False
        
    except Exception as e:
        print(f"❌ Error starting voice bot server: {e}")
        return False

def start_ngrok():
    """Start ngrok tunnel (skipped in production mode)"""
    global ngrok_process
    
    # In production, use BASE_URL directly
    if PRODUCTION_MODE:
        if BASE_URL:
            running_services['tunnel'] = 'production'
            print(f"✅ Production mode: Using BASE_URL: {BASE_URL}")
            return BASE_URL.rstrip('/')
        else:
            print("❌ Production mode requires BASE_URL environment variable")
            return None
    
    if 'ngrok' in running_services:
        ngrok_url = get_ngrok_url()
        if ngrok_url:
            print(f"✅ Ngrok already running: {ngrok_url}")
            return ngrok_url
    
    try:
        # Start ngrok
        bot_port = str(int(os.environ.get('PORT', 5015)))
        ngrok_process = subprocess.Popen(['ngrok', 'http', bot_port], 
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
    """Get the current public URL (ngrok in dev, BASE_URL in production)"""
    # In production, use BASE_URL
    if PRODUCTION_MODE and BASE_URL:
        return BASE_URL.rstrip('/')
    
    # In development, try ngrok
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
    whatsapp_ok = 'whatsapp' in running_services
    
    print(f"Audio Server: {'✅ RUNNING' if audio_ok else '❌ STOPPED'}")
    print(f"Voice Bot Server: {'✅ RUNNING' if bot_ok else '❌ STOPPED'}")
    print(f"Ngrok Tunnel: {'✅ ACTIVE' if ngrok_url else '❌ STOPPED'}")
    
    # WhatsApp status
    if WHATSAPP_AVAILABLE:
        if is_whatsapp_enabled():
            print(f"WhatsApp Service: {'✅ RUNNING' if whatsapp_ok else '⚠️ NOT STARTED'}")
            if whatsapp_ok:
                wa_status = get_whatsapp_status()
                print(f"  - Payment Links: {'✅ Enabled' if wa_status.get('payment_links_enabled') else '❌ Disabled'}")
                print(f"  - Service Health: {'✅ OK' if wa_status.get('service_healthy') else '❌ Unavailable'}")
        else:
            print(f"WhatsApp Service: ⚪ DISABLED (set ENABLE_WHATSAPP=true)")
    else:
        print(f"WhatsApp Service: ⚪ NOT INSTALLED")
    
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
        
        # Stop ngrok (only in development mode)
        if not PRODUCTION_MODE and ngrok_process:
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
    
    # 4. Start WhatsApp service (if enabled)
    if WHATSAPP_AVAILABLE and is_whatsapp_enabled():
        try:
            from start_whatsapp_service import start_service_background, wait_for_service
            print("📱 Starting WhatsApp service...")
            whatsapp_thread = start_service_background()
            if wait_for_service(timeout=10):
                print("✅ WhatsApp service ready on port 8001")
                running_services['whatsapp'] = whatsapp_thread
            else:
                print("⚠️ WhatsApp service failed to start (continuing without it)")
        except Exception as e:
            print(f"⚠️ WhatsApp service error: {e} (continuing without it)")
    elif WHATSAPP_AVAILABLE:
        print("📱 WhatsApp integration available but disabled (set ENABLE_WHATSAPP=true to enable)")
    
    print("✅ All services ready!")
    print(f"🌐 Webhook: {ngrok_url}/voice")
    if WHATSAPP_AVAILABLE and is_whatsapp_enabled():
        print(f"📱 WhatsApp: http://localhost:8001")
    time.sleep(2)
    
    # Show main menu
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()