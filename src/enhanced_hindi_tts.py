"""
OpenAI-only TTS with language-aware voice selection and fallback
===============================================================

This module provides high-quality TTS using OpenAI only, with automatic
voice selection for English/Hindi and a fallback voice.
"""

import os
import tempfile
import time
import glob
from pathlib import Path
from typing import Optional
import io
import contextlib
try:
    from .debug_logger import logger, log_timing
except Exception:
    class _Null:
        def __getattr__(self, *_):
            return lambda *a, **k: None
    logger = _Null()
    def log_timing(name):
        def _d(f):
            return f
        return _d

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from .language_detector import detect_language
except ImportError:
    from language_detector import detect_language


class EnhancedHindiTTS:
    """OpenAI-only TTS with language-aware voice selection and fallback"""
    
    def __init__(self):
        self._cleanup_old_audio_files()
    
    # OpenAI-only, so no multi-provider initialization
    
    def _cleanup_old_audio_files(self):
        """Clean up old audio files to save space"""
        try:
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
                print(f"🧹 Cleaned up {deleted_count} old audio files (older than 5 minutes)")
                
        except Exception as e:
            print(f"⚠️ Audio cleanup error: {e}")
    
    def _check_openai_credentials(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY'))
    
    # Removed: Azure/Google/gTTS providers (OpenAI-only)
    
    # Removed: Google TTS
    
    def _select_openai_voice(self, text: str) -> str:
        from .language_detector import detect_language
        lang = detect_language(text)
        try:
            from .config import OPENAI_TTS_VOICE_ENGLISH, OPENAI_TTS_VOICE_HINDI, OPENAI_TTS_VOICE_FALLBACK
        except Exception:
            OPENAI_TTS_VOICE_ENGLISH = os.getenv('OPENAI_TTS_VOICE_ENGLISH', 'nova')
            OPENAI_TTS_VOICE_HINDI = os.getenv('OPENAI_TTS_VOICE_HINDI', 'shimmer')
            OPENAI_TTS_VOICE_FALLBACK = os.getenv('OPENAI_TTS_VOICE_FALLBACK', 'alloy')
        # Allow dashboard override
        try:
            from .dashboard_integration import sales_dashboard
            settings = sales_dashboard.get_voice_settings()
            OPENAI_TTS_VOICE_ENGLISH = settings.get('tts_voice_english', OPENAI_TTS_VOICE_ENGLISH)
            OPENAI_TTS_VOICE_HINDI = settings.get('tts_voice_hindi', OPENAI_TTS_VOICE_HINDI)
        except Exception:
            pass
        if lang == 'hi':
            return OPENAI_TTS_VOICE_HINDI or OPENAI_TTS_VOICE_FALLBACK
        elif lang == 'mixed':
            return OPENAI_TTS_VOICE_ENGLISH or OPENAI_TTS_VOICE_FALLBACK
        return OPENAI_TTS_VOICE_ENGLISH or OPENAI_TTS_VOICE_FALLBACK

    @log_timing("TTS generation (OpenAI)")
    def speak_openai(self, text: str) -> Optional[str]:
        try:
            from openai import OpenAI
            api_key = os.getenv('OPENAI_API_KEY')
            # Use faster tts-1 model instead of tts-1-hd for lower latency
            model = 'tts-1'  # Force faster model
            voice = self._select_openai_voice(text)
            client = OpenAI(api_key=api_key, timeout=10.0)  # Add 10s timeout

            audio_dir = Path("audio_files")
            audio_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)
            audio_filename = f"sara_voice_{timestamp}.mp3"
            audio_file = audio_dir / audio_filename

            optimized_text = self._optimize_text_for_tts(text)
            
            print(f"🎤 Generating TTS for: {text[:50]}...")

            # Generate MP3 bytes with timeout
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=optimized_text,
                response_format="mp3"
            )

            with open(audio_file, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ TTS file created: {audio_filename}")
            logger.debug(f"TTS generated via OpenAI model={model} voice={voice} -> {audio_file}")
            # Return just the filename, not the full path
            return audio_filename
        except Exception as e:
            print(f"❌ OpenAI TTS error: {e}")
            try:
                logger.error(f"OpenAI TTS error: {type(e).__name__}: {e}")
            except:
                pass  # Logger may not be available in this context
            return None
    
    def _optimize_text_for_tts(self, text: str) -> str:
        """Optimize text for better TTS pronunciation - Use simpler approach for clearer audio"""
        # Use the simpler fallback approach for better pronunciation clarity
        # The advanced transliterator was over-processing and making audio unclear
        return self._fallback_text_optimization(text)
    
    def _fallback_text_optimization(self, text: str) -> str:
        """Fallback text optimization when advanced transliterator is not available"""
        # Add natural pauses and speech patterns for more human-like delivery
        text = self._add_natural_pauses(text)
        
        # Comprehensive Hindi to Romanized transliteration for better TTS
        replacements = {
            # Basic pronouns and common words
            'नमस्ते': 'Namaste',
            'हैं': 'hain',
            'है': 'hai',
            'मैं': 'main',
            'आप': 'aap',
            'कैसे': 'kaise',
            'क्या': 'kya',
            'कहाँ': 'kahan',
            'कब': 'kab',
            'क्यों': 'kyun',
            'कितना': 'kitna',
            'कौन': 'kaun',
            'कौन सा': 'kaun sa',
            'कौन सी': 'kaun si',
            'कौन से': 'kaun se',
            'मुझे': 'mujhe',
            'तुम्हें': 'tumhe',
            'आपको': 'aapko',
            'हमें': 'hamein',
            'उन्हें': 'unhein',
            'इस': 'is',
            'उस': 'us',
            'यह': 'yah',
            'वह': 'vah',
            'ये': 'ye',
            'वे': 've',
            'मेरा': 'mera',
            'मेरी': 'meri',
            'मेरे': 'mere',
            'आपका': 'aapka',
            'आपकी': 'aapki',
            'आपके': 'aapke',
            'हमारा': 'hamara',
            'हमारी': 'hamari',
            'हमारे': 'hamare',
            'उनका': 'unka',
            'उनकी': 'unki',
            'उनके': 'unke',
            
            # Common verbs and actions - more natural pronunciation
            'जाना': 'jana',
            'आना': 'aana',
            'करना': 'karna',
            'करो': 'karo',
            'करें': 'karen',
            'करते': 'karte',
            'करता': 'karta',
            'करती': 'karti',
            'करेंगे': 'karenge',
            'करूंगा': 'karunga',
            'करूंगी': 'karungi',
            'होना': 'hona',
            'हो': 'ho',
            'होगा': 'hoga',
            'होगी': 'hogi',
            'होंगे': 'honge',
            'देना': 'dena',
            'दो': 'do',
            'दें': 'den',
            'लेना': 'lena',
            'लो': 'lo',
            'लें': 'len',
            'बोलना': 'bolna',
            'बताओ': 'batao',
            'बताएं': 'batayen',
            'सुनना': 'sunna',
            'देखना': 'dekhna',
            'समझना': 'samajhna',
            'समझ': 'samajh',
            'चाहिए': 'chahiye',
            'चाहता': 'chahta',
            'चाहती': 'chahti',
            'चाहते': 'chahte',
            'पसंद': 'pasand',
            'अच्छा': 'accha',
            'बुरा': 'bura',
            'ठीक': 'theek',
            'बुक करना': 'book karna',
            'बुक करो': 'book karo',
            'बुक करें': 'book karen',
            'सुझाव': 'sujhav',
            'सुझाव देना': 'sujhav dena',
            'मदद': 'madad',
            'मदद करना': 'madad karna',
            
            # Places and locations
            'जयपुर': 'Jaipur',
            'दिल्ली': 'Delhi',
            'मुंबई': 'Mumbai',
            'बैंगलोर': 'Bangalore',
            'चेन्नई': 'Chennai',
            'कोलकाता': 'Kolkata',
            'हैदराबाद': 'Hyderabad',
            'पुणे': 'Pune',
            'अहमदाबाद': 'Ahmedabad',
            'राजस्थान': 'Rajasthan',
            'महाराष्ट्र': 'Maharashtra',
            'कर्नाटक': 'Karnataka',
            'तमिलनाडु': 'Tamil Nadu',
            'पश्चिम बंगाल': 'West Bengal',
            
            # Food and restaurants
            'रेस्टोरेंट': 'restaurant',
            'होटल': 'hotel',
            'खाना': 'khana',
            'पानी': 'pani',
            'चाय': 'chai',
            'कॉफी': 'coffee',
            'दूध': 'doodh',
            'रोटी': 'roti',
            'चावल': 'chawal',
            'दाल': 'dal',
            'सब्जी': 'sabzi',
            'मांस': 'maans',
            'मछली': 'machhli',
            'अंडा': 'anda',
            
            # Numbers and money
            'एक': 'ek',
            'दो': 'do',
            'तीन': 'teen',
            'चार': 'chaar',
            'पांच': 'paanch',
            'छह': 'chhah',
            'सात': 'saat',
            'आठ': 'aath',
            'नौ': 'nau',
            'दस': 'das',
            'बीस': 'bees',
            'तीस': 'tees',
            'चालीस': 'chaalis',
            'पचास': 'pachaas',
            'साठ': 'saath',
            'सत्तर': 'sattar',
            'अस्सी': 'assi',
            'नब्बे': 'nabbe',
            'सौ': 'sau',
            'हज़ार': 'hazaar',
            'लाख': 'laakh',
            'करोड़': 'karod',
            'रुपए': 'rupaye',
            'रुपया': 'rupya',
            
            # Time and dates
            'आज': 'aaj',
            'कल': 'kal',
            'परसों': 'parson',
            'सुबह': 'subah',
            'दोपहर': 'dopahar',
            'शाम': 'shaam',
            'रात': 'raat',
            'सोमवार': 'somvaar',
            'मंगलवार': 'mangalvaar',
            'बुधवार': 'budhvaar',
            'गुरुवार': 'guruvaar',
            'शुक्रवार': 'shukravaar',
            'शनिवार': 'shanivaar',
            'रविवार': 'ravivaar',
            
            # Common phrases
            'धन्यवाद': 'dhanyawad',
            'शुक्रिया': 'shukriya',
            'माफ़ करें': 'maaf karein',
            'क्षमा करें': 'kshama karein',
            'हाँ': 'haan',
            'नहीं': 'nahi',
            'हो सकता है': 'ho sakta hai',
            'ज़रूर': 'zaroor',
            'बिल्कुल': 'bilkul',
            'शायद': 'shayad',
            'कभी नहीं': 'kabhi nahi',
            'हमेशा': 'hamesha',
            'कभी-कभी': 'kabhi-kabhi',
            
            # Business and travel terms
            'बुकिंग': 'booking',
            'रिजर्वेशन': 'reservation',
            'टिकट': 'ticket',
            'यात्रा': 'yatra',
            'घूमना': 'ghoomna',
            'देखना': 'dekhna',
            'मिलना': 'milna',
            'बात करना': 'baat karna',
            'सहायता': 'sahayata',
            'मदद': 'madad',
            'जानकारी': 'jankari',
            'सुझाव': 'sujhaav',
            'प्लान': 'plan',
            'प्रोग्राम': 'program',
            
            # Technology terms
            'इंटरनेट': 'internet',
            'वाईफाई': 'WiFi',
            'मोबाइल': 'mobile',
            'फोन': 'phone',
            'कंप्यूटर': 'computer',
            'लैपटॉप': 'laptop',
            'टैबलेट': 'tablet',
            'ऐप': 'app',
            'वेबसाइट': 'website',
            'ईमेल': 'email',
            'पासवर्ड': 'password',
            'लॉगिन': 'login',
            'साइन अप': 'sign up',
            'डाउनलोड': 'download',
            'अपलोड': 'upload',
            
            # Remove "Sara:" prefix if present
            'Sara: ': '',
            'Sara:': ''
        }
        
        optimized_text = text
        for hindi, romanized in replacements.items():
            optimized_text = optimized_text.replace(hindi, romanized)
        
        # Additional cleanup for better pronunciation
        optimized_text = optimized_text.replace('  ', ' ')  # Remove double spaces
        optimized_text = optimized_text.strip()  # Remove leading/trailing spaces
        
        return optimized_text
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses and speech patterns for more human-like delivery"""
        # Add subtle pauses after punctuation for more natural flow
        text = text.replace(',', ', ')
        text = text.replace('.', '. ')
        text = text.replace('!', '! ')
        text = text.replace('?', '? ')
        
        # Add natural pauses for common Hindi/English transitions
        text = text.replace(' और ', ' aur ')
        text = text.replace(' तो ', ' to ')
        text = text.replace(' लेकिन ', ' lekin ')
        text = text.replace(' क्योंकि ', ' kyunki ')
        
        # Add emphasis for important words (subtle)
        text = text.replace(' धन्यवाद ', ' dhanyavaad ')
        text = text.replace(' शुक्रिया ', ' shukriya ')
        text = text.replace(' नमस्ते ', ' namaste ')
        
        # Add natural breathing pauses for longer sentences
        sentences = text.split('.')
        if len(sentences) > 1:
            # Add slight pause between sentences
            text = '. '.join(sentences)
        
        # Clean up multiple spaces
        import re
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    # Removed: gTTS fallback
    
    def speak_enhanced_hindi(self, text: str) -> str:
        """
        Generate high-quality Hindi speech using the best available provider.
        
        Args:
            text: Hindi text to convert to speech
            
        Returns:
            Audio URL or original text if all providers fail
        """
        print(f"🎤 Generating enhanced Hindi TTS for: '{text}'")
        
        # TTS cache removed for reliability
        
        # Detect if text contains Hindi characters
        has_hindi = any('\u0900' <= char <= '\u097F' for char in text)
        
        # OpenAI-only path
        result = self.speak_openai(text)
        if result:
            self._cleanup_old_audio_files()
            return result
        print("❌ OpenAI TTS failed, returning text")
        return text
    
    def speak_mixed_language(self, text: str) -> str:
        """
        Generate speech for mixed language text.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio URL or original text
        """
        language = detect_language(text)
        
        if language == 'hi':
            return self.speak_enhanced_hindi(text)
        elif language == 'mixed':
            # For mixed text, use the best available provider
            return self.speak_enhanced_hindi(text)
        else:
            # For English, also use OpenAI
            return self.speak_enhanced_hindi(text)
    
    def speak_enhanced_hindi_bytes(self, text: str) -> bytes:
        """
        Generate speech and return WAV bytes for Media Streams compatibility.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            WAV bytes ready for Media Streams
        """
        try:
            # Generate audio file using existing logic
            audio_filename = self.speak_enhanced_hindi(text)
            
            if not audio_filename or audio_filename == text:
                # TTS failed, return silence
                return self._generate_silence_wav()
            
            # Convert audio file to WAV bytes
            return self._audio_file_to_wav_bytes(audio_filename)
            
        except Exception as e:
            print(f"❌ Enhanced Hindi TTS bytes error: {e}")
            return self._generate_silence_wav()
    
    def speak_mixed_language_bytes(self, text: str) -> bytes:
        """
        Generate speech for mixed language text and return WAV bytes.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            WAV bytes ready for Media Streams
        """
        try:
            # Generate audio file using existing logic
            audio_filename = self.speak_mixed_language(text)
            
            if not audio_filename or audio_filename == text:
                # TTS failed, return silence
                return self._generate_silence_wav()
            
            # Convert audio file to WAV bytes
            return self._audio_file_to_wav_bytes(audio_filename)
            
        except Exception as e:
            print(f"❌ Mixed language TTS bytes error: {e}")
            return self._generate_silence_wav()
    
    def _audio_file_to_wav_bytes(self, audio_filename: str) -> bytes:
        """
        Convert audio file to WAV bytes for Media Streams.
        
        Args:
            audio_filename: Name of the audio file
            
        Returns:
            WAV bytes
        """
        try:
            audio_path = Path("audio_files") / audio_filename
            
            if not audio_path.exists():
                print(f"❌ Audio file not found: {audio_path}")
                return self._generate_silence_wav()
            
            # Read the audio file
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Convert MP3 to WAV if needed
            if audio_filename.endswith('.mp3'):
                wav_bytes = self._convert_mp3_to_wav(audio_bytes)
            elif audio_filename.endswith('.wav'):
                wav_bytes = audio_bytes
            else:
                print(f"❌ Unsupported audio format: {audio_filename}")
                return self._generate_silence_wav()
            
            return wav_bytes
            
        except Exception as e:
            print(f"❌ Audio file to WAV conversion error: {e}")
            return self._generate_silence_wav()
    
    def _convert_mp3_to_wav(self, mp3_bytes: bytes) -> bytes:
        """Convert MP3 bytes to WAV bytes using ffmpeg"""
        try:
            import subprocess
            
            # Use pipe approach for better reliability
            process = subprocess.Popen([
                'ffmpeg',
                '-loglevel', 'error',
                '-i', 'pipe:0',
                '-ar', '8000',  # 8kHz sample rate for Twilio
                '-ac', '1',     # Mono
                '-f', 'wav',
                'pipe:1'
            ], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = process.communicate(input=mp3_bytes)
            
            if process.returncode != 0:
                print(f"❌ FFmpeg conversion failed with return code {process.returncode}")
                print(f"❌ FFmpeg stderr: {stderr.decode() if stderr else 'No stderr'}")
                return self._generate_silence_wav()
            
            print(f"✅ MP3 to WAV conversion successful: {len(stdout)} bytes")
            return stdout
                    
        except Exception as e:
            print(f"❌ MP3 to WAV conversion error: {e}")
            return self._generate_silence_wav()
    
    def _generate_silence_wav(self, duration_ms: int = 100) -> bytes:
        """Generate a short silence WAV file"""
        try:
            import subprocess
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                wav_path = wav_file.name
            
            try:
                # Generate silence using ffmpeg
                process = subprocess.run([
                    'ffmpeg',
                    '-f', 'lavfi',
                    '-i', f'anullsrc=duration={duration_ms}ms',
                    '-ar', '8000',
                    '-ac', '1',
                    '-f', 'wav',
                    wav_path
                ], capture_output=True, check=True)
                
                with open(wav_path, 'rb') as f:
                    wav_bytes = f.read()
                
                return wav_bytes
                
            finally:
                try:
                    os.unlink(wav_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Silence generation error: {e}")
            # Return minimal WAV header as last resort
            return self._minimal_wav_header()
    
    def _minimal_wav_header(self) -> bytes:
        """Generate minimal WAV header for silence"""
        # Minimal WAV header for 8kHz mono 16-bit PCM
        return bytes([
            # RIFF header
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x24, 0x00, 0x00, 0x00,  # File size - 8
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            
            # fmt chunk
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # Chunk size
            0x01, 0x00,              # Audio format (PCM)
            0x01, 0x00,              # Number of channels (mono)
            0x40, 0x1F, 0x00, 0x00,  # Sample rate (8000)
            0x80, 0x3E, 0x00, 0x00,  # Byte rate
            0x02, 0x00,              # Block align
            0x10, 0x00,              # Bits per sample
            
            # data chunk
            0x64, 0x61, 0x74, 0x61,  # "data"
            0x00, 0x00, 0x00, 0x00,  # Data size (0 for silence)
        ])


# Global instance
enhanced_hindi_tts = EnhancedHindiTTS()


def speak_enhanced_hindi(text: str) -> str:
    """Main function to generate enhanced Hindi speech"""
    return enhanced_hindi_tts.speak_enhanced_hindi(text)


def speak_mixed_enhanced(text: str) -> str:
    """Main function to generate enhanced mixed language speech"""
    result = enhanced_hindi_tts.speak_openai(text)
    return result if result else text


def speak_enhanced_hindi_bytes(text: str) -> bytes:
    """Main function to generate enhanced Hindi speech as WAV bytes"""
    return enhanced_hindi_tts.speak_enhanced_hindi_bytes(text)


def speak_mixed_enhanced_bytes(text: str) -> bytes:
    """Main function to generate enhanced mixed language speech as WAV bytes"""
    return enhanced_hindi_tts.speak_mixed_language_bytes(text)

