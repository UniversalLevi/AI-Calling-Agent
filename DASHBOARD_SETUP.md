# Dashboard Setup Guide 🎯

## The Issue

You have **two servers** that need to run:
1. **Flask Calling Bot** - Port 8000 (Python) ✅ Working
2. **Dashboard Backend** - Port 5000 (Node.js) ❌ Not running

The frontend is trying to connect to port 5000 for dashboard APIs and getting 404s.

---

## Quick Fix

### Terminal 1: Start Dashboard Backend

```bash
cd sara-dashboard/backend
npm install
npm start
```

This should start the Node.js backend on port 5000.

### Terminal 2: Start Dashboard Frontend

```bash
cd sara-dashboard/frontend  
npm start
```

This runs on port 3000.

### Terminal 3: Start Flask Calling Bot

```bash
python main.py
```

This runs on port 8000.

---

## If Dashboard Backend Won't Start

### Check MongoDB

The dashboard backend needs MongoDB running:

**Windows:**
```powershell
# Check if MongoDB is running
Get-Service -Name MongoDB

# Start MongoDB if stopped
net start MongoDB
```

**Or use MongoDB Atlas** (cloud):
1. Create free account at mongodb.com/cloud/atlas
2. Get connection string
3. Update `.env` in `sara-dashboard/backend/.env`:
```
MONGODB_URI=your_atlas_connection_string
```

### Check Port 5000

If something else is using port 5000:

**Option A: Change Dashboard Backend Port**

Edit `sara-dashboard/backend/.env`:
```
PORT=3001
```

Then update frontend: Create `sara-dashboard/frontend/.env`:
```
REACT_APP_API_URL=http://localhost:3001
REACT_APP_SOCKET_URL=http://localhost:3001
```

**Option B: Free up port 5000**

```powershell
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F
```

---

## Proper Startup Order

1. **MongoDB** (if using local)
   ```bash
   net start MongoDB
   ```

2. **Dashboard Backend** (Terminal 1)
   ```bash
   cd sara-dashboard/backend
   npm start
   ```
   
   Should see:
   ```
   ✅ MongoDB connected
   🚀 Dashboard backend running on port 5000
   ```

3. **Dashboard Frontend** (Terminal 2)
   ```bash
   cd sara-dashboard/frontend
   npm start
   ```
   
   Opens http://localhost:3000

4. **Flask Calling Bot** (Terminal 3)
   ```bash
   python main.py
   ```
   
   Runs on port 8000

---

## Testing Dashboard Connection

Once all services are running:

1. Open http://localhost:3000
2. Login with admin@sara.ai / admin123
3. You should see:
   - No 404 errors in console
   - Dashboard loads
   - WebSocket connects (green status)
   - System health updates every 30s

---

## Common Errors & Fixes

### Error: `ECONNREFUSED ::1:27017`

**Problem**: MongoDB not running

**Fix**:
```bash
net start MongoDB
```

### Error: `Port 5000 already in use`

**Problem**: Something else on port 5000

**Fix**: Use Option A or B above

### Error: `Cannot find module 'bcrypt'`

**Problem**: Missing Node.js dependencies

**Fix**:
```bash
cd sara-dashboard/backend
npm install
```

### Error: Frontend still shows 404s

**Problem**: Backend not fully started

**Fix**:
1. Stop frontend (Ctrl+C)
2. Ensure backend is fully running (see "MongoDB connected" message)
3. Restart frontend

---

## Using `start_sara.py` (Alternative)

The `start_sara.py` script should handle this, but it may need updating for the new port:

```bash
python start_sara.py
```

If it doesn't work, use the manual method above.

---

## Expected URLs

| Service | URL | Status |
|---------|-----|--------|
| Dashboard Frontend | http://localhost:3000 | ✅ |
| Dashboard Backend API | http://localhost:5000 | Should be ✅ |
| Flask Calling Bot | http://localhost:8000 | ✅ |
| Ngrok Webhook | https://xxx.ngrok-free.app | ✅ |

---

## Verifying Backend is Running

Test the dashboard backend manually:

```bash
# Health check
curl http://localhost:5000/health

# Should return:
# {"status":"ok","mongodb":"connected"}
```

If this works, the backend is running correctly!

---

## Next Steps

1. Start all three services as shown above
2. Check console for any remaining errors
3. Dashboard should load with no 404s
4. Make a test call - it should appear in dashboard

**Need help?** Check the logs in:
- Dashboard backend: Terminal 1 output
- Dashboard frontend: Browser console (F12)
- Flask bot: Terminal 3 output

