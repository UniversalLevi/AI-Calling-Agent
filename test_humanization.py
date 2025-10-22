"""
Humanization Testing Script
===========================

Comprehensive testing script to validate all humanization features:
- Feature flag system
- Language detection with phone bias
- Emotion detection
- Humanized responses
- TTS cache
- Async processing
- Dashboard integration
"""

import os
import sys
import time
import json
from typing import Dict, List, Any

# Add src to path
sys.path.append('src')

def test_feature_flags():
    """Test feature flag system"""
    print("\n🧪 Testing Feature Flag System...")
    
    try:
        from src.config import is_humanized_mode_enabled, get_humanization_config
        
        # Test feature flag
        humanized_mode = is_humanized_mode_enabled()
        print(f"✅ Humanized mode enabled: {humanized_mode}")
        
        # Test config retrieval
        config = get_humanization_config()
        print(f"✅ Config loaded: {len(config)} settings")
        
        # Validate key settings
        required_settings = [
            'humanized_mode', 'hindi_bias_threshold', 'filler_frequency',
            'tts_speed', 'emotion_detection_mode'
        ]
        
        for setting in required_settings:
            if setting in config:
                print(f"✅ {setting}: {config[setting]}")
            else:
                print(f"❌ Missing setting: {setting}")
        
        return True
        
    except Exception as e:
        print(f"❌ Feature flag test failed: {e}")
        return False

