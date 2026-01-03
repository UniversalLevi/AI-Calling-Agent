"""
WhatsApp Cloud API Client
=========================

Low-level wrapper for Meta WhatsApp Business Cloud API.
Handles all direct API calls to Meta's WhatsApp infrastructure.

API Documentation: https://developers.facebook.com/docs/whatsapp/cloud-api
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

import httpx

# Configure logging
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """WhatsApp message types"""
    TEXT = "text"
    TEMPLATE = "template"
    IMAGE = "image"
    DOCUMENT = "document"
    INTERACTIVE = "interactive"


@dataclass
class WhatsAppResponse:
    """Response from WhatsApp API"""
    success: bool
    message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class WhatsAppClient:
    """
    Low-level client for Meta WhatsApp Business Cloud API.
    
    This client handles:
    - Sending text messages (24h window only)
    - Sending template messages (for cold outreach)
    - Checking message delivery status
    - Managing media uploads
    
    Usage:
        client = WhatsAppClient()
        result = await client.send_template_message(
            phone="+919876543210",
            template_name="payment_link_v1",
            variables={"1": "John", "2": "Hotel Booking", "3": "5000", "4": "https://pay.link"}
        )
    """
    
    # Meta Graph API version
    API_VERSION = "v18.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        business_account_id: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize WhatsApp client.
        
        Args:
            access_token: Meta access token (from env if not provided)
            phone_number_id: WhatsApp Phone Number ID
            business_account_id: WhatsApp Business Account ID
            timeout: Request timeout in seconds
        """
        self.access_token = access_token or os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = phone_number_id or os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.business_account_id = business_account_id or os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")
        self.timeout = timeout
        
        # Validate configuration
        if not self.access_token:
            logger.warning("WHATSAPP_ACCESS_TOKEN not configured")
        if not self.phone_number_id:
            logger.warning("WHATSAPP_PHONE_NUMBER_ID not configured")
        
        # HTTP client will be created per-request for async safety
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def messages_url(self) -> str:
        """Get the messages endpoint URL"""
        return f"{self.BASE_URL}/{self.phone_number_id}/messages"
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to WhatsApp format (no + prefix, just digits).
        
        Args:
            phone: Phone number in any format
            
        Returns:
            Normalized phone number (e.g., "919876543210")
        """
        # Remove all non-digit characters
        normalized = ''.join(filter(str.isdigit, phone))
        
        # Ensure it starts with country code (assume India 91 if 10 digits)
        if len(normalized) == 10:
            normalized = "91" + normalized
        
        return normalized
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for logging (show only last 4 digits)"""
        if len(phone) > 4:
            return "*" * (len(phone) - 4) + phone[-4:]
        return "****"
    
    async def _make_request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to WhatsApp API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL
            json_data: JSON payload
            
        Returns:
            Response JSON
            
        Raises:
            httpx.HTTPError: On network errors
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                json=json_data
            )
            
            # Log response for debugging
            if response.status_code >= 400:
                logger.error(f"WhatsApp API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    async def send_text_message(
        self,
        phone: str,
        text: str,
        preview_url: bool = False
    ) -> WhatsAppResponse:
        """
        Send a plain text message.
        
        Note: Only works within 24-hour customer service window.
        For cold outreach, use send_template_message().
        
        Args:
            phone: Recipient phone number
            text: Message text
            preview_url: Whether to show URL preview
            
        Returns:
            WhatsAppResponse with success status and message_id
        """
        normalized_phone = self._normalize_phone(phone)
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_phone,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": text
            }
        }
        
        try:
            logger.info(f"Sending text message to {self._mask_phone(normalized_phone)}")
            response = await self._make_request("POST", self.messages_url, payload)
            
            if "messages" in response and len(response["messages"]) > 0:
                message_id = response["messages"][0]["id"]
                logger.info(f"Message sent successfully: {message_id}")
                return WhatsAppResponse(
                    success=True,
                    message_id=message_id,
                    raw_response=response
                )
            elif "error" in response:
                error = response["error"]
                logger.error(f"WhatsApp API error: {error}")
                return WhatsAppResponse(
                    success=False,
                    error_code=str(error.get("code", "unknown")),
                    error_message=error.get("message", "Unknown error"),
                    raw_response=response
                )
            else:
                return WhatsAppResponse(
                    success=False,
                    error_message="Unexpected response format",
                    raw_response=response
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending message: {e}")
            return WhatsAppResponse(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return WhatsAppResponse(
                success=False,
                error_message=str(e)
            )
    
    async def send_template_message(
        self,
        phone: str,
        template_name: str,
        variables: Dict[str, str],
        language_code: str = "en"
    ) -> WhatsAppResponse:
        """
        Send a template message (for cold outreach outside 24h window).
        
        Templates must be pre-approved in Meta Business Suite.
        
        Args:
            phone: Recipient phone number
            template_name: Approved template name (e.g., "payment_link_v1")
            variables: Template variables as dict (e.g., {"1": "John", "2": "Product"})
            language_code: Template language code (default: "en")
            
        Returns:
            WhatsAppResponse with success status and message_id
        """
        normalized_phone = self._normalize_phone(phone)
        
        # Build template components
        components = []
        
        # Add body parameters if variables provided
        if variables:
            body_params = [
                {"type": "text", "text": value}
                for key, value in sorted(variables.items(), key=lambda x: int(x[0]))
            ]
            components.append({
                "type": "body",
                "parameters": body_params
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                },
                "components": components
            }
        }
        
        try:
            logger.info(f"Sending template '{template_name}' to {self._mask_phone(normalized_phone)}")
            response = await self._make_request("POST", self.messages_url, payload)
            
            if "messages" in response and len(response["messages"]) > 0:
                message_id = response["messages"][0]["id"]
                logger.info(f"Template message sent successfully: {message_id}")
                return WhatsAppResponse(
                    success=True,
                    message_id=message_id,
                    raw_response=response
                )
            elif "error" in response:
                error = response["error"]
                logger.error(f"WhatsApp API error: {error}")
                return WhatsAppResponse(
                    success=False,
                    error_code=str(error.get("code", "unknown")),
                    error_message=error.get("message", "Unknown error"),
                    raw_response=response
                )
            else:
                return WhatsAppResponse(
                    success=False,
                    error_message="Unexpected response format",
                    raw_response=response
                )
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending template: {e}")
            return WhatsAppResponse(
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error sending template: {e}")
            return WhatsAppResponse(
                success=False,
                error_message=str(e)
            )
    
    async def send_payment_link(
        self,
        phone: str,
        payment_url: str,
        button_text: str = "Pay Now"
    ) -> WhatsAppResponse:
        """
        Send an interactive message with a payment link button.
        
        Note: This uses interactive message type which requires 24h window.
        For cold outreach, use template with payment link in body text.
        
        Args:
            phone: Recipient phone number
            payment_url: Payment link URL
            button_text: Button text (default: "Pay Now")
            
        Returns:
            WhatsAppResponse with success status and message_id
        """
        normalized_phone = self._normalize_phone(phone)
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": normalized_phone,
            "type": "interactive",
            "interactive": {
                "type": "cta_url",
                "body": {
                    "text": "Click below to complete your payment securely."
                },
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": button_text,
                        "url": payment_url
                    }
                }
            }
        }
        
        try:
            logger.info(f"Sending payment link to {self._mask_phone(normalized_phone)}")
            response = await self._make_request("POST", self.messages_url, payload)
            
            if "messages" in response and len(response["messages"]) > 0:
                message_id = response["messages"][0]["id"]
                logger.info(f"Payment link sent successfully: {message_id}")
                return WhatsAppResponse(
                    success=True,
                    message_id=message_id,
                    raw_response=response
                )
            elif "error" in response:
                error = response["error"]
                return WhatsAppResponse(
                    success=False,
                    error_code=str(error.get("code", "unknown")),
                    error_message=error.get("message", "Unknown error"),
                    raw_response=response
                )
            else:
                return WhatsAppResponse(
                    success=False,
                    error_message="Unexpected response format",
                    raw_response=response
                )
                
        except Exception as e:
            logger.error(f"Error sending payment link: {e}")
            return WhatsAppResponse(
                success=False,
                error_message=str(e)
            )
    
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get the delivery status of a message.
        
        Note: Status updates are typically received via webhook,
        but this can be used for manual checking.
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            Status information dict
        """
        url = f"{self.BASE_URL}/{message_id}"
        
        try:
            response = await self._make_request("GET", url)
            return response
        except Exception as e:
            logger.error(f"Error getting message status: {e}")
            return {"error": str(e)}
    
    async def mark_message_read(self, message_id: str) -> bool:
        """
        Mark a message as read (for inbound messages).
        
        Args:
            message_id: WhatsApp message ID
            
        Returns:
            True if successful
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = await self._make_request("POST", self.messages_url, payload)
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if the client is properly configured"""
        return bool(self.access_token and self.phone_number_id)


# Singleton instance for convenience
_default_client: Optional[WhatsAppClient] = None


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create the default WhatsApp client instance"""
    global _default_client
    if _default_client is None:
        _default_client = WhatsAppClient()
    return _default_client

