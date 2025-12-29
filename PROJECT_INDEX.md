# SARA Calling Agent - Project Index & Architecture

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Component Breakdown](#component-breakdown)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Key Features](#key-features)
7. [File Structure](#file-structure)
8. [Integration Points](#integration-points)

---

## Project Overview

**SARA** is an AI-powered voice calling agent that can make and receive phone calls with native support for **Hindi, English, and Hinglish** (mixed language) conversations. The system includes:

- **Python Backend**: Voice bot with AI conversation engine
- **MERN Dashboard**: Full-stack web dashboard for management
- **Twilio Integration**: Real phone call handling
- **Product-Aware Conversations**: Dynamic conversation flows based on active products
- **Real-time Monitoring**: Live call tracking and analytics

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER PHONE                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Phone Call (Voice)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                     TWILIO API                               │
│  - Voice Calls                                              │
│  - Media Streams                                            │
│  - Webhooks                                                 │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTPS Webhook
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  NGROK TUNNEL                                │
│  (Local Development: Exposes localhost:8000 to internet)    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP Requests
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FLASK VOICE BOT SERVER (Port 8000)              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Main Endpoints:                                       │ │
│  │  - /voice              (Incoming call handler)        │ │
│  │  - /process_speech     (Traditional mode)             │ │
│  │  - /process_speech_realtime (Enhanced mode)           │ │
│  │  - /audio/<filename>   (Serve audio files)            │ │
│  │  - /status             (Call status callback)         │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   STT       │ │     AI      │ │     TTS     │
│ (Faster-    │ │  (OpenAI    │ │  (OpenAI    │
│  Whisper)   │ │  GPT-4o-    │ │  tts-1-hd)  │
│             │ │   mini)     │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              PRODUCT SERVICE & PROMPT BUILDER                │
│  - Fetches active product from dashboard                    │
│  - Builds dynamic prompts with product context              │
│  - Manages conversation history                             │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ HTTP API Calls
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          DASHBOARD BACKEND (Node.js/Express, Port 5000)     │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Endpoints:                                        │ │
│  │  - /api/calls          (Call logs & management)       │ │
│  │  - /api/sales          (Products & scripts)           │ │
│  │  - /api/aida           (AIDA products)                │ │
│  │  - /api/analytics      (Analytics data)               │ │
│  │  - /api/users          (User management)              │ │
│  │  - /api/system         (System config)                │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Socket.IO Server                                      │ │
│  │  - Real-time call updates                              │ │
│  │  - Live transcript streaming                           │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ MongoDB
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      MONGODB DATABASE                        │
│  - CallLogs                                                  │
│  - Products / AidaProducts                                   │
│  - Users                                                     │
│  - SalesScripts                                              │
│  - SystemConfig                                              │
│  - Analytics                                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│          DASHBOARD FRONTEND (React, Port 3000)              │
│  - Live Call Monitoring                                     │
│  - Call History & Analytics                                 │
│  - Product Management                                       │
│  - User Management                                          │
│  - Settings & Configuration                                 │
└─────────────────────────────────────────────────────────────┘
```

### Call Flow Diagram

```
1. User Receives Call from SARA
   │
   ├─> Twilio routes to /voice endpoint
   │
2. Flask Server (/voice endpoint)
   │
   ├─> Fetch active product (ProductService)
   │
   ├─> Generate product-specific greeting
   │
   ├─> Initialize call session
   │
   ├─> Log call start to dashboard
   │
   └─> Play greeting + Start speech gathering
   │
3. User Speaks
   │
   ├─> Twilio sends speech to /process_speech_realtime
   │
4. Speech Processing
   │
   ├─> Detect language (LanguageDetector)
   │
   ├─> Update transcript in dashboard
   │
   ├─> Get conversation history from session
   │
   ├─> Build dynamic prompt (DynamicPromptBuilder)
   │     ├─> Include product context
   │     ├─> Include conversation history
   │     └─> Add scope control rules
   │
   ├─> Generate AI response (MixedAIBrain)
   │     └─> OpenAI GPT-4o-mini
   │
   ├─> Generate speech audio (EnhancedHindiTTS)
   │     └─> OpenAI tts-1-hd (or fallback to gTTS)
   │
   ├─> Update conversation history
   │
   ├─> Update transcript in dashboard
   │
   └─> Play audio to user (with interruption support)
   │
5. Loop back to step 3 until call ends
   │
6. Call End Detection
   │
   ├─> Goodbye keywords detected
   │
   └─> Update call status in dashboard
```

---

## Component Breakdown

### 1. Python Backend (Voice Bot)

#### Entry Points
- **`main.py`**: Main launcher for calling bot
  - Auto-checks dependencies
  - Starts Flask servers (audio server + voice bot server)
  - Starts ngrok tunnel
  - Provides menu system for making calls
  
- **`start_sara.py`**: Dashboard launcher
  - Starts Node.js dashboard (frontend + backend)
  - Monitors processes

#### Core Modules (`src/`)

**Speech Processing:**
- **`mixed_stt.py`**: Speech-to-Text engine using Faster-Whisper
  - Supports Hindi and English transcription
  - Language auto-detection
  - Configurable model sizes (tiny, small, base, medium, large)

- **`language_detector.py`**: Language detection utility
  - Detects Hindi, English, and Hinglish
  - Uses Devanagari script detection
  - Hinglish keyword matching
  - Phone number country code bias (India +91 → Hindi bias)

**AI & Conversation:**
- **`mixed_ai_brain.py`**: AI conversation engine
  - `MixedAIBrain`: Main AI brain class
  - `MixedOpenAIProvider`: OpenAI GPT-4o-mini implementation
  - `MixedGeminiProvider`: Google Gemini alternative (fallback)
  - Maintains conversation history
  - Language-aware prompts

- **`dynamic_prompt_builder.py`**: Dynamic prompt generation
  - Builds prompts with product context
  - Includes conversation history
  - Scope control rules (handling off-topic questions)
  - AIDA framework support (Attention, Interest, Desire, Action)

- **`product_service.py`**: Product data service
  - Fetches active product from dashboard API
  - Caches product data (60s TTL)
  - Supports both Product and AidaProduct models
  - Standardizes product format

- **`prompt_manager.py`**: Prompt template management
  - Loads prompts from `prompts/` directory
  - Core persona, sales, booking, support prompts

**Text-to-Speech:**
- **`enhanced_hindi_tts.py`**: High-quality TTS system
  - Multiple provider support (OpenAI, gTTS)
  - OpenAI tts-1-hd for high quality
  - Automatic cleanup of old audio files
  - Language-aware voice selection

**Response Processing:**
- **`responses/`**: Response handler system
  - `humanized_response.py`: Humanized response pipeline
  - `response_factory.py`: Factory pattern for response handlers

**Humanization:**
- **`humanizer.py`**: Adds natural conversation elements
  - Filler words
  - Micro-sentences
  - Semantic pacing

- **`emotion_detector.py`**: Emotion detection
  - Keyword-based detection
  - GPT-based detection (optional)
  - Hybrid mode

**Dashboard Integration:**
- **`simple_dashboard_integration.py`**: Dashboard API client
- **`dashboard_api.py`**: Dashboard Flask blueprint

**Voice Features:**
- **`ultra_simple_interruption.py`**: Voice interruption handling
- **`realtime_voice_bot.py`**: Real-time voice bot implementation
- **`realtime_vad.py`**: Voice activity detection

**Utilities:**
- **`config.py`**: Configuration management
  - Environment variable loading
  - Settings validation
  - Feature flags

- **`conversation_memory.py`**: Conversation history management
- **`hinglish_translator.py`**: Hinglish transliteration
- **`script_integration.py`**: Sales script integration

### 2. Dashboard Backend (Node.js/Express)

**Server (`server.js`)**:
- Express server on port 5000
- Socket.IO for real-time updates
- MongoDB connection
- CORS configuration
- Request logging

**Models (`models/`)**:
- `CallLog.js`: Call records with transcripts
- `Product.js`: Basic product model
- `AidaProduct.js`: AIDA framework product model
- `SalesScript.js`: Sales conversation scripts
- `User.js`: User authentication
- `SystemConfig.js`: System settings
- `SalesAnalytics.js`: Analytics data
- `ObjectionHandler.js`: Objection handling rules

**Controllers (`controllers/`)**:
- `callController.js`: Call log management
- `salesController.js`: Product and script management
- `aidaController.js`: AIDA product management
- `analyticsController.js`: Analytics generation
- `userController.js`: User management
- `systemController.js`: System configuration

**Routes (`routes/`)**:
- RESTful API endpoints
- Authentication middleware
- Request validation

**Socket Handler (`socket/socketHandler.js`)**:
- Real-time call updates
- Live transcript streaming
- Connection management

### 3. Dashboard Frontend (React)

**Pages (`pages/`)**:
- `Dashboard/`: Main dashboard overview
- `Calls/`: 
  - `LiveCalls.js`: Real-time call monitoring
  - `CallLogs.js`: Call history
- `Sales/`:
  - `ProductManager.js`: Product management
  - `AidaProductManager.js`: AIDA product editor
  - `ScriptEditor.js`: Sales script editor
- `Analytics/`: Analytics and insights
- `Users/`: User management
- `Settings/`: System configuration
- `Auth/Login.js`: Authentication

**Components (`components/`)**:
- `Layout/`: Navbar, Sidebar, Layout wrapper
- `Auth/`: Protected routes
- `Common/`: Loading spinner, etc.

**Contexts (`contexts/`)**:
- `AuthContext.js`: Authentication state
- `SocketContext.js`: Socket.IO connection

---

## Data Flow

### Call Initiation Flow

1. User runs `python main.py`
2. System checks dependencies (auto-installs if needed)
3. Flask servers start:
   - Audio server (port 5001)
   - Voice bot server (port 8000)
4. Ngrok tunnel starts (exposes port 8000)
5. Webhook URL configured in Twilio
6. User selects "Call a number" from menu
7. Twilio initiates call
8. Call routed to `/voice` endpoint

### Conversation Flow

1. **Call Start**:
   - ProductService fetches active product
   - DynamicPromptBuilder creates initial prompt
   - Product-specific greeting generated
   - Call logged to dashboard

2. **User Speaks**:
   - Twilio captures speech
   - Speech sent to `/process_speech_realtime`
   - Language detection (LanguageDetector)
   - Transcript updated in dashboard

3. **AI Processing**:
   - Conversation history retrieved from session
   - DynamicPromptBuilder builds enhanced prompt:
     - Product context
     - Conversation history
     - Scope control rules
   - MixedAIBrain generates response
   - Response logged to transcript

4. **Speech Generation**:
   - EnhancedHindiTTS generates audio
   - Audio file saved to `audio_files/`
   - File served via `/audio/<filename>`
   - Twilio plays audio to user

5. **Interruption Handling**:
   - Partial speech detection via `/partial_speech`
   - Interruption flags set
   - Current audio stopped
   - New user input processed

6. **Call End**:
   - Goodbye keywords detected
   - Call status updated in dashboard
   - Session data cleared
   - Audio files cleaned up (after 5 minutes)

---

## Technology Stack

### Python Backend
- **Flask**: Web framework for voice bot server
- **OpenAI**: GPT-4o-mini (AI) + tts-1-hd (TTS)
- **Faster-Whisper**: Speech-to-text
- **Twilio**: Phone call infrastructure
- **ngrok**: Webhook tunneling
- **python-dotenv**: Environment management

### Dashboard Backend
- **Node.js**: Runtime
- **Express**: Web framework
- **MongoDB**: Database
- **Mongoose**: ODM
- **Socket.IO**: Real-time communication
- **JWT**: Authentication
- **bcrypt**: Password hashing

### Dashboard Frontend
- **React**: UI framework
- **React Router**: Routing
- **Tailwind CSS**: Styling
- **Socket.IO Client**: Real-time updates
- **Axios**: HTTP client
- **Recharts**: Data visualization

---

## Key Features

### 1. Multilingual Support
- **Hindi** (Devanagari script)
- **English**
- **Hinglish** (mixed Romanized Hindi + English)
- Automatic language detection
- Language-aware AI responses

### 2. Product-Aware Conversations
- Dynamic prompts based on active product
- Product-specific greetings
- AIDA framework support
- Objection handling
- Scope control (handling off-topic)

### 3. Voice Features
- High-quality TTS (OpenAI tts-1-hd)
- Voice interruptions (barge-in)
- Real-time speech processing
- Natural conversation flow

### 4. Dashboard Features
- Live call monitoring
- Call history & analytics
- Product management
- Script editor
- User management
- Real-time transcript updates

### 5. Reliability Features
- Auto-dependency installation
- Graceful error handling
- Audio file cleanup
- Conversation session management
- Fallback TTS providers

---

## File Structure

```
SARA_CallingAgent/
├── main.py                          # Main calling bot launcher
├── start_sara.py                    # Dashboard launcher
├── dependency_checker.py            # Auto dependency installer
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create from env.example)
├── env.example                     # Environment template
│
├── src/                            # Core Python modules
│   ├── config.py                   # Configuration management
│   ├── mixed_ai_brain.py           # AI conversation engine
│   ├── mixed_stt.py                # Speech-to-text
│   ├── enhanced_hindi_tts.py       # Text-to-speech
│   ├── language_detector.py        # Language detection
│   ├── product_service.py          # Product data service
│   ├── dynamic_prompt_builder.py   # Dynamic prompt builder
│   ├── prompt_manager.py           # Prompt templates
│   ├── conversation_memory.py      # Conversation history
│   ├── humanizer.py                # Response humanization
│   ├── emotion_detector.py         # Emotion detection
│   ├── dashboard_api.py            # Dashboard integration
│   ├── simple_dashboard_integration.py
│   ├── script_integration.py       # Sales scripts
│   ├── realtime_voice_bot.py       # Real-time voice bot
│   ├── ultra_simple_interruption.py
│   ├── responses/                  # Response handlers
│   └── tools/                      # Utility tools
│
├── sara-dashboard/                 # MERN Dashboard
│   ├── backend/                    # Node.js/Express backend
│   │   ├── server.js               # Main server
│   │   ├── models/                 # MongoDB models
│   │   ├── controllers/            # API controllers
│   │   ├── routes/                 # API routes
│   │   ├── middleware/             # Auth & validation
│   │   ├── socket/                 # Socket.IO handlers
│   │   └── scripts/                # Database seeds
│   │
│   └── frontend/                   # React frontend
│       ├── src/
│       │   ├── pages/              # Page components
│       │   ├── components/         # Reusable components
│       │   ├── contexts/           # React contexts
│       │   └── App.js              # Main app component
│       └── package.json
│
├── prompts/                        # AI prompt templates
│   ├── core_persona.txt
│   ├── sales_prompt.txt
│   ├── booking_prompt.txt
│   └── support_prompt.txt
│
├── audio_files/                    # Generated audio (auto-cleaned)
└── docs/                           # Documentation
```

---

## Integration Points

### 1. Twilio Integration
- **Webhook URLs**: `/voice`, `/process_speech_realtime`, `/status`
- **Media Streams**: `/media/<call_sid>` (for real-time processing)
- **Audio Serving**: `/audio/<filename>`

### 2. Dashboard API Integration
- **Product Service**: `GET /api/aida/active` or `GET /api/sales/products/active`
- **Call Logging**: `POST /api/calls`
- **Call Updates**: `PATCH /api/calls/:id`
- **Transcript Updates**: `PATCH /api/calls/:id/transcript`

### 3. OpenAI Integration
- **GPT-4o-mini**: Conversation generation
- **tts-1-hd**: High-quality text-to-speech
- **Voice**: `nova` (default), `shimmer`, `alloy`

### 4. MongoDB Schema
- **CallLogs**: Call records with transcripts, status, metadata
- **AidaProducts**: Product data with AIDA framework
- **Users**: Authentication and authorization
- **SystemConfig**: System-wide settings

---

## Environment Variables

### Required
- `OPENAI_API_KEY`: OpenAI API key
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_PHONE_NUMBER`: Twilio phone number

### Optional
- `MONGODB_URI`: MongoDB connection string
- `JWT_SECRET`: JWT secret for dashboard
- `OPENAI_TTS_MODEL`: TTS model (default: tts-1-hd)
- `OPENAI_TTS_VOICE`: Voice name (default: nova)
- `WHISPER_MODEL_SIZE`: Whisper model size (default: base)

---

## Getting Started

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   cd sara-dashboard && npm install
   cd frontend && npm install
   ```

2. **Configure Environment**:
   - Copy `env.example` to `.env`
   - Fill in required credentials

3. **Start Dashboard**:
   ```bash
   python start_sara.py
   ```

4. **Start Calling Bot**:
   ```bash
   python main.py
   ```

5. **Access Dashboard**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Default credentials: `admin` / `admin123`

---

## Notes

- The system uses **Romanized Hinglish** (Latin script) for Hindi responses, not Devanagari
- Audio files are automatically cleaned up after 5 minutes
- Product data is cached for 60 seconds
- Real-time mode requires Twilio Media Streams
- Dashboard backend runs on port 5000, frontend on 3000
- Voice bot server runs on port 8000, audio server on 5001
- Ngrok exposes port 8000 to the internet for webhooks

---

*Last Updated: 2025*
