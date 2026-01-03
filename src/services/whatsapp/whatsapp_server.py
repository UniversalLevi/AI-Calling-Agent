"""
WhatsApp Microservice Server
============================

FastAPI-based microservice for WhatsApp Business API integration.
Runs independently on port 8001.

Endpoints:
- POST /api/whatsapp/send-payment-link - Send payment link via WhatsApp
- POST /api/whatsapp/send-message - Send generic template message
- POST /api/whatsapp/send-followup - Send call followup
- POST /api/whatsapp/send-reminder - Send payment reminder
- GET  /api/whatsapp/status/{message_id} - Get message status
- POST /webhook/whatsapp - Meta webhook for inbound events
- GET  /webhook/whatsapp - Meta webhook verification
- GET  /health - Health check
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .models import (
    SendPaymentLinkRequest,
    SendMessageRequest,
    SendFollowupRequest,
    SendReminderRequest,
    PaymentLinkResponse,
    MessageResponse,
    StatusResponse,
    MessageStatus,
)
from .whatsapp_service import WhatsAppService, get_whatsapp_service
from .webhook_handler import WebhookHandler, get_webhook_handler
from .config import (
    WHATSAPP_SERVICE_HOST,
    WHATSAPP_SERVICE_PORT,
    WHATSAPP_WEBHOOK_VERIFY_TOKEN,
    get_config_summary,
    is_configured,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# =============================================================================
# APPLICATION LIFECYCLE
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager"""
    logger.info("Starting WhatsApp Service...")
    
    # Initialize services
    service = get_whatsapp_service()
    webhook_handler = get_webhook_handler()
    
    # Set up webhook callbacks
    webhook_handler.on_message_status_update(on_status_update)
    webhook_handler.on_user_reply(on_user_reply)
    webhook_handler.on_payment_confirmation(on_payment_confirmation)
    
    # Check configuration
    if is_configured():
        logger.info("WhatsApp service configured and ready")
    else:
        logger.warning("WhatsApp service not fully configured - some features disabled")
    
    yield
    
    logger.info("Shutting down WhatsApp Service...")


# Create FastAPI app
app = FastAPI(
    title="SARA WhatsApp Service",
    description="WhatsApp Business API integration for SARA Calling Agent",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_service() -> WhatsAppService:
    """Dependency to get WhatsApp service"""
    return get_whatsapp_service()


async def get_handler() -> WebhookHandler:
    """Dependency to get webhook handler"""
    return get_webhook_handler()


# =============================================================================
# WEBHOOK CALLBACKS
# =============================================================================

async def on_status_update(status):
    """Handle message status updates"""
    logger.info(f"Status update: {status.message_id} -> {status.status}")
    service = get_whatsapp_service()
    await service.update_message_status(
        message_id=status.message_id,
        status=MessageStatus(status.status) if status.status in MessageStatus.__members__.values() else MessageStatus.PENDING,
        timestamp=status.timestamp
    )


async def on_user_reply(message):
    """Handle user replies"""
    logger.info(f"User reply from {message.from_phone}: {message.text}")
    # TODO: Forward to SARA for processing


async def on_payment_confirmation(phone: str, text: str):
    """Handle payment confirmation messages"""
    logger.info(f"Payment confirmation from {phone}: {text}")
    # TODO: Verify with Razorpay and update status


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    config = get_config_summary()
    return {
        "status": "healthy",
        "service": "whatsapp",
        "timestamp": datetime.utcnow().isoformat(),
        "config": config
    }


@app.post("/api/whatsapp/send-payment-link", response_model=PaymentLinkResponse)
async def send_payment_link(
    request: SendPaymentLinkRequest,
    service: WhatsAppService = Depends(get_service)
):
    """
    Send a payment link via WhatsApp.
    
    Creates a Razorpay payment link and sends it to the user via WhatsApp template.
    """
    logger.info(f"Payment link request for {request.phone}")
    
    result = await service.send_payment_link(
        phone=request.phone,
        amount=request.amount,
        customer_name=request.customer_name,
        product_name=request.product_name,
        call_id=request.call_id,
        language=request.language,
        customer_email=request.customer_email,
        notes=request.notes
    )
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": result.error_code,
                "error_message": result.error_message
            }
        )
    
    return result


