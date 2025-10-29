# 🤖 Sara - AI Calling Bot with Dashboard | Advanced Voice Assistant

Meet **Sara**, your intelligent AI voice assistant that can make and receive phone calls with native support for **Hindi, English, and Hinglish** (mixed language) conversations. Sara is designed to be a helpful, professional, and natural-sounding female AI assistant with **product-aware conversation capabilities** and a **full-featured management dashboard**.

---

## ✨ Major Features (2025 Update)

### 🎯 **NEW: Product-Aware Conversations**
- Dynamic conversation flows based on active product from dashboard
- Product-specific greetings and responses
- Natural scope control with flexible redirects
- AIDA framework support (Attention, Interest, Desire, Action)
- Objection handling and FAQs

### 📊 **NEW: Full MERN Stack Dashboard**
- **Live Call Monitoring** - Real-time call status and transcripts
- **Call History & Analytics** - Comprehensive call logs with filtering
- **Product Management** - Add/edit products and conversation scripts
- **Voice Configuration** - Customize voice settings per product
- **User Management** - Multi-user support with authentication
- **Dark Theme** - Modern, professional UI

### 🎤 **Enhanced Voice Quality (tts-1-hd)**
- Upgraded to OpenAI's `tts-1-hd` model for higher quality
- Natural speech speed (0.95x) for clarity
- Warm, expressive `nova` voice for Sara
- Multi-provider TTS fallback system

### ⚡ **Voice Interruption System**
- Natural barge-in support (user can interrupt Sara)
- Real-time voice activity detection
- Graceful conversation flow management

### 🛡️ **Auto-Dependency Management**
- Automatic dependency checking on startup
- Auto-installs missing packages
- Safe and non-destructive
- No manual pip installs needed!

---

## 🌟 Core Features

### 👩 **Sara's Personality**
- Professional female AI assistant with consistent voice
- Warm, friendly, and empathetic responses
- Context-aware conversations
- Handles off-topic questions gracefully
- Natural conversation flow with pauses

### 📞 **Phone Call Integration**
- Make and receive actual phone calls via Twilio
- Real-time speech processing
- Automatic language detection
- Clean call termination on goodbye detection

### 🌐 **Multilingual Support**
- **Hindi** (Devanagari): नमस्ते, आप कैसे हैं?
- **English**: Hello, how can I help you?
- **Hinglish** (Romanized): Namaste, kaise ho aap?
- **Mixed**: Automatic detection and switching

### 🧠 **AI-Powered Intelligence**
- OpenAI GPT-4o-mini for natural conversations
- Context-aware responses
- Emotion detection and appropriate tone
- Product knowledge and sales capabilities

### 🎯 **Advanced Features**
- ✅ Voice interruptions (barge-in)
- ✅ Hangup detection (multiple languages)
- ✅ No-response handling (graceful call termination)
- ✅ Real-time transcription
- ✅ Dashboard logging
- ✅ Auto audio cleanup
- ✅ WebSocket for live updates

---

## 🚀 Quick Start (Ultra Simple!)

### 1. Clone the Repository
```bash
git clone https://github.com/UniversalLevi/AI-Calling-Agent.git
cd AI-Calling-Agent
```

### 2. Set Up Environment Variables
Create a `.env` file in the root directory (see `env.example`):

```env
# Required - OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Required - Twilio (for phone calls)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# TTS Configuration (Sara's Voice)
OPENAI_TTS_MODEL=tts-1-hd
OPENAI_TTS_VOICE=nova
OPENAI_TTS_SPEED=0.95

# Optional - MongoDB for Dashboard (if using dashboard)
MONGODB_URI=mongodb://localhost:27017/sara-dashboard
JWT_SECRET=your_jwt_secret_here
```

### 3. Install Dependencies (Auto or Manual)

**Option A: Auto-Install (Recommended)**
```bash
python main.py
# Dependencies are automatically checked and installed!
```

**Option B: Manual Install**
```bash
pip install -r requirements.txt
```

### 4. Start Sara!

**For Calling Bot Only:**
```bash
python main.py
# Choose your option from the menu
```

**For Dashboard + Calling Bot:**
```bash
# Terminal 1: Start Dashboard
python start_sara.py

# Terminal 2: Start Calling Bot
python main.py
```

### 5. Access Dashboard (if running)
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Default credentials**: `admin` / `admin123`

