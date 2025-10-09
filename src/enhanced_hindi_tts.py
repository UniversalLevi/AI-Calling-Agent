"""
Enhanced Hindi TTS - Better Quality Hindi Speech
===============================================

This module provides high-quality Hindi text-to-speech using multiple providers.
"""

import os
import tempfile
import time
import glob
from pathlib import Path
from typing import Optional

try:
    from .language_detector import detect_language
except ImportError:
    from language_detector import detect_language


class EnhancedHindiTTS:
    """Enhanced Hindi TTS with multiple provider support"""
    
    def __init__(self):
        self.providers = []
        self._initialize_providers()
        self._cleanup_old_audio_files()
    
    def _initialize_providers(self):
        """Initialize available TTS providers based on .env configuration"""
        
        # Get preferred TTS provider from .env
        preferred_provider = os.getenv('TTS_PROVIDER', 'twilio').lower()
        print(f"🎯 Preferred TTS provider from .env: {preferred_provider}")
        
        # Add preferred provider first if available
        if preferred_provider == 'azure' and self._check_azure_credentials():
            self.providers.append('azure')
            print("🔊 Azure TTS available (Preferred)")
        elif preferred_provider == 'google' and self._check_google_credentials():
            self.providers.append('google')
            print("🔊 Google Cloud TTS available (Preferred)")
        elif preferred_provider == 'openai' and self._check_openai_credentials():
            self.providers.append('openai')
            print("🔊 OpenAI TTS available (Preferred)")
        
        # Add other available providers as fallbacks
        if 'azure' not in self.providers and self._check_azure_credentials():
            self.providers.append('azure')
            print("🔊 Azure TTS available (Fallback)")
        
        if 'google' not in self.providers and self._check_google_credentials():
            self.providers.append('google')
            print("🔊 Google Cloud TTS available (Fallback)")
        
        if 'openai' not in self.providers and self._check_openai_credentials():
            self.providers.append('openai')
            print("🔊 OpenAI TTS available (Fallback)")
        
        # Always have gTTS as final fallback
        self.providers.append('gtts')
        print("🔊 gTTS available (Final Fallback)")
        
        print(f"🎤 Hindi TTS providers available: {len(self.providers)}")
    
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
    
    def _check_azure_credentials(self) -> bool:
        """Check if Azure credentials are available"""
        return bool(os.getenv('AZURE_SPEECH_KEY') and os.getenv('AZURE_SPEECH_REGION'))
    
    def _check_google_credentials(self) -> bool:
        """Check if Google Cloud credentials are available"""
        return bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('GOOGLE_CLOUD_TTS_KEY'))
    
    def _check_openai_credentials(self) -> bool:
        """Check if OpenAI credentials are available"""
        return bool(os.getenv('OPENAI_API_KEY'))
    
    def speak_hindi_azure(self, text: str) -> Optional[str]:
        """Generate Hindi speech using Azure Cognitive Services"""
        try:
            import azure.cognitiveservices.speech as speechsdk
            
            speech_key = os.getenv('AZURE_SPEECH_KEY')
            service_region = os.getenv('AZURE_SPEECH_REGION')
            
            speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
            
            # Use high-quality Hindi voice
            speech_config.speech_synthesis_voice_name = "hi-IN-SwaraNeural"  # Female voice
            # Alternative: "hi-IN-MadhurNeural" (Male voice)
            
            # Create audio file
            audio_dir = Path("audio_files")
            audio_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)
            audio_file = audio_dir / f"azure_hindi_{timestamp}.wav"
            
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(audio_file))
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"🎵 Azure Hindi TTS: {audio_file.name}")
                # Return just the filename; the controller will build a public URL
                return audio_file.name
            else:
                print(f"❌ Azure TTS failed: {result.reason}")
                return None
                
        except Exception as e:
            print(f"❌ Azure TTS error: {e}")
            return None
    
    def speak_hindi_google(self, text: str) -> Optional[str]:
        """Generate Hindi speech using Google Cloud TTS"""
        try:
            from google.cloud import texttospeech
            
            client = texttospeech.TextToSpeechClient()
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            # High-quality Hindi voice
            voice = texttospeech.VoiceSelectionParams(
                language_code="hi-IN",
                name="hi-IN-Wavenet-A",  # High-quality WaveNet voice
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            # Save audio file
            audio_dir = Path("audio_files")
            audio_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)
            audio_file = audio_dir / f"google_hindi_{timestamp}.mp3"
            
            with open(audio_file, "wb") as out:
                out.write(response.audio_content)
            
            print(f"🎵 Google Hindi TTS: {audio_file.name}")
            # Return just the filename; the controller will build a public URL
            return audio_file.name
            
        except Exception as e:
            print(f"❌ Google TTS error: {e}")
            return None
    
    def speak_hindi_openai(self, text: str) -> Optional[str]:
        """Generate speech using OpenAI TTS with Sara's female voice"""
        try:
            import openai
            
            api_key = os.getenv('OPENAI_API_KEY')
            model = os.getenv('OPENAI_TTS_MODEL', 'tts-1')  # Use standard model for natural speech
            
            # Use female voice for Sara with master branch settings
            voice = os.getenv('OPENAI_TTS_VOICE', 'nova')  # Nova is a female voice
            
            client = openai.OpenAI(api_key=api_key)
            
            # Create audio file
            audio_dir = Path("audio_files")
            audio_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)
            audio_file = audio_dir / f"sara_voice_{timestamp}.mp3"
            
            # Optimize text for better Hinglish pronunciation
            optimized_text = self._optimize_text_for_tts(text)
            
            # Generate speech with master branch settings for natural speech
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=optimized_text,
                speed=1.0,  # Normal speed for natural speech (master branch setting)
                response_format="mp3"
            )
            
            # Save audio file
            with open(audio_file, 'wb') as f:
                f.write(response.content)
            
            print(f"🎵 Sara's Voice (OpenAI): {audio_file.name}")
            return audio_file.name
            
        except Exception as e:
            print(f"❌ OpenAI TTS error: {e}")
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
    
    def speak_hindi_gtts(self, text: str) -> Optional[str]:
        """Generate Hindi speech using gTTS (fallback)"""
        try:
            from gtts import gTTS
            
            # Create audio file
            audio_dir = Path("audio_files")
            audio_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)
            audio_file = audio_dir / f"gtts_hindi_{timestamp}.mp3"
            
            tts = gTTS(text=text, lang='hi', slow=False)
            tts.save(str(audio_file))
            
            print(f"🎵 gTTS Hindi TTS: {audio_file.name}")
            # Return just the filename; the controller will build a public URL
            return audio_file.name
            
        except Exception as e:
            print(f"❌ gTTS error: {e}")
            return None
    
    def speak_enhanced_hindi(self, text: str) -> str:
        """
        Generate high-quality Hindi speech using the best available provider.
        
        Args:
            text: Hindi text to convert to speech
            
        Returns:
            Audio URL or original text if all providers fail
        """
        print(f"🎤 Generating enhanced Hindi TTS for: '{text}'")
        
        # Detect if text contains Hindi characters
        has_hindi = any('\u0900' <= char <= '\u097F' for char in text)
        
        # For Hindi/mixed content, prioritize Hindi-optimized providers
        if has_hindi:
            print("🔍 Hindi content detected - prioritizing Hindi-optimized providers")
            # Reorder providers for Hindi content: Azure > Google > OpenAI > gTTS
            hindi_optimized_providers = []
            for provider in ['azure', 'google', 'openai', 'gtts']:
                if provider in self.providers:
                    hindi_optimized_providers.append(provider)
        else:
            print("🔍 English content detected - using preferred provider")
            # For English content, use the preferred provider order
            hindi_optimized_providers = self.providers
        
        # Try providers in optimized order
        for provider in hindi_optimized_providers:
            try:
                if provider == 'azure':
                    result = self.speak_hindi_azure(text)
                elif provider == 'google':
                    result = self.speak_hindi_google(text)
                elif provider == 'openai':
                    result = self.speak_hindi_openai(text)
                elif provider == 'gtts':
                    result = self.speak_hindi_gtts(text)
                else:
                    continue
                
                if result:
                    print(f"✅ Enhanced Hindi TTS successful with {provider}")
                    # Clean up old files after successful generation
                    self._cleanup_old_audio_files()
                    return result
                    
            except Exception as e:
                print(f"❌ {provider} failed: {e}")
                continue
        
        print("❌ All Hindi TTS providers failed, returning text")
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
            # For English, also use enhanced TTS
            return self.speak_enhanced_hindi(text)


# Global instance
enhanced_hindi_tts = EnhancedHindiTTS()


def speak_enhanced_hindi(text: str) -> str:
    """Main function to generate enhanced Hindi speech"""
    return enhanced_hindi_tts.speak_enhanced_hindi(text)


def speak_mixed_enhanced(text: str) -> str:
    """Main function to generate enhanced mixed language speech"""
    return enhanced_hindi_tts.speak_mixed_language(text)

