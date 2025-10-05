# 🚀 SARA AI CALLING BOT WITH DASHBOARD - QUICK START GUIDE

## 📋 ONE-COMMAND START

Simply run the following command to start both the calling bot and the dashboard:

```bash
python start_sara.py
```

This will start:
- ✅ Sara Dashboard (Frontend + Backend)
- ✅ Sara AI Calling Bot

## 🌐 Access Points

### Dashboard
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Login Credentials**: 
  - Username: `admin`
  - Password: `admin123`

### Calling Bot
- Running from `main.py`
- All calling bot features available

## 📝 Log Files

All logs are written to separate files for easy monitoring:

- **Dashboard logs**: `dashboard.log`
- **Calling Bot logs**: `calling_bot.log`

You can monitor logs in real-time:

```bash
# Watch dashboard logs
tail -f dashboard.log

# Watch calling bot logs
tail -f calling_bot.log
```

## ⚙️ Prerequisites

### Required:
1. **Python 3.8+** - Already installed (for calling bot)
2. **Node.js 16+** - Required for dashboard
   - Download from: https://nodejs.org/

### Optional:
- **MongoDB** (local or Atlas) - For dashboard database
  - If not installed, dashboard will have limited functionality

## 📦 First Time Setup

Before running for the first time, install dependencies:

### 1. Dashboard Dependencies

```bash
cd sara-dashboard

# Install root dependencies
npm install

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install

cd ../..
```

### 2. Configure Environment

Create `.env` files:

**Backend (.env in `sara-dashboard/backend/`):**
```env
MONGO_URI=mongodb://localhost:27017/sara-dashboard
JWT_SECRET=your-super-secret-jwt-key
PORT=5000
FRONTEND_URL=http://localhost:3000
```

**Frontend (.env in `sara-dashboard/frontend/`):**
```env
REACT_APP_SOCKET_URL=http://localhost:5000
REACT_APP_API_URL=http://localhost:5000/api
```

## 🛑 Stopping Services

Press `Ctrl+C` to stop all services gracefully.

The script will automatically clean up all processes.

## 🔧 Troubleshooting

### Node.js Not Found
```bash
# Install Node.js from: https://nodejs.org/
# Restart terminal after installation
```

### Port Already in Use
If ports 3000 or 5000 are busy:

1. Stop the conflicting service
2. Or change ports in environment files

### MongoDB Connection Error
```bash
# Option 1: Install MongoDB locally
# Download from: https://www.mongodb.com/try/download/community

# Option 2: Use MongoDB Atlas (cloud)
# Sign up at: https://www.mongodb.com/cloud/atlas
# Update MONGO_URI in backend/.env
```

### Dependencies Not Installed
```bash
cd sara-dashboard

# Reinstall all dependencies
npm install
cd backend && npm install
cd ../frontend && npm install
```

## 📊 Dashboard Features

Once logged in, you'll have access to:

- **📞 Live Calls** - Monitor active calls in real-time
- **📚 Call Logs** - View historical call data
- **📈 Analytics** - Performance metrics and statistics
- **⚙️ Settings** - System configuration
- **👥 Users** - User management (admin only)

## 🤖 Calling Bot Features

All existing calling bot features remain available:
- Hinglish/English support
- Real-time interruption
- Smart call handling
- AI-powered conversations

## 📈 Monitoring

### View Real-time Logs

**PowerShell:**
```powershell
Get-Content dashboard.log -Wait
Get-Content calling_bot.log -Wait
```

**Command Prompt:**
```cmd
type dashboard.log
type calling_bot.log
```

### Check Service Status

The launcher script will automatically monitor both services and alert you if either stops unexpectedly.

## 🎯 What's Running

When you start the system, the following services are launched:

1. **Dashboard Backend** (Port 5000)
   - Express.js API server
   - MongoDB connection
   - Socket.io for real-time updates

2. **Dashboard Frontend** (Port 3000)
   - React application
   - Real-time dashboard
   - Admin interface

3. **Calling Bot**
   - Main AI calling bot
   - Twilio integration
   - All calling features

## 🔄 Restarting Services

To restart everything:

1. Press `Ctrl+C` to stop
2. Run `python start_sara.py` again

## 📞 Support

If you encounter any issues:

1. Check the log files for error messages
2. Ensure all prerequisites are installed
3. Verify environment configuration
4. Check that required ports are available

---

**Built with ❤️ for Sara AI Calling Bot**  
**Single command. Full system. Ready to go! 🚀**

