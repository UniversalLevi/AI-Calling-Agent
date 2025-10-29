# 🔧 Auto-Dependency Management System

## ✨ What's New?

Sara now has **automatic dependency checking and installation**! No more manual `pip install` commands. Just run and go! 🚀

---

## 🎯 How It Works

### **1. Dependency Checker (`dependency_checker.py`)**

This is the core module that:
- ✅ Checks if all required Python packages are installed
- ✅ Auto-installs missing packages
- ✅ Verifies critical imports work
- ✅ Shows clear progress and status
- ✅ Handles errors gracefully

### **2. Integrated into `main.py`**

When you run `python main.py`, it:
1. Checks dependencies first (silent mode)
2. Installs missing packages automatically
3. Continues even if some fail (with warning)
4. Then starts the bot normally

### **3. Integrated into `start_sara.py`**

When you run `python start_sara.py`, it:
1. Checks dependencies with full output
2. Installs missing packages automatically
3. Only continues if all succeed
4. Then starts the dashboard

---

## 🚀 Usage

### **Option 1: Just Run It (Recommended)**

```bash
# For calling bot
python main.py
# Dependencies auto-checked and installed!

# For dashboard + bot
python start_sara.py
# Dependencies auto-checked and installed!
```

### **Option 2: Manual Check**

```bash
# Check dependencies explicitly
python dependency_checker.py

# Output:
# ✅ All required dependencies are installed!
# 🎉 System is ready to run!
```

### **Option 3: Traditional Install**

```bash
# Still works if you prefer manual control
pip install -r requirements.txt
```

---

## 📦 What Gets Checked & Installed

### **Required Packages** (auto-installed if missing)
- ✅ python-dotenv, openai, flask, requests, twilio
- ✅ numpy, sounddevice, soundfile, pygame, pyaudio, wave
- ✅ faster-whisper, gtts, google-generativeai
- ✅ httpx, httpcore, psutil
- ✅ webrtcvad, librosa, websockets
- ✅ indic-transliteration, regex

### **Optional Packages** (informational only)
- ⚪ asyncio-mqtt, pjsua2, threading-timer

### **Critical Import Verification**
- Flask app initialization
- OpenAI client
- Twilio client
- Faster Whisper model
- NumPy arrays
- Requests library

---

## 🛡️ Safety Features

### **Non-Destructive**
- Never removes or downgrades existing packages
- Only installs missing packages
- Uses exact versions from `requirements.txt`

### **Error Handling**
- Continues if optional packages fail
- Shows clear error messages
- Suggests manual installation if needed
- Never crashes the application

### **Timeout Protection**
- 2-minute timeout per package
- Prevents hanging on slow networks
- Graceful failure handling

---

## 📊 Output Examples

### **All Dependencies Present**
```
🔧 Checking system dependencies...
✅ All required dependencies are installed!
✅ Environment variables loaded from .env file
```

### **Missing Dependencies**
```
🔧 Checking system dependencies...

🔍 Checking dependencies...
✅ python-dotenv
❌ openai - MISSING
✅ flask
...

📦 Installing 1 missing package(s)...
   Installing openai...
   ✅ openai installed successfully

✅ All required dependencies are installed!
```

### **Failed Installation**
```
❌ Some dependencies failed to install.
   Attempting to continue anyway...
   You may encounter errors. Consider running: pip install -r requirements.txt
```

---

## 🔧 Troubleshooting

### **"Package failed to install"**

**Cause**: Network issue, missing system dependencies, or permission error

**Fix**:
```bash
# Try manual install
pip install <package-name>

# Or install all
pip install -r requirements.txt

# Check for system dependencies (PyAudio)
# Windows: Install Microsoft C++ Build Tools
# macOS: brew install portaudio
# Linux: sudo apt-get install portaudio19-dev
```

### **"Critical import failed"**

**Cause**: Package installed but not working (corrupted, version mismatch)

**Fix**:
```bash
# Reinstall the problematic package
pip uninstall <package-name>
pip install <package-name>

# Or reinstall all
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

### **"Dependency checker not found"**

**Cause**: `dependency_checker.py` is missing or not in the same directory

**Fix**:
```bash
# Download from GitHub
git pull origin integration-stage

