#!/usr/bin/env python3
"""
Simple Humanization Validation Script
"""

import sys
import os

# Add src to path
sys.path.append('src')

def main():
    print("🧪 Quick Humanization Validation")
    print("=" * 40)
    
    # Test 1: Feature flags
    try:
        from src.config import is_humanized_mode_enabled
        enabled = is_humanized_mode_enabled()
        print(f"✅ Feature flags: HUMANIZED_MODE = {enabled}")
    except Exception as e:
        print(f"❌ Feature flags: {e}")
    
    # Test 2: Language detection
    try:
        from src.language_detector import detect_language_with_phone_bias
        result = detect_language_with_phone_bias("Namaste, kaise hain aap?", "+91-9876543210")
        print(f"✅ Language detection: {result}")
    except Exception as e:
        print(f"❌ Language detection: {e}")
    
    # Test 3: Emotion detection
    try:
        from src.emotion_detector import detect_emotion
        emotion = detect_emotion("I am so angry!")
        print(f"✅ Emotion detection: {emotion.value}")
    except Exception as e:
        print(f"❌ Emotion detection: {e}")
    
    # Test 4: Response factory
    try:
        from src.responses import generate_response
        response = generate_response("Hello, I need help", context="booking")
        print(f"✅ Response generation: {response[:50]}...")
    except Exception as e:
        print(f"❌ Response generation: {e}")
    
    # Test 5: TTS cache (DISABLED - module removed)
    print("❌ TTS cache: Module removed as requested")
    
    # Test 6: Async processor (DISABLED - module removed)
    print("❌ Async processing: Module removed as requested")
    
    print("\n🎉 Validation complete!")

if __name__ == "__main__":
    main()

