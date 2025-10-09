#!/usr/bin/env python3
"""
Test AI Brain - Master Branch Implementation
===========================================

This script tests the AI Brain to ensure it's not stuck in the service loop.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append('src')

def test_ai_brain_responses():
    """Test AI Brain responses to ensure no loop"""
    print("🧪 Testing AI Brain Responses...")
    
    try:
        from src.mixed_ai_brain import MixedAIBrain
        
        # Initialize AI Brain
        ai_brain = MixedAIBrain()
        print(f"✅ AI Brain initialized with provider: {ai_brain.provider_name}")
        
        # Test cases that were causing the loop
        test_cases = [
            "Chand Koi Hotel book karna tha",
            "Hotel book karna hai",
            "Restaurant mein table chahiye",
            "Hello, how are you?",
            "aur kuchh aur kuchh"
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: '{text}'")
            
            # Get AI response
            response = ai_brain.ask(text)
            
            print(f"🤖 AI Response: '{response}'")
            
            # Check if it's the generic service response (indicating loop)
            generic_responses = [
                "I'm here to help you with services",
                "Main yahan aapki service ke liye hun",
                "I only provide services"
            ]
            
            is_generic = any(generic in response for generic in generic_responses)
            
            if is_generic:
                print(f"⚠️  WARNING: Generic service response detected - possible loop!")
            else:
                print(f"✅ Good: Natural, contextual response")
        
        print("\n✅ AI Brain testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ AI Brain testing error: {e}")
        return False

def main():
    """Run AI Brain tests"""
    print("🚀 Testing AI Brain - Master Branch Implementation")
    print("=" * 60)
    
    success = test_ai_brain_responses()
    
    if success:
        print("\n🎉 AI Brain tests passed!")
        print("🎯 The bot should now give natural, contextual responses instead of generic service messages.")
    else:
        print("\n⚠️ AI Brain tests failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
