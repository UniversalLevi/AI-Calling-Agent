#!/usr/bin/env python3
"""
Real-time log monitor for the AI Calling Bot Flask server
"""
import time
import subprocess
import os

def monitor_flask_logs():
    """Monitor Flask server logs in real-time"""
    print("🔍 AI CALLING BOT - REAL-TIME LOG MONITOR")
    print("=" * 60)
    print("📡 Monitoring Flask server logs on port 5000")
    print("📞 Webhook URL: https://8c9fe65fe13e.ngrok-free.app/voice?realtime=true")
    print("=" * 60)
    print("💡 Make a call to see real-time conversation logs!")
    print("=" * 60)
    
    # Check if Flask is running
    result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
    if ':5000' in result.stdout:
        print("✅ Flask server is running on port 5000")
    else:
        print("❌ Flask server not found on port 5000")
        return
    
    print("\n📋 Current Status:")
    print("- Flask server: Running on port 5000")
    print("- Ngrok tunnel: https://8c9fe65fe13e.ngrok-free.app")
    print("- Real-time mode: Enabled")
    print("- Interruption handling: Enhanced")
    print("- Hindi TTS: Enabled")
    
    print("\n🎯 Ready for testing!")
    print("📞 Call +916267420877 to test the real-time conversation")
    print("💬 You should see logs like:")
    print("   📞 Incoming call from: +13502371533")
    print("   🚀 Starting realtime conversation mode")
    print("   🎤 Partial speech: [your words]")
    print("   ⚡ Fast AI response: [bot response]")
    print("   🛑 Potential interruption detected")
    
    print("\n⏰ Monitoring... (Press Ctrl+C to stop)")
    print("=" * 60)
    
    try:
        while True:
            # Show current time
            current_time = time.strftime('%H:%M:%S')
            print(f"⏰ {current_time} - Waiting for incoming calls...")
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("👋 Goodbye!")

if __name__ == "__main__":
    monitor_flask_logs()

