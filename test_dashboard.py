"""
Test Dashboard Integration
Creates test call data and verifies dashboard functionality
"""

import requests
import json
from datetime import datetime, timedelta
import random

API_URL = "http://localhost:5000"

def create_test_calls():
    """Create test call data"""
    print("🧪 Creating test call data...")
    
    # Sample phone numbers
    callers = ["+919026505441", "+919876543210", "+919123456789", "+919988776655"]
    receivers = ["+12723155611", "+13502371533"]
    statuses = ["success", "failed", "in-progress"]
    languages = ["en", "hi", "mixed"]
    
    created_count = 0
    
    for i in range(10):
        # Create call with varied data
        start_time = datetime.now() - timedelta(hours=random.randint(1, 48))
        duration = random.randint(30, 300) if i < 8 else 0  # Last 2 are in-progress
        status = "in-progress" if i >= 8 else random.choice(statuses[:2])
        
        call_data = {
            "callId": f"TEST{datetime.now().timestamp()}{i}",
            "type": random.choice(["inbound", "outbound"]),
            "caller": random.choice(callers),
            "receiver": random.choice(receivers),
            "startTime": start_time.isoformat(),
            "status": status,
            "duration": duration,
            "language": random.choice(languages),
            "transcript": f"User: Hello\nBot: Hi! How can I help you?\nUser: I need information\nBot: Sure, I can help with that.",
            "interruptionCount": random.randint(0, 5),
            "satisfaction": random.choice(["positive", "neutral", "negative"]),
            "metadata": {
                "deviceType": "mobile",
                "location": "India"
            }
        }
        
        if status != "in-progress":
            call_data["endTime"] = (start_time + timedelta(seconds=duration)).isoformat()
        
        try:
            response = requests.post(
                f"{API_URL}/api/calls",
                json=call_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                created_count += 1
                print(f"✅ Created call {i+1}: {call_data['callId'][:20]}... ({status})")
            else:
                print(f"❌ Failed to create call {i+1}: {response.status_code}")
                print(f"   Response: {response.text[:100]}")
        except Exception as e:
            print(f"❌ Error creating call {i+1}: {e}")
    
    print(f"\n✅ Created {created_count}/10 test calls")
    return created_count

def test_api_endpoints():
    """Test all API endpoints"""
    print("\n🧪 Testing API endpoints...")
    
    tests = [
        ("Health Check", "GET", "/api/health", None),
        ("Get Calls (Public)", "GET", "/api/calls/stats", None),
    ]
    
    for name, method, endpoint, data in tests:
        try:
            url = f"{API_URL}{endpoint}"
            if method == "GET":
                response = requests.get(url)
            else:
                response = requests.post(url, json=data)
            
            if response.status_code in [200, 201]:
                print(f"✅ {name}: OK ({response.status_code})")
            else:
                print(f"⚠️  {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")

def main():
    print("="*60)
    print("🧪 DASHBOARD INTEGRATION TEST")
    print("="*60)
    print()
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("⚠️  Backend responded with:", response.status_code)
    except Exception as e:
        print(f"❌ Backend is not accessible: {e}")
        print("   Make sure the dashboard is running: python start_sara.py")
        return
    
    print()
    
    # Create test data
    created = create_test_calls()
    
    if created > 0:
        print()
        test_api_endpoints()
        
        print()
        print("="*60)
        print("✅ TEST COMPLETE")
        print("="*60)
        print()
        print("📊 Dashboard should now show:")
        print(f"   - {created} call logs")
        print("   - 2 active calls (in-progress)")
        print("   - Statistics and analytics")
        print()
        print("🌐 Open dashboard: http://localhost:3000")
        print("   Login: admin / admin123")
        print()
    else:
        print("\n❌ No test data created. Check errors above.")

if __name__ == "__main__":
    main()

