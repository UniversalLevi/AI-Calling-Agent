# 🚀 SARA SYSTEM - COMPLETE SETUP & RUNNING GUIDE

## ✅ FIXED ISSUES

All errors have been fixed:
- ✅ Corrected import paths in Layout component
- ✅ Removed missing Tailwind CSS plugins
- ✅ Updated launcher to properly start dashboard only
- ✅ Calling bot runs separately (as it requires user interaction)

## 📦 FIRST TIME SETUP

Run these commands **ONCE** before first use:

```powershell
# Navigate to dashboard
cd "C:\Users\deepa\Desktop\Extra's\Calling_Agent\sara-dashboard"

# Install root dependencies
npm install

# Install backend dependencies
cd backend
npm install

# Install frontend dependencies
cd ../frontend
npm install

# Go back to main directory
cd ../..
```

## 🚀 RUNNING THE SYSTEM

### **Option 1: Quick Start (Dashboard Only)**

```powershell
python start_sara.py
```

This starts:
- ✅ Dashboard Frontend (http://localhost:3000)
- ✅ Dashboard Backend (http://localhost:5000)

### **Option 2: Run Calling Bot Separately**

In a **separate terminal**:

```powershell
python main.py
```

Then select your calling bot options as usual.

### **Option 3: Run Everything Together**

**Terminal 1** - Dashboard:
```powershell
python start_sara.py
```

**Terminal 2** - Calling Bot:
```powershell
python main.py
```

## 🌐 ACCESS POINTS

### Dashboard
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Login**: 
  - Username: `admin`
  - Password: `admin123`

### Calling Bot
- Run from `main.py` in separate terminal
- All existing features available

## 📝 LOG FILES

- `dashboard.log` - Dashboard logs (backend + frontend)
- Check terminal output for real-time status

## 🛑 STOPPING

- **Dashboard**: Press `Ctrl+C` in the terminal running `start_sara.py`
- **Calling Bot**: Press `Ctrl+C` in the terminal running `main.py`

## 🎯 WHAT'S INCLUDED

### Sara Dashboard
- ✅ Real-time call monitoring
- ✅ User management
- ✅ System analytics
- ✅ Configuration management
- ✅ Live updates via Socket.io

### Sara Calling Bot
- ✅ Hinglish/English support
- ✅ Real-time interruption
- ✅ Smart AI conversations
- ✅ All existing features

## 🔧 TROUBLESHOOTING

### Frontend Compilation Errors
```powershell
cd sara-dashboard/frontend
npm install
npm start
```

### Backend Errors
```powershell
cd sara-dashboard/backend
npm install
npm run dev
```

### Port Already in Use
- Stop other services using ports 3000 or 5000
- Or change ports in environment files

### Dependencies Missing
Run the setup commands again (see First Time Setup)

## 💡 TIPS

1. **First run takes longer** - React needs to compile
2. **Keep terminals open** - Don't close the terminal windows
3. **Check logs** - If something fails, check `dashboard.log`
4. **Separate terminals** - Run calling bot in separate terminal for better control

## 📚 DOCUMENTATION

- **Dashboard Guide**: `sara-dashboard/docs/DEVELOPMENT_GUIDE.md`
- **Project Summary**: `sara-dashboard/PROJECT_SUMMARY.md`
- **Quick Start**: `QUICK_START.md`

---

**Ready to use! Just run `python start_sara.py` and access http://localhost:3000 🎉**

