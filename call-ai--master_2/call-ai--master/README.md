## AI Calling Bot – Phase 1 + Phase 2 (Windows-friendly)

This project implements a local voice bot pipeline (STT → GPT → TTS) and provides Asterisk + softphone configs for a no-cost call simulation environment.

### What you get
- Mic → Speech-to-Text (offline via Faster-Whisper)
- Bot brain via OpenAI Chat API
- Text-to-Speech via gTTS → playback via FFmpeg
- Asterisk configs for a fake-call lab with Zoiper/Linphone

### Prerequisites (Windows 10/11)
1) Install Python 3.10+
2) Install FFmpeg and add to PATH
   - Download build and add `bin` to PATH. Verify: `ffmpeg -version`.
3) Install PortAudio runtime (for mic I/O)
   - Easiest: install `sounddevice` wheels via pip; PortAudio is bundled for Windows.
4) (Optional) Git

### Setup
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` in project root:
```
OPENAI_API_KEY=sk-...
```

List input/output audio devices (optional):
```bash
python -m src.tools.list_devices
```

Run the voice bot:
```bash
python -m src.voice_bot
```

Interaction model: press Enter to start a turn, speak for up to ~5 seconds, wait for bot reply.

### Configuration
Edit `src/config.py` to tweak:
- `RECORD_SECONDS` (default 5)
- `LANGUAGE` (e.g., `en`)
- `DEVICE_INDEX_IN` and `DEVICE_INDEX_OUT` if you need specific devices

### Notes on Models
- STT: `faster-whisper` uses the `base` model by default (CPU okay). Change in `src/stt.py`.
- LLM: OpenAI `gpt-4o-mini` by default; you can change the model in `src/gpt_brain.py`.
- TTS: gTTS requires internet. For offline TTS, see Coqui TTS section below.

### Troubleshooting
- If no audio: ensure microphone permissions are enabled and correct input device index is set.
- If playback fails: confirm FFmpeg is installed and in PATH.
- If STT is slow: switch to `tiny`/`small` models in `src/stt.py`.
- If OpenAI errors: verify `OPENAI_API_KEY` in `.env`.

### Optional: Offline TTS (Coqui)
Install: `pip install TTS` then set `USE_COQUI_TTS=True` in `src/config.py`. The first run downloads a model.

---

## Phase 2 – Fake Call Environment (Asterisk + Softphone)

Goal: simulate calls with zero telco cost.

### 1) Install a Softphone
- Zoiper or Linphone on your PC. You will register it to Asterisk as `1002` in the sample config.

### 2) Asterisk Setup (local or VPS)
- Install Asterisk (Debian/Ubuntu: `sudo apt install asterisk`) or use a prebuilt image.
- Copy the sample configs from `asterisk/` into your Asterisk: `/etc/asterisk/`.
  - Backup originals first.

Files provided:
- `asterisk/sip.conf` – two local SIP peers: `1001` (bot), `1002` (softphone)
- `asterisk/extensions.conf` – dialplan to route calls between peers and to a bot hook

Reload Asterisk after changes:
```bash
sudo asterisk -rx "sip reload" && sudo asterisk -rx "dialplan reload"
```

Register softphone to Asterisk server IP as `1002` with the password in `sip.conf`.

### 3) Bot Integration Options
You have two common options to connect the bot audio to Asterisk:
- RTP/SIP media bridge using an Asterisk ARI/AGI app that pipes audio to the local bot (custom dev)
- Use a small media gateway (e.g., `baresip` or `pjsua`) that dials extension `1001` and forwards audio to the bot process via stdin/stdout or local UDP

This repo includes an outline script and comments in `asterisk/README.md` describing approaches. For production, consider ARI with a media handler that streams raw audio to the STT loop.

---

## Scripts
- `src/voice_bot.py` – main loop (press Enter → speak → bot responds)
- `src/stt.py` – Faster-Whisper wrapper
- `src/gpt_brain.py` – OpenAI chat
- `src/tts.py` – gTTS and optional Coqui
- `src/tools/list_devices.py` – enumerate audio devices

---

## License
MIT


