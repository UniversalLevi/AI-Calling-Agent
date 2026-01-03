"""
Test script to manually send a WhatsApp message
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_send_whatsapp():
    """Test sending a WhatsApp message directly"""
    import httpx
    
    # Get credentials from environment
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    print("=" * 60)
    print("WhatsApp Direct Send Test")
    print("=" * 60)
    
    # Check configuration
    if not access_token:
        print("❌ WHATSAPP_ACCESS_TOKEN not set!")
        return
    if not phone_number_id:
        print("❌ WHATSAPP_PHONE_NUMBER_ID not set!")
        return
    
    print(f"✅ Access Token: {access_token[:20]}...{access_token[-10:]}")
    print(f"✅ Phone Number ID: {phone_number_id}")
    
    # Target phone number (user's number)
    target_phone = "919026505441"  # Without + prefix for WhatsApp API
    
    print(f"\n📱 Sending to: {target_phone}")
    
    # WhatsApp API URL
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Simple text message payload
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": target_phone,
        "type": "text",
        "text": {
            "preview_url": True,
            "body": "🧪 Test Message from SARA!\n\nThis is a test to verify WhatsApp integration is working.\n\n✅ If you see this, the connection is successful!"
        }
    }
    
    print(f"\n📤 Sending request to: {url}")
    print(f"📝 Payload: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            print(f"\n📥 Response Status: {response.status_code}")
            print(f"📥 Response Body: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if "messages" in data:
                    msg_id = data["messages"][0]["id"]
                    print(f"\n✅ SUCCESS! Message ID: {msg_id}")
                    print("📱 Check your WhatsApp - you should receive the message!")
                else:
                    print(f"\n⚠️ Unexpected response format: {data}")
            else:
                print(f"\n❌ FAILED! Status: {response.status_code}")
                error_data = response.json()
                if "error" in error_data:
                    error = error_data["error"]
                    print(f"   Error Code: {error.get('code')}")
                    print(f"   Error Type: {error.get('type')}")
                    print(f"   Error Message: {error.get('message')}")
                    
                    # Common error explanations
                    if error.get('code') == 131030:
                        print("\n💡 This error means the recipient hasn't messaged your business first.")
                        print("   WhatsApp requires users to initiate conversation or opt-in first.")
                        print("   Solution: Send a message FROM your WhatsApp to the business number first.")
                    elif error.get('code') == 190:
                        print("\n💡 Access token expired or invalid. Generate a new one from Meta.")
                    elif "template" in str(error.get('message', '')).lower():
                        print("\n💡 Template issue - we're using plain text, so this shouldn't happen.")
                        
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_send_whatsapp())

