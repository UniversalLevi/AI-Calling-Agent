"""
WhatsApp Webhook Handler
========================

Handles inbound webhooks from Meta WhatsApp Business API.
Processes message status updates and user replies.

Webhook Events:
- messages: Inbound messages from users
- statuses: Delivery status updates (sent, delivered, read, failed)
"""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from .models import (
    MessageStatus,
    PaymentStatus,
    WebhookMessage,
    WebhookStatus,
)
from .config import WHATSAPP_WEBHOOK_VERIFY_TOKEN

# Configure logging
logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handles WhatsApp webhook events from Meta.
    
    Responsibilities:
    - Verify webhook signature
    - Parse webhook payloads
    - Update message statuses
    - Process user replies
    - Trigger SARA notifications
    """
    
    def __init__(self, app_secret: Optional[str] = None):
        """
        Initialize webhook handler.
        
        Args:
            app_secret: Meta App Secret for signature verification
        """
        import os
        self.app_secret = app_secret or os.getenv("META_APP_SECRET", "")
        self.verify_token = WHATSAPP_WEBHOOK_VERIFY_TOKEN
        
        # Callbacks
        self._on_message_status_update = None
        self._on_user_reply = None
        self._on_payment_confirmation = None
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription (GET request from Meta).
        
        Args:
            mode: hub.mode parameter
            token: hub.verify_token parameter
            challenge: hub.challenge parameter
            
        Returns:
            Challenge string if verified, None otherwise
        """
        if mode == "subscribe" and token == self.verify_token:
            logger.info("Webhook verified successfully")
            return challenge
        
        logger.warning(f"Webhook verification failed: mode={mode}, token mismatch")
        return None
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature from X-Hub-Signature-256 header.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not self.app_secret:
            logger.warning("App secret not configured, skipping signature verification")
            return True  # Skip verification if not configured
        
        if not signature:
            logger.warning("No signature provided")
            return False
        
        try:
            # Signature format: "sha256=<hash>"
            if signature.startswith("sha256="):
                signature = signature[7:]
            
            expected = hmac.new(
                self.app_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            is_valid = hmac.compare_digest(expected, signature)
            
            if not is_valid:
                logger.warning("Webhook signature mismatch")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    async def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming webhook payload from Meta.
        
        Args:
            payload: Parsed JSON payload
            
        Returns:
            Processing result
        """
        results = {
            "messages_processed": 0,
            "statuses_processed": 0,
            "errors": []
        }
        
        try:
            # Validate payload structure
            if payload.get("object") != "whatsapp_business_account":
                logger.debug("Ignoring non-WhatsApp webhook")
                return results
            
            entries = payload.get("entry", [])
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    if change.get("field") != "messages":
                        continue
                    
                    value = change.get("value", {})
                    
                    # Process status updates
                    statuses = value.get("statuses", [])
                    for status_data in statuses:
                        try:
                            await self._handle_status_update(status_data)
                            results["statuses_processed"] += 1
                        except Exception as e:
                            logger.error(f"Error processing status: {e}")
                            results["errors"].append(str(e))
                    
                    # Process inbound messages
                    messages = value.get("messages", [])
                    for message_data in messages:
                        try:
                            await self._handle_inbound_message(message_data, value)
                            results["messages_processed"] += 1
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            results["errors"].append(str(e))
            
            logger.info(f"Webhook processed: {results['messages_processed']} messages, {results['statuses_processed']} statuses")
            return results
            
        except Exception as e:
            logger.exception(f"Error processing webhook: {e}")
            results["errors"].append(str(e))
            return results
    
    async def _handle_status_update(self, status_data: Dict[str, Any]):
        """
        Handle message status update.
        
        Args:
            status_data: Status update from webhook
        """
        message_id = status_data.get("id")
        status = status_data.get("status")
        timestamp = status_data.get("timestamp")
        recipient = status_data.get("recipient_id")
        
        if not message_id or not status:
            return
        
        # Map Meta status to our enum
        status_map = {
            "sent": MessageStatus.SENT,
            "delivered": MessageStatus.DELIVERED,
            "read": MessageStatus.READ,
            "failed": MessageStatus.FAILED
        }
        
        mapped_status = status_map.get(status)
        if not mapped_status:
            logger.debug(f"Unknown status: {status}")
            return
        
        logger.info(f"Status update: {message_id} -> {status}")
        
        # Parse timestamp
        ts = None
        if timestamp:
            try:
                ts = datetime.fromtimestamp(int(timestamp))
            except:
                pass
        
        # Handle errors
        error_code = None
        error_message = None
        if status == "failed":
            errors = status_data.get("errors", [])
            if errors:
                error = errors[0]
                error_code = str(error.get("code", ""))
                error_message = error.get("message", "")
                logger.error(f"Message {message_id} failed: {error_code} - {error_message}")
        
        # Create status object
        webhook_status = WebhookStatus(
            message_id=message_id,
            status=status,
            timestamp=ts or datetime.utcnow(),
            recipient_phone=recipient or "",
            error_code=error_code,
            error_message=error_message
        )
        
        # Notify callback
        if self._on_message_status_update:
            await self._on_message_status_update(webhook_status)
    
    async def _handle_inbound_message(self, message_data: Dict[str, Any], value: Dict[str, Any]):
        """
        Handle inbound message from user.
        
        Args:
            message_data: Message data from webhook
            value: Full value object containing contacts
        """
        message_id = message_data.get("id")
        from_phone = message_data.get("from")
        timestamp = message_data.get("timestamp")
        message_type = message_data.get("type")
        
        if not message_id or not from_phone:
            return
        
        # Get message text
        text = None
        if message_type == "text":
            text = message_data.get("text", {}).get("body")
        elif message_type == "button":
            text = message_data.get("button", {}).get("text")
        elif message_type == "interactive":
            interactive = message_data.get("interactive", {})
            if interactive.get("type") == "button_reply":
                text = interactive.get("button_reply", {}).get("title")
            elif interactive.get("type") == "list_reply":
                text = interactive.get("list_reply", {}).get("title")
        
        # Parse timestamp
        ts = datetime.utcnow()
        if timestamp:
            try:
                ts = datetime.fromtimestamp(int(timestamp))
            except:
                pass
        
        logger.info(f"Inbound message from {self._mask_phone(from_phone)}: {text[:50] if text else '[no text]'}")
        
        # Create message object
        webhook_message = WebhookMessage(
            message_id=message_id,
            from_phone=from_phone,
            timestamp=ts,
            message_type=message_type,
            text=text
        )
        
        # Check for payment confirmation keywords
        if text:
            await self._check_payment_confirmation(from_phone, text.lower())
        
        # Notify callback
        if self._on_user_reply:
            await self._on_user_reply(webhook_message)
    
    async def _check_payment_confirmation(self, phone: str, text: str):
        """
        Check if message indicates payment was made.
        
        Args:
            phone: User's phone number
            text: Message text (lowercase)
        """
        # Payment confirmation keywords
        paid_keywords = [
            "paid", "payment done", "done", "completed",
            "bhugtan", "kar diya", "ho gaya", "payment kar diya",
            "पेमेंट", "भुगतान"
        ]
        
        is_payment_mention = any(keyword in text for keyword in paid_keywords)
        
        if is_payment_mention:
            logger.info(f"Possible payment confirmation from {self._mask_phone(phone)}")
            
            if self._on_payment_confirmation:
                await self._on_payment_confirmation(phone, text)
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone for logging"""
        if len(phone) > 4:
            return "*" * (len(phone) - 4) + phone[-4:]
        return "****"
    
    # Callback setters
    def on_message_status_update(self, callback):
        """Set callback for status updates"""
        self._on_message_status_update = callback
    
    def on_user_reply(self, callback):
        """Set callback for user replies"""
        self._on_user_reply = callback
    
    def on_payment_confirmation(self, callback):
        """Set callback for payment confirmations"""
        self._on_payment_confirmation = callback


# Singleton instance
_webhook_handler: Optional[WebhookHandler] = None


def get_webhook_handler() -> WebhookHandler:
    """Get or create the webhook handler instance"""
    global _webhook_handler
    if _webhook_handler is None:
        _webhook_handler = WebhookHandler()
    return _webhook_handler