@app.post("/api/whatsapp/send-message", response_model=MessageResponse)
async def send_message(
    request: SendMessageRequest,
    service: WhatsAppService = Depends(get_service)
):
    """
    Send a generic template message via WhatsApp.
    """
    logger.info(f"Message request: template={request.template_name}, phone={request.phone}")
    
    # Use the underlying client for generic messages
    client = service.whatsapp_client
    result = await client.send_template_message(
        phone=request.phone,
        template_name=request.template_name,
        variables=request.variables,
        language_code=request.language
    )
    
    return MessageResponse(
        success=result.success,
        message_id=result.message_id,
        status=MessageStatus.SENT if result.success else MessageStatus.FAILED,
        error_code=result.error_code,
        error_message=result.error_message
    )


@app.post("/api/whatsapp/send-followup", response_model=MessageResponse)
async def send_followup(
    request: SendFollowupRequest,
    service: WhatsAppService = Depends(get_service)
):
    """
    Send a call followup message.
    """
    logger.info(f"Followup request for call {request.call_id}")
    
    result = await service.send_call_followup(
        phone=request.phone,
        customer_name=request.customer_name,
        call_summary=request.call_summary,
        call_id=request.call_id,
        language=request.language
    )
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": result.error_code,
                "error_message": result.error_message
            }
        )
    
    return result


@app.post("/api/whatsapp/send-reminder", response_model=MessageResponse)
async def send_reminder(
    request: SendReminderRequest,
    service: WhatsAppService = Depends(get_service)
):
    """
    Send a payment reminder message.
    """
    logger.info(f"Reminder request for {request.phone}")
    
    result = await service.send_payment_reminder(
        phone=request.phone,
        customer_name=request.customer_name,
        product_name=request.product_name,
        amount=request.amount,
        payment_link=request.payment_link,
        original_message_id=request.original_message_id
    )
    
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": result.error_code,
                "error_message": result.error_message
            }
        )
    
    return result


@app.get("/api/whatsapp/status/{message_id}", response_model=StatusResponse)
async def get_message_status(
    message_id: str,
    service: WhatsAppService = Depends(get_service)
):
    """
    Get the status of a sent message.
    """
    # For now, just return from WhatsApp API
    # In production, this would check MongoDB first
    client = service.whatsapp_client
    result = await client.get_message_status(message_id)
    
    return StatusResponse(
        message_id=message_id,
        message_status=MessageStatus.PENDING,  # Would come from DB
        last_updated=datetime.utcnow()
    )


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@app.get("/webhook/whatsapp")
async def verify_webhook(
    request: Request,
    handler: WebhookHandler = Depends(get_handler)
):
    """
    Webhook verification endpoint (called by Meta during setup).
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if not all([mode, token, challenge]):
        raise HTTPException(status_code=400, detail="Missing required parameters")
    
    result = handler.verify_webhook(mode, token, challenge)
    
    if result:
        return Response(content=result, media_type="text/plain")
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook/whatsapp")
async def receive_webhook(
    request: Request,
    handler: WebhookHandler = Depends(get_handler)
):
    """
    Receive webhook events from Meta.
    """
    # Get raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Verify signature
    if not handler.verify_signature(body, signature):
        logger.warning("Webhook signature verification failed")
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse and process
    try:
        payload = await request.json()
        result = await handler.process_webhook(payload)
        return {"status": "ok", **result}
    except Exception as e:
        logger.exception(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_server():
    """Run the WhatsApp microservice server"""
    import uvicorn
    
    logger.info(f"Starting WhatsApp Service on {WHATSAPP_SERVICE_HOST}:{WHATSAPP_SERVICE_PORT}")
    
    uvicorn.run(
        "src.services.whatsapp.whatsapp_server:app",
        host=WHATSAPP_SERVICE_HOST,
        port=WHATSAPP_SERVICE_PORT,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()