---

## 📊 Dashboard Features

### 🎛️ **Live Call Monitoring**
- See active calls in real-time
- View live transcriptions
- Monitor call duration
- Track conversation language

### 📈 **Analytics & Insights**
- Total calls and duration
- Success/completion rates
- Language distribution
- Product performance metrics

### 🛍️ **Product Management**
- Add/edit products
- Configure AIDA conversation flows
- Set custom greetings and taglines
- Define objection handling
- Manage FAQs and selling points

### ⚙️ **Voice Configuration**
- Choose TTS provider per product
- Adjust voice speed and tone
- Configure emotion settings
- Test voice output

### 📞 **Call Logs**
- Complete call history
- Filter by status, date, language
- Search by caller/receiver
- View full transcripts
- Export call data

---

## 🏗️ Technical Architecture

### **Tech Stack**

**Backend (Python)**
- Flask server for Twilio webhooks
- OpenAI GPT-4o-mini for AI conversations
- Faster-Whisper for speech recognition
- OpenAI TTS (tts-1-hd) with multi-provider fallback
- Real-time voice activity detection

**Dashboard (MERN)**
- **MongoDB** - Database for calls, products, users
- **Express.js** - REST API backend
- **React** - Modern dashboard UI
- **Node.js** - Server runtime
- **WebSocket** - Real-time updates

**Telephony**
- Twilio Voice API
- Media Streams for real-time audio
- Ngrok for webhook tunneling

### **System Workflow**
```
Phone Call → Twilio → Ngrok → Flask Server
    ↓
Speech Input → Faster-Whisper STT → Language Detection
    ↓
Product Service → Active Product Data
    ↓
Dynamic Prompt Builder → Context-Aware Prompt
    ↓
OpenAI GPT → AI Response Generation
    ↓
OpenAI TTS (tts-1-hd) → Audio Response
    ↓
Twilio → Phone Output
    ↓
Dashboard Logging → MongoDB → Real-time UI Update
```

---

## 📁 Project Structure

```
AI-Calling-Agent/
├── main.py                          # Main calling bot (run this!)
├── start_sara.py                    # Dashboard launcher
├── dependency_checker.py            # Auto dependency installer
├── requirements.txt                 # Python dependencies
├── .env                            # Environment variables (create this)
├── env.example                     # Environment template
│
├── src/                            # Core Python modules
│   ├── config.py                   # Configuration
│   ├── mixed_ai_brain.py           # AI conversation engine
│   ├── mixed_stt.py                # Speech-to-text
│   ├── enhanced_hindi_tts.py       # High-quality TTS
│   ├── language_detector.py        # Language detection
│   ├── tts_adapter.py              # TTS adapter wrapper
│   ├── ultra_simple_interruption.py # Voice interruption
│   ├── product_service.py          # Product data fetching
│   ├── dynamic_prompt_builder.py   # Dynamic prompts
│   ├── simple_dashboard_integration.py # Dashboard API
│   ├── dashboard_api.py            # Dashboard Flask blueprint
│   ├── prompt_manager.py           # Prompt templates
│   ├── conversation_memory.py      # Conversation history
│   ├── humanizer.py                # Response humanization
│   ├── emotion_detector.py         # Emotion detection
│   └── responses/                  # Response handlers
│
├── sara-dashboard/                 # MERN Dashboard
│   ├── frontend/                   # React frontend
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   │   ├── Dashboard/
│   │   │   │   ├── Calls/
│   │   │   │   ├── Sales/
│   │   │   │   ├── Analytics/
│   │   │   │   └── Settings/
│   │   │   ├── components/
│   │   │   └── contexts/
│   │   └── package.json
│   │
│   └── backend/                    # Node.js/Express backend
│       ├── server.js
│       ├── models/                 # MongoDB models
│       ├── controllers/            # API controllers
│       ├── routes/                 # API routes
│       ├── middleware/             # Auth & validation
│       └── package.json
│
├── prompts/                        # AI prompts
│   ├── core_persona.txt
│   ├── sales_prompt.txt
│   ├── booking_prompt.txt
│   └── support_prompt.txt
│
├── audio_files/                    # Generated audio (auto-cleaned)
├── tests/                          # Test files
└── docs/                           # Documentation
    ├── INTEGRATION_LOG.md
    ├── PRODUCT_CONVERSATION_TESTING.md
    └── VOICE_IMPROVEMENT_GUIDE.md
```

