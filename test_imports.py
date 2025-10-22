#!/usr/bin/env python3
"""
Quick Import Test
"""

import sys
sys.path.append('src')

print("Testing imports...")

try:
    print("1. Testing config import...")
    from src.config import is_humanized_mode_enabled
    print("✅ Config import successful")
except Exception as e:
    print(f"❌ Config import failed: {e}")

try:
    print("2. Testing response factory import...")
    from src.responses import generate_response, get_greeting
    print("✅ Response factory import successful")
except Exception as e:
    print(f"❌ Response factory import failed: {e}")

try:
    print("3. Testing mixed STT import...")
    from src.mixed_stt import MixedSTTEngine
    print("✅ Mixed STT import successful")
except Exception as e:
    print(f"❌ Mixed STT import failed: {e}")

print("Import test complete!")

