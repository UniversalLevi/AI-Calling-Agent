# 🤖 Sara - AI Sales Calling Bot | Hindi & English Voice Assistant

Meet **Sara**, your intelligent AI sales assistant that can make and receive phone calls with native support for **Hindi, English, and Hinglish** (mixed language) conversations. Sara is designed to be a professional sales representative with advanced selling techniques, analytics, and management capabilities.

## 🌟 Core Features

- **👩 Sara's Voice** - Professional female AI sales assistant with consistent voice across all languages
- **📞 Real Phone Calls** - Make and receive actual phone calls via Twilio
- **🌐 Multilingual Support** - Hindi, English, and mixed language conversations
- **🧠 AI-Powered** - Uses OpenAI GPT-4o-mini for intelligent responses
- **🎤 Advanced Speech Recognition** - Faster-Whisper with language auto-detection
- **🗣️ High-Quality Text-to-Speech** - OpenAI TTS with Sara's female voice
- **🔄 Language Detection** - Automatically detects and switches between languages
- **🛡️ Content Filtering** - Handles inappropriate content professionally
- **⚡ Real-time Interruption** - Fast interruption detection for natural conversations
- **🧹 Auto Cleanup** - Automatic audio file cleanup to save space
- **🎯 One-Click Setup** - Single command to start everything

## 🚀 Sales AI Features

- **💼 Sales Mode** - Transform Sara into a professional sales representative
- **📊 SPIN Selling** - Systematic qualification using Situation, Problem, Implication, Need-payoff questions
- **🤝 Consultative Approach** - Build trust and rapport with empathy-driven conversations
- **🎯 Challenger Techniques** - Teach value, tailor solutions, and take control of conversations
- **🛡️ Objection Handling** - Pre-configured responses to common sales objections
- **📊 Real-time Analytics** - Track sentiment, talk-listen ratio, conversion stages, and keywords
- **🎛️ Admin Dashboard** - Manage products, scripts, objections, and sales techniques
- **🔄 A/B Testing** - Test different approaches and automatically select winners
- **📱 Multi-Product Support** - Sell hotels, insurance, SaaS, real estate, and more

## 👩 About Sara

Sara is designed to be your professional AI sales assistant with the following characteristics:

- **Professional Sales Representative**: Uses proven sales techniques (SPIN, Consultative, Challenger)
- **Multilingual Sales Expert**: Fluent in Hindi, English, and Hinglish with natural language switching
- **Consistent Voice**: Uses OpenAI's Nova voice (female) across all languages for consistency
- **Smart Objection Handling**: Automatically detects and responds to sales objections professionally
- **Fast Response**: Optimized for real-time sales conversations with quick interruption detection
- **Analytics-Driven**: Tracks conversion metrics, sentiment, and sales performance in real-time
- **Memory Efficient**: Automatically cleans up audio files to save storage space

## 💼 Sales AI System Overview

Sara's Sales AI system transforms the basic calling bot into a sophisticated sales machine:

### 🎯 Sales Techniques
- **SPIN Selling**: Systematic qualification using Situation, Problem, Implication, Need-payoff questions
- **Consultative Selling**: Build trust through empathy, active listening, and understanding customer needs
- **Challenger Selling**: Teach customers new insights, tailor solutions, and take control of conversations

### 📊 Lead Qualification
- **Needs Assessment**: Understand customer requirements and pain points
- **Authority Identification**: Identify decision-makers and influencers
- **Need**: Understand customer pain points and requirements
- **Timeline**: Determine urgency and buying timeline

### 🛡️ Objection Handling
Pre-configured responses for common objections:
- "Too expensive" → Value demonstration and ROI calculation
- "Need to think" → Urgency creation and risk mitigation
- "Already have a solution" → Competitive differentiation
- "Not interested" → Pain point discovery and need creation

### 📈 Real-time Analytics
- **Sentiment Analysis**: Track customer mood and engagement
- **Talk-Listen Ratio**: Optimize conversation balance (target: 40% AI, 60% customer)
- **Conversion Funnel**: Track progression through sales stages
- **Keyword Success Mapping**: Identify phrases that lead to conversions

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/ai-calling-bot.git
cd ai-calling-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the root directory:

