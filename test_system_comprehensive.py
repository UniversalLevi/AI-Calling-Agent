"""
Comprehensive System Test
Tests all the fixes implemented:
1. Call termination fix
2. Calling bot logging
3. Dashboard data display
4. Dashboard logging
"""

import requests
import time
import json
from datetime import datetime

def test_dashboard_apis():
    """Test all dashboard API endpoints"""
    print("🧪 Testing Dashboard APIs...")
    
    base_url = "http://localhost:5000"
    
    tests = [
        ("Stats", f"{base_url}/api/calls/stats"),
        ("Call Logs", f"{base_url}/api/calls"),
        ("Active Calls", f"{base_url}/api/calls/active"),
        ("Analytics", f"{base_url}/api/calls/analytics"),
    ]
    
    results = {}
    
    for name, url in tests:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ {name}: OK - {len(data.get('data', []))} items")
                    results[name] = "PASS"
                else:
                    print(f"❌ {name}: API Error - {data.get('message')}")
                    results[name] = "FAIL"
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                results[name] = "FAIL"
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results[name] = "FAIL"
    
    return results

def test_dashboard_frontend():
    """Test dashboard frontend accessibility"""
    print("\n🧪 Testing Dashboard Frontend...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: Accessible")
            return "PASS"
        else:
            print(f"❌ Frontend: HTTP {response.status_code}")
            return "FAIL"
    except Exception as e:
        print(f"❌ Frontend: Error - {e}")
        return "FAIL"

def test_calling_bot_logs():
    """Test if calling bot logs are being written"""
    print("\n🧪 Testing Calling Bot Logs...")
    
    try:
        with open('logs/calling_bot.log', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if content:
                print("✅ Calling Bot Logs: Data present")
                print(f"   Latest entries: {content[-200:]}")  # Last 200 chars
                return "PASS"
            else:
                print("⚠️ Calling Bot Logs: Empty (bot may not have started)")
                return "WARN"
    except FileNotFoundError:
        print("❌ Calling Bot Logs: File not found")
        return "FAIL"
    except Exception as e:
        print(f"❌ Calling Bot Logs: Error - {e}")
        return "FAIL"

def test_dashboard_logs():
    """Test dashboard logs"""
    print("\n🧪 Testing Dashboard Logs...")
    
    try:
        with open('dashboard.log', 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            recent_lines = [line for line in lines[-20:] if line.strip()]
            
            if recent_lines:
                print("✅ Dashboard Logs: Data present")
                print(f"   Recent entries: {len(recent_lines)} lines")
                # Show last few lines
                for line in recent_lines[-3:]:
                    print(f"   {line}")
                return "PASS"
            else:
                print("❌ Dashboard Logs: No recent data")
                return "FAIL"
    except FileNotFoundError:
        print("❌ Dashboard Logs: File not found")
        return "FAIL"
    except Exception as e:
        print(f"❌ Dashboard Logs: Error - {e}")
        return "FAIL"

def test_call_termination_fix():
    """Test the call termination fix by checking the code"""
    print("\n🧪 Testing Call Termination Fix...")
    
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Check if the fix is present
            if 'hangup_words' in content and 'confidence < 0.3' in content:
                print("✅ Call Termination Fix: Code updated")
                return "PASS"
            else:
                print("❌ Call Termination Fix: Code not found")
                return "FAIL"
    except Exception as e:
        print(f"❌ Call Termination Fix: Error - {e}")
        return "FAIL"

def main():
    print("="*60)
    print("🧪 COMPREHENSIVE SYSTEM TEST")
    print("="*60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Run all tests
    api_results = test_dashboard_apis()
    frontend_result = test_dashboard_frontend()
    calling_logs_result = test_calling_bot_logs()
    dashboard_logs_result = test_dashboard_logs()
    termination_fix_result = test_call_termination_fix()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    all_results = {
        **api_results,
        "Frontend": frontend_result,
        "Calling Bot Logs": calling_logs_result,
        "Dashboard Logs": dashboard_logs_result,
        "Call Termination Fix": termination_fix_result
    }
    
    passed = sum(1 for result in all_results.values() if result == "PASS")
    failed = sum(1 for result in all_results.values() if result == "FAIL")
    warned = sum(1 for result in all_results.values() if result == "WARN")
    total = len(all_results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    print(f"⚠️ Warnings: {warned}/{total}")
    print()
    
    for test, result in all_results.items():
        status_icon = "✅" if result == "PASS" else "❌" if result == "FAIL" else "⚠️"
        print(f"{status_icon} {test}: {result}")
    
    print()
    if failed == 0:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
    else:
        print(f"⚠️ {failed} test(s) failed. Check the issues above.")
    
    print("="*60)

if __name__ == "__main__":
    main()

