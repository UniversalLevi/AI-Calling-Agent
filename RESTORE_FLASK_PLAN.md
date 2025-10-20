# Flask System Restoration Plan

## Current Status
- Reverted to commit: `b3846795eb4ea5d4bfe7197921141507d9a60402`
- Created new branch: `restore-flask-system`
- This is the Flask-based system before FastAPI migration

## What This System Has
✅ Flask voice bot server (working)
✅ Twilio Media Streams integration
✅ Real-time interruption (ultra_simple_interruption.py, simple_interruption.py)
✅ Mixed language support (Hindi + English)
✅ OpenAI GPT-4o-mini AI brain
✅ Enhanced Hindi TTS with multiple providers
✅ WebSocket-based interruption
✅ Dashboard integration
✅ Sales AI features

## Known Issues to Fix

### 1. Call Processing
- Need to ensure single processing per user input
- Buffer management to prevent duplicate processing
- Proper audio buffer clearing

### 2. Interruption System
- Verify ultra_simple_interruption.py works correctly
- Check simple_interruption.py integration
- Ensure WebSocket interruption is functional

### 3. Dashboard Integration
- Call logging (start/end)
- Proper payload formatting
- MongoDB connection

### 4. TTS Voice Quality
- Voice selection settings
- Language detection
- Natural-sounding responses

## Files to Check/Fix

### Core System Files
- `main.py` - Main Flask application
- `src/ultra_simple_interruption.py` - Primary interruption handler
- `src/simple_interruption.py` - Secondary interruption handler
- `src/twilio_media_streams.py` - Media streams handling
- `src/realtime_voice_bot.py` - Real-time voice conversation
- `src/websocket_interruption.py` - WebSocket-based interruption

### AI & TTS
- `src/mixed_ai_brain.py` - AI conversation handler
- `src/enhanced_hindi_tts.py` - TTS with multiple providers
- `src/mixed_stt.py` - Speech-to-text

### Dashboard
- `src/dashboard_integration.py` - Dashboard API calls
- Dashboard backend (sara-dashboard/backend/)

## Next Steps

1. **Test Current System**
   ```powershell
   python main.py
   ```
   - Make a test call
   - Note any errors
   - Check what's working vs broken

2. **Fix Identified Issues**
   - Start with most critical (duplicate processing)
   - Then interruption
   - Then dashboard logging
   - Finally voice quality

3. **Commit Fixes**
   ```powershell
   git add .
   git commit -m "fix: [description]"
   git push origin restore-flask-system
   ```

4. **Merge to Main When Stable**
   ```powershell
   git checkout main
   git merge restore-flask-system
   git push origin main
   ```

## How to Test

### Basic Call Test
1. Start system: `python main.py`
2. Choose option 1 (Make Smart Call)
3. Enter phone number
4. Test:
   - Say something once → Should respond once
   - Interrupt the bot → Bot should stop
   - Say "bye" → Call should end
   - Check dashboard for call log

### Features to Verify
- ✓ Single response per user input
- ✓ Interruption works
- ✓ Call termination on "bye"
- ✓ Hindi/English detection
- ✓ Dashboard call logs
- ✓ Natural voice quality

## Important Notes
- This system uses Flask, not FastAPI
- Uses Twilio Media Streams for real-time audio
- Has multiple interruption methods (ultra_simple, simple, websocket)
- Dashboard integration via REST APIs
- OpenAI-only TTS (other providers were removed in this commit)

## If Issues Persist
Document the specific error messages and behavior, then we'll fix them one by one in this Flask system.

