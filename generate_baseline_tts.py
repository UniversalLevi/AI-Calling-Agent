"""
Generate Baseline TTS Audio for Regression Testing
Run this to create baseline audio samples for comparison
"""

import sys
import shutil
import os
from pathlib import Path

# Add src to path
sys.path.append('src')

from enhanced_hindi_tts import speak_enhanced_hindi

def generate_baseline_audio():
    """Generate baseline TTS audio samples"""
    print("🎤 Generating baseline TTS audio samples...")
    
    # Ensure baseline directory exists
    baseline_dir = Path("tests/baseline_audio")
    baseline_dir.mkdir(parents=True, exist_ok=True)
    
    # Test cases
    test_cases = [
        ('नमस्ते, आप कैसे हैं?', 'hindi'),
        ('Hello, how can I help you today?', 'english'),
        ('Hi नमस्ते, I need help', 'mixed')
    ]
    
    for text, lang in test_cases:
        print(f"\n📝 Generating {lang} sample: '{text}'")
        audio_filename = speak_enhanced_hindi(text)
        
        if audio_filename and os.path.exists(f'audio_files/{audio_filename}'):
            # Copy to baseline
            dest_path = baseline_dir / f'{lang}.mp3'
            shutil.copy(f'audio_files/{audio_filename}', str(dest_path))
            print(f"✅ Saved baseline: {dest_path}")
        else:
            print(f"❌ Failed to generate {lang} audio")
    
    print("\n✅ Baseline audio generation complete!")
    print(f"📁 Baseline audio saved in: {baseline_dir.absolute()}")

if __name__ == "__main__":
    generate_baseline_audio()

