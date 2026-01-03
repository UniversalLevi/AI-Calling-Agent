"""
WhatsApp Integration Bridge for SARA
====================================

This module provides the bridge between SARA Calling Agent and the 
WhatsApp microservice. It handles async communication and provides
simple functions for triggering WhatsApp messages from call flows.

Usage in main.py:
    from src.whatsapp_integration import trigger_payment_link, trigger_followup
    
    # In call flow:
    await trigger_payment_link(
        phone=user_phone,
        amount=50000,
        customer_name="John",
        product_name="Hotel Booking",
        call_id=call_sid
    )
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import httpx

# Configure logging
logger = logging.getLogger(__name__)

# Thread pool for running async code from sync context
_executor = ThreadPoolExecutor(max_workers=4)


# =============================================================================
# CONFIGURATION
# =============================================================================

def get_whatsapp_service_url() -> str:
    """Get WhatsApp service URL from config"""
    try:
        from .config import WHATSAPP_SERVICE_URL
        return WHATSAPP_SERVICE_URL
    except ImportError:
        return os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:8001")


def is_whatsapp_enabled() -> bool:
    """Check if WhatsApp is enabled"""
    try:
        from .config import ENABLE_WHATSAPP
        return ENABLE_WHATSAPP
    except ImportError:
        return os.getenv("ENABLE_WHATSAPP", "false").lower() == "true"


def is_payment_links_enabled() -> bool:
    """Check if payment links are enabled"""
    try:
        from .config import ENABLE_WHATSAPP_PAYMENT_LINKS
        return is_whatsapp_enabled() and ENABLE_WHATSAPP_PAYMENT_LINKS
    except ImportError:
        return is_whatsapp_enabled() and os.getenv("ENABLE_WHATSAPP_PAYMENT_LINKS", "false").lower() == "true"


def is_followups_enabled() -> bool:
    """Check if followups are enabled"""
    try:
        from .config import ENABLE_WHATSAPP_FOLLOWUPS
        return is_whatsapp_enabled() and ENABLE_WHATSAPP_FOLLOWUPS
    except ImportError:
        return is_whatsapp_enabled() and os.getenv("ENABLE_WHATSAPP_FOLLOWUPS", "false").lower() == "true"


# =============================================================================
# ASYNC API CALLS
# =============================================================================

async def _send_payment_link_async(
    phone: str,
    amount: int,
    customer_name: str,
    product_name: str,
    call_id: Optional[str] = None,
    language: str = "en",
    customer_email: Optional[str] = None,
    notes: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Async function to send payment link via WhatsApp service.
    
    Args:
        phone: Customer phone number
        amount: Amount in paise (e.g., 50000 for ₹500)
        customer_name: Customer's name
        product_name: Product/service name
        call_id: SARA call ID
        language: Message language ("en" or "hi")
        customer_email: Optional customer email
        notes: Additional metadata
        
    Returns:
        Response dict with success status and message ID
    """
    if not is_payment_links_enabled():
        logger.debug("WhatsApp payment links disabled, skipping")
        return {"success": False, "error": "Payment links disabled"}
    
    # Validate inputs before sending
    if not phone:
        return {"success": False, "error": "Phone number is required"}
    
    # Ensure customer_name is always a valid string
    if not customer_name or not isinstance(customer_name, str):
        customer_name = 'Customer'
        logger.warning("customer_name was None or invalid, using default 'Customer'")
    
    # Ensure product_name is always a valid string
    if not product_name or not isinstance(product_name, str):
        product_name = 'Service'
        logger.warning("product_name was None or invalid, using default 'Service'")
    
    url = f"{get_whatsapp_service_url()}/api/whatsapp/send-payment-link"
    
    payload = {
        "phone": phone,
        "amount": amount,
        "customer_name": customer_name,
        "product_name": product_name,
        "language": language
    }
    
    if call_id:
        payload["call_id"] = call_id
    if customer_email:
        payload["customer_email"] = customer_email
    if notes:
        payload["notes"] = notes
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Payment link sent: {data.get('message_id')}")
                return data
            else:
                error = response.json() if response.content else {"error": "Unknown error"}
                logger.error(f"Payment link failed: {error}")
                return {"success": False, "error": error}
                
    except httpx.ConnectError:
        logger.warning("WhatsApp service not available")
        return {"success": False, "error": "WhatsApp service not available"}
    except Exception as e:
        logger.error(f"Error sending payment link: {e}")
        return {"success": False, "error": str(e)}


