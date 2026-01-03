"""
SMS Service using Twilio
Sends SMS to users asking them to opt-in for WhatsApp messaging
"""
import os
import logging
from typing import Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

# Twilio configuration (reuse existing credentials)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# WhatsApp Business number for opt-in
WHATSAPP_BUSINESS_NUMBER = os.getenv("WHATSAPP_BUSINESS_DISPLAY_NUMBER", "+91 91791 77847")

# Feature flag
ENABLE_WHATSAPP_OPTIN_SMS = os.getenv("ENABLE_WHATSAPP_OPTIN_SMS", "true").lower() == "true"

# Track which numbers we've already sent opt-in SMS to (in-memory cache)
# In production, this should be stored in a database
_optin_sms_sent = set()


def get_twilio_client() -> Optional[Client]:
    """Get Twilio client if configured"""
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        logger.warning("Twilio credentials not configured")
        return None
    try:
        return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    except Exception as e:
        logger.error(f"Failed to create Twilio client: {e}")
        return None


def normalize_phone_number(phone: str) -> str:
    """Normalize phone number to E.164 format"""
    if not phone:
        return ""
    # Remove spaces, dashes, parentheses
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    # Add + if missing
    if not phone.startswith('+'):
        # Assume Indian number if 10 digits
        if len(phone) == 10:
            phone = '+91' + phone
        elif len(phone) == 12 and phone.startswith('91'):
            phone = '+' + phone
    return phone


def send_whatsapp_optin_sms(
    to_phone: str,
    customer_name: Optional[str] = None,
    force: bool = False
) -> bool:
    """
    Send SMS asking user to opt-in for WhatsApp messaging
    
    Args:
        to_phone: Recipient phone number
        customer_name: Optional customer name for personalization
        force: If True, send even if already sent before
        
    Returns:
        True if SMS sent successfully, False otherwise
    """
    if not ENABLE_WHATSAPP_OPTIN_SMS:
        logger.info("WhatsApp opt-in SMS is disabled")
        return False
    
    # Normalize phone number
    to_phone = normalize_phone_number(to_phone)
    if not to_phone:
        logger.error("Invalid phone number for SMS")
        return False
    
    # Check if we've already sent to this number (avoid spam)
    if to_phone in _optin_sms_sent and not force:
        logger.info(f"WhatsApp opt-in SMS already sent to {to_phone[-4:]}")
        return True  # Already sent, consider it success
    
    # Get Twilio client
    client = get_twilio_client()
    if not client:
        logger.error("Twilio client not available")
        return False
    
    # Personalize greeting
    greeting = f"Hi {customer_name}!" if customer_name else "Hi!"
    
    # Compose SMS message
    sms_body = f"""{greeting}

🤖 This is SARA from Eazy Dropshipping.

📱 To receive payment links and updates on WhatsApp, please send "Hi" to:

👉 {WHATSAPP_BUSINESS_NUMBER}

Just send any message to that number, and we'll be able to send you:
✅ Payment links
✅ Order updates
✅ Quick support

Thank you! 🙏"""

    try:
        message = client.messages.create(
            body=sms_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logger.info(f"📱 SMS queued to ****{to_phone[-4:]}, SID: {message.sid}")
        
        # Check delivery status after a short delay
        import time
        time.sleep(2)  # Wait for delivery status update
        
        # Fetch updated message status
        try:
            updated_msg = client.messages(message.sid).fetch()
            status = updated_msg.status
            
            if status in ['delivered', 'sent']:
                logger.info(f"✅ SMS delivered to ****{to_phone[-4:]}")
                _optin_sms_sent.add(to_phone)
                return True
            elif status == 'failed':
                error_code = updated_msg.error_code
                logger.warning(f"❌ SMS failed: Error {error_code}")
                # Error 30044 = carrier blocked (common for India)
                if error_code == 30044:
                    logger.warning("⚠️ SMS blocked by carrier (Error 30044)")
                return False
            elif status == 'undelivered':
                logger.warning(f"❌ SMS undelivered: {updated_msg.error_message}")
                return False
            else:
                # Status is 'queued' or 'sending' - assume it might work
                logger.info(f"📱 SMS status: {status} - assuming delivery")
                _optin_sms_sent.add(to_phone)
                return True
                
        except Exception as fetch_error:
            logger.warning(f"Could not verify SMS delivery: {fetch_error}")
            # Assume sent if we got this far
            _optin_sms_sent.add(to_phone)
            return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio SMS error: {e.code} - {e.msg}")
        return False
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        return False


def send_payment_link_sms(
    to_phone: str,
    payment_link: str,
    amount: float,
    product_name: str = "Service",
    customer_name: Optional[str] = None
) -> bool:
    """
    Send SMS with payment link (fallback if WhatsApp fails)
    
    Args:
        to_phone: Recipient phone number
        payment_link: The payment URL
        amount: Payment amount
        product_name: Name of the product/service
        customer_name: Optional customer name
        
    Returns:
        True if SMS sent successfully
    """
    to_phone = normalize_phone_number(to_phone)
    if not to_phone:
        logger.error("Invalid phone number for payment SMS")
        return False
    
    client = get_twilio_client()
    if not client:
        logger.error("Twilio client not available")
        return False
    
    greeting = f"Hi {customer_name}!" if customer_name else "Hi!"
    
    sms_body = f"""{greeting}

💳 Payment Link for {product_name}

Amount: ₹{amount:.0f}

Pay here: {payment_link}

Thank you for choosing us! 🙏
- SARA, Eazy Dropshipping"""

    try:
        message = client.messages.create(
            body=sms_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        logger.info(f"💳 Payment link SMS sent to ****{to_phone[-4:]}, SID: {message.sid}")
        return True
        
    except TwilioRestException as e:
        logger.error(f"Twilio SMS error: {e.code} - {e.msg}")
        return False
    except Exception as e:
        logger.error(f"Failed to send payment SMS: {e}")
        return False


def has_optin_sms_been_sent(phone: str) -> bool:
    """Check if opt-in SMS was already sent to this number"""
    phone = normalize_phone_number(phone)
    return phone in _optin_sms_sent


def clear_optin_cache():
    """Clear the opt-in SMS cache (for testing)"""
    _optin_sms_sent.clear()
    logger.info("Opt-in SMS cache cleared")


# Export key functions
__all__ = [
    'send_whatsapp_optin_sms',
    'send_payment_link_sms',
    'has_optin_sms_been_sent',
    'clear_optin_cache',
    'ENABLE_WHATSAPP_OPTIN_SMS',
    'WHATSAPP_BUSINESS_NUMBER'
]

