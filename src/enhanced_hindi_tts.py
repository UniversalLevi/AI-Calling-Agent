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
            model = os.getenv('OPENAI_TTS_MODEL', 'tts-1')
            
            # Use female voice for Sara
            voice = os.getenv('OPENAI_TTS_VOICE', 'nova')  # Nova is a female voice
            
            client = openai.OpenAI(api_key=api_key)
            
            # Create audio file
            audio_dir = Path("audio_files")
            audio_dir.mkdir(exist_ok=True)
            timestamp = int(time.time() * 1000)
            audio_file = audio_dir / f"sara_voice_{timestamp}.mp3"
            
            # Optimize text for better Hinglish pronunciation
            optimized_text = self._optimize_text_for_tts(text)
            
            # Generate speech with optimized settings
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=optimized_text,
                speed=1.0,  # Normal speed for natural speech
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
        """Optimize text for better TTS pronunciation, especially for Hinglish"""
        # Replace common Hindi-English mixed words with better pronunciation
        replacements = {
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
            'उनके': 'unke'
        }
        
        optimized_text = text
        for hindi, english in replacements.items():
            optimized_text = optimized_text.replace(hindi, english)
        
        return optimized_text
    
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

