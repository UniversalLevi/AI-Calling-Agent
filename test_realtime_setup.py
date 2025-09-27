#!/usr/bin/env python3
"""
Test Script for Real-time Voice Bot Setup
=========================================

This script tests if all real-time components are properly installed and configured.
"""

import sys
import os
import importlib
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    required_modules = [
        ('webrtcvad', 'Voice Activity Detection'),
        ('librosa', 'Audio processing'),
        ('numpy', 'Numerical computing'),
        ('sounddevice', 'Audio I/O'),
        ('pygame', 'Audio playback'),
    ]
    
    results = {}
    for module_name, description in required_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name} ({description})")
            results[module_name] = True
        except ImportError as e:
            print(f"❌ {module_name} ({description}) - {e}")
            results[module_name] = False
    
    return results

def test_realtime_modules():
    """Test if our realtime modules can be imported"""
    print("\n🤖 Testing realtime modules...")
    
    sys.path.insert(0, 'src')
    
    try:
        from realtime_vad import VoiceActivityDetector, RealtimeConversationManager
        print("✅ realtime_vad module")
        
        from realtime_voice_bot import RealtimeVoiceBot
        print("✅ realtime_voice_bot module")
        
        return True
    except ImportError as e:
        print(f"❌ Realtime modules - {e}")
        return False

def test_vad_functionality():
    """Test VAD functionality"""
    print("\n🎤 Testing Voice Activity Detection...")
    
    try:
        sys.path.insert(0, 'src')
        from realtime_vad import VoiceActivityDetector
        import numpy as np
        
        # Create VAD instance
        vad = VoiceActivityDetector(aggressiveness=2, sample_rate=16000)
        
        # Test with silent audio
        silent_audio = np.zeros(480)  # 30ms at 16kHz
        is_speech_silent = vad.is_speech(silent_audio)
        
        # Test with noise audio
        noise_audio = np.random.normal(0, 0.1, 480)
        is_speech_noise = vad.is_speech(noise_audio)
        
        print(f"✅ VAD initialized successfully")
        print(f"   Silent audio detected as speech: {is_speech_silent}")
        print(f"   Noise audio detected as speech: {is_speech_noise}")
        
        return True
    except Exception as e:
        print(f"❌ VAD test failed - {e}")
        return False

def test_audio_devices():
    """Test audio device availability"""
    print("\n🔊 Testing audio devices...")
    
    try:
        import sounddevice as sd
        
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        output_devices = [d for d in devices if d['max_output_channels'] > 0]
        
        print(f"✅ Found {len(input_devices)} input devices")
        print(f"✅ Found {len(output_devices)} output devices")
        
        if len(input_devices) == 0:
            print("⚠️ No microphone detected - voice input may not work")
        
        if len(output_devices) == 0:
            print("⚠️ No speakers detected - audio output may not work")
        
        return len(input_devices) > 0 and len(output_devices) > 0
    except Exception as e:
        print(f"❌ Audio device test failed - {e}")
        return False

def test_ai_components():
    """Test AI components"""
    print("\n🧠 Testing AI components...")
    
    try:
        sys.path.insert(0, 'src')
        
        # Test language detection
        from language_detector import detect_language
        
        test_cases = [
            ("Hello how are you", "en"),
            ("नमस्ते कैसे हैं आप", "hi"),
            ("Hello नमस्ते", "mixed")
        ]
        
        for text, expected in test_cases:
            detected = detect_language(text)
            status = "✅" if detected == expected else "⚠️"
            print(f"{status} '{text}' -> {detected} (expected: {expected})")
        
        return True
    except Exception as e:
        print(f"❌ AI components test failed - {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n⚙️ Testing environment configuration...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'TWILIO_PHONE_NUMBER'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value in ['REPLACE_ME', 'your_key_here']:
            missing_vars.append(var)
            print(f"❌ {var} not configured")
        else:
            print(f"✅ {var} configured")
    
    if missing_vars:
        print(f"\n⚠️ Please configure these variables in your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_actual_value")
    
    return len(missing_vars) == 0

def main():
    """Run all tests"""
    print("🚀 Real-time Voice Bot Setup Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Realtime Modules", test_realtime_modules),
        ("VAD Functionality", test_vad_functionality),
        ("Audio Devices", test_audio_devices),
        ("AI Components", test_ai_components),
        ("Environment Config", test_environment_config),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your real-time voice bot is ready!")
        print("\n🚀 Next steps:")
        print("   1. Run: python main.py")
        print("   2. Choose option 4 to test locally")
        print("   3. Choose option 3 for real-time phone calls")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please fix the issues above.")
        print("\n📖 Check REALTIME_SETUP.md for troubleshooting guide")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
