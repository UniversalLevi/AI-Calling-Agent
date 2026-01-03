"""
WhatsApp Service Data Models
============================

Pydantic models for request/response validation and MongoDB schemas.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS
# =============================================================================

class MessageStatus(str, Enum):
    """WhatsApp message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class PaymentStatus(str, Enum):
    """Payment link status"""
    CREATED = "created"
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    FAILED = "failed"


class MessageType(str, Enum):
    """Types of WhatsApp messages"""
    TEXT = "text"
    TEMPLATE = "template"
    PAYMENT_LINK = "payment_link"
    FOLLOWUP = "followup"
    REMINDER = "reminder"


# =============================================================================
# REQUEST MODELS
# =============================================================================

class SendPaymentLinkRequest(BaseModel):
    """Request to send a payment link via WhatsApp"""
    phone: str = Field(..., description="Recipient phone number")
    amount: int = Field(..., gt=0, description="Amount in paise (e.g., 50000 for ₹500)")
    customer_name: str = Field(..., min_length=1, description="Customer's name")
    product_name: str = Field(..., min_length=1, description="Product/service name")
    call_id: Optional[str] = Field(None, description="Associated call ID from SARA")
    language: str = Field("en", description="Message language (en/hi)")
    customer_email: Optional[str] = Field(None, description="Customer email for Razorpay")
    notes: Optional[Dict[str, str]] = Field(None, description="Additional metadata")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate and normalize phone number"""
        digits = ''.join(filter(str.isdigit, v))
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return v
    
    @field_validator('customer_name', mode='before')
    @classmethod
    def validate_customer_name(cls, v: Any) -> str:
        """Ensure customer_name is always a valid string"""
        if v is None or not isinstance(v, str) or len(v.strip()) == 0:
            return 'Customer'
        return v.strip()
    
    @field_validator('product_name', mode='before')
    @classmethod
    def validate_product_name(cls, v: Any) -> str:
        """Ensure product_name is always a valid string"""
        if v is None or not isinstance(v, str) or len(v.strip()) == 0:
            return 'Service'
        return v.strip()


class SendMessageRequest(BaseModel):
    """Request to send a generic WhatsApp message"""
    phone: str = Field(..., description="Recipient phone number")
    template_name: str = Field(..., description="Template name to use")
    variables: Dict[str, str] = Field(..., description="Template variables")
    language: str = Field("en", description="Template language code")
    call_id: Optional[str] = Field(None, description="Associated call ID")


class SendFollowupRequest(BaseModel):
    """Request to send a call followup message"""
    phone: str = Field(..., description="Recipient phone number")
    customer_name: str = Field(..., description="Customer's name")
    call_summary: str = Field(..., description="Summary of the call")
    call_id: str = Field(..., description="Associated call ID")
    language: str = Field("en", description="Message language")


class SendReminderRequest(BaseModel):
    """Request to send a payment reminder"""
    phone: str = Field(..., description="Recipient phone number")
    customer_name: str = Field(..., description="Customer's name")
    product_name: str = Field(..., description="Product/service name")
    amount: int = Field(..., gt=0, description="Amount in paise")
    payment_link: str = Field(..., description="Payment link URL")
    original_message_id: Optional[str] = Field(None, description="Original payment link message ID")


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class MessageResponse(BaseModel):
    """Response after sending a WhatsApp message"""
    success: bool
    message_id: Optional[str] = None
    phone: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaymentLinkResponse(BaseModel):
    """Response after creating and sending a payment link"""
    success: bool
    message_id: Optional[str] = None
    payment_link_id: Optional[str] = None
    payment_url: Optional[str] = None
    amount: Optional[int] = None
    status: MessageStatus = MessageStatus.PENDING
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatusResponse(BaseModel):
    """Response for message/payment status check"""
    message_id: str
    message_status: MessageStatus
    payment_status: Optional[PaymentStatus] = None
    last_updated: datetime


# =============================================================================
# DATABASE MODELS (MongoDB)
# =============================================================================

class WhatsAppMessageDocument(BaseModel):
    """MongoDB document for tracking WhatsApp messages"""
    message_id: str = Field(..., description="WhatsApp message ID")
    phone: str = Field(..., description="Recipient phone number (masked)")
    phone_hash: str = Field(..., description="Hashed phone number for lookup")
    message_type: MessageType
    template_name: Optional[str] = None
    template_variables: Optional[Dict[str, str]] = None
    status: MessageStatus = MessageStatus.PENDING
    call_id: Optional[str] = None
    payment_link_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Error tracking
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaymentLinkDocument(BaseModel):
    """MongoDB document for tracking payment links"""
    payment_link_id: str = Field(..., description="Razorpay payment link ID")
    short_url: str = Field(..., description="Razorpay short URL")
    phone: str = Field(..., description="Customer phone (masked)")
    phone_hash: str = Field(..., description="Hashed phone for lookup")
    customer_name: str
    product_name: str
    amount: int = Field(..., description="Amount in paise")
    
    status: PaymentStatus = PaymentStatus.CREATED
    whatsapp_message_id: Optional[str] = None
    call_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    paid_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Razorpay response data
    razorpay_response: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationState(BaseModel):
    """Track conversation state for a user"""
    phone_hash: str = Field(..., description="Hashed phone number")
    
    # Last interaction
    last_message_id: Optional[str] = None
    last_message_type: Optional[MessageType] = None
    last_message_at: Optional[datetime] = None
    
    # Payment state
    pending_payment_link_id: Optional[str] = None
    last_payment_status: Optional[PaymentStatus] = None
    
    # Call association
    last_call_id: Optional[str] = None
    
    # User responses
    has_replied: bool = False
    last_reply_at: Optional[datetime] = None
    last_reply_text: Optional[str] = None
    
    # State
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# WEBHOOK MODELS
# =============================================================================

class WebhookMessage(BaseModel):
    """Inbound message from WhatsApp webhook"""
    message_id: str
    from_phone: str
    timestamp: datetime
    message_type: str
    text: Optional[str] = None
    media_id: Optional[str] = None
    media_url: Optional[str] = None


class WebhookStatus(BaseModel):
    """Status update from WhatsApp webhook"""
    message_id: str
    status: str  # sent, delivered, read, failed
    timestamp: datetime
    recipient_phone: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class WebhookPayload(BaseModel):
    """Full webhook payload from Meta"""
    object: str
    entry: List[Dict[str, Any]]

