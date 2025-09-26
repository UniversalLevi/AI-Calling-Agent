"""
SIP Client for Phase 2 - Connects to Asterisk and bridges audio to the voice bot
"""
import threading
import time
import queue
import logging
from typing import Optional, Callable
import numpy as np
import sounddevice as sd
try:
    from .config import SAMPLE_RATE, CHANNELS
except ImportError:
    # Handle direct execution
    from config import SAMPLE_RATE, CHANNELS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pjsua2 as pj
    PJSIP_AVAILABLE = True
except ImportError:
    PJSIP_AVAILABLE = False
    logger.warning("PJSIP not available. Install with: pip install pjsua2")


class SIPClient:
    """SIP client that connects to Asterisk and bridges audio to the voice bot"""
    
    def __init__(self, server_ip: str = "localhost", username: str = "1001", password: str = "botpass123"):
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.ep = None
        self.account = None
        self.call = None
        self.is_registered = False
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.recording_thread = None
        self.playback_thread = None
        self.on_call_state_change: Optional[Callable] = None
        self.on_audio_received: Optional[Callable] = None
        
    def initialize(self) -> bool:
        """Initialize PJSIP endpoint"""
        if not PJSIP_AVAILABLE:
            logger.error("PJSIP not available. Cannot initialize SIP client.")
            return False
            
        try:
            # Create endpoint
            self.ep = pj.Endpoint()
            self.ep.libCreate()
            
            # Configure transport
            tcfg = pj.TransportConfig()
            tcfg.port = 0  # Use any available port
            self.ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, tcfg)
            
            # Start the library
            self.ep.libStart()
            
            logger.info("PJSIP endpoint initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PJSIP: {e}")
            return False
    
    def register_account(self) -> bool:
        """Register SIP account with Asterisk"""
        if not self.ep:
            logger.error("Endpoint not initialized")
            return False
            
        try:
            # Configure account
            acc_cfg = pj.AccountConfig()
            acc_cfg.idUri = f"sip:{self.username}@{self.server_ip}"
            acc_cfg.regConfig.registrarUri = f"sip:{self.server_ip}"
            auth_cfg = pj.AuthCredInfo()
            auth_cfg.scheme = "digest"
            auth_cfg.realm = "*"
            auth_cfg.username = self.username
            auth_cfg.dataType = pj.PJSIP_CRED_DATA_PLAIN_PASSWD
            auth_cfg.data = self.password
            acc_cfg.sipConfig.authCreds.append(auth_cfg)
            
            # Create account
            self.account = pj.Account()
            self.account.create(acc_cfg)
            
            # Wait for registration
            time.sleep(2)
            
            if self.account.isValid():
                self.is_registered = True
                logger.info(f"Successfully registered as {self.username}@{self.server_ip}")
                return True
            else:
                logger.error("Failed to register SIP account")
                return False
                
        except Exception as e:
            logger.error(f"Failed to register account: {e}")
            return False
    
    def make_call(self, target: str) -> bool:
        """Make a call to target extension"""
        if not self.is_registered:
            logger.error("Not registered with SIP server")
            return False
            
        try:
            # Create call
            call_cfg = pj.CallOpParam()
            call_cfg.opt.audioCount = 1
            call_cfg.opt.videoCount = 0
            
            self.call = pj.Call(self.account)
            self.call.makeCall(f"sip:{target}@{self.server_ip}", call_cfg)
            
            logger.info(f"Calling {target}@{self.server_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to make call: {e}")
            return False
    
    def answer_call(self) -> bool:
        """Answer incoming call"""
        if not self.call:
            logger.error("No call to answer")
            return False
            
        try:
            call_cfg = pj.CallOpParam()
            call_cfg.statusCode = pj.PJSIP_SC_OK
            self.call.answer(call_cfg)
            logger.info("Call answered")
            return True
            
        except Exception as e:
            logger.error(f"Failed to answer call: {e}")
            return False
    
    def hangup_call(self):
        """Hangup current call"""
        if self.call:
            try:
                self.call.hangup(pj.CallOpParam())
                logger.info("Call hung up")
            except Exception as e:
                logger.error(f"Error hanging up call: {e}")
            finally:
                self.call = None
    
    def start_audio_bridge(self):
        """Start audio bridging between SIP and voice bot"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._audio_recording_loop)
        self.playback_thread = threading.Thread(target=self._audio_playback_loop)
        
        self.recording_thread.start()
        self.playback_thread.start()
        
        logger.info("Audio bridge started")
    
    def stop_audio_bridge(self):
        """Stop audio bridging"""
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join()
        if self.playback_thread:
            self.playback_thread.join()
            
        logger.info("Audio bridge stopped")
    
    def _audio_recording_loop(self):
        """Record audio from microphone and send to SIP"""
        try:
            while self.is_recording:
                # Record audio
                audio = sd.rec(int(0.1 * SAMPLE_RATE), samplerate=SAMPLE_RATE, 
                              channels=CHANNELS, dtype='float32')
                sd.wait()
                
                # Convert to bytes for SIP transmission
                audio_bytes = (audio * 32767).astype(np.int16).tobytes()
                
                # Here you would send audio to SIP call
                # This is a simplified version - real implementation would use RTP
                if self.call and self.call.isActive():
                    # Placeholder for actual RTP audio transmission
                    pass
                    
        except Exception as e:
            logger.error(f"Audio recording error: {e}")
    
    def _audio_playback_loop(self):
        """Play audio received from SIP"""
        try:
            while self.is_recording:
                # Placeholder for receiving audio from SIP
                # In real implementation, this would receive RTP audio
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_audio_bridge()
        self.hangup_call()
        
        if self.account:
            self.account.delete()
        if self.ep:
            self.ep.libDestroy()
            
        logger.info("SIP client cleaned up")


class SimpleSIPClient:
    """Simplified SIP client for testing without PJSIP"""
    
    def __init__(self, server_ip: str = "localhost", username: str = "1001", password: str = "botpass123"):
        self.server_ip = server_ip
        self.username = username
        self.password = password
        self.is_connected = False
        self.call_active = False
        
    def initialize(self) -> bool:
        """Initialize simple SIP client"""
        logger.info("Initializing simple SIP client (simulation mode)")
        return True
    
    def register_account(self) -> bool:
        """Simulate account registration"""
        logger.info(f"Simulating registration as {self.username}@{self.server_ip}")
        self.is_connected = True
        return True
    
    def make_call(self, target: str) -> bool:
        """Simulate making a call"""
        logger.info(f"Simulating call to {target}@{self.server_ip}")
        self.call_active = True
        return True
    
    def answer_call(self) -> bool:
        """Simulate answering a call"""
        logger.info("Simulating call answer")
        self.call_active = True
        return True
    
    def hangup_call(self):
        """Simulate hanging up"""
        logger.info("Simulating call hangup")
        self.call_active = False
    
    def start_audio_bridge(self):
        """Start audio bridge simulation"""
        logger.info("Starting audio bridge simulation")
    
    def stop_audio_bridge(self):
        """Stop audio bridge simulation"""
        logger.info("Stopping audio bridge simulation")
    
    def cleanup(self):
        """Cleanup simulation"""
        logger.info("Cleaning up simple SIP client")


def create_sip_client(server_ip: str = "localhost", username: str = "1001", password: str = "botpass123") -> SIPClient:
    """Create appropriate SIP client based on available libraries"""
    if PJSIP_AVAILABLE:
        return SIPClient(server_ip, username, password)
    else:
        logger.warning("PJSIP not available, using simulation mode")
        return SimpleSIPClient(server_ip, username, password)

