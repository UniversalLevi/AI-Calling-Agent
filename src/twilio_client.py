"""
Twilio Client for Real Phone Calls - Phase 3
This module integrates Twilio for making real phone calls with the AI voice bot
"""
import os
import logging
from typing import Optional, Callable
from twilio.rest import Client
from twilio.twiml import VoiceResponse
from flask import Flask, request
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TwilioClient:
    """Twilio client for making real phone calls with AI voice bot"""
    
    def __init__(self, account_sid: str, auth_token: str, phone_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        self.client = Client(account_sid, auth_token)
        self.app = Flask(__name__)
        self.voice_bot_callback: Optional[Callable] = None
        self.webhook_url = None
        
        # Setup Flask routes for Twilio webhooks
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes for Twilio webhooks"""
        
        @self.app.route('/voice', methods=['POST'])
        def voice():
            """Handle incoming calls"""
            response = VoiceResponse()
            
            # Get the caller's phone number
            caller = request.form.get('From', 'Unknown')
            logger.info(f"Incoming call from: {caller}")
            
            # Say greeting
            response.say("Hello! I'm your AI assistant. Please wait while I connect you.")
            
            # Start the voice bot conversation
            if self.voice_bot_callback:
                # Start voice bot in a separate thread
                threading.Thread(
                    target=self.voice_bot_callback,
                    args=(caller,),
                    daemon=True
                ).start()
            
            # Keep the call alive
            response.pause(length=30)
            response.say("Thank you for calling. Goodbye!")
            
            return str(response)
        
        @self.app.route('/status', methods=['POST'])
        def status():
            """Handle call status updates"""
            call_sid = request.form.get('CallSid')
            call_status = request.form.get('CallStatus')
            logger.info(f"Call {call_sid} status: {call_status}")
            return "OK"
    
    def set_voice_bot_callback(self, callback: Callable):
        """Set the voice bot callback function"""
        self.voice_bot_callback = callback
    
    def make_call(self, to_number: str, webhook_url: str) -> str:
        """Make an outbound call"""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=webhook_url,
                status_callback=f"{webhook_url}/status"
            )
            logger.info(f"Call initiated to {to_number}, SID: {call.sid}")
            return call.sid
        except Exception as e:
            logger.error(f"Failed to make call: {e}")
            raise
    
    def start_webhook_server(self, host: str = "0.0.0.0", port: int = 5000):
        """Start the webhook server"""
        self.webhook_url = f"http://{host}:{port}"
        logger.info(f"Starting webhook server at {self.webhook_url}")
        
        # Run Flask app
        self.app.run(host=host, port=port, debug=False, threaded=True)
    
    def get_phone_number_info(self) -> dict:
        """Get information about the Twilio phone number"""
        try:
            incoming_phone_numbers = self.client.incoming_phone_numbers.list()
            for number in incoming_phone_numbers:
                if number.phone_number == self.phone_number:
                    return {
                        'phone_number': number.phone_number,
                        'friendly_name': number.friendly_name,
                        'voice_url': number.voice_url,
                        'status_callback': number.status_callback
                    }
            return {}
        except Exception as e:
            logger.error(f"Failed to get phone number info: {e}")
            return {}


class TwilioVoiceBot:
    """Voice bot that works with Twilio calls"""
    
    def __init__(self, twilio_client: TwilioClient):
        self.twilio_client = twilio_client
        self.is_active = False
        
    def start_conversation(self, caller_number: str):
        """Start a conversation with the caller"""
        logger.info(f"Starting conversation with {caller_number}")
        self.is_active = True
        
        # This is where you would integrate with your existing voice bot
        # For now, we'll simulate the conversation
        self._simulate_conversation(caller_number)
    
    def _simulate_conversation(self, caller_number: str):
        """Simulate a conversation (replace with actual voice bot integration)"""
        logger.info(f"Simulating conversation with {caller_number}")
        
        # Here you would:
        # 1. Use your STT to convert caller's speech to text
        # 2. Use your GPT brain to generate responses
        # 3. Use your TTS to convert responses to speech
        # 4. Send the audio back to Twilio
        
        time.sleep(5)  # Simulate conversation time
        logger.info(f"Conversation with {caller_number} completed")
        self.is_active = False


def create_twilio_integration():
    """Create a complete Twilio integration setup"""
    
    # Get Twilio credentials from environment
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    phone_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, phone_number]):
        logger.error("Missing Twilio credentials in environment variables")
        logger.info("Please set:")
        logger.info("TWILIO_ACCOUNT_SID=your_account_sid")
        logger.info("TWILIO_AUTH_TOKEN=your_auth_token")
        logger.info("TWILIO_PHONE_NUMBER=your_phone_number")
        return None
    
    # Create Twilio client
    twilio_client = TwilioClient(account_sid, auth_token, phone_number)
    
    # Create voice bot
    voice_bot = TwilioVoiceBot(twilio_client)
    
    # Set up the callback
    twilio_client.set_voice_bot_callback(voice_bot.start_conversation)
    
    return twilio_client, voice_bot


if __name__ == "__main__":
    # Example usage
    twilio_client, voice_bot = create_twilio_integration()
    
    if twilio_client:
        logger.info("Twilio integration created successfully!")
        logger.info("Starting webhook server...")
        twilio_client.start_webhook_server()
    else:
        logger.error("Failed to create Twilio integration")