async def _send_followup_async(
    phone: str,
    customer_name: str,
    call_summary: str,
    call_id: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Async function to send call followup via WhatsApp service.
    
    Args:
        phone: Customer phone number
        customer_name: Customer's name
        call_summary: Summary of the call
        call_id: SARA call ID
        language: Message language
        
    Returns:
        Response dict with success status
    """
    if not is_followups_enabled():
        logger.debug("WhatsApp followups disabled, skipping")
        return {"success": False, "error": "Followups disabled"}
    
    url = f"{get_whatsapp_service_url()}/api/whatsapp/send-followup"
    
    payload = {
        "phone": phone,
        "customer_name": customer_name,
        "call_summary": call_summary,
        "call_id": call_id,
        "language": language
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Followup sent: {data.get('message_id')}")
                return data
            else:
                error = response.json() if response.content else {"error": "Unknown error"}
                logger.error(f"Followup failed: {error}")
                return {"success": False, "error": error}
                
    except httpx.ConnectError:
        logger.warning("WhatsApp service not available")
        return {"success": False, "error": "WhatsApp service not available"}
    except Exception as e:
        logger.error(f"Error sending followup: {e}")
        return {"success": False, "error": str(e)}


async def _send_reminder_async(
    phone: str,
    customer_name: str,
    product_name: str,
    amount: int,
    payment_link: str,
    original_message_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async function to send payment reminder.
    """
    if not is_payment_links_enabled():
        return {"success": False, "error": "Payment links disabled"}
    
    url = f"{get_whatsapp_service_url()}/api/whatsapp/send-reminder"
    
    payload = {
        "phone": phone,
        "customer_name": customer_name,
        "product_name": product_name,
        "amount": amount,
        "payment_link": payment_link
    }
    
    if original_message_id:
        payload["original_message_id"] = original_message_id
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            return response.json() if response.status_code == 200 else {"success": False}
    except Exception as e:
        logger.error(f"Error sending reminder: {e}")
        return {"success": False, "error": str(e)}


# =============================================================================
# SYNC WRAPPER FUNCTIONS (For use in Flask/sync code)
# =============================================================================

def _run_async(coro):
    """Run async coroutine from sync context (fire-and-forget)"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, schedule as task
            asyncio.create_task(coro)
        else:
            # Run in event loop
            loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        asyncio.run(coro)


def trigger_payment_link(
    phone: str,
    amount: int,
    customer_name: str,
    product_name: str,
    call_id: Optional[str] = None,
    language: str = "en",
    customer_email: Optional[str] = None,
    notes: Optional[Dict[str, str]] = None,
    fire_and_forget: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Trigger sending a payment link via WhatsApp (sync wrapper).
    
    This is the main function to call from SARA's Flask routes.
    By default, it runs as fire-and-forget (non-blocking).
    
    Args:
        phone: Customer phone number
        amount: Amount in paise (e.g., 50000 for ₹500)
        customer_name: Customer's name
        product_name: Product/service name
        call_id: SARA call ID
        language: Message language ("en" or "hi")
        customer_email: Optional customer email
        notes: Additional metadata
        fire_and_forget: If True, don't wait for response
        
    Returns:
        Response dict if fire_and_forget=False, else None
        
    Example:
        # Fire-and-forget (non-blocking)
        trigger_payment_link(
            phone="+919876543210",
            amount=50000,
            customer_name="John",
            product_name="Hotel Booking",
            call_id="CA123"
        )
        
        # Wait for response
        result = trigger_payment_link(..., fire_and_forget=False)
    """
    if not is_payment_links_enabled():
        logger.debug("WhatsApp payment links disabled")
        return None
    
    # Validate and sanitize inputs
    if not phone:
        logger.error("Phone number is required")
        return None
    
    # Ensure customer_name is always a valid string
    if not customer_name or not isinstance(customer_name, str):
        customer_name = 'Customer'
        logger.warning(f"Invalid customer_name provided, using default: 'Customer'")
    
    # Ensure product_name is always a valid string
    if not product_name or not isinstance(product_name, str):
        product_name = 'Service'
        logger.warning(f"Invalid product_name provided, using default: 'Service'")
    
    logger.info(f"Triggering payment link for {_mask_phone(phone)}")
    
    coro = _send_payment_link_async(
        phone=phone,
        amount=amount,
        customer_name=customer_name,
        product_name=product_name,
        call_id=call_id,
        language=language,
        customer_email=customer_email,
        notes=notes
    )
    
    if fire_and_forget:
        # Run in background thread
        _executor.submit(asyncio.run, coro)
        return None
    else:
        # Wait for result
        return asyncio.run(coro)


def trigger_followup(
    phone: str,
    customer_name: str,
    call_summary: str,
    call_id: str,
    language: str = "en",
    fire_and_forget: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Trigger sending a call followup via WhatsApp (sync wrapper).
    
    Args:
        phone: Customer phone number
        customer_name: Customer's name
        call_summary: Summary of the call
        call_id: SARA call ID
        language: Message language
        fire_and_forget: If True, don't wait for response
        
    Returns:
        Response dict if fire_and_forget=False, else None
    """
    if not is_followups_enabled():
        logger.debug("WhatsApp followups disabled")
        return None
    
    logger.info(f"Triggering followup for call {call_id}")
    
    coro = _send_followup_async(
        phone=phone,
        customer_name=customer_name,
        call_summary=call_summary,
        call_id=call_id,
        language=language
    )
    
    if fire_and_forget:
        _executor.submit(asyncio.run, coro)
        return None
    else:
        return asyncio.run(coro)


def trigger_reminder(
    phone: str,
    customer_name: str,
    product_name: str,
    amount: int,
    payment_link: str,
    original_message_id: Optional[str] = None,
    fire_and_forget: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Trigger sending a payment reminder (sync wrapper).
    """
    if not is_payment_links_enabled():
        return None
    
    coro = _send_reminder_async(
        phone=phone,
        customer_name=customer_name,
        product_name=product_name,
        amount=amount,
        payment_link=payment_link,
        original_message_id=original_message_id
    )
    
    if fire_and_forget:
        _executor.submit(asyncio.run, coro)
        return None
    else:
        return asyncio.run(coro)


# =============================================================================
# INTENT DETECTION (For call flow integration)
# =============================================================================

# Keywords that indicate user wants payment link (more comprehensive)
PAYMENT_LINK_KEYWORDS = {
    "en": [
        # Direct requests
        "send link", "send me link", "send payment link", "payment link",
        "whatsapp link", "message link", "send on whatsapp", "share link",
        "upi link", "send upi", "upi payment", "gpay link", "phonepe link",
        # Variations
        "send it", "message me", "text me", "whatsapp me",
        "send to my number", "send to my phone", "send to whatsapp"
    ],
    "hi": [
        # Romanized Hindi - Core
        "link bhejo", "link send karo", "whatsapp pe bhejo",
        "payment link bhejo", "link de do", "message karo",
        "whatsapp karo", "link share karo", "link bhej do",
        "payment link bhej do", "whatsapp par bhejo",
        # UPI specific
        "upi bhejo", "upi link bhejo", "upi bhej do",
        "upi link bhej do", "upi calling bhej do",
        "gpay bhejo", "phonepe bhejo", "paytm bhejo",
        # More variations
        "mere number pe bhejo", "mere phone pe bhejo",
        "whatsapp pe de do", "message kar do", "link de dijiye",
        "bhej do mere ko", "mere ko bhej do", "mujhe bhej do",
        # Devanagari Hindi
        "लिंक भेजो", "लिंक भेज दो", "व्हाट्सएप पर भेजो",
        "पेमेंट लिंक", "पेमेंट लिंक भेजो", "पेमेंट लिंक भेज दो",
        "व्हाट्सएप मैसेज", "व्हाट्सएप पर", "लिंक दे दो",
        "मैसेज कर दो", "व्हाट्सएप कर दो", "मुझे भेज दो",
        "मेरे को भेज दो", "मेरे नंबर पर भेजो", "भेज दो",
        "यूपीआई भेजो", "यूपीआई भेज दो", "यूपीआई लिंक",
        "यूपीआई कॉलिंग", "यूपीआई कॉलिंग भेज दो",
        "जीपे भेजो", "फोनपे भेजो", "पेटीएम भेजो"
    ]
}

# Keywords that indicate payment confirmation / purchase intent
PAYMENT_CONFIRMED_KEYWORDS = {
    "en": [
        "i will pay", "ready to pay", "let me pay",
        "proceed with payment", "confirm booking", "book it",
        "yes confirm", "go ahead", "purchase", "buy it",
        "direct purchase", "i want to buy", "i want it",
        "i'll take it", "i want this", "buying", "taking it"
    ],
    "hi": [
        # Romanized Hindi
        "payment kar deta", "pay kar dunga", "book kar do",
        "confirm karo", "haan theek hai", "kar do",
        "payment karta hun", "booking confirm", "kharidna hai",
        "purchase karna", "direct purchase", "lena hai",
        "le lunga", "kharid lunga", "chahiye", "chahta hun",
        "kharidna chahta", "lena chahta", "book karo",
        # Devanagari Hindi
        "खरीदना है", "खरीदना चाहता", "पेमेंट कर दूंगा",
        "बुक कर दो", "कन्फर्म करो", "हां ठीक है",
        "परचेज", "परचेस करना", "डायरेक्ट परचेस",
        "लेना है", "ले लूंगा", "खरीद लूंगा", "चाहिए",
        "चाहता हूं", "बुक करो", "लेना चाहता"
    ]
}

# Keywords indicating number confirmation
NUMBER_CONFIRM_KEYWORDS = {
    "positive": [
        # English
        "yes", "yeah", "yep", "correct", "right", "same number",
        "this number", "same", "isi par", "isi pe", "same number par",
        # Hindi Romanized
        "haan", "ha", "haa", "theek hai", "sahi hai", "bilkul",
        "isi number pe", "isi par bhejo", "yahi number", "same hi",
        # Devanagari
        "हां", "हाँ", "ठीक है", "सही है", "बिल्कुल", "इसी पर",
        "यही नंबर", "इसी नंबर पर"
    ],
    "negative": [
        # English
        "no", "different number", "another number", "other number",
        "not this", "change number", "different",
        # Hindi Romanized  
        "nahi", "naa", "dusra number", "alag number", "koi aur number",
        "ye nahi", "change karo", "doosra",
        # Devanagari
        "नहीं", "दूसरा नंबर", "अलग नंबर", "कोई और नंबर",
        "ये नहीं", "दूसरा"
    ]
}


def detect_payment_link_intent(text: str, language: str = "en") -> bool:
    """
    Dynamically detect if user is asking for a payment link.
    Uses keyword matching + pattern detection for flexibility.
    
    Args:
        text: User's speech text
        language: Detected language
        
    Returns:
        True if user wants payment link sent
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check all language keywords (both romanized and Devanagari)
    for lang_keywords in PAYMENT_LINK_KEYWORDS.values():
        for keyword in lang_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower or keyword in text:
                print(f"📱 WhatsApp: Payment link intent detected - matched '{keyword}'")
                logger.info(f"Payment link intent detected: matched '{keyword}'")
                return True
    
    # Dynamic pattern matching for variations
    # Payment-related words
    payment_words = [
        "payment", "पेमेंट", "pay", "पे", "upi", "यूपीआई", "यूपी",
        "gpay", "जीपे", "phonepe", "फोनपे", "paytm", "पेटीएम"
    ]
    
    # Action words indicating sending
    send_words = [
        "link", "लिंक", "whatsapp", "व्हाट्सएप", "bhej", "भेज",
        "calling", "कॉलिंग", "send", "message", "मैसेज", "de do",
        "दे दो", "kar do", "कर दो", "dijiye", "दीजिये"
    ]
    
    has_payment = any(p in text_lower or p in text for p in payment_words)
    has_send = any(s in text_lower or s in text for s in send_words)
    
    if has_payment and has_send:
        print(f"📱 WhatsApp: Payment link intent detected via pattern")
        logger.info(f"Payment link intent detected via pattern matching")
        return True
    
    # Check for implicit link requests
    implicit_patterns = [
        ("mere", "bhej"),  # mere ko bhej do
        ("मेरे", "भेज"),
        ("mujhe", "bhej"),  # mujhe bhej do
        ("मुझे", "भेज"),
        ("number", "bhej"),  # number pe bhej do
        ("नंबर", "भेज"),
    ]
    
    for pattern1, pattern2 in implicit_patterns:
        if (pattern1 in text_lower or pattern1 in text) and (pattern2 in text_lower or pattern2 in text):
            print(f"📱 WhatsApp: Payment link intent detected via implicit pattern")
            logger.info(f"Payment link intent detected via implicit pattern")
            return True
    
    return False


def detect_payment_confirmation_intent(text: str, language: str = "en") -> bool:
    """
    Detect if user is confirming they want to pay/purchase.
    
    Args:
        text: User's speech text
        language: Detected language
        
    Returns:
        True if user is confirming payment intent
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Check for negative modifiers that negate the intent (word-level check)
    import re
    negative_patterns = [
        r'\bnahi\b', r'\bnaa\b', r'\bno\b', r'\bnot\b', r"\bdon't\b", r'\bdont\b', r'\bcancel\b',
        r'\bनहीं\b', r'\bना\b', r'\bमत\b', r'रहने दो', r'\brehne do\b', r'\bmat\b'
    ]
    
    for pattern in negative_patterns:
        if re.search(pattern, text_lower) or re.search(pattern, text):
            return False
    
    for lang_keywords in PAYMENT_CONFIRMED_KEYWORDS.values():
        for keyword in lang_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in text_lower or keyword in text:
                logger.info(f"Payment confirmation detected: matched '{keyword}'")
                return True


def detect_number_confirmation(text: str) -> str:
    """
    Detect if user confirms or rejects using their current number.
    
    Args:
        text: User's speech text
        
    Returns:
        "yes" if confirmed, "no" if rejected, "unknown" otherwise
    """
    if not text:
        return "unknown"
    
    text_lower = text.lower()
    
    # Check for positive confirmation
    for keyword in NUMBER_CONFIRM_KEYWORDS["positive"]:
        if keyword.lower() in text_lower or keyword in text:
            logger.info(f"Number confirmed: matched '{keyword}'")
            return "yes"
    
    # Check for negative (different number)
    for keyword in NUMBER_CONFIRM_KEYWORDS["negative"]:
        if keyword.lower() in text_lower or keyword in text:
            logger.info(f"Different number requested: matched '{keyword}'")
            return "no"
    
    return "unknown"


def extract_phone_from_text(text: str) -> Optional[str]:
    """
    Extract phone number from user's speech.
    
    Args:
        text: User's speech text
        
    Returns:
        Phone number if found, None otherwise
    """
    import re
    
    # Remove common words and punctuation
    cleaned = text.replace("।", "").replace(".", "").replace(",", " ")
    
    # Find sequences of digits
    digits = re.findall(r'\d+', cleaned)
    
    # Combine and check if it's a valid phone number
    number = ''.join(digits)
    
    # Indian mobile number (10 digits) or with country code
    if len(number) == 10:
        return "+91" + number
    elif len(number) == 12 and number.startswith("91"):
        return "+" + number
    elif len(number) == 13 and number.startswith("91"):
        return "+" + number
    
    return None
    
    return False


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _mask_phone(phone: str) -> str:
    """Mask phone for logging"""
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) > 4:
        return "*" * (len(digits) - 4) + digits[-4:]
    return "****"


def check_whatsapp_service_health() -> bool:
    """
    Check if WhatsApp service is running and healthy.
    
    Returns:
        True if service is healthy
    """
    try:
        import requests
        url = f"{get_whatsapp_service_url()}/health"
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except:
        return False


def get_whatsapp_status() -> Dict[str, Any]:
    """
    Get WhatsApp integration status.
    
    Returns:
        Status dict with enabled flags and service health
    """
    return {
        "whatsapp_enabled": is_whatsapp_enabled(),
        "payment_links_enabled": is_payment_links_enabled(),
        "followups_enabled": is_followups_enabled(),
        "service_healthy": check_whatsapp_service_health(),
        "service_url": get_whatsapp_service_url()
    }

