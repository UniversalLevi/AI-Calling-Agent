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
import signal
import requests
import warnings
from pathlib import Path
from flask import Flask, request, send_file
from twilio.twiml.voice_response import VoiceResponse

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Add src to path
sys.path.append('src')

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Global variables
voice_bot_app = None
audio_server_app = None
ngrok_process = None
running_services = {}

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
        
        # Mixed language greeting
        greeting = "Hello! नमस्ते! I'm your AI assistant. How can I help you today? आज मैं आपकी कैसे मदद कर सकता हूं?"
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
    
    @bot_app.route('/status', methods=['POST'])
    def status():
        call_sid = request.form.get('CallSid')
        call_status = request.form.get('CallStatus')
        print(f"📊 Call {call_sid} status: {call_status}")
        return "OK"
    
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
        print("-" * 30)
        print("1. 📞 Call a number")
        print("2. 📱 Call me")
        print("3. 🔍 Status")
        print("4. 🧪 Test")
        print("5. 🎤 Voice bot")
        print("6. ❌ Exit")
        print("-" * 30)
        
        choice = input("Choice (1-6): ").strip()
        
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
            
        elif choice == "3":
            show_status()
            input("\nPress Enter to continue...")
            
        elif choice == "4":
            print("🧪 Running tests...")
            try:
                subprocess.run([sys.executable, "test_mixed_language.py"], check=True)
            except:
                print("❌ Test failed")
            input("\nPress Enter to continue...")
            
        elif choice == "5":
            print("🎤 Starting voice bot...")
            print("💡 Speak Hindi or English!")
            try:
                subprocess.run([sys.executable, "-m", "src.voice_bot"])
            except KeyboardInterrupt:
                print("\n🎤 Stopped.")
            input("\nPress Enter to continue...")
            
        elif choice == "6":
            print("👋 Goodbye!")
            break
            
        else:
            print("❌ Invalid choice (1-6)")
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