```env
# Required - OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Required - Twilio (for phone calls)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# TTS Provider Selection
TTS_PROVIDER=openai

# OpenAI TTS Configuration (Sara's Voice)
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=nova

# Optional - Enhanced Hindi TTS (fallbacks)
# Azure Cognitive Services (Best Hindi quality)
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_region

# Google Cloud TTS (Very good Hindi quality)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Optional - Gemini AI (alternative to OpenAI)
GEMINI_API_KEY=your_gemini_api_key

# Sales AI Configuration
SALES_MODE_ENABLED=true
ACTIVE_PRODUCT_ID=your_product_id_here
SALES_API_URL=http://localhost:5000
QUALIFICATION_THRESHOLD=20
SENTIMENT_ANALYSIS_ENABLED=true
TALK_LISTEN_TARGET_RATIO=0.4
SALES_CACHE_DURATION=300

# Dashboard Integration
DASHBOARD_API_URL=http://localhost:5000
DASHBOARD_API_KEY=your_dashboard_api_key
```

### 4. Install ngrok
Download and install [ngrok](https://ngrok.com/) for webhook tunneling.

### 5. Set Up Sales AI (Optional)
To enable Sales AI features:

1. **Start the Dashboard**:
   ```bash
   cd sara-dashboard
   npm install
   npm start
   ```

2. **Add a Product**:
   - Go to http://localhost:5000
   - Navigate to Sales → Products
   - Add your product with features, pricing, and FAQs

3. **Configure Sales Scripts**:
   - Go to Sales → Scripts
   - Create SPIN questions and sales scripts
   - Set up objection handlers

### 6. Run the Bot
```bash
python main.py
```

That's it! The bot will:
- Start the voice bot server
- Start the audio server
- Launch ngrok tunnel
- Show you a menu to make calls
- Use Sales AI if enabled and configured

## 📞 Usage Examples

### Making Calls
1. Run `python main.py`
2. Choose option 1 to call any number
3. Choose option 2 to call yourself (for testing)

### Sales Conversation Examples
- **Sales Greeting**: "Namaste! Main Sara hun aur main aapko hotel booking service ke baare mein batana chahti hun. Kya aap interested hain?"
- **SPIN Qualification**: "Aap currently kahan se hotel book karte hain? Koi challenges face karte hain?"
- **Objection Handling**: "Samajh gaya, price ka concern hai. Lekin aapko pata hai ki hum guaranteed lowest price dete hain?"
- **Closing**: "Perfect! Toh main aapke liye booking confirm kar dun?"

### Regular Conversation Examples
- **Hindi**: "नमस्ते, मुझे restaurant booking चाहिए"
- **English**: "Hello, I need help with hotel reservation"
- **Hinglish**: "Namaste, booking chahiye please"

## 🏗️ Architecture

### Core Components
- **main.py** - Complete launcher and server (the only file you need to run)
- **src/mixed_ai_brain.py** - AI brain with language-aware responses
- **src/sales_ai_brain.py** - Sales AI brain with SPIN/Consultative/Challenger techniques
- **src/sales_context_manager.py** - Manages sales conversation state and context tracking
- **src/sales_analytics_tracker.py** - Real-time sales analytics and performance tracking
- **src/mixed_stt.py** - Speech-to-text with Hindi/English support
- **src/enhanced_hindi_tts.py** - High-quality Hindi text-to-speech
- **src/language_detector.py** - Smart language detection including Hinglish

### Sales AI Components
- **sara-dashboard/backend/models/** - MongoDB models for products, scripts, objections, analytics
- **sara-dashboard/backend/controllers/** - API controllers for sales management
- **sara-dashboard/backend/routes/** - REST API routes for sales and analytics
- **sara-dashboard/frontend/src/pages/Sales/** - Admin interface for sales management
- **sara-dashboard/frontend/src/pages/Analytics/** - Sales performance dashboards

### Workflow
```
Phone Call → Twilio → ngrok → Voice Bot Server
    ↓
Speech Input → STT (Faster-Whisper) → Language Detection
    ↓
Sales AI Processing (SPIN/Consultative/Challenger) → Response Generation
    ↓
TTS (OpenAI Nova Voice) → Audio Response → Twilio → Phone
    ↓
Analytics Tracking → Dashboard → Performance Insights
```

## 🎯 Language Detection

The bot automatically detects:
- **Hindi** (Devanagari script): "नमस्ते कैसे हैं आप"
- **English** (Latin script): "Hello how are you"
- **Hinglish** (Latin with Hindi words): "Namaste, kaise ho aap"
- **Mixed** (Both scripts): "Hello नमस्ते, how are you"

## 🔊 Text-to-Speech Quality Ranking

1. **Azure Cognitive Services** ⭐⭐⭐⭐⭐ (Best Hindi quality)
2. **Google Cloud TTS** ⭐⭐⭐⭐ (Very good Hindi quality)
3. **ElevenLabs** ⭐⭐⭐⭐ (Good for custom voices)
4. **gTTS** ⭐⭐ (Basic quality, always available as fallback)

The system automatically tries providers in order of quality and falls back if needed.

## 📁 Project Structure

```
ai-calling-bot/
├── main.py                    # Main launcher (run this!)
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore file
├── SALES_AI_IMPLEMENTATION_COMPLETE.md # Sales AI documentation
├── asterisk/                # SIP configuration (optional)
│   ├── extensions.conf
│   └── sip.conf
├── src/                     # Core modules
│   ├── config.py           # Configuration settings
│   ├── mixed_ai_brain.py   # AI brain with language support
│   ├── sales_ai_brain.py   # Sales AI brain with SPIN/Consultative/Challenger
│   ├── sales_context_manager.py # Sales conversation state management
│   ├── sales_analytics_tracker.py # Real-time sales analytics
│   ├── sales_config.json   # Sales configuration cache
│   ├── mixed_stt.py        # Speech-to-text engine
│   ├── enhanced_hindi_tts.py # High-quality Hindi TTS
│   ├── mixed_tts.py        # Mixed language TTS
│   ├── language_detector.py # Language detection
│   ├── conversation_memory.py # Conversation memory system
│   ├── humanizer.py        # Human-like response enhancement
│   ├── tts_cache.py        # TTS caching system
│   ├── sip_client.py       # SIP client (optional)
│   ├── sip_voice_bot.py    # SIP voice bot (optional)
│   ├── twilio_client.py    # Twilio integration
│   ├── voice_bot.py        # Local voice bot
│   └── tools/
│       └── list_devices.py # Audio device listing
└── sara-dashboard/         # Sales AI Dashboard
    ├── backend/            # Node.js/Express backend
    │   ├── models/        # MongoDB models
    │   ├── controllers/   # API controllers
    │   ├── routes/        # API routes
    │   └── scripts/       # Database seed scripts
    └── frontend/          # React frontend
        └── src/
            ├── pages/Sales/    # Sales management pages
            ├── pages/Analytics/ # Analytics dashboards
            └── components/     # Reusable components
```

## ⚙️ Configuration Options

### Audio Settings
```env
SAMPLE_RATE=16000           # Audio sample rate
CHANNELS=1                  # Audio channels
RECORD_SECONDS=7.0          # Recording duration
WHISPER_MODEL_SIZE=base     # Whisper model (tiny/small/base/medium/large)
```

### Sales AI Settings
```env
SALES_MODE_ENABLED=true              # Enable sales AI features
ACTIVE_PRODUCT_ID=product_id         # Current product being sold
SALES_API_URL=http://localhost:5000  # Dashboard API endpoint
QUALIFICATION_THRESHOLD=20           # Minimum qualification score to proceed
SENTIMENT_ANALYSIS_ENABLED=true      # Enable real-time sentiment tracking
TALK_LISTEN_TARGET_RATIO=0.4         # Target AI talk percentage (40%)
SALES_CACHE_DURATION=300            # Cache duration in seconds
```

## 🔧 Advanced Setup

### For Better Hindi Recognition
1. Use a larger Whisper model:
   ```env
   WHISPER_MODEL_SIZE=medium
   ```

2. Set up Azure or Google TTS for best Hindi quality:
   ```env
   AZURE_SPEECH_KEY=your_key
   AZURE_SPEECH_REGION=eastus
   ```

### For Sales AI Setup
1. **Start the Dashboard**:
   ```bash
   cd sara-dashboard
   npm install
   npm start
   ```

2. **Configure Products**:
   - Go to http://localhost:5000
   - Navigate to Sales → Products
   - Add products with features, pricing, FAQs
   - Set target audience and competitor comparison

3. **Set Up Sales Scripts**:
   - Go to Sales → Scripts
   - Create SPIN questions for qualification
   - Add consultative phrases for trust building
   - Configure challenger closing techniques

4. **Configure Objection Handlers**:
   - Go to Sales → Objection Library
   - Add responses for common objections
   - Set success rates and A/B test different responses

5. **Enable Sales Mode**:
   ```env
   SALES_MODE_ENABLED=true
   ACTIVE_PRODUCT_ID=your_product_id
   ```

## 🐛 Troubleshooting

### Common Issues

**"No speech detected"**
- Check microphone permissions
- Verify `DEVICE_INDEX_IN` in config
- Try speaking louder or closer to microphone

**"TTS failed"**
- Check your TTS provider credentials
- Verify internet connection
- System falls back to gTTS automatically

**"Call failed"**
- Verify Twilio credentials in `.env`
- Check Twilio account balance
- Ensure ngrok is running

**"Sales AI not working"**
- Check `SALES_MODE_ENABLED=true` in `.env`
- Verify `ACTIVE_PRODUCT_ID` is set correctly
- Ensure dashboard is running on http://localhost:5000
- Check MongoDB connection in dashboard

**"Dashboard not loading"**
- Run `npm install` in sara-dashboard directory
- Check if MongoDB is running
- Verify port 5000 is not in use
- Check dashboard logs for errors

**"Product not found"**
- Add a product via Sales → Products in dashboard
- Set `ACTIVE_PRODUCT_ID` to the correct product ID
- Restart the bot after changing product ID

### Debug Mode
Set environment variable for detailed logging:
```env
PRINT_TRANSCRIPTS=true
PRINT_BOT_TEXT=true
```

## 📊 System Requirements

- **Python 3.8+**
- **Internet connection** (for AI and TTS services)
- **Microphone** (for local voice testing)
- **Twilio account** (for phone calls)
- **ngrok** (for webhook tunneling)

### Recommended Specs
- **RAM**: 4GB+ (for Whisper model)
- **CPU**: Multi-core recommended
- **Storage**: 2GB+ free space

## 🌍 Supported Languages

| Language | Code | Script | STT | TTS | AI |
|----------|------|--------|-----|-----|----| 
| Hindi | `hi` | Devanagari | ✅ | ✅ | ✅ |
| English | `en` | Latin | ✅ | ✅ | ✅ |
| Hinglish | `mixed` | Mixed | ✅ | ✅ | ✅ |

## 🔐 Security & Privacy

- **No hardcoded secrets** - All sensitive data in environment variables
- **Local processing** - Speech recognition runs locally
- **Secure tunneling** - ngrok provides HTTPS endpoints
- **API key protection** - Keys never logged or exposed

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both Hindi and English
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4o-mini API
- **Twilio** for phone call infrastructure
- **Faster-Whisper** for speech recognition
- **Azure/Google/ElevenLabs** for high-quality TTS
- **ngrok** for webhook tunneling

## 💡 Tips for Best Experience

1. **Speak clearly** - Both Hindi and English work best with clear pronunciation
2. **Use natural language** - The AI understands context and mixed languages
3. **Be patient** - First call might take a moment to initialize
4. **Test locally first** - Use the voice bot mode (option 5) to test before phone calls
5. **Check audio quality** - Generated audio files are saved in `audio_files/` directory

---

### FastAPI Parallel Server (New)
- Added `src/fastapi_server.py` running on port 8001 alongside existing Flask for phased migration.
- Startup tasks (in DEBUG_MODE=true): TTS cache warmup, health monitor.
- Health endpoint: `GET http://localhost:8001/health`.

### Voice Settings via Dashboard (New)
- Backend endpoints:
  - `GET /api/system/voice-settings`
  - `PUT /api/system/voice-settings`
- Frontend: Settings page allows selecting English/Hindi OpenAI voices.
- Bot reads voice settings dynamically before calls.

### Active Product Selection (Updated)
- Endpoints:
  - `PATCH /api/sales/products/:id/activate`
  - `GET /api/sales/products/active`
- Frontend: Product Manager has "Set Active" control.

### Debug Mode & Logs (New)
- `.env`: `DEBUG_MODE=true`, `DEBUG_LOG_FILE=debug.log`
- Console shows INFO; file logs at DEBUG with rotation (10MB, 3 backups).
- Timing instrumentation across STT/AI/TTS/streaming when debug enabled.

**Made with ❤️ for the Hindi and English speaking community**

For support or questions, please open an issue on GitHub.