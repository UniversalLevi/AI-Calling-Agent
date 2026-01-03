"""
WhatsApp Service Security
=========================

Security utilities for the WhatsApp microservice.
Handles signature verification, rate limiting, and input validation.
"""

import hashlib
import hmac
import time
import logging
from typing import Dict, Optional, Callable
from functools import wraps
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# SIGNATURE VERIFICATION
# =============================================================================

class SignatureVerifier:
    """
    Verifies Meta webhook signatures using HMAC-SHA256.
    
    Meta sends a signature in the X-Hub-Signature-256 header that must be
    verified to ensure the webhook request is authentic.
    """
    
    def __init__(self, app_secret: str):
        """
        Initialize verifier with app secret.
        
        Args:
            app_secret: Meta App Secret (from App Dashboard)
        """
        self.app_secret = app_secret
    
    def verify(self, payload: bytes, signature: str) -> bool:
        """
        Verify the webhook signature.
        
        Args:
            payload: Raw request body bytes
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not self.app_secret:
            logger.warning("App secret not configured, skipping verification")
            return True
        
        if not signature:
            logger.warning("No signature provided in request")
            return False
        
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith("sha256="):
                signature = signature[7:]
            
            # Calculate expected signature
            expected = hmac.new(
                key=self.app_secret.encode('utf-8'),
                msg=payload,
                digestmod=hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison
            is_valid = hmac.compare_digest(expected, signature)
            
            if not is_valid:
                logger.warning("Webhook signature mismatch")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if a request is allowed for the given key.
        
        Args:
            key: Rate limit key (e.g., IP address or API key)
            
        Returns:
            True if request is allowed
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > window_start
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {key}")
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key"""
        now = time.time()
        window_start = now - self.window_seconds
        
        current_requests = len([
            ts for ts in self.requests[key]
            if ts > window_start
        ])
        
        return max(0, self.max_requests - current_requests)
    
    def reset(self, key: str):
        """Reset rate limit for a key"""
        self.requests[key] = []


# Rate limiter instances
_webhook_limiter = RateLimiter(max_requests=100, window_seconds=60)
_api_limiter = RateLimiter(max_requests=60, window_seconds=60)


def check_webhook_rate_limit(ip: str) -> bool:
    """Check webhook rate limit"""
    return _webhook_limiter.is_allowed(ip)


def check_api_rate_limit(ip: str) -> bool:
    """Check API rate limit"""
    return _api_limiter.is_allowed(ip)


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_phone_number(phone: str) -> tuple[bool, str]:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Tuple of (is_valid, normalized_phone)
    """
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Check length
    if len(digits) < 10:
        return False, "Phone number too short"
    
    if len(digits) > 15:
        return False, "Phone number too long"
    
    # Add country code if missing (default to India)
    if len(digits) == 10:
        digits = "91" + digits
    
    return True, digits


def validate_amount(amount: int) -> tuple[bool, Optional[str]]:
    """
    Validate payment amount.
    
    Args:
        amount: Amount in paise
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if amount <= 0:
        return False, "Amount must be positive"
    
    if amount < 100:  # Less than ₹1
        return False, "Minimum amount is ₹1 (100 paise)"
    
    if amount > 50000000:  # More than ₹5 lakh
        return False, "Amount exceeds maximum limit"
    
    return True, None


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text input.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Truncate if too long
    text = text[:max_length]
    
    # Remove control characters (except newlines and tabs)
    sanitized = ''.join(
        char for char in text
        if char >= ' ' or char in '\n\t\r'
    )
    
    return sanitized.strip()


# =============================================================================
# PHONE MASKING
# =============================================================================

def mask_phone(phone: str, visible_digits: int = 4) -> str:
    """
    Mask phone number for logging/display.
    
    Args:
        phone: Phone number
        visible_digits: Number of digits to show at end
        
    Returns:
        Masked phone number
    """
    digits = ''.join(filter(str.isdigit, phone))
    
    if len(digits) <= visible_digits:
        return "*" * len(digits)
    
    masked_count = len(digits) - visible_digits
    return "*" * masked_count + digits[-visible_digits:]


def hash_phone(phone: str) -> str:
    """
    Create a hash of phone number for database lookup.
    
    Args:
        phone: Phone number
        
    Returns:
        SHA256 hash (first 32 characters)
    """
    digits = ''.join(filter(str.isdigit, phone))
    return hashlib.sha256(digits.encode()).hexdigest()[:32]


# =============================================================================
# REQUEST VALIDATION DECORATOR
# =============================================================================

def validate_request(
    require_phone: bool = False,
    require_amount: bool = False,
    rate_limit_key: Optional[Callable] = None
):
    """
    Decorator for validating API requests.
    
    Args:
        require_phone: Validate phone number in request
        require_amount: Validate amount in request
        rate_limit_key: Function to extract rate limit key from request
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or first arg
            request = kwargs.get('request')
            
            # Rate limiting
            if rate_limit_key and request:
                key = rate_limit_key(request)
                if not check_api_rate_limit(key):
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# SECURITY HEADERS
# =============================================================================

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'",
    "Referrer-Policy": "strict-origin-when-cross-origin"
}


def get_security_headers() -> Dict[str, str]:
    """Get security headers to add to responses"""
    return SECURITY_HEADERS.copy()

