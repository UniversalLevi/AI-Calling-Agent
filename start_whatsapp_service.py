"""
WhatsApp Service Launcher
=========================

Standalone launcher for the WhatsApp microservice.
Can be run independently or called from main.py.

Usage:
    python start_whatsapp_service.py

Or from main.py:
    from start_whatsapp_service import start_service
    start_service()
"""

import os
import sys
import time
import signal
import logging
import threading
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("whatsapp_launcher")


def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    required = ['fastapi', 'uvicorn', 'httpx', 'pydantic']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.error(f"Missing dependencies: {', '.join(missing)}")
        logger.info("Install with: pip install " + " ".join(missing))
        return False
    
    return True


def check_configuration() -> dict:
    """Check WhatsApp configuration status"""
    from dotenv import load_dotenv
    load_dotenv()
    
    config = {
        "whatsapp_enabled": os.getenv("ENABLE_WHATSAPP", "false").lower() == "true",
        "payment_links_enabled": os.getenv("ENABLE_WHATSAPP_PAYMENT_LINKS", "false").lower() == "true",
        "access_token_set": bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
        "phone_number_id_set": bool(os.getenv("WHATSAPP_PHONE_NUMBER_ID")),
        "razorpay_configured": bool(os.getenv("RAZORPAY_KEY_ID") and os.getenv("RAZORPAY_KEY_SECRET")),
        "port": int(os.getenv("WHATSAPP_SERVICE_PORT", "8001")),
        "host": os.getenv("WHATSAPP_SERVICE_HOST", "0.0.0.0")
    }
    
    return config


def print_startup_banner(config: dict):
    """Print startup banner with configuration status"""
    print("\n" + "=" * 60)
    print("🟢 SARA WhatsApp Service")
    print("=" * 60)
    print(f"Host: {config['host']}")
    print(f"Port: {config['port']}")
    print("-" * 60)
    print("Configuration Status:")
    print(f"  WhatsApp Enabled:      {'✅' if config['whatsapp_enabled'] else '❌'}")
    print(f"  Payment Links Enabled: {'✅' if config['payment_links_enabled'] else '❌'}")
    print(f"  Access Token:          {'✅ Set' if config['access_token_set'] else '❌ Not set'}")
    print(f"  Phone Number ID:       {'✅ Set' if config['phone_number_id_set'] else '❌ Not set'}")
    print(f"  Razorpay:              {'✅ Configured' if config['razorpay_configured'] else '❌ Not configured'}")
    print("-" * 60)
    
    if not config['whatsapp_enabled']:
        print("⚠️  WhatsApp is DISABLED. Set ENABLE_WHATSAPP=true in .env to enable.")
    
    if not config['access_token_set'] or not config['phone_number_id_set']:
        print("⚠️  WhatsApp credentials not configured. See env.example for required variables.")
    
    print("=" * 60 + "\n")


def run_server():
    """Run the WhatsApp service using uvicorn"""
    import uvicorn
    
    config = check_configuration()
    
    uvicorn.run(
        "src.services.whatsapp.whatsapp_server:app",
        host=config['host'],
        port=config['port'],
        reload=False,
        log_level="info",
        access_log=True
    )


def start_service_background() -> threading.Thread:
    """Start the WhatsApp service in a background thread"""
    
    def run_in_thread():
        try:
            run_server()
        except Exception as e:
            logger.error(f"WhatsApp service error: {e}")
    
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    return thread


def start_service_subprocess() -> subprocess.Popen:
    """Start the WhatsApp service as a subprocess"""
    config = check_configuration()
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "src.services.whatsapp.whatsapp_server:app",
        "--host", config['host'],
        "--port", str(config['port']),
        "--log-level", "info"
    ]
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=str(PROJECT_ROOT)
    )
    
    logger.info(f"WhatsApp service started (PID: {process.pid})")
    
    return process


def wait_for_service(timeout: int = 30) -> bool:
    """Wait for the service to be ready"""
    import requests
    
    config = check_configuration()
    url = f"http://localhost:{config['port']}/health"
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                logger.info("WhatsApp service is ready")
                return True
        except:
            pass
        time.sleep(1)
    
    logger.error(f"WhatsApp service failed to start within {timeout}s")
    return False


def main():
    """Main entry point"""
    print("\n🚀 Starting SARA WhatsApp Service...")
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Missing dependencies. Please install required packages.")
        sys.exit(1)
    
    # Check configuration
    config = check_configuration()
    print_startup_banner(config)
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print("\n🛑 Shutting down WhatsApp service...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run server
    try:
        run_server()
    except KeyboardInterrupt:
        print("\n👋 WhatsApp service stopped")
    except Exception as e:
        logger.exception(f"Failed to start WhatsApp service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

