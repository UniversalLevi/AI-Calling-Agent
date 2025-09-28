# 🤖 Sara - AI Calling Bot | Hindi & English Voice Assistant

Meet **Sara**, your intelligent AI voice assistant that can make and receive phone calls with native support for **Hindi, English, and Hinglish** (mixed language) conversations. Sara is designed to be a helpful, professional, and respectful female AI assistant.

## 🌟 Features

- **👩 Sara's Voice** - Professional female AI assistant with consistent voice across all languages
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

## 👩 About Sara

Sara is designed to be your helpful AI assistant with the following characteristics:

- **Professional & Respectful**: Always maintains a professional tone and handles inappropriate content gracefully
- **Multilingual**: Fluent in Hindi, English, and Hinglish with natural language switching
- **Consistent Voice**: Uses OpenAI's Nova voice (female) across all languages for consistency
- **Smart Content Filtering**: Automatically detects and responds appropriately to inappropriate content
- **Fast Response**: Optimized for real-time conversations with quick interruption detection
- **Memory Efficient**: Automatically cleans up audio files to save storage space

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
```

### 4. Install ngrok
Download and install [ngrok](https://ngrok.com/) for webhook tunneling.

### 5. Run the Bot
```bash
python main.py
```

That's it! The bot will:
- Start the voice bot server
- Start the audio server
- Launch ngrok tunnel
- Show you a menu to make calls

## 📞 Usage Examples

### Making Calls
1. Run `python main.py`
2. Choose option 1 to call any number
3. Choose option 2 to call yourself (for testing)

### Conversation Examples
- **Hindi**: "नमस्ते, मुझे restaurant booking चाहिए"
- **English**: "Hello, I need help with hotel reservation"
- **Hinglish**: "Namaste, booking chahiye please"

## 🏗️ Architecture

### Core Components
- **main.py** - Complete launcher and server (the only file you need to run)
- **src/mixed_ai_brain.py** - AI brain with language-aware responses
- **src/mixed_stt.py** - Speech-to-text with Hindi/English support
- **src/enhanced_hindi_tts.py** - High-quality Hindi text-to-speech
- **src/language_detector.py** - Smart language detection including Hinglish

### Workflow
```
Phone Call → Twilio → ngrok → Voice Bot Server
    ↓
Speech Input → STT (Faster-Whisper) → Language Detection
    ↓
AI Processing (OpenAI GPT-4o-mini) → Response Generation
    ↓
TTS (Azure/Google/ElevenLabs/gTTS) → Audio Response → Twilio → Phone
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
├── asterisk/                # SIP configuration (optional)
│   ├── extensions.conf
│   └── sip.conf
└── src/                     # Core modules
    ├── config.py           # Configuration settings
    ├── mixed_ai_brain.py   # AI brain with language support
    ├── mixed_stt.py        # Speech-to-text engine
    ├── enhanced_hindi_tts.py # High-quality Hindi TTS
    ├── mixed_tts.py        # Mixed language TTS
    ├── language_detector.py # Language detection
    ├── sip_client.py       # SIP client (optional)
    ├── sip_voice_bot.py    # SIP voice bot (optional)
    ├── twilio_client.py    # Twilio integration
    ├── voice_bot.py        # Local voice bot
    └── tools/
        └── list_devices.py # Audio device listing
```

## ⚙️ Configuration Options

### Audio Settings
```env
SAMPLE_RATE=16000           # Audio sample rate
CHANNELS=1                  # Audio channels
RECORD_SECONDS=7.0          # Recording duration
WHISPER_MODEL_SIZE=base     # Whisper model (tiny/small/base/medium/large)
```

### Language Settings
```env
LANGUAGE=en                 # Default language
AUTO_DETECT_LANGUAGE=true   # Enable auto-detection
DEFAULT_LANGUAGE=en         # Fallback language
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

### For Custom Voice (ElevenLabs)
1. Create a voice at [ElevenLabs](https://elevenlabs.io)
2. Add to `.env`:
   ```env
   ELEVENLABS_API_KEY=your_key
   ELEVENLABS_VOICE_ID=your_voice_id
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

**"Language detection wrong"**
- System learns from conversation context
- Try speaking more clearly
- Mixed language is detected as intended behavior

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

**Made with ❤️ for the Hindi and English speaking community**

For support or questions, please open an issue on GitHub.