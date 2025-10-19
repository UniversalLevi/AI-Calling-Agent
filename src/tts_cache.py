"""
TTS Cache System for Common Phrases
Pre-generates and caches frequently used responses for instant playback
"""

import os
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
from functools import lru_cache
import threading

class TTSCache:
    """Cache system for TTS responses to reduce latency"""
    
    def __init__(self, cache_dir: str = "tts_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
        self.lock = threading.Lock()
        # Lightweight in-memory cache (LRU for small common phrases)
        self._memory_cache: Dict[str, str] = {}
        
        # Pre-defined common phrases to cache
        self.common_phrases = self._get_common_phrases()
        
        print(f"🎵 TTS Cache initialized: {len(self.cache_index)} cached phrases")
    
    def _load_cache_index(self) -> Dict[str, Dict]:
        """Load cache index from file"""
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading cache index: {e}")
        return {}
    
    def _save_cache_index(self):
        """Save cache index to file"""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving cache index: {e}")
    
    def _get_common_phrases(self) -> List[Dict[str, str]]:
        """Get list of common phrases to pre-generate"""
        return [
            # Greetings
            {"text": "Hi there! I am Sara. How can I help you today?", "language": "en", "voice": "nova"},
            {"text": "Namaste! Main Sara hun. Aapki kya madad kar sakti hun?", "language": "hi", "voice": "nova"},
            {"text": "Hello! Main Sara hun. Kaise help kar sakti hun?", "language": "mixed", "voice": "nova"},
            
            # Confirmations
            {"text": "Okay", "language": "en", "voice": "nova"},
            {"text": "Sure", "language": "en", "voice": "nova"},
            {"text": "Let me check", "language": "en", "voice": "nova"},
            {"text": "Got it", "language": "en", "voice": "nova"},
            {"text": "Acha", "language": "hi", "voice": "nova"},
            {"text": "Theek hai", "language": "hi", "voice": "nova"},
            {"text": "Ek minute", "language": "hi", "voice": "nova"},
            {"text": "Bilkul", "language": "hi", "voice": "nova"},
            
            # Clarifications
            {"text": "Sorry, I didn't catch that. Could you please repeat?", "language": "en", "voice": "nova"},
            {"text": "Maaf kariye, main samajh nahi paya. Kya aap phir se bol sakte hain?", "language": "hi", "voice": "nova"},
            {"text": "Sorry, samajh nahi aaya. Phir se bolo please?", "language": "mixed", "voice": "nova"},
            
            # Thinking/Processing
            {"text": "Let me see", "language": "en", "voice": "nova"},
            {"text": "Give me a moment", "language": "en", "voice": "nova"},
            {"text": "Dekho", "language": "hi", "voice": "nova"},
            {"text": "Ek minute ruko", "language": "hi", "voice": "nova"},
            {"text": "Let me check", "language": "mixed", "voice": "nova"},
            
            # Positive responses
            {"text": "Great!", "language": "en", "voice": "nova"},
            {"text": "Perfect!", "language": "en", "voice": "nova"},
            {"text": "Excellent!", "language": "en", "voice": "nova"},
            {"text": "Bahut accha!", "language": "hi", "voice": "nova"},
            {"text": "Shabash!", "language": "hi", "voice": "nova"},
            
            # Goodbyes
            {"text": "Thank you for calling. Have a great day!", "language": "en", "voice": "nova"},
            {"text": "Dhanyawad! Aapka din accha rahe!", "language": "hi", "voice": "nova"},
            {"text": "Thank you! Goodbye!", "language": "mixed", "voice": "nova"},
            
            # Hotel/Travel related
            {"text": "Which city would you like to book a hotel in?", "language": "en", "voice": "nova"},
            {"text": "Kis sheher mein hotel book karna hai?", "language": "hi", "voice": "nova"},
            {"text": "Kis city mein hotel chahiye?", "language": "mixed", "voice": "nova"},
            
            {"text": "How many nights will you be staying?", "language": "en", "voice": "nova"},
            {"text": "Kitne din ke liye rukna hai?", "language": "hi", "voice": "nova"},
            {"text": "Kitne nights ke liye stay karna hai?", "language": "mixed", "voice": "nova"},
            
            # Train related
            {"text": "Which train route are you looking for?", "language": "en", "voice": "nova"},
            {"text": "Kis route ki train chahiye?", "language": "hi", "voice": "nova"},
            {"text": "Kahan se kahan tak train chahiye?", "language": "mixed", "voice": "nova"},
            
            # Restaurant related
            {"text": "What type of cuisine are you looking for?", "language": "en", "voice": "nova"},
            {"text": "Kis type ka khana chahiye?", "language": "hi", "voice": "nova"},
            {"text": "Kya khana pasand hai?", "language": "mixed", "voice": "nova"},
        ]
    
    def _get_cache_key(self, text: str, language: str, voice: str) -> str:
        """Generate cache key for text, language, and voice combination"""
        content = f"{text}|{language}|{voice}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_cached_audio(self, text: str, language: str, voice: str) -> Optional[str]:
        """Get cached audio file path if exists"""
        cache_key = self._get_cache_key(text, language, voice)
        
        with self.lock:
            # Memory first
            mem = self._memory_cache.get(cache_key)
            if mem:
                return mem
            if cache_key in self.cache_index:
                cache_info = self.cache_index[cache_key]
                audio_file = self.cache_dir / f"{cache_key}.mp3"
                
                # Check if file still exists
                if audio_file.exists():
                    # Promote to memory cache
                    self._memory_cache[cache_key] = str(audio_file)
                    return str(audio_file)
                else:
                    # Remove from index if file missing
                    del self.cache_index[cache_key]
                    self._save_cache_index()
        
        return None
    
    def cache_audio(self, text: str, language: str, voice: str, audio_file_path: str):
        """Cache audio file for future use"""
        cache_key = self._get_cache_key(text, language, voice)
        
        with self.lock:
            # Memory record
            self._memory_cache[cache_key] = str(self.cache_dir / f"{cache_key}.mp3")
            # Copy audio file to cache directory
            cached_file = self.cache_dir / f"{cache_key}.mp3"
            try:
                import shutil
                import os
                
                # Ensure source file exists and get absolute path
                if not os.path.exists(audio_file_path):
                    print(f"⚠️ Source file not found: {audio_file_path}")
                    return False
                
                # Get absolute path to avoid path issues
                abs_source = os.path.abspath(audio_file_path)
                abs_dest = os.path.abspath(cached_file)
                
                shutil.copy2(abs_source, abs_dest)
                
                # Update cache index
                self.cache_index[cache_key] = {
                    "text": text,
                    "language": language,
                    "voice": voice,
                    "cached_at": time.time(),
                    "file_size": cached_file.stat().st_size
                }
                self._save_cache_index()
                
                print(f"🎵 Cached TTS: {text[:30]}...")
                return True
                
            except Exception as e:
                print(f"⚠️ Error caching audio: {e}")
                return False
    
    def pre_generate_common_phrases(self, tts_function):
        """Pre-generate common phrases for instant access"""
        print("🎵 Pre-generating common TTS phrases...")
        
        generated_count = 0
        for phrase_info in self.common_phrases:
            text = phrase_info["text"]
            language = phrase_info["language"]
            voice = phrase_info["voice"]
            
            # Check if already cached
            if self.get_cached_audio(text, language, voice):
                continue
            
            try:
                # Generate TTS
                audio_file = tts_function(text)
                if audio_file:
                    self.cache_audio(text, language, voice, audio_file)
                    generated_count += 1
                    
                    # Clean up temporary file
                    try:
                        os.remove(audio_file)
                    except:
                        pass
                        
            except Exception as e:
                print(f"⚠️ Error pre-generating '{text}': {e}")
        
        print(f"✅ Pre-generated {generated_count} common phrases")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            total_size = sum(
                Path(self.cache_dir / f"{key}.mp3").stat().st_size 
                for key in self.cache_index.keys()
                if (self.cache_dir / f"{key}.mp3").exists()
            )
            
            return {
                "cached_phrases": len(self.cache_index),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_dir": str(self.cache_dir)
            }
    
    def clear_cache(self):
        """Clear all cached files"""
        with self.lock:
            for cache_file in self.cache_dir.glob("*.mp3"):
                try:
                    cache_file.unlink()
                except:
                    pass
            
            self.cache_index = {}
            self._save_cache_index()
            print("🧹 TTS cache cleared")


# Global cache instance
_tts_cache = None

def get_tts_cache() -> TTSCache:
    """Get global TTS cache instance"""
    global _tts_cache
    if _tts_cache is None:
        _tts_cache = TTSCache()
    return _tts_cache

def initialize_tts_cache(tts_function):
    """Initialize TTS cache with pre-generated phrases"""
    cache = get_tts_cache()
    cache.pre_generate_common_phrases(tts_function)
    return cache