def test_language_detection():
    """Test enhanced language detection"""
    print("\n🧪 Testing Language Detection...")
    
    try:
        from src.language_detector import detect_language_with_phone_bias, detect_language_with_bias
        
        # Test cases
        test_cases = [
            ("Hello, how are you?", None, "en"),
            ("Namaste, kaise hain aap?", None, "hi"),
            ("Main hotel book karna chahta hun", None, "hi"),
            ("Hello, main Sara hun", "+91-9876543210", "hi"),  # Indian number
            ("Hello, I am John", "+1-555-123-4567", "en"),    # US number
            ("Namaste, kaise ho?", "+91-9876543210", "hi"),    # Indian number with Hindi
        ]
        
        passed = 0
        for text, phone, expected in test_cases:
            if phone:
                result = detect_language_with_phone_bias(text, phone)
            else:
                result = detect_language_with_bias(text)
            
            if result == expected:
                print(f"✅ '{text[:30]}...' + {phone} → {result}")
                passed += 1
            else:
                print(f"❌ '{text[:30]}...' + {phone} → {result} (expected {expected})")
        
        print(f"✅ Language detection: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)
        
    except Exception as e:
        print(f"❌ Language detection test failed: {e}")
        return False

def test_emotion_detection():
    """Test emotion detection system"""
    print("\n🧪 Testing Emotion Detection...")
    
    try:
        from src.emotion_detector import detect_emotion, EmotionalTone
        
        # Test cases
        test_cases = [
            ("I am so angry!", EmotionalTone.ANGRY),
            ("I don't understand this", EmotionalTone.CONFUSED),
            ("This is great!", EmotionalTone.HAPPY),
            ("I need help with this", EmotionalTone.EMPATHETIC),
            ("What time is it?", EmotionalTone.NEUTRAL),
            ("Main pareshan hun", EmotionalTone.ANGRY),
            ("Samajh nahi aaya", EmotionalTone.CONFUSED),
            ("Bahut accha hai!", EmotionalTone.HAPPY),
        ]
        
        passed = 0
        for text, expected in test_cases:
            result = detect_emotion(text)
            if result == expected:
                print(f"✅ '{text}' → {result.value}")
                passed += 1
            else:
                print(f"❌ '{text}' → {result.value} (expected {expected.value})")
        
        print(f"✅ Emotion detection: {passed}/{len(test_cases)} passed")
        return passed >= len(test_cases) * 0.8  # 80% accuracy threshold
        
    except Exception as e:
        print(f"❌ Emotion detection test failed: {e}")
        return False

def test_response_pipeline():
    """Test humanized response pipeline"""
    print("\n🧪 Testing Response Pipeline...")
    
    try:
        from src.responses import generate_response, get_greeting
        from src.config import is_humanized_mode_enabled
        
        if not is_humanized_mode_enabled():
            print("⚠️ Humanized mode disabled, skipping response test")
            return True
        
        # Test greeting generation
        greetings = {
            'en': get_greeting('en'),
            'hi': get_greeting('hi'),
            'mixed': get_greeting('mixed')
        }
        
        for lang, greeting in greetings.items():
            if greeting and len(greeting) > 10:
                print(f"✅ {lang} greeting: {greeting[:50]}...")
            else:
                print(f"❌ Invalid {lang} greeting: {greeting}")
        
        # Test response generation
        test_inputs = [
            ("Hello, I need help", "en", "booking"),
            ("Namaste, hotel book karna hai", "hi", "booking"),
            ("I want to book a train", "en", "booking"),
            ("Main pareshan hun", "hi", "support"),
        ]
        
        passed = 0
        for user_input, language, context in test_inputs:
            try:
                response = generate_response(user_input, context=context)
                if response and len(response) > 5:
                    print(f"✅ '{user_input}' → '{response[:50]}...'")
                    passed += 1
                else:
                    print(f"❌ Invalid response for '{user_input}': {response}")
            except Exception as e:
                print(f"❌ Error generating response for '{user_input}': {e}")
        
        print(f"✅ Response pipeline: {passed}/{len(test_inputs)} passed")
        return passed >= len(test_inputs) * 0.8
        
    except Exception as e:
        print(f"❌ Response pipeline test failed: {e}")
        return False

def test_tts_cache():
    """Test TTS cache system - DISABLED (module removed)"""
    print("\n🧪 Testing TTS Cache...")
    print("❌ TTS cache test skipped - module removed as requested")
    return False

def test_async_processing():
    """Test async processing system - DISABLED (module removed)"""
    print("\n🧪 Testing Async Processing...")
    print("❌ Async processing test skipped - module removed as requested")
    return False

def test_conversation_memory():
    """Test conversation memory system"""
    print("\n🧪 Testing Conversation Memory...")
    
    try:
        from src.conversation_memory import (
            start_call_memory, add_conversation_exchange, 
            get_context_summary, get_recent_conversation_history,
            store_neutral_facts, get_neutral_context
        )
        
        # Test call memory
        call_sid = "test_call_123"
        start_call_memory(call_sid, "hi")
        
        # Add some exchanges
        exchanges = [
            ("Namaste, main Raj hun", "Namaste Raj ji! Kaise hain aap?", "hi"),
            ("Main hotel book karna chahta hun", "Bilkul! Kis sheher mein hotel chahiye?", "hi"),
            ("Delhi mein", "Accha! Kitne din ke liye rukna hai?", "hi"),
        ]
        
        for user_text, bot_response, language in exchanges:
            add_conversation_exchange(call_sid, user_text, bot_response, language)
        
        # Test context summary
        context = get_context_summary(call_sid)
        if context and len(context) > 10:
            print(f"✅ Context summary: {context[:100]}...")
        else:
            print(f"❌ Invalid context summary: {context}")
        
        # Test recent history
        recent_history = get_recent_conversation_history(call_sid)
        if recent_history and len(recent_history) <= 5:  # Should be limited to 5
            print(f"✅ Recent history: {len(recent_history)} exchanges")
        else:
            print(f"❌ Invalid recent history: {len(recent_history)} exchanges")
        
        # Test neutral facts
        store_neutral_facts(call_sid, "My name is Raj and I live in Delhi")
        neutral_context = get_neutral_context(call_sid)
        if neutral_context and "raj" in neutral_context.lower():
            print(f"✅ Neutral context: {neutral_context}")
        else:
            print(f"❌ Invalid neutral context: {neutral_context}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation memory test failed: {e}")
        return False

def test_dashboard_integration():
    """Test dashboard integration"""
    print("\n🧪 Testing Dashboard Integration...")
    
    try:
        # Test if dashboard files exist
        dashboard_files = [
            "sara-dashboard/backend/controllers/systemController.js",
            "sara-dashboard/backend/routes/systemRoutes.js",
        ]
        
        for file_path in dashboard_files:
            if os.path.exists(file_path):
                print(f"✅ Dashboard file exists: {file_path}")
            else:
                print(f"❌ Missing dashboard file: {file_path}")
        
        # Test if new endpoints are defined
        with open("sara-dashboard/backend/controllers/systemController.js", "r") as f:
            controller_content = f.read()
        
        required_endpoints = [
            "getVoiceSettings",
            "updateVoiceSettings", 
            "testVoiceSettings",
            "getHumanizationSettings",
            "updateHumanizationSettings"
        ]
        
        for endpoint in required_endpoints:
            if endpoint in controller_content:
                print(f"✅ Endpoint defined: {endpoint}")
            else:
                print(f"❌ Missing endpoint: {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard integration test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and generate report"""
    print("🚀 Starting Comprehensive Humanization Testing")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Feature Flags", test_feature_flags),
        ("Language Detection", test_language_detection),
        ("Emotion Detection", test_emotion_detection),
        ("Response Pipeline", test_response_pipeline),
        ("TTS Cache", test_tts_cache),
        ("Async Processing", test_async_processing),
        ("Conversation Memory", test_conversation_memory),
        ("Dashboard Integration", test_dashboard_integration),
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            test_results[test_name] = False
    
    # Generate report
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Humanization system is ready!")
    elif passed >= total * 0.8:
        print("⚠️ Most tests passed. System is mostly functional.")
    else:
        print("❌ Multiple test failures. System needs attention.")
    
    # Save results to file
    with open("humanization_test_results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "results": test_results,
            "summary": {
                "passed": passed,
                "total": total,
                "percentage": passed/total*100
            }
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: humanization_test_results.json")
    
    return passed == total

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

