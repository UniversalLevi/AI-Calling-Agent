"""
Enhanced Hindi TTS - Better Quality Hindi Speech
===============================================

This module provides high-quality Hindi text-to-speech using multiple providers.
"""

import os
import tempfile
import time
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
    
    def _initialize_providers(self):
        """Initialize available TTS providers in order of preference"""
        
        # 1. Try Azure Cognitive Services (Best Hindi quality)
        if self._check_azure_credentials():
            self.providers.append('azure')
            print("🔊 Azure TTS available (Best Hindi quality)")
        
        # 2. Try Google Cloud TTS (Good Hindi quality)
        if self._check_google_credentials():
            self.providers.append('google')
            print("🔊 Google Cloud TTS available (Good Hindi quality)")
        
        # 3. Try ElevenLabs (Good for cloned voices)
        if self._check_elevenlabs_credentials():
            self.providers.append('elevenlabs')
            print("🔊 ElevenLabs TTS available")
        
        # 4. Always have gTTS as fallback (Basic Hindi quality)
        self.providers.append('gtts')
        print("🔊 gTTS available (Fallback Hindi)")
        
        print(f"🎤 Hindi TTS providers available: {len(self.providers)}")
    
    def _check_azure_credentials(self) -> bool:
        """Check if Azure credentials are available"""
        return bool(os.getenv('AZURE_SPEECH_KEY') and os.getenv('AZURE_SPEECH_REGION'))
    
    def _check_google_credentials(self) -> bool:
        """Check if Google Cloud credentials are available"""
        return bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('GOOGLE_CLOUD_TTS_KEY'))
    
    def _check_elevenlabs_credentials(self) -> bool:
        """Check if ElevenLabs credentials are available"""
        return bool(os.getenv('ELEVENLABS_API_KEY') and os.getenv('ELEVENLABS_VOICE_ID'))
    
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
    
    def speak_hindi_elevenlabs(self, text: str) -> Optional[str]:
        """Generate Hindi speech using ElevenLabs"""
        try:
            import requests
            
            api_key = os.getenv('ELEVENLABS_API_KEY')
            voice_id = os.getenv('ELEVENLABS_VOICE_ID')
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",  # Supports Hindi
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.5,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Save audio file
                audio_dir = Path("audio_files")
                audio_dir.mkdir(exist_ok=True)
                timestamp = int(time.time() * 1000)
                audio_file = audio_dir / f"elevenlabs_hindi_{timestamp}.mp3"
                
                with open(audio_file, 'wb') as f:
                    f.write(response.content)
                
                print(f"🎵 ElevenLabs Hindi TTS: {audio_file.name}")
                # Return just the filename; the controller will build a public URL
                return audio_file.name
            else:
                print(f"❌ ElevenLabs TTS failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ ElevenLabs TTS error: {e}")
            return None
    
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
        
        # Try providers in order of quality
        for provider in self.providers:
            try:
                if provider == 'azure':
                    result = self.speak_hindi_azure(text)
                elif provider == 'google':
                    result = self.speak_hindi_google(text)
                elif provider == 'elevenlabs':
                    result = self.speak_hindi_elevenlabs(text)
                elif provider == 'gtts':
                    result = self.speak_hindi_gtts(text)
                else:
                    continue
                
                if result:
                    print(f"✅ Enhanced Hindi TTS successful with {provider}")
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
            # For English, use Twilio TTS (handled by the calling function)
            return text


# Global instance
enhanced_hindi_tts = EnhancedHindiTTS()


def speak_enhanced_hindi(text: str) -> str:
    """Main function to generate enhanced Hindi speech"""
    return enhanced_hindi_tts.speak_enhanced_hindi(text)


def speak_mixed_enhanced(text: str) -> str:
    """Main function to generate enhanced mixed language speech"""
    return enhanced_hindi_tts.speak_mixed_language(text)