---

## 🎯 Usage Examples

### **Making Calls**
```bash
python main.py
# Menu options:
# 1. Call any number
# 2. Call yourself (testing)
# 3. Exit
```

### **Conversation Examples**

**Product Sales (English):**
```
User: "What's the price?"
Sara: "The AI Trading Bot is priced at ₹2000. It's a great investment for automated trading. Would you like to know more about its features?"
```

**Product Sales (Hinglish):**
```
User: "Price kya hai?"
Sara: "Price hai sirf 2000 rupees. Bahut sasta hai automatic trading ke liye. Interested ho?"
```

**Off-Topic Handling:**
```
User: "What's the weather?"
Sara: "Aaj to garmi hai! Waise, AI Trading Bot ki planning kar rahe ho kya?"
```

**Goodbye Detection:**
```
User: "Bye, thanks!"
Sara: "Thank you for your time! Have a great day!"
[Call ends automatically]
```

---

## ⚙️ Configuration

### **TTS Voice Settings**
Edit `.env` file:
```env
OPENAI_TTS_MODEL=tts-1-hd          # or tts-1 (faster, lower quality)
OPENAI_TTS_VOICE=nova              # Female voices: nova, shimmer, alloy
OPENAI_TTS_SPEED=0.95              # 0.9 (slower) to 1.0 (normal)
```

### **Voice Options**
- `nova` - Warm, expressive (recommended for Sara)
- `shimmer` - Soft, gentle
- `alloy` - Neutral, versatile

### **Feature Flags**
In `main.py` or environment:
```python
ENABLE_INTERRUPTION = True         # Voice interruptions
ENABLE_PRODUCT_AWARE = True        # Product-specific conversations
AUTO_CLEANUP_AUDIO = True          # Auto-delete old audio files
```

---

## 🔧 Advanced Setup

### **Dashboard Setup (Optional)**

1. **Install Node.js** (v16+)
   - Download from: https://nodejs.org/

2. **Install MongoDB**
   - Local: https://www.mongodb.com/try/download/community
   - Cloud: https://www.mongodb.com/cloud/atlas (free tier)

3. **Install Dashboard Dependencies**
```bash
cd sara-dashboard
npm install

# Install frontend
cd frontend
npm install
cd ../..
```

4. **Create Dashboard User**
```bash
python create_dashboard_user.py
# Enter: admin / admin123 (or custom)
```

5. **Start Dashboard**
```bash
python start_sara.py
# Or manually:
# Terminal 1: cd sara-dashboard && npm run dev
# Terminal 2: python main.py
```

### **For Better Hindi Recognition**

1. Use larger Whisper model:
```env
WHISPER_MODEL_SIZE=medium  # or large for best quality
```

2. Set up fallback TTS providers:
```env
# Azure (best Hindi quality)
AZURE_SPEECH_KEY=your_key
AZURE_SPEECH_REGION=eastus

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

---

## 🐛 Troubleshooting

### **Dependency Issues**
```bash
# Auto-fix
python main.py  # Dependencies auto-install

# Manual fix
pip install -r requirements.txt

# Check manually
python dependency_checker.py
```

### **"No speech detected"**
- Check microphone permissions
- Speak louder or closer
- Adjust Twilio timeout in main.py (currently 8 seconds)

### **"TTS failed"**
- Verify OpenAI API key in `.env`
- Check API quota/credits
- System will fallback to gTTS automatically

### **"Call failed"**
- Verify Twilio credentials
- Check account balance
- Ensure ngrok is running
- Check webhook URL in Twilio console

### **Dashboard Not Loading**
```bash
# Check Node.js
node --version

# Check MongoDB
# Local: mongod --version
# Cloud: verify connection string

