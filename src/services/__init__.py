"""
SARA Services Package
=====================

This package contains external service integrations for SARA Calling Agent.
"""

# Lazy imports to avoid dependency issues
try:
    from .whatsapp import WhatsAppService, WhatsAppClient, RazorpayClient
    WHATSAPP_AVAILABLE = True
except ImportError:
    WHATSAPP_AVAILABLE = False
    WhatsAppService = None
    WhatsAppClient = None
    RazorpayClient = None

__all__ = ['WhatsAppService', 'WhatsAppClient', 'RazorpayClient', 'WHATSAPP_AVAILABLE']

