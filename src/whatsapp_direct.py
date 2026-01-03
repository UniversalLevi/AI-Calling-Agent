"""
Direct WhatsApp Integration for SARA
=====================================

Simplified, production-ready WhatsApp integration that sends messages
directly to Meta's API without requiring the separate microservice.

This provides:
- Direct WhatsApp message sending
- Razorpay payment link creation
- Combined payment link + WhatsApp flow
- Fallback handling for 24-hour window issues
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

# Thread pool for async operations
_executor = ThreadPoolExecutor(max_workers=4)

# =============================================================================
# CONFIGURATION
# =============================================================================

# WhatsApp Cloud API
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_BUSINESS_NUMBER = os.getenv("WHATSAPP_BUSINESS_DISPLAY_NUMBER", "+91 91791 77847")

# Razorpay
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

# Feature flags
ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "false").lower() == "true"
ENABLE_PAYMENT_LINKS = os.getenv("ENABLE_WHATSAPP_PAYMENT_LINKS", "false").lower() == "true"

# Track sent messages (in production, use Redis/DB)
_messages_sent = {}  # {phone: {'payment_link_sent': bool, 'last_message_time': datetime}}


def is_configured() -> bool:
    """Check if WhatsApp is properly configured"""
    return bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID and ENABLE_WHATSAPP)


def is_payment_enabled() -> bool:
    """Check if payment links are enabled"""
    return is_configured() and ENABLE_PAYMENT_LINKS


# =============================================================================
# PHONE NUMBER UTILITIES
# =============================================================================

def normalize_phone(phone: str) -> str:
    """Normalize phone number to WhatsApp format (no + prefix)"""
    if not phone:
        return ""
    # Remove all non-digits
    digits = ''.join(c for c in phone if c.isdigit())
    # Handle Indian numbers
    if len(digits) == 10:
        return "91" + digits
    elif len(digits) == 11 and digits.startswith("0"):
        return "91" + digits[1:]
    elif len(digits) == 12 and digits.startswith("91"):
        return digits
    elif len(digits) == 13 and digits.startswith("91"):
        return digits[1:]  # Remove extra 9
    return digits


def mask_phone(phone: str) -> str:
    """Mask phone number for logging"""
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) > 4:
        return "*" * 8 + digits[-4:]
    return "****"


# =============================================================================
# RAZORPAY PAYMENT LINK
# =============================================================================

async def create_payment_link(
    amount: int,  # In paise
    customer_name: str,
    customer_phone: str,
    product_name: str = "Service",
    customer_email: Optional[str] = None
) -> Optional[str]:
    """
    Create a Razorpay payment link.
    
    Args:
        amount: Amount in paise (e.g., 50000 for ₹500)
        customer_name: Customer's name
        customer_phone: Customer's phone with country code
        product_name: Name of product/service
        customer_email: Optional email
        
    Returns:
        Payment link URL or None on failure
    """
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        logger.error("Razorpay credentials not configured")
        return None
    
    import base64
    auth = base64.b64encode(f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode()).decode()
    
    # Normalize phone
    phone = normalize_phone(customer_phone)
    if not phone:
        logger.error("Invalid phone number for payment link")
        return None
    
    # Ensure amount is always an integer (Razorpay requires whole numbers in paise)
    amount_int = int(amount) if amount else 100  # Default to ₹1 if no amount
    
    payload = {
        "amount": amount_int,
        "currency": "INR",
        "description": f"Payment for {product_name}",
        "customer": {
            "name": customer_name or "Customer",
            "contact": f"+{phone}"
        },
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
        "callback_method": "get"
    }
    
    if customer_email:
        payload["customer"]["email"] = customer_email
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.razorpay.com/v1/payment_links",
                headers={
                    "Authorization": f"Basic {auth}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                link = data.get("short_url")
                logger.info(f"💳 Payment link created: {link}")
                return link
            else:
                error = response.json()
                logger.error(f"Razorpay error: {error}")
                
                # Handle test mode UPI error
                if "UPI Payment Links" in str(error):
                    logger.info("Retrying without UPI (test mode)")
                    # Try standard link
                    response2 = await client.post(
                        "https://api.razorpay.com/v1/payment_links",
                        headers={
                            "Authorization": f"Basic {auth}",
                            "Content-Type": "application/json"
                        },
                        json=payload
                    )
                    if response2.status_code == 200:
                        return response2.json().get("short_url")
                
                return None
                
    except Exception as e:
        logger.error(f"Payment link creation failed: {e}")
        return None


# =============================================================================
# WHATSAPP MESSAGING
# =============================================================================

async def send_whatsapp_message(
    to_phone: str,
    message: str,
    preview_url: bool = True
) -> Dict[str, Any]:
    """
    Send a WhatsApp text message.
    
    Args:
        to_phone: Recipient phone number
        message: Message text
        preview_url: Whether to show URL previews
        
    Returns:
        Response dict with success status and message_id
    """
    if not is_configured():
        return {"success": False, "error": "WhatsApp not configured"}
    
    phone = normalize_phone(to_phone)
    if not phone:
        return {"success": False, "error": "Invalid phone number"}
    
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "text",
        "text": {
            "preview_url": preview_url,
            "body": message
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                msg_id = data.get("messages", [{}])[0].get("id", "")
                logger.info(f"✅ WhatsApp sent to {mask_phone(phone)}: {msg_id}")
                return {"success": True, "message_id": msg_id}
            else:
                error = response.json()
                error_msg = error.get("error", {}).get("message", "Unknown error")
                error_code = error.get("error", {}).get("code", 0)
                
                logger.error(f"❌ WhatsApp failed: {error_code} - {error_msg}")
                
                # Check for 24-hour window issue
                needs_optin = error_code == 131030 or "24" in error_msg.lower()
                
                return {
                    "success": False,
                    "error": error_msg,
                    "error_code": error_code,
                    "needs_optin": needs_optin
                }
                
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# COMBINED PAYMENT LINK + WHATSAPP FLOW
# =============================================================================

async def send_payment_link_whatsapp(
    phone: str,
    amount: int,
    customer_name: str,
    product_name: str,
    call_id: Optional[str] = None,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Create payment link and send via WhatsApp.
    
    This is the main function for the payment flow:
    1. Creates Razorpay payment link
    2. Sends WhatsApp message with the link
    3. Returns result with fallback info
    
    Args:
        phone: Customer phone number
        amount: Amount in paise
        customer_name: Customer's name
        product_name: Product/service name
        call_id: Optional call ID for tracking
        language: Message language (en/hi)
        
    Returns:
        Result dict with success, payment_link, message_id, or error info
    """
    if not is_payment_enabled():
        return {"success": False, "error": "Payment links disabled"}
    
    # Validate inputs
    customer_name = customer_name or "Customer"
    product_name = product_name or "Service"
    
    # Create payment link
    payment_link = await create_payment_link(
        amount=amount,
        customer_name=customer_name,
        customer_phone=phone,
        product_name=product_name
    )
    
    if not payment_link:
        return {"success": False, "error": "Failed to create payment link"}
    
    # Format amount for display
    amount_rupees = amount / 100
    
    # Clean customer name (remove "Customer" default, capitalize properly)
    display_name = customer_name.strip().title() if customer_name and customer_name.lower() != "customer" else ""
    
    # Compose WhatsApp message - Clean, minimal English template
    if display_name:
        greeting = f"Hi {display_name},"
    else:
        greeting = "Hi,"
    
    message = f"""{greeting}

Your payment link for *{product_name}* is ready.

*Amount:* ₹{amount_rupees:,.0f}
*Pay here:* {payment_link}

— SARA"""

    # Send WhatsApp message
    result = await send_whatsapp_message(phone, message)
    
    result["payment_link"] = payment_link
    result["amount"] = amount
    result["product"] = product_name
    
    if result.get("needs_optin"):
        result["optin_message"] = f"User needs to message {WHATSAPP_BUSINESS_NUMBER} first"
        result["business_number"] = WHATSAPP_BUSINESS_NUMBER
    
    return result


