"""Check WhatsApp Business phone number details"""
import asyncio
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def check_phone_number():
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        print("WhatsApp Business Phone Number Details:")
        print("=" * 50)
        print(response.json())

if __name__ == "__main__":
    asyncio.run(check_phone_number())

