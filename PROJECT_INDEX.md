# SARA AI Calling Agent - Project Index

## Overview

SARA (Smart AI Response Agent) is an AI-powered calling bot that handles Hindi/English phone conversations, sends payment links via WhatsApp, and integrates with a full-stack dashboard for monitoring and management.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SARA AI CALLING SYSTEM                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────────────────────┐ │
│  │   Twilio    │◄──►│  main.py     │◄──►│  Dashboard (React + Node.js)   │ │
│  │  (Voice)    │    │  Flask App   │    │                                 │ │
│  └─────────────┘    └──────────────┘    │  ┌─────────┐  ┌─────────────┐  │ │
│                            │             │  │Frontend │  │  Backend    │  │ │
│  ┌─────────────┐          │             │  │ :3000   │  │  :5000      │  │ │
│  │  OpenAI     │◄─────────┤             │  └─────────┘  └─────────────┘  │ │
│  │  (GPT/TTS)  │          │             └─────────────────────────────────┘ │
│  └─────────────┘          │                                                 │
│                           │             ┌─────────────────────────────────┐ │
│  ┌─────────────┐          │             │         MongoDB                 │ │
│  │  WhatsApp   │◄─────────┤             │  (Calls, Payments, Messages)    │ │
│  │  (Meta)     │          │             └─────────────────────────────────┘ │
│  └─────────────┘          │                                                 │
│                           │                                                 │
│  ┌─────────────┐          │                                                 │
│  │  Razorpay   │◄─────────┘                                                 │
│  │  (Payments) │                                                            │
│  └─────────────┘                                                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
SARA_CallingAgent/
├── main.py                          # Main entry point - Flask voice bot server
├── start_sara.py                    # Alternative startup script
├── requirements.txt                 # Python dependencies
├── env.example                      # Environment variables template
│
├── src/                             # Python source modules
│   ├── config.py                    # Configuration management
│   ├── mixed_ai_brain.py            # OpenAI GPT integration
│   ├── enhanced_hindi_tts.py        # Text-to-Speech (OpenAI TTS)
│   ├── mixed_stt.py                 # Speech-to-Text engine
│   ├── language_detector.py         # Hindi/English detection
│   ├── dynamic_prompt_builder.py    # Context-aware prompt generation
│   ├── product_service.py           # Product data management
│   ├── conversation_memory.py       # Conversation history
│   ├── emotion_detector.py          # Sentiment analysis
│   ├── humanizer.py                 # Response humanization
│   ├── realtime_voice_bot.py        # Real-time voice processing
│   ├── realtime_vad.py              # Voice Activity Detection
│   ├── ultra_simple_interruption.py # Call interruption handling
│   ├── whatsapp_direct.py           # WhatsApp API + Razorpay integration
│   ├── whatsapp_integration.py      # WhatsApp intent detection
│   │
│   ├── services/
│   │   ├── sms_service.py           # Twilio SMS (disabled for India)
│   │   └── whatsapp/
│   │       ├── razorpay_client.py   # Razorpay payment links
│   │       ├── whatsapp_client.py   # Meta WhatsApp API
│   │       ├── whatsapp_service.py  # WhatsApp business logic
│   │       └── whatsapp_templates.py # Message templates
│   │
│   └── responses/
│       ├── humanized_response.py    # Natural response generation
│       └── response_factory.py      # Response builder
│
├── prompts/                         # AI personality prompts
│   ├── core_persona.txt             # Sara's personality definition
│   ├── sales_prompt.txt             # Sales conversation prompts
│   ├── booking_prompt.txt           # Booking flow prompts
│   └── support_prompt.txt           # Support conversation prompts
│
├── audio_files/                     # Generated TTS audio (temporary)
│
└── sara-dashboard/                  # Full-stack dashboard
    ├── backend/                     # Node.js/Express API
    │   ├── server.js                # Express server entry
    │   ├── config/db.js             # MongoDB connection
    │   ├── models/
    │   │   ├── CallLog.js           # Call records
    │   │   ├── PaymentLink.js       # Payment tracking
    │   │   ├── WhatsAppMessage.js   # Message logs
    │   │   ├── AidaProduct.js       # AIDA products
    │   │   ├── User.js              # Dashboard users
    │   │   └── SystemConfig.js      # System settings
    │   ├── controllers/
    │   │   ├── callController.js    # Call API handlers
    │   │   ├── paymentController.js # Payment API handlers
    │   │   ├── whatsappController.js# WhatsApp API handlers
    │   │   └── ...
    │   ├── routes/
    │   │   ├── callRoutes.js        # /api/calls
    │   │   ├── paymentRoutes.js     # /api/payments
    │   │   ├── whatsappRoutes.js    # /api/whatsapp
    │   │   └── ...
    │   ├── middleware/
    │   │   ├── authMiddleware.js    # JWT authentication
    │   │   └── errorHandler.js      # Error handling
    │   └── socket/
    │       └── socketHandler.js     # Real-time WebSocket
    │
    └── frontend/                    # React dashboard
        ├── src/
        │   ├── App.js               # Main React app
        │   ├── pages/
        │   │   ├── Dashboard/       # Main dashboard
        │   │   ├── Calls/           # Call logs & live calls
        │   │   ├── Payments/        # Payment tracking
        │   │   ├── WhatsApp/        # WhatsApp messages
        │   │   ├── Analytics/       # Call analytics
        │   │   ├── Sales/           # Product management
        │   │   └── Settings/        # System settings
        │   ├── components/
        │   │   └── Layout/          # Sidebar, Navbar
        │   └── contexts/
        │       ├── AuthContext.js   # Auth state
        │       └── SocketContext.js # WebSocket state
        └── tailwind.config.js       # Tailwind CSS config
