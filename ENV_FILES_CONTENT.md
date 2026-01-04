# Environment Files Content

## 1. ROOT .env file (`/var/www/sara-bot/.env`)

```bash
# ============================================================================
# AI CALLING BOT - ENVIRONMENT CONFIGURATION
# ============================================================================

# ============================================================================
# DEPLOYMENT MODE
# ============================================================================
FLASK_ENV=production
BASE_URL=https://veilforce.com
DASHBOARD_API_URL=http://dashboard-api:5016/api

# ============================================================================
# REQUIRED - OPENAI API
# ============================================================================
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# ============================================================================
# REQUIRED - TWILIO (FOR PHONE CALLS)
# ============================================================================
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# ============================================================================
# AUDIO CONFIGURATION
# ============================================================================
AUDIO_PORT=5018
SAMPLE_RATE=16000
CHANNELS=1
RECORD_SECONDS=7.0

# ============================================================================
# SPEECH-TO-TEXT CONFIGURATION
# ============================================================================
WHISPER_MODEL_SIZE=base
LANGUAGE=en
AUTO_DETECT_LANGUAGE=true
DEFAULT_LANGUAGE=en

# ============================================================================
# TEXT-TO-SPEECH CONFIGURATION
# ============================================================================
USE_COQUI_TTS=false
TTS_VOICE=en
HINDI_TTS_VOICE=hi
ENGLISH_TTS_VOICE=en

# ============================================================================
# WHATSAPP BUSINESS API (Meta Cloud API)
# ============================================================================
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_random_verify_token_for_webhook

# ============================================================================
# RAZORPAY (Payment Links)
# ============================================================================
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_CALLBACK_URL=https://veilforce.com/api/payments/callback

# ============================================================================
# WHATSAPP INTEGRATION FEATURE FLAGS
# ============================================================================
ENABLE_WHATSAPP=false
ENABLE_WHATSAPP_PAYMENT_LINKS=false
ENABLE_WHATSAPP_FOLLOWUPS=false
WHATSAPP_SERVICE_URL=http://localhost:8001
WHATSAPP_BUSINESS_DISPLAY_NUMBER=+91 91791 77847
ENABLE_WHATSAPP_OPTIN_SMS=true

# ============================================================================
# DEBUG AND LOGGING
# ============================================================================
PRINT_TRANSCRIPTS=true
PRINT_BOT_TEXT=true

# ============================================================================
# SYSTEM PROMPT (OPTIONAL)
# ============================================================================
SYSTEM_PROMPT=You are an Female AI Calling Assistant whose only job is to handle phone conversations in a natural, human-like, empathetic, and professional manner. Always speak in short, clear sentences with a friendly and confident tone, using light human fillers sparingly but never sounding robotic or repetitive. Greet warmly at the start, explain the call's purpose, ask one question at a time, confirm important details, and politely close at the end. Stay strictly focused on the specific purpose of the call (e.g., booking, support, survey) and never answer or engage with anything outside this boundary; if the caller asks something unrelated, simply say: "Sorry, I can't help with that. I can only assist with [purpose of call]." If you don't understand something, ask them to repeat or rephrase politely. Your goal is to simulate a real human phone call where the caller feels heard, respected, and helped—without ever stepping outside your defined role.
```

---

## 2. BACKEND .env file (`/var/www/sara-bot/sara-dashboard/.env`)

```bash
# ============================================================================
# SARA DASHBOARD BACKEND - ENVIRONMENT CONFIGURATION
# ============================================================================

# Database Configuration
# Replace with your actual MongoDB credentials
MONGODB_URI=mongodb://MONGO_ROOT_USERNAME:MONGO_ROOT_PASSWORD@host.docker.internal:27017/sara-dashboard?authSource=admin

# Server Configuration
PORT=5016
NODE_ENV=production

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production-use-random-string
JWT_EXPIRE=7d

# CORS Configuration
FRONTEND_URL=https://veilforce.com

# Socket.io Configuration
SOCKET_CORS_ORIGIN=https://veilforce.com

# Sara Bot Integration
SARA_BOT_URL=http://voice-bot:5015
SARA_BOT_API_KEY=your-sara-bot-api-key

# Admin Default Credentials (change these!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# File Upload Configuration
MAX_FILE_SIZE=10485760
UPLOAD_PATH=./uploads
```

**IMPORTANT:** Replace `MONGO_ROOT_USERNAME` and `MONGO_ROOT_PASSWORD` with your actual MongoDB root credentials.

---

## 3. FRONTEND .env file (`/var/www/sara-bot/sara-dashboard/frontend/.env`)

```bash
# ============================================================================
# SARA DASHBOARD FRONTEND - ENVIRONMENT CONFIGURATION
# ============================================================================

# API Configuration (used during build)
REACT_APP_API_URL=https://veilforce.com/api
REACT_APP_SOCKET_URL=https://veilforce.com

# Optional: Disable Socket.io if causing issues
# REACT_APP_ENABLE_SOCKET=false
```

---

## Quick Setup Commands

Run these on your server:

```bash
# 1. Create root .env
cd /var/www/sara-bot
nano .env
# Paste root .env content above, save with Ctrl+X, Y, Enter

# 2. Create backend .env
cd /var/www/sara-bot/sara-dashboard
nano .env
# Paste backend .env content above, REPLACE MONGO credentials, save

# 3. Create frontend .env
cd /var/www/sara-bot/sara-dashboard/frontend
nano .env
# Paste frontend .env content above, save

# 4. Install frontend dependencies (if react-scripts missing)
cd /var/www/sara-bot/sara-dashboard/frontend
npm install

# 5. Rebuild frontend
npm run build

# 6. Restart Docker containers
cd /var/www/sara-bot
docker-compose restart
```

---

## Notes:

1. **MongoDB URI**: Replace `MONGO_ROOT_USERNAME` and `MONGO_ROOT_PASSWORD` in backend .env with your actual MongoDB root credentials
2. **JWT_SECRET**: Use a strong random string (at least 32 characters)
3. **API Keys**: Replace all `your_*` placeholders with actual API keys
4. **Domain**: All URLs use `veilforce.com` - change if different
5. **Frontend .env**: Only needed for build-time variables. The built app will use these values.