# =============================================================================
# SYNC WRAPPERS (For Flask routes)
# =============================================================================

def send_payment_link_sync(
    phone: str,
    amount: int,
    customer_name: str,
    product_name: str,
    call_id: Optional[str] = None,
    language: str = "en",
    fire_and_forget: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Sync wrapper for send_payment_link_whatsapp.
    
    Args:
        phone: Customer phone
        amount: Amount in paise
        customer_name: Customer name
        product_name: Product name
        call_id: Call ID
        language: Message language
        fire_and_forget: If True, run async and don't wait
        
    Returns:
        Result dict or None if fire_and_forget
    """
    if not is_payment_enabled():
        logger.debug("WhatsApp payment disabled")
        return None
    
    coro = send_payment_link_whatsapp(
        phone=phone,
        amount=amount,
        customer_name=customer_name or "Customer",
        product_name=product_name or "Service",
        call_id=call_id,
        language=language
    )
    
    if fire_and_forget:
        _executor.submit(asyncio.run, coro)
        logger.info(f"📱 Payment link triggered for {mask_phone(phone)}")
        return None
    else:
        return asyncio.run(coro)


def send_message_sync(
    phone: str,
    message: str,
    fire_and_forget: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Sync wrapper for send_whatsapp_message.
    """
    if not is_configured():
        return None
    
    coro = send_whatsapp_message(phone, message)
    
    if fire_and_forget:
        _executor.submit(asyncio.run, coro)
        return None
    else:
        return asyncio.run(coro)


# =============================================================================
# CALL SESSION HELPERS
# =============================================================================

def get_whatsapp_greeting_prompt(language: str = "hi") -> str:
    """
    Get verbal prompt asking user to opt-in to WhatsApp.
    This should be added to SARA's greeting.
    
    Args:
        language: Greeting language
        
    Returns:
        Verbal prompt text
    """
    # Clean the business number for speech
    business_num = WHATSAPP_BUSINESS_NUMBER.replace("+", "").replace(" ", " ")
    
    if language == "hi":
        return f"Aur agar aapko payment link ya updates WhatsApp par chahiye, toh {business_num} par 'Hi' message kar dijiye."
    else:
        return f"If you'd like payment links or updates on WhatsApp, please send 'Hi' to {business_num}."


def should_send_payment_link(session: Dict[str, Any], speech: str) -> bool:
    """
    Check if we should send payment link based on session state and speech.
    
    Args:
        session: Call session dict
        speech: User's speech text
        
    Returns:
        True if we should send payment link
    """
    # Don't send if already sent
    if session.get('payment_link_sent'):
        return False
    
    # Check for explicit request
    from src.whatsapp_integration import detect_payment_link_intent, detect_payment_confirmation_intent
    
    if detect_payment_link_intent(speech):
        return True
    
    if detect_payment_confirmation_intent(speech):
        return True
    
    return False


def mark_payment_link_sent(session: Dict[str, Any], phone: str, link: str):
    """Mark that payment link was sent in session"""
    session['payment_link_sent'] = True
    session['payment_link_sent_at'] = datetime.now().isoformat()
    session['payment_link_phone'] = phone
    session['payment_link_url'] = link


# =============================================================================
# STATUS & HEALTH
# =============================================================================

def get_status() -> Dict[str, Any]:
    """Get WhatsApp integration status"""
    return {
        "enabled": ENABLE_WHATSAPP,
        "payment_links_enabled": ENABLE_PAYMENT_LINKS,
        "configured": is_configured(),
        "business_number": WHATSAPP_BUSINESS_NUMBER,
        "razorpay_configured": bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
    }


async def test_connection() -> Dict[str, Any]:
    """Test WhatsApp API connection"""
    if not is_configured():
        return {"success": False, "error": "Not configured"}
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}",
                headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "business_name": data.get("verified_name", "Unknown"),
                    "display_number": data.get("display_phone_number", "Unknown")
                }
            else:
                return {"success": False, "error": response.text}
                
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    'is_configured',
    'is_payment_enabled',
    'WHATSAPP_BUSINESS_NUMBER',
    
    # Core functions
    'send_whatsapp_message',
    'send_payment_link_whatsapp',
    'create_payment_link',
    
    # Sync wrappers
    'send_payment_link_sync',
    'send_message_sync',
    
    # Helpers
    'get_whatsapp_greeting_prompt',
    'should_send_payment_link',
    'mark_payment_link_sent',
    'normalize_phone',
    'mask_phone',
    
    # Status
    'get_status',
    'test_connection'
]

