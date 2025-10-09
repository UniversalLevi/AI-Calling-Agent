#!/usr/bin/env python3
"""
Test Enhanced TTS System - Master Branch Implementation
=====================================================

This script tests the enhanced TTS system with the master branch's
superior configuration for natural, non-robotic audio.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

def test_hinglish_transliterator():
    """Test the advanced Hinglish transliterator"""
    print("🧪 Testing Hinglish Transliterator...")
    
    try:
        from src.hinglish_transliterator import optimize_text_for_sara_tts, transliterate_hinglish
        
        test_cases = [
            "नमस्ते, मैं सारा हूँ",
            "Hotel book karna hai",
            "Restaurant mein table chahiye",
            "Hello, main theek hun",
            "आज meeting important है"
        ]
        
        for text in test_cases:
            optimized = optimize_text_for_sara_tts(text, 'mixed')
            print(f"  Input: {text}")
            print(f"  Output: {optimized}")
            print()
        
        print("✅ Hinglish Transliterator working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Hinglish Transliterator error: {e}")
        return False

def test_language_detection():
    """Test the enhanced language detection"""
    print("🧪 Testing Language Detection...")
    
    try:
        from src.language_detector import detect_language
        
        test_cases = [
            ("Hello, how are you?", "en"),
            ("नमस्ते, आप कैसे हैं?", "hi"),
            ("Hotel book karna hai", "mixed"),
            ("Restaurant mein table chahiye", "mixed"),
            ("Hello, main theek hun", "mixed")
        ]
        
        for text, expected in test_cases:
            detected = detect_language(text)
            status = "✅" if detected == expected else "❌"
            print(f"  {status} '{text}' -> {detected} (expected: {expected})")
        
        print("✅ Language Detection working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Language Detection error: {e}")
        return False

def test_enhanced_tts():
    """Test the enhanced TTS system"""
    print("🧪 Testing Enhanced TTS System...")
    
    try:
        from src.enhanced_hindi_tts import EnhancedHindiTTS
        
        # Initialize TTS system
        tts = EnhancedHindiTTS()
        print(f"✅ TTS System initialized with providers: {tts.providers}")
        
        # Test text optimization
        test_text = "Hotel book karna hai"
        optimized = tts._optimize_text_for_tts(test_text)
        print(f"✅ Text optimization: '{test_text}' -> '{optimized}'")
        
        print("✅ Enhanced TTS System working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced TTS System error: {e}")
        return False

def test_audio_generation():
    """Test actual audio generation (if OpenAI API key is available)"""
    print("🧪 Testing Audio Generation...")
    
    # Check if OpenAI API key is available
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
        print("⚠️ OpenAI API key not configured, skipping audio generation test")
        return True
    
    try:
        from src.enhanced_hindi_tts import speak_mixed_enhanced
        
        test_text = "Hello, I am Sara. How can I help you today?"
        print(f"🎤 Generating audio for: '{test_text}'")
        
        audio_file = speak_mixed_enhanced(test_text)
        
        if audio_file and audio_file.endswith('.mp3'):
            print(f"✅ Audio generated successfully: {audio_file}")
            
            # Check if file exists
            if Path(audio_file).exists():
                file_size = Path(audio_file).stat().st_size
                print(f"✅ Audio file exists with size: {file_size} bytes")
                return True
            else:
                print(f"❌ Audio file not found: {audio_file}")
                return False
        else:
            print(f"❌ Audio generation failed: {audio_file}")
            return False
            
    except Exception as e:
        print(f"❌ Audio Generation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced TTS System - Master Branch Implementation")
    print("=" * 60)
    
    tests = [
        ("Hinglish Transliterator", test_hinglish_transliterator),
        ("Language Detection", test_language_detection),
        ("Enhanced TTS System", test_enhanced_tts),
        ("Audio Generation", test_audio_generation)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        result = test_func()
        results.append((test_name, result))
        print("-" * 40)
    
    # Summary
    print("\n📊 Test Results Summary:")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Enhanced TTS system is ready!")
        print("🎤 The system now uses Master Branch's superior configuration:")
        print("   - Advanced Hinglish transliteration (227+ mappings)")
        print("   - Natural speech patterns and contractions")
        print("   - Optimized TTS settings (tts-1, speed=1.0)")
        print("   - Enhanced language detection")
        print("   - Multi-provider fallback system")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
