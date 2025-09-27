# 🚀 Real-time Voice Conversation Setup

Your AI Calling Bot now supports **real-time conversation** with interruption handling, similar to ChatGPT's voice mode!

## ✨ New Features

- **⚡ Real-time Voice Interaction**: Bot responds immediately while you speak
- **🛑 Interruption Handling**: You can interrupt the bot mid-sentence
- **🎯 Voice Activity Detection**: Smart detection of when you're speaking
- **🔄 Full-duplex Communication**: Simultaneous listening and speaking
- **🌐 Mixed Language Support**: Hindi, English, and Hinglish in real-time

## 🛠️ Installation

### 1. Install New Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `webrtcvad==2.0.10` - Voice Activity Detection
- `librosa==0.10.1` - Audio processing
- `websockets==12.0` - Real-time communication
- `pyaudio==0.2.14` - Audio streaming

### 2. Test Local Real-time Mode

Run the bot locally to test real-time conversation:

```bash
python -m src.realtime_voice_bot
```

**What to expect:**
- 🎤 The bot will start listening continuously
- 💬 Speak naturally in Hindi or English
- 🛑 Try interrupting the bot while it's speaking
- ⚡ Notice the immediate responses

## 📞 Using Real-time Phone Calls

### Option 1: Through Main Menu

1. Run the main bot:
   ```bash
   python main.py
   ```

2. Choose option **3** (⚡ Call with real-time mode)

3. Enter the phone number and make the call

### Option 2: Direct Real-time Endpoint

Your bot now has a new endpoint: `/voice_realtime`

Update your Twilio webhook to use this endpoint for automatic real-time mode.

## 🎯 How It Works

### Traditional Mode (Old)
```
User speaks → [Wait for silence] → STT → GPT → TTS → Bot responds
```

### Real-time Mode (New)
```
User speaks ──┐
              ├─ Continuous VAD → STT → GPT → TTS ──┐
Bot speaks  ──┘                                    └─ Can be interrupted
```

### Key Improvements

1. **Voice Activity Detection (VAD)**
   - Continuously monitors audio for speech
   - Detects when user starts speaking
   - Immediately stops bot when interruption detected

2. **Interruption Handling**
   - Bot stops speaking when user interrupts
   - Clears pending responses to avoid confusion
   - Immediately starts listening to new input

3. **Full-duplex Audio**
   - Bot can listen while speaking
   - Real-time audio processing in 100ms chunks
   - Low-latency response generation

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file for optimal performance:

```env
# Real-time conversation settings
SAMPLE_RATE=16000          # Optimal for VAD
VAD_AGGRESSIVENESS=2       # 0-3, higher = more sensitive
REALTIME_CHUNK_SIZE=0.1    # Audio chunk duration in seconds
INTERRUPT_THRESHOLD=0.3    # Speech confidence for interruption
```

### Audio Quality Settings

For best results:
```env
# Use higher quality Whisper model for real-time
WHISPER_MODEL_SIZE=base    # or 'small' for faster processing

# Enhanced TTS for better quality
AZURE_SPEECH_KEY=your_key  # For best Hindi quality
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

## 🎤 Testing Guide

### 1. Local Testing

```bash
python -m src.realtime_voice_bot
```

**Test scenarios:**
- Say "Hello" and wait for response
- Say "नमस्ते" (Hindi greeting)
- Try interrupting mid-response
- Mix languages: "Hello नमस्ते, how are you?"

### 2. Phone Testing

1. Make a real-time call to your own number
2. Test natural conversation flow
3. Try interrupting the bot
4. Test language switching

### 3. VAD Testing

```bash
python -c "from src.realtime_vad import test_vad; test_vad()"
```

## 🐛 Troubleshooting

### Common Issues

**"VAD not available"**
```bash
pip install webrtcvad
```

**"Audio device error"**
- Check microphone permissions
- Run: `python -m src.tools.list_devices`
- Update `DEVICE_INDEX_IN` in config

**"Real-time mode not available"**
- Check if all dependencies are installed
- Look for import errors in console

**"Bot doesn't stop when interrupted"**
- Adjust `VAD_AGGRESSIVENESS` (try 3)
- Check audio input levels
- Test with `python -m src.realtime_vad`

### Performance Optimization

**For faster responses:**
```env
WHISPER_MODEL_SIZE=tiny    # Fastest, lower accuracy
SAMPLE_RATE=16000          # Optimal balance
```

**For better accuracy:**
```env
WHISPER_MODEL_SIZE=base    # Better accuracy
AZURE_SPEECH_KEY=your_key  # Better TTS quality
```

## 📊 Performance Metrics

### Expected Latency
- **Voice Activity Detection**: < 100ms
- **Speech Recognition**: 200-500ms
- **AI Response Generation**: 300-800ms
- **Text-to-Speech**: 200-400ms
- **Total Response Time**: 700-1700ms

### System Requirements
- **RAM**: 2GB+ (for Whisper model)
- **CPU**: Multi-core recommended
- **Network**: Stable internet for AI APIs
- **Audio**: Working microphone and speakers

## 🎯 Advanced Usage

### Custom VAD Settings

```python
from src.realtime_vad import VoiceActivityDetector

# Create custom VAD
vad = VoiceActivityDetector(
    aggressiveness=3,      # More sensitive
    sample_rate=16000
)
```

### Custom Interruption Handling

```python
from src.realtime_voice_bot import RealtimeVoiceBot

bot = RealtimeVoiceBot()
bot.conversation_manager.on_interruption = my_custom_handler
```

## 🌟 What's Next?

Your bot now supports:
- ✅ Real-time conversation
- ✅ Interruption handling
- ✅ Voice activity detection
- ✅ Mixed language support

**Future enhancements could include:**
- OpenAI Realtime API integration
- WebRTC for better audio quality
- Multi-speaker detection
- Emotion recognition
- Custom wake words

---

**🎉 Congratulations!** Your AI Calling Bot now behaves like a real conversational AI with natural interruption handling!
