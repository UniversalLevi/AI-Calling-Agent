"""
WhatsApp Business Service
=========================

High-level business logic layer for WhatsApp integration.
This is the main service that SARA uses to send messages.

Features:
- Payment link sending with Razorpay integration
- Call followup messages
- Payment reminders
- Conversation state tracking
- Feature flag checks
- MongoDB persistence
"""

import os
import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from .whatsapp_client import WhatsAppClient, WhatsAppResponse, get_whatsapp_client
from .razorpay_client import RazorpayClient, PaymentLinkResponse as RazorpayPaymentLinkResponse, get_razorpay_client
from .whatsapp_templates import get_template_for_language, TEMPLATES
from .models import (
    MessageResponse,
    PaymentLinkResponse,
    MessageStatus,
    PaymentStatus,
    MessageType,
    WhatsAppMessageDocument,
    PaymentLinkDocument,
    ConversationState,
)
from .config import (
    ENABLE_WHATSAPP,
    ENABLE_WHATSAPP_PAYMENT_LINKS,
    ENABLE_WHATSAPP_FOLLOWUPS,
    MONGODB_URI,
    MONGODB_DATABASE,
    MASK_PHONE_NUMBERS,
)

# Configure logging
logger = logging.getLogger(__name__)

# Optional MongoDB import
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False
    logger.warning("motor not installed - MongoDB persistence disabled")


