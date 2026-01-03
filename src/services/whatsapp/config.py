"""
WhatsApp Service Configuration
==============================

Configuration settings specific to the WhatsApp microservice.
Inherits from main config but can be used standalone.
"""

import os
from typing import Optional

# Try to load from main config first
try:
    from ...config import (
        ENABLE_WHATSAPP,
        ENABLE_WHATSAPP_PAYMENT_LINKS,
        ENABLE_WHATSAPP_FOLLOWUPS,
        WHATSAPP_SERVICE_URL,
        WHATSAPP_ACCESS_TOKEN,
        WHATSAPP_PHONE_NUMBER_ID,
        WHATSAPP_BUSINESS_ACCOUNT_ID,
        WHATSAPP_WEBHOOK_VERIFY_TOKEN,
        RAZORPAY_KEY_ID,
        RAZORPAY_KEY_SECRET,
        RAZORPAY_CALLBACK_URL,
    )
except ImportError:
    # Standalone mode - load from environment
    from dotenv import load_dotenv
    load_dotenv()
    
    # Feature Flags
    ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "false").lower() == "true"
    ENABLE_WHATSAPP_PAYMENT_LINKS = os.getenv("ENABLE_WHATSAPP_PAYMENT_LINKS", "false").lower() == "true"
    ENABLE_WHATSAPP_FOLLOWUPS = os.getenv("ENABLE_WHATSAPP_FOLLOWUPS", "false").lower() == "true"
    
    # WhatsApp Configuration
    WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:8001")
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    WHATSAPP_BUSINESS_ACCOUNT_ID = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "")
    WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
    
    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_CALLBACK_URL = os.getenv("RAZORPAY_CALLBACK_URL", "")


# =============================================================================
# WHATSAPP SERVICE SETTINGS
# =============================================================================

# Server Configuration
WHATSAPP_SERVICE_HOST = os.getenv("WHATSAPP_SERVICE_HOST", "0.0.0.0")
WHATSAPP_SERVICE_PORT = int(os.getenv("WHATSAPP_SERVICE_PORT", "8001"))

# MongoDB Configuration (for message tracking)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "sara_dashboard")

# Rate Limiting
WHATSAPP_RATE_LIMIT_PER_MINUTE = int(os.getenv("WHATSAPP_RATE_LIMIT_PER_MINUTE", "60"))
WEBHOOK_RATE_LIMIT_PER_MINUTE = int(os.getenv("WEBHOOK_RATE_LIMIT_PER_MINUTE", "100"))

# Retry Configuration
MAX_RETRY_ATTEMPTS = int(os.getenv("WHATSAPP_MAX_RETRY_ATTEMPTS", "3"))
RETRY_BACKOFF_SECONDS = float(os.getenv("WHATSAPP_RETRY_BACKOFF_SECONDS", "1.0"))

# Timeout Settings
API_TIMEOUT_SECONDS = float(os.getenv("WHATSAPP_API_TIMEOUT_SECONDS", "30.0"))

# Logging
LOG_LEVEL = os.getenv("WHATSAPP_LOG_LEVEL", "INFO")
MASK_PHONE_NUMBERS = os.getenv("WHATSAPP_MASK_PHONE_NUMBERS", "true").lower() == "true"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_configured() -> bool:
    """Check if WhatsApp service is properly configured"""
    return bool(WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID)


def is_razorpay_configured() -> bool:
    """Check if Razorpay is properly configured"""
    return bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def get_config_summary() -> dict:
    """Get a summary of current configuration (for health checks)"""
    return {
        "whatsapp_enabled": ENABLE_WHATSAPP,
        "payment_links_enabled": ENABLE_WHATSAPP_PAYMENT_LINKS,
        "followups_enabled": ENABLE_WHATSAPP_FOLLOWUPS,
        "whatsapp_configured": is_configured(),
        "razorpay_configured": is_razorpay_configured(),
        "service_port": WHATSAPP_SERVICE_PORT,
        "mongodb_database": MONGODB_DATABASE
    }

