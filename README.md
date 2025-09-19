# 🚀 AI Calling Bot (Prototype)

## Setup

1. Install dependencies
   ```bash
   sudo apt install ffmpeg
   pip install -r requirements.txt
   ```

2. Export OpenAI key
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

3. Run Flask bot
   ```bash
   python bot_server.py
   ```

4. Configure Asterisk:
   - Copy `asterisk/extensions.conf` into your Asterisk config.
   - Copy `asterisk_post.sh` into `/usr/local/bin/` and `chmod +x`.

5. Test with softphone by dialing `100`.

---

Customer speech → Whisper (STT) → GPT → gTTS → Asterisk Playback