# Or run without checker
# Both main.py and start_sara.py will continue without it
```

### **PyAudio Installation Fails**

**Windows**:
1. Install Microsoft C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Or download pre-built wheel: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
3. Install with: `pip install pyaudio-0.2.14-cp312-cp312-win_amd64.whl`

**macOS**:
```bash
brew install portaudio
pip install pyaudio
```

**Linux**:
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

---

## 🎯 Advanced Usage

### **Programmatic Usage**

```python
from dependency_checker import run_full_check

# Run with auto-install
success = run_full_check(auto_install=True, verbose=True)
if not success:
    print("Dependencies missing!")

# Check only (no install)
success = run_full_check(auto_install=False, verbose=True)

# Silent check
success = run_full_check(auto_install=True, verbose=False)
```

### **Check Specific Package**

```python
from dependency_checker import check_package_installed

if check_package_installed('openai'):
    print("OpenAI is installed")
else:
    print("OpenAI is missing")
```

### **Install Specific Package**

```python
from dependency_checker import install_package

success = install_package('openai==1.51.2', 'OpenAI API')
if success:
    print("Installed successfully")
```

---

## 📈 Benefits

### **For Users**
1. ✅ **Zero Configuration** - Just run and it works
2. ✅ **No Manual Steps** - No need to remember pip commands
3. ✅ **Clear Feedback** - Know exactly what's happening
4. ✅ **Error Recovery** - Automatic retry and fallback

### **For Developers**
1. ✅ **Consistent Environment** - Everyone has same packages
2. ✅ **Version Control** - Exact versions from requirements.txt
3. ✅ **Quick Onboarding** - New devs can start immediately
4. ✅ **CI/CD Ready** - Works in automated environments

---

## 🔄 Update Process

### **When New Dependencies Are Added**

1. Update `requirements.txt` with new package
2. Update `REQUIRED_PACKAGES` dict in `dependency_checker.py`
3. Commit and push
4. Users automatically get new dependencies on next run!

**Example**:
```python
# In dependency_checker.py
REQUIRED_PACKAGES = {
    # ... existing packages ...
    'newpackage': 'newpackage==1.0.0',  # Add new package here
}
```

---

## 📝 Files Modified

| File | Changes |
|------|---------|
| `dependency_checker.py` | ✅ **NEW** - Core dependency checking module |
| `main.py` | ✅ Added auto-check at startup (silent mode) |
| `start_sara.py` | ✅ Added auto-check at startup (verbose mode) |
| `requirements.txt` | ✅ Comprehensive documentation and categorization |
| `README.md` | ✅ Complete rewrite with current features |

---

## 🎉 Summary

### **What You Get**
- 🚀 **Automatic dependency management**
- 🛡️ **Safe and non-destructive**
- 📊 **Clear progress indicators**
- 🔧 **Manual override available**
- ✅ **Works on all platforms**

### **What You Don't Need Anymore**
- ❌ Manual `pip install` commands
- ❌ Remembering package names
- ❌ Debugging missing dependencies
- ❌ Version mismatch issues

---

## 💡 Best Practices

### **For Users**
1. ✅ Run `python main.py` or `python start_sara.py` - it auto-checks
2. ✅ If errors occur, check the output for specific package failures
3. ✅ Keep `requirements.txt` and `dependency_checker.py` in sync with Git

### **For Developers**
1. ✅ Test with fresh virtual environment to verify auto-install works
2. ✅ Update both `requirements.txt` AND `dependency_checker.py` when adding packages
3. ✅ Document any system dependencies (like portaudio for PyAudio)

---

## 🔗 Related Documentation

- **README.md** - Main project documentation
- **requirements.txt** - Python dependencies with installation notes
- **env.example** - Environment variable template
- **INTEGRATION_LOG.md** - Development history

---

## 📞 Support

If dependency checking fails:

1. Check output for specific error
2. Try manual install: `pip install -r requirements.txt`
3. Check system dependencies (especially PyAudio)
4. Open an issue on GitHub with error message

---

**Made with ❤️ to make Sara easier to use!**

✅ No more dependency headaches!
✅ Just run and go!
✅ It just works! 🎉