# Restart dashboard
python start_sara.py
```

### **Interruptions Not Working**
- Ensure `ENABLE_INTERRUPTION = True` in main.py
- Check Twilio Media Streams are enabled
- Verify `<Gather>` wraps `<Play>` in TwiML

---

## 📊 System Requirements

### **Minimum**
- **Python**: 3.8+
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Stable connection
- **Node.js**: 16+ (for dashboard)
- **MongoDB**: 4.4+ (for dashboard)

### **Recommended**
- **Python**: 3.10+
- **RAM**: 8GB+
- **CPU**: Multi-core (4+ cores)
- **Storage**: 5GB+ SSD
- **Node.js**: 18 LTS
- **MongoDB**: 6.0+

### **Required Accounts**
- [OpenAI API](https://platform.openai.com/) - For AI & TTS
- [Twilio](https://www.twilio.com/) - For phone calls
- [ngrok](https://ngrok.com/) - For webhooks (free tier OK)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - For dashboard (free tier OK)

---

## 🌍 Supported Languages

| Language | Code | Script | STT | TTS | AI | Dashboard |
|----------|------|--------|-----|-----|----|-----------|
| Hindi | `hi` | Devanagari | ✅ | ✅ | ✅ | ✅ |
| English | `en` | Latin | ✅ | ✅ | ✅ | ✅ |
| Hinglish | `mixed` | Mixed | ✅ | ✅ | ✅ | ✅ |

---

## 🔐 Security & Privacy

- ✅ **No hardcoded secrets** - All in environment variables
- ✅ **Local STT processing** - Faster-Whisper runs locally
- ✅ **Secure tunneling** - HTTPS via ngrok
- ✅ **API key protection** - Never logged or exposed
- ✅ **JWT authentication** - Dashboard uses secure tokens
- ✅ **MongoDB security** - Optional authentication & encryption

---

## 📈 Performance Metrics

### **Voice Quality**
- **TTS Model**: tts-1-hd (higher quality than tts-1)
- **Speed**: 0.95x (20-30% more natural than 1.0x)
- **Latency**: ~1-2 seconds per response
- **Interruption Detection**: <500ms

### **Call Handling**
- **Concurrent Calls**: 10+ (depends on server)
- **Max Call Duration**: Unlimited (user-controlled)
- **Auto Cleanup**: Every 5 minutes
- **Crash Recovery**: Graceful shutdown with cleanup

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test with both Hindi and English
5. Commit: `git commit -m "feat: description"`
6. Push: `git push origin feature-name`
7. Submit a pull request

### **Areas for Contribution**
- Additional language support
- New TTS providers
- Dashboard features
- Documentation improvements
- Bug fixes
- Performance optimizations

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **OpenAI** - GPT-4o-mini & TTS-1-HD
- **Twilio** - Phone call infrastructure
- **Faster-Whisper** - Speech recognition
- **MongoDB** - Database for dashboard
- **React** - Dashboard frontend
- **ngrok** - Webhook tunneling
- **Community** - For feedback and contributions

---

## 💡 Tips for Best Experience

### **For Users**
1. ✅ Speak clearly in Hindi, English, or mixed
2. ✅ Use natural language - Sara understands context
3. ✅ Test locally first before production calls
4. ✅ Check audio quality in `audio_files/` directory
5. ✅ Use dashboard to monitor and improve conversations

### **For Developers**
1. ✅ Use `dependency_checker.py` to verify setup
2. ✅ Check logs in `dashboard.log` for debugging
3. ✅ Use `INTEGRATION_LOG.md` for version tracking
4. ✅ Test TTS with different voices (see `VOICE_IMPROVEMENT_GUIDE.md`)
5. ✅ Follow product conversation testing guide (`PRODUCT_CONVERSATION_TESTING.md`)

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/UniversalLevi/AI-Calling-Agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/UniversalLevi/AI-Calling-Agent/discussions)
- **Email**: [Your Email]
- **Documentation**: Check `docs/` folder

---

## 🎯 Roadmap

### **Version 2.0 (Current)**
- ✅ Product-aware conversations
- ✅ Full MERN dashboard
- ✅ Voice interruptions
- ✅ Auto-dependency management
- ✅ Enhanced voice quality (tts-1-hd)

### **Version 2.1 (Planned)**
- 🔲 Multi-language TTS per conversation
- 🔲 Voice cloning for custom Sara voices
- 🔲 Advanced analytics & reporting
- 🔲 CRM integrations
- 🔲 WhatsApp integration
- 🔲 SMS fallback support

### **Version 3.0 (Future)**
- 🔲 Multi-agent conversations
- 🔲 Video call support
- 🔲 Screen sharing for demos
- 🔲 AI-powered call routing
- 🔲 Sentiment analysis
- 🔲 Auto-call scheduling

---

**Made with ❤️ for the Hindi and English speaking community**

**Star ⭐ this repo if Sara helped you!**

For questions or support, please open an issue on GitHub.