```

## API Endpoints

### Voice Bot (main.py - Flask)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/voice` | POST | Twilio webhook for incoming calls |
| `/process_speech` | POST | Process speech input |
| `/process_speech_realtime` | POST | Real-time speech processing |
| `/status` | POST | Call status webhook |
| `/audio/<filename>` | GET | Serve TTS audio files |

### Dashboard Backend (Node.js)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/calls` | GET/POST | List/Create calls |
| `/api/calls/:id` | GET/PATCH/DELETE | Single call operations |
| `/api/calls/stats` | GET | Call statistics |
| `/api/payments` | GET/POST | List/Create payments |
| `/api/payments/stats` | GET | Payment statistics |
| `/api/whatsapp/messages` | GET/POST | WhatsApp messages |
| `/api/whatsapp/stats` | GET | WhatsApp statistics |
| `/api/users/login` | POST | User authentication |
| `/api/sales/products` | GET/POST | Product management |

## Environment Variables

### Python Bot (.env)
```env
# Twilio
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1...

# OpenAI
OPENAI_API_KEY=sk-...

# WhatsApp (Meta)
WHATSAPP_API_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_BUSINESS_NUMBER=+91...

# Razorpay
RAZORPAY_KEY_ID=rzp_...
RAZORPAY_KEY_SECRET=...

# Dashboard
DASHBOARD_API_URL=http://localhost:5000/api
```

### Dashboard Backend (.env)
```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/sara_dashboard
JWT_SECRET=your_jwt_secret
FRONTEND_URL=http://localhost:3000
```

### Dashboard Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:5000/api
REACT_APP_SOCKET_URL=http://localhost:5000
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Voice Bot | Python 3.12, Flask |
| AI/LLM | OpenAI GPT-4.1-mini |
| TTS | OpenAI TTS (alloy voice) |
| STT | Twilio Enhanced Speech Recognition |
| Telephony | Twilio Voice API |
| WhatsApp | Meta WhatsApp Business API |
| Payments | Razorpay Payment Links |
| Dashboard Backend | Node.js, Express, MongoDB |
| Dashboard Frontend | React, Tailwind CSS |
| Real-time | Socket.io |
| Tunnel (Dev) | ngrok |

## Ports

| Service | Port |
|---------|------|
| Voice Bot (Flask) | 8080 |
| Audio Server | 8081 |
| Dashboard Backend | 5000 |
| Dashboard Frontend | 3000 |
| MongoDB | 27017 |

## Key Features

1. **Bilingual Voice Bot** - Hindi/English real-time conversation
2. **Interruption Handling** - Users can interrupt the bot mid-speech
3. **Payment Links** - Razorpay integration via WhatsApp
4. **WhatsApp Messages** - Automated payment link delivery
5. **Real-time Dashboard** - Live call monitoring
6. **Payment Tracking** - Revenue and conversion analytics
7. **Call Analytics** - Duration, success rates, trends
8. **Product Management** - AIDA-based sales scripts

## Version

- **Current Version**: 2.0.0 (Dashboard Integration)
- **Last Updated**: January 2026