class WhatsAppService:
    """
    High-level WhatsApp service for SARA integration.
    
    This service provides:
    - Feature flag-protected operations
    - Razorpay payment link generation + WhatsApp delivery
    - Call followup messages
    - Payment reminders
    - Conversation state tracking
    - MongoDB persistence (optional)
    
    Usage:
        service = WhatsAppService()
        result = await service.send_payment_link(
            phone="+919876543210",
            amount=50000,  # Amount in paise
            customer_name="John",
            product_name="Hotel Booking",
            call_id="CA123"
        )
    """
    
    def __init__(
        self,
        whatsapp_client: Optional[WhatsAppClient] = None,
        razorpay_client: Optional[RazorpayClient] = None,
        mongodb_uri: Optional[str] = None,
        mongodb_database: Optional[str] = None
    ):
        """
        Initialize WhatsApp service.
        
        Args:
            whatsapp_client: WhatsApp client instance (creates default if None)
            razorpay_client: Razorpay client instance (creates default if None)
            mongodb_uri: MongoDB connection URI
            mongodb_database: MongoDB database name
        """
        self.whatsapp_client = whatsapp_client or get_whatsapp_client()
        self.razorpay_client = razorpay_client or get_razorpay_client()
        
        # MongoDB setup
        self._mongodb_uri = mongodb_uri or MONGODB_URI
        self._mongodb_database = mongodb_database or MONGODB_DATABASE
        self._db_client = None
        self._db = None
        
        logger.info("WhatsAppService initialized")
    
    async def _get_db(self):
        """Get MongoDB database connection (lazy initialization)"""
        if not MONGODB_AVAILABLE:
            return None
        
        if self._db is None:
            try:
                self._db_client = AsyncIOMotorClient(self._mongodb_uri)
                self._db = self._db_client[self._mongodb_database]
                logger.info(f"Connected to MongoDB: {self._mongodb_database}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                return None
        
        return self._db
    
    def _hash_phone(self, phone: str) -> str:
        """Create a hash of phone number for database lookup"""
        normalized = ''.join(filter(str.isdigit, phone))
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for logging/storage"""
        if not MASK_PHONE_NUMBERS:
            return phone
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) > 4:
            return "*" * (len(digits) - 4) + digits[-4:]
        return "****"
    
    def _check_whatsapp_enabled(self) -> tuple[bool, Optional[str]]:
        """Check if WhatsApp is enabled and configured"""
        if not ENABLE_WHATSAPP:
            return False, "WhatsApp integration is disabled (ENABLE_WHATSAPP=false)"
        if not self.whatsapp_client.is_configured():
            return False, "WhatsApp credentials not configured"
        return True, None
    
    def _check_payment_links_enabled(self) -> tuple[bool, Optional[str]]:
        """Check if payment links feature is enabled"""
        enabled, error = self._check_whatsapp_enabled()
        if not enabled:
            return False, error
        if not ENABLE_WHATSAPP_PAYMENT_LINKS:
            return False, "WhatsApp payment links disabled (ENABLE_WHATSAPP_PAYMENT_LINKS=false)"
        if not self.razorpay_client.is_configured():
            return False, "Razorpay credentials not configured"
        return True, None
    
    def _check_followups_enabled(self) -> tuple[bool, Optional[str]]:
        """Check if followups feature is enabled"""
        enabled, error = self._check_whatsapp_enabled()
        if not enabled:
            return False, error
        if not ENABLE_WHATSAPP_FOLLOWUPS:
            return False, "WhatsApp followups disabled (ENABLE_WHATSAPP_FOLLOWUPS=false)"
        return True, None
    
    def _normalize_language_code(self, language: str) -> str:
        """Normalize language code for Meta WhatsApp API.
        
        Meta only accepts standard language codes like 'en', 'hi', 'en_US', etc.
        SARA uses 'mixed' for bilingual conversations, which needs to default to 'en'.
        """
        if language in ("mixed", "auto", ""):
            return "en"  # Default to English for mixed/unknown languages
        return language.split("-")[0].lower()  # Convert 'en-IN' to 'en', 'hi-IN' to 'hi'
    
    async def send_payment_link(
        self,
        phone: str,
        amount: int,
        customer_name: str,
        product_name: str,
        call_id: Optional[str] = None,
        language: str = "en",
        customer_email: Optional[str] = None,
        notes: Optional[Dict[str, str]] = None
    ) -> PaymentLinkResponse:
        """
        Create a Razorpay payment link and send it via WhatsApp.
        
        This is the main use case for SARA integration.
        
        Args:
            phone: Customer phone number
            amount: Amount in paise (e.g., 50000 for ₹500)
            customer_name: Customer's name
            product_name: Product/service name
            call_id: SARA call ID for tracking
            language: Message language ("en" or "hi")
            customer_email: Optional email for Razorpay
            notes: Additional metadata
            
        Returns:
            PaymentLinkResponse with success status and IDs
        """
        # Check feature flags
        enabled, error = self._check_payment_links_enabled()
        if not enabled:
            logger.warning(f"Payment link not sent: {error}")
            return PaymentLinkResponse(
                success=False,
                error_message=error
            )
        
        logger.info(f"Sending payment link to {self._mask_phone(phone)} for ₹{amount/100}")
        
        try:
            # Step 1: Create Razorpay payment link
            razorpay_notes = notes or {}
            if call_id:
                razorpay_notes["call_id"] = call_id
            razorpay_notes["product"] = product_name
            
            razorpay_result = await self.razorpay_client.create_payment_link(
                amount=amount,
                customer_name=customer_name,
                customer_phone=phone,
                customer_email=customer_email,
                description=f"Payment for {product_name}",
                reference_id=call_id,
                notes=razorpay_notes
            )
            
            if not razorpay_result.success:
                logger.error(f"Failed to create Razorpay link: {razorpay_result.error_message}")
                return PaymentLinkResponse(
                    success=False,
                    error_code=razorpay_result.error_code,
                    error_message=f"Payment link creation failed: {razorpay_result.error_message}"
                )
            
            payment_url = razorpay_result.short_url
            payment_link_id = razorpay_result.link_id
            
            logger.info(f"Razorpay link created: {payment_link_id}")
            
            # Step 2: Send via WhatsApp
            # Try template first, fall back to plain text if template doesn't exist
            template = get_template_for_language("payment_link", language)
            template_name = template.name if template else "payment_link_v1"
            
            # Format amount for display (convert paise to rupees)
            amount_display = str(int(amount / 100))
            
            # Normalize language code for Meta API (mixed -> en)
            meta_language = self._normalize_language_code(language)
            
            whatsapp_result = await self.whatsapp_client.send_template_message(
                phone=phone,
                template_name=template_name,
                variables={
                    "1": customer_name,
                    "2": product_name,
                    "3": amount_display,
                    "4": payment_url
                },
                language_code=meta_language
            )
            
            # If template failed (not found), fall back to plain text message
            if not whatsapp_result.success:
                error_msg = whatsapp_result.error_message or ""
                error_code = whatsapp_result.error_code or ""
                
                # Check if it's a template-not-found error (code 132001)
                if "132001" in error_code or "template" in error_msg.lower():
                    logger.warning(f"⚠️ Template not found, sending plain text message instead")
                    
                    # Create a nice plain text message
                    if meta_language == "hi":
                        text_message = (
                            f"🙏 Namaste {customer_name}!\n\n"
                            f"Aapka {product_name} ka payment link:\n"
                            f"💰 Amount: ₹{amount_display}\n\n"
                            f"🔗 Pay here: {payment_url}\n\n"
                            f"Thank you for choosing us! 🙏"
                        )
                    else:
                        text_message = (
                            f"Hello {customer_name}! 👋\n\n"
                            f"Here's your payment link for {product_name}:\n"
                            f"💰 Amount: ₹{amount_display}\n\n"
                            f"🔗 Pay here: {payment_url}\n\n"
                            f"Thank you for your business! 🙏"
                        )
                    
                    whatsapp_result = await self.whatsapp_client.send_text_message(
                        phone=phone,
                        text=text_message
                    )
                    
                    if whatsapp_result.success:
                        logger.info(f"✅ Payment link sent via plain text: {whatsapp_result.message_id}")
            
            if not whatsapp_result.success:
                logger.error(f"Failed to send WhatsApp: {whatsapp_result.error_message}")
                # Payment link was created but WhatsApp failed
                return PaymentLinkResponse(
                    success=False,
                    payment_link_id=payment_link_id,
                    payment_url=payment_url,
                    amount=amount,
                    error_code=whatsapp_result.error_code,
                    error_message=f"WhatsApp send failed: {whatsapp_result.error_message}"
                )
            
            logger.info(f"Payment link sent successfully: {whatsapp_result.message_id}")
            
            # Step 3: Save to MongoDB
            await self._save_payment_link(
                payment_link_id=payment_link_id,
                payment_url=payment_url,
                phone=phone,
                customer_name=customer_name,
                product_name=product_name,
                amount=amount,
                message_id=whatsapp_result.message_id,
                call_id=call_id,
                razorpay_response=razorpay_result.raw_response
            )
            
            return PaymentLinkResponse(
                success=True,
                message_id=whatsapp_result.message_id,
                payment_link_id=payment_link_id,
                payment_url=payment_url,
                amount=amount,
                status=MessageStatus.SENT
            )
            
        except Exception as e:
            logger.exception(f"Error sending payment link: {e}")
            return PaymentLinkResponse(
                success=False,
                error_message=str(e)
            )
    
    async def send_call_followup(
        self,
        phone: str,
        customer_name: str,
        call_summary: str,
        call_id: str,
        language: str = "en"
    ) -> MessageResponse:
        """
        Send a call followup message after a call ends.
        
        Args:
            phone: Customer phone number
            customer_name: Customer's name
            call_summary: Brief summary of the call
            call_id: SARA call ID
            language: Message language
            
        Returns:
            MessageResponse with success status
        """
        # Check feature flags
        enabled, error = self._check_followups_enabled()
        if not enabled:
            logger.warning(f"Followup not sent: {error}")
            return MessageResponse(
                success=False,
                error_message=error
            )
        
        logger.info(f"Sending call followup to {self._mask_phone(phone)}")
        
        try:
            template = get_template_for_language("call_followup", language)
            template_name = template.name if template else "call_followup_v1"
            
            # Normalize language code for Meta API
            meta_language = self._normalize_language_code(language)
            
            result = await self.whatsapp_client.send_template_message(
                phone=phone,
                template_name=template_name,
                variables={
                    "1": customer_name,
                    "2": call_summary
                },
                language_code=meta_language
            )
            
            if result.success:
                await self._save_message(
                    message_id=result.message_id,
                    phone=phone,
                    message_type=MessageType.FOLLOWUP,
                    template_name=template_name,
                    call_id=call_id
                )
            
            return MessageResponse(
                success=result.success,
                message_id=result.message_id,
                phone=self._mask_phone(phone),
                status=MessageStatus.SENT if result.success else MessageStatus.FAILED,
                error_code=result.error_code,
                error_message=result.error_message
            )
            
        except Exception as e:
            logger.exception(f"Error sending followup: {e}")
            return MessageResponse(
                success=False,
                error_message=str(e)
            )
    
    async def send_payment_reminder(
        self,
        phone: str,
        customer_name: str,
        product_name: str,
        amount: int,
        payment_link: str,
        original_message_id: Optional[str] = None
    ) -> MessageResponse:
        """
        Send a payment reminder for pending payments.
        
        Args:
            phone: Customer phone number
            customer_name: Customer's name
            product_name: Product/service name
            amount: Amount in paise
            payment_link: Payment link URL
            original_message_id: Original payment link message ID
            
        Returns:
            MessageResponse with success status
        """
        enabled, error = self._check_payment_links_enabled()
        if not enabled:
            return MessageResponse(success=False, error_message=error)
        
        logger.info(f"Sending payment reminder to {self._mask_phone(phone)}")
        
        try:
            amount_display = str(int(amount / 100))
            
            result = await self.whatsapp_client.send_template_message(
                phone=phone,
                template_name="payment_reminder_v1",
                variables={
                    "1": customer_name,
                    "2": product_name,
                    "3": amount_display,
                    "4": payment_link
                }
            )
            
            if result.success:
                await self._save_message(
                    message_id=result.message_id,
                    phone=phone,
                    message_type=MessageType.REMINDER,
                    template_name="payment_reminder_v1",
                    metadata={"original_message_id": original_message_id}
                )
            
            return MessageResponse(
                success=result.success,
                message_id=result.message_id,
                phone=self._mask_phone(phone),
                status=MessageStatus.SENT if result.success else MessageStatus.FAILED,
                error_code=result.error_code,
                error_message=result.error_message
            )
            
        except Exception as e:
            logger.exception(f"Error sending reminder: {e}")
            return MessageResponse(
                success=False,
                error_message=str(e)
            )
    
    async def get_conversation_state(self, phone: str) -> Optional[ConversationState]:
        """
        Get the conversation state for a user.
        
        Args:
            phone: User's phone number
            
        Returns:
            ConversationState or None if not found
        """
        db = await self._get_db()
        if db is None:
            return None
        
        try:
            phone_hash = self._hash_phone(phone)
            doc = await db.conversation_states.find_one({"phone_hash": phone_hash})
            if doc:
                return ConversationState(**doc)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation state: {e}")
            return None
    
    async def get_payment_status(self, payment_link_id: str) -> Optional[PaymentStatus]:
        """
        Get the status of a payment link.
        
        Args:
            payment_link_id: Razorpay payment link ID
            
        Returns:
            PaymentStatus or None
        """
        try:
            status = await self.razorpay_client.get_payment_status(payment_link_id)
            status_map = {
                "created": PaymentStatus.CREATED,
                "paid": PaymentStatus.PAID,
                "partially_paid": PaymentStatus.PARTIALLY_PAID,
                "expired": PaymentStatus.EXPIRED,
                "cancelled": PaymentStatus.CANCELLED,
            }
            return status_map.get(status, PaymentStatus.PENDING)
        except Exception as e:
            logger.error(f"Error getting payment status: {e}")
            return None
    
    async def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        timestamp: Optional[datetime] = None
    ):
        """
        Update the status of a sent message (called by webhook handler).
        
        Args:
            message_id: WhatsApp message ID
            status: New status
            timestamp: Status change timestamp
        """
        db = await self._get_db()
        if db is None:
            return
        
        try:
            update = {"status": status.value, "updated_at": datetime.utcnow()}
            
            if status == MessageStatus.SENT:
                update["sent_at"] = timestamp or datetime.utcnow()
            elif status == MessageStatus.DELIVERED:
                update["delivered_at"] = timestamp or datetime.utcnow()
            elif status == MessageStatus.READ:
                update["read_at"] = timestamp or datetime.utcnow()
            elif status == MessageStatus.FAILED:
                update["failed_at"] = timestamp or datetime.utcnow()
            
            await db.whatsapp_messages.update_one(
                {"message_id": message_id},
                {"$set": update}
            )
            logger.debug(f"Updated message {message_id} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Error updating message status: {e}")
    
    async def _save_payment_link(
        self,
        payment_link_id: str,
        payment_url: str,
        phone: str,
        customer_name: str,
        product_name: str,
        amount: int,
        message_id: str,
        call_id: Optional[str] = None,
        razorpay_response: Optional[Dict] = None
    ):
        """Save payment link to MongoDB"""
        db = await self._get_db()
        if db is None:
            return
        
        try:
            doc = PaymentLinkDocument(
                payment_link_id=payment_link_id,
                short_url=payment_url,
                phone=self._mask_phone(phone),
                phone_hash=self._hash_phone(phone),
                customer_name=customer_name,
                product_name=product_name,
                amount=amount,
                status=PaymentStatus.PENDING,
                whatsapp_message_id=message_id,
                call_id=call_id,
                razorpay_response=razorpay_response or {}
            )
            
            await db.payment_links.insert_one(doc.model_dump())
            logger.debug(f"Saved payment link {payment_link_id}")
            
        except Exception as e:
            logger.error(f"Error saving payment link: {e}")
    
    async def _save_message(
        self,
        message_id: str,
        phone: str,
        message_type: MessageType,
        template_name: Optional[str] = None,
        call_id: Optional[str] = None,
        payment_link_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Save message to MongoDB"""
        db = await self._get_db()
        if db is None:
            return
        
        try:
            doc = WhatsAppMessageDocument(
                message_id=message_id,
                phone=self._mask_phone(phone),
                phone_hash=self._hash_phone(phone),
                message_type=message_type,
                template_name=template_name,
                status=MessageStatus.SENT,
                call_id=call_id,
                payment_link_id=payment_link_id,
                sent_at=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            await db.whatsapp_messages.insert_one(doc.model_dump())
            logger.debug(f"Saved message {message_id}")
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
    
    def is_configured(self) -> bool:
        """Check if the service is properly configured"""
        return self.whatsapp_client.is_configured()
    
    def is_payment_links_ready(self) -> bool:
        """Check if payment links feature is ready to use"""
        return (
            ENABLE_WHATSAPP and
            ENABLE_WHATSAPP_PAYMENT_LINKS and
            self.whatsapp_client.is_configured() and
            self.razorpay_client.is_configured()
        )


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_default_service: Optional[WhatsAppService] = None


def get_whatsapp_service() -> WhatsAppService:
    """Get or create the default WhatsApp service instance"""
    global _default_service
    if _default_service is None:
        _default_service = WhatsAppService()
    return _default_service

