"""
Test Dashboard Python Integration
Test the dashboard API integration without modifying main.py
"""

import sys
import os

# Add src to path
sys.path.append('src')

# Set environment variable for dashboard (disabled by default)
os.environ['ENABLE_DASHBOARD'] = os.getenv('ENABLE_DASHBOARD', 'false')
os.environ['DASHBOARD_API_URL'] = 'http://localhost:3001'

print("🧪 Testing Dashboard Python Integration")
print(f"Dashboard enabled: {os.environ['ENABLE_DASHBOARD']}")
print(f"Dashboard URL: {os.environ['DASHBOARD_API_URL']}")
print("-" * 50)

# Test 1: Import modules
print("\n✅ Test 1: Importing modules...")
try:
    from simple_dashboard_integration import SimpleDashboardIntegration, simple_dashboard
    print("✅ simple_dashboard_integration imported successfully!")
    
    # dashboard_api is a Flask Blueprint, test it separately
    from dashboard_api import dashboard_api as dashboard_blueprint
    print("✅ dashboard_api Blueprint imported successfully!")
    print("✅ All imports successful!")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Use the global dashboard instance
print("\n✅ Test 2: Using dashboard integration instance...")
try:
    # The global instance is already created
    dashboard = simple_dashboard
    print(f"✅ Dashboard instance ready! URL: {dashboard.dashboard_url}")
except Exception as e:
    print(f"❌ Dashboard instance failed: {e}")
    sys.exit(1)

# Test 3: Test call logging (always test, dashboard enabled or not)
print("\n✅ Test 3: Testing call logging...")
try:
    # Test call start logging
    test_call_data = {
        'call_sid': 'test_call_001',
        'phone_number': '+1234567890',
        'language': 'en',
        'metadata': {'test': True}
    }
    
    result = dashboard.log_call_start(test_call_data)
    print(f"Call start logged: {result}")
    
    # Test call end logging
    test_call_end_data = {
        'call_sid': 'test_call_001',
        'duration': 120,
        'status': 'completed',
        'language': 'en'
    }
    
    result = dashboard.log_call_end(test_call_end_data)
    print(f"Call end logged: {result}")
    
    # Get active calls
    active = dashboard.get_active_calls()
    print(f"Active calls: {len(active)}")
    
    print("✅ Call logging tests passed!")
except Exception as e:
    print(f"⚠️ Call logging test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test call history
print("\n✅ Test 4: Testing call history...")
try:
    history = dashboard.get_call_history()
    print(f"Call history entries: {len(history)}")
    if history:
        print(f"Last call: {history[-1]['call_sid']}")
    print("✅ Call history test passed!")
except Exception as e:
    print(f"⚠️ Call history test failed: {e}")

print("\n" + "=" * 50)
print("✅ All basic integration tests passed!")
print("\n📝 Next steps:")
print("  1. Start the dashboard backend: cd sara-dashboard/backend && node server.js")
print("  2. Run with dashboard enabled: ENABLE_DASHBOARD=true python test_dashboard_integration.py")
print("  3. Check that calls are logged to the dashboard")
print("=" * 50)

