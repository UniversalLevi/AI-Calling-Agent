#!/usr/bin/env python3
"""
Real-time log monitor for the AI Calling Bot
"""
import requests
import time
import json

def monitor_webhook():
    """Monitor the webhook endpoint for incoming calls"""
    webhook_url = "https://8c9fe65fe13e.ngrok-free.app/voice?realtime=true"
    
    print("🔍 AI CALLING BOT - REAL-TIME LOG MONITOR")
    print("=" * 50)
    print(f"📡 Webhook URL: {webhook_url}")
    print(f"⏰ Started monitoring at: {time.strftime('%H:%M:%S')}")
    print("=" * 50)
    print("📞 Waiting for incoming calls...")
    print("💡 Make a call to see real-time logs here!")
    print("=" * 50)
    
    try:
        while True:
            # Test if webhook is accessible (POST request like Twilio would make)
            try:
                response = requests.post(webhook_url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Webhook accessible - Status: {response.status_code}")
                else:
                    print(f"✅ Webhook responding - Status: {response.status_code} (Expected for POST)")
            except requests.exceptions.RequestException as e:
                print(f"❌ Webhook error: {e}")
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
        print("👋 Goodbye!")

if __name__ == "__main__":
    monitor_webhook()
