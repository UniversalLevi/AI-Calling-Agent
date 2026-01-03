"""
Razorpay Payment Links Client
=============================

Client for creating and managing Razorpay payment links.
Used to generate payment URLs that are sent via WhatsApp.

API Documentation: https://razorpay.com/docs/api/payment-links/
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PaymentLinkResponse:
    """Response from Razorpay Payment Links API"""
    success: bool
    link_id: Optional[str] = None
    short_url: Optional[str] = None
    amount: Optional[int] = None  # Amount in paise
    status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class RazorpayClient:
    """
    Client for Razorpay Payment Links API.
    
    This client handles:
    - Creating payment links
    - Checking payment status
    - Managing link expiry
    
    Usage:
        client = RazorpayClient()
        result = await client.create_payment_link(
            amount=50000,  # Amount in paise (500 INR)
            customer_name="John Doe",
            customer_phone="+919876543210",
            description="Hotel Booking Payment"
        )
        print(result.short_url)  # Payment link URL
    """
    
    BASE_URL = "https://api.razorpay.com/v1"
    
    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize Razorpay client.
        
        Args:
            key_id: Razorpay Key ID (from env if not provided)
            key_secret: Razorpay Key Secret (from env if not provided)
            timeout: Request timeout in seconds
        """
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        self.timeout = timeout
        
        # Validate configuration
        if not self.key_id:
            logger.warning("RAZORPAY_KEY_ID not configured")
        if not self.key_secret:
            logger.warning("RAZORPAY_KEY_SECRET not configured")
    
    @property
    def auth(self) -> tuple:
        """Get basic auth credentials"""
        return (self.key_id, self.key_secret)
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to E.164 format"""
        normalized = ''.join(filter(str.isdigit, phone))
        if len(normalized) == 10:
            normalized = "+91" + normalized
        elif not normalized.startswith("+"):
            normalized = "+" + normalized
        return normalized
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for logging"""
        if len(phone) > 4:
            return "*" * (len(phone) - 4) + phone[-4:]
        return "****"
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Razorpay API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (e.g., "/payment_links")
            json_data: JSON payload
            
        Returns:
            Response JSON
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                auth=self.auth,
                json=json_data
            )
            
            if response.status_code >= 400:
                logger.error(f"Razorpay API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def create_payment_link(
        self,
        amount: int,
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str] = None,
        description: str = "Payment",
        reference_id: Optional[str] = None,
        expire_by: Optional[int] = None,
        reminder_enable: bool = True,
        notes: Optional[Dict[str, str]] = None,
        upi_link: bool = True  # Default to UPI payment
    ) -> PaymentLinkResponse:
        """
        Create a new payment link.
        
        Args:
            amount: Amount in paise (e.g., 50000 for INR 500)
            customer_name: Customer's name
            customer_phone: Customer's phone number
            customer_email: Customer's email (optional)
            description: Payment description
            reference_id: Your internal reference ID (e.g., call_id)
            expire_by: Unix timestamp for link expiry (default: 24 hours)
            reminder_enable: Whether to send payment reminders
            notes: Additional metadata
            upi_link: If True, creates UPI-enabled payment link (default: True)
            
        Returns:
            PaymentLinkResponse with link_id and short_url
        """
        # Default expiry: 24 hours from now
        if expire_by is None:
            expire_by = int((datetime.utcnow() + timedelta(hours=24)).timestamp())
        
        normalized_phone = self._normalize_phone(customer_phone)
        
        # Build base payload
        payload = {
            "amount": amount,
            "currency": "INR",
            "description": description,
            "customer": {
                "name": customer_name,
                "contact": normalized_phone
            },
            "notify": {
                "sms": False,  # We'll send via WhatsApp instead
                "email": False
            },
            "reminder_enable": reminder_enable,
            "expire_by": expire_by,
            "callback_url": os.getenv("RAZORPAY_CALLBACK_URL", ""),
            "callback_method": "get"
        }
        
        # Add UPI link option if requested
        if upi_link:
            payload["upi_link"] = True
        
        # Add email if provided
        if customer_email:
            payload["customer"]["email"] = customer_email
        
        # Add reference ID if provided
        if reference_id:
            payload["reference_id"] = reference_id
        
        # Add notes/metadata
        if notes:
            payload["notes"] = notes
        
        try:
            link_type = "UPI" if upi_link else "standard"
            logger.info(f"Creating {link_type} payment link for {self._mask_phone(normalized_phone)}, amount: {amount/100} INR")
            response = await self._make_request("POST", "/payment_links", payload)
            
            if "id" in response:
                logger.info(f"✅ Payment link created: {response['id']} ({link_type})")
                return PaymentLinkResponse(
                    success=True,
                    link_id=response["id"],
                    short_url=response.get("short_url"),
                    amount=response.get("amount"),
                    status=response.get("status"),
                    raw_response=response
                )
            elif "error" in response:
                error = response["error"]
                error_desc = error.get("description", "Unknown error")
                
                # Check if UPI failed due to test mode - retry without UPI
                if upi_link and "UPI" in error_desc and "Test Mode" in error_desc:
                    logger.warning(f"⚠️ UPI not available in test mode, falling back to standard payment link")
                    # Retry without UPI
                    return await self.create_payment_link(
                        amount=amount,
                        customer_name=customer_name,
                        customer_phone=customer_phone,
                        customer_email=customer_email,
                        description=description,
                        reference_id=reference_id,
                        expire_by=expire_by,
                        reminder_enable=reminder_enable,
                        notes=notes,
                        upi_link=False  # Disable UPI for retry
                    )
                
                logger.error(f"Razorpay error: {error}")
                return PaymentLinkResponse(
                    success=False,
                    error_code=error.get("code", "unknown"),
                    error_message=error_desc,
                    raw_response=response
                )
            else:
                return PaymentLinkResponse(
                    success=False,
                    error_message="Unexpected response format",
                    raw_response=response
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating payment link: {e}")
            return PaymentLinkResponse(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error creating payment link: {e}")
            return PaymentLinkResponse(
                success=False,
                error_message=str(e)
            )
    
    async def get_payment_link(self, link_id: str) -> PaymentLinkResponse:
        """
        Get details of a payment link.
        
        Args:
            link_id: Razorpay payment link ID
            
        Returns:
            PaymentLinkResponse with current status
        """
        try:
            response = await self._make_request("GET", f"/payment_links/{link_id}")
            
            if "id" in response:
                return PaymentLinkResponse(
                    success=True,
                    link_id=response["id"],
                    short_url=response.get("short_url"),
                    amount=response.get("amount"),
                    status=response.get("status"),
                    raw_response=response
                )
            elif "error" in response:
                error = response["error"]
                return PaymentLinkResponse(
                    success=False,
                    error_code=error.get("code", "unknown"),
                    error_message=error.get("description", "Unknown error"),
                    raw_response=response
                )
            else:
                return PaymentLinkResponse(
                    success=False,
                    error_message="Unexpected response format",
                    raw_response=response
                )
                
        except Exception as e:
            logger.error(f"Error getting payment link: {e}")
            return PaymentLinkResponse(
                success=False,
                error_message=str(e)
            )
    
    async def get_payment_status(self, link_id: str) -> str:
        """
        Get the payment status for a link.
        
        Possible statuses:
        - created: Link created, payment pending
        - paid: Payment completed
        - partially_paid: Partial payment received
        - expired: Link expired
        - cancelled: Link cancelled
        
        Args:
            link_id: Razorpay payment link ID
            
        Returns:
            Status string
        """
        result = await self.get_payment_link(link_id)
        if result.success:
            return result.status or "unknown"
        return "error"
    
    async def cancel_payment_link(self, link_id: str) -> bool:
        """
        Cancel a payment link.
        
        Args:
            link_id: Razorpay payment link ID
            
        Returns:
            True if cancelled successfully
        """
        try:
            response = await self._make_request("POST", f"/payment_links/{link_id}/cancel")
            return response.get("status") == "cancelled"
        except Exception as e:
            logger.error(f"Error cancelling payment link: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if the client is properly configured"""
        return bool(self.key_id and self.key_secret)


# Singleton instance
_default_client: Optional[RazorpayClient] = None


def get_razorpay_client() -> RazorpayClient:
    """Get or create the default Razorpay client instance"""
    global _default_client
    if _default_client is None:
        _default_client = RazorpayClient()
    return _default_client

