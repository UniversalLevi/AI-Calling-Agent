# SARA Deployment Guide - VPS with Apache & PM2

This guide covers deploying SARA on a Ubuntu VPS with Apache as a reverse proxy and PM2 for process management.

## Prerequisites

- Ubuntu 20.04+ VPS with root access
- Domain name pointing to your VPS IP
- At least 2GB RAM, 2 CPU cores
- SSL certificate (Let's Encrypt recommended)

## Table of Contents

1. [Server Setup](#1-server-setup)
2. [Install Dependencies](#2-install-dependencies)
3. [Clone and Configure](#3-clone-and-configure)
4. [MongoDB Setup](#4-mongodb-setup)
5. [PM2 Process Management](#5-pm2-process-management)
6. [Apache Reverse Proxy](#6-apache-reverse-proxy)
7. [SSL with Let's Encrypt](#7-ssl-with-lets-encrypt)
8. [Twilio Webhook Configuration](#8-twilio-webhook-configuration)
9. [Maintenance & Monitoring](#9-maintenance--monitoring)

---

## 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Create application user
sudo adduser sara
sudo usermod -aG sudo sara

# Switch to sara user
su - sara
```

## 2. Install Dependencies

### Node.js (v18+)
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
node --version  # Should be 18.x+
```

### Python 3.12
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev python3-pip -y

# Set as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
```

### PM2
```bash
sudo npm install -g pm2
```

### Apache
```bash
sudo apt install apache2 -y
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers ssl
sudo systemctl enable apache2
```

### MongoDB
```bash
# Import MongoDB GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# Add repository
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
   sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Install
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl start mongod
sudo systemctl enable mongod
```

## 3. Clone and Configure

### Clone Repository
```bash
cd /home/sara
git clone https://github.com/UniversalLevi/AI-Calling-Agent.git sara-agent
cd sara-agent
```

### Python Environment
```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Dashboard Backend
```bash
cd sara-dashboard/backend
npm install --production
```

### Dashboard Frontend (Build for Production)
```bash
cd ../frontend
npm install
npm run build
```

### Environment Files

#### Python Bot (.env in root)
```bash
cat > /home/sara/sara-agent/.env << 'EOF'
# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX

# OpenAI
OPENAI_API_KEY=sk-your_api_key

# WhatsApp
WHATSAPP_API_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_NUMBER=+91XXXXXXXXXX
ENABLE_WHATSAPP=true

# Razorpay
RAZORPAY_KEY_ID=rzp_your_key_id
RAZORPAY_KEY_SECRET=your_key_secret

# Dashboard API
DASHBOARD_API_URL=http://localhost:5000/api

# Production
FLASK_ENV=production
EOF
```

#### Dashboard Backend (.env)
```bash
cat > /home/sara/sara-agent/sara-dashboard/backend/.env << 'EOF'
PORT=5000
MONGODB_URI=mongodb://localhost:27017/sara_dashboard
JWT_SECRET=your_super_secret_jwt_key_change_this
NODE_ENV=production
FRONTEND_URL=https://yourdomain.com
SOCKET_CORS_ORIGIN=https://yourdomain.com
EOF
```

#### Dashboard Frontend (.env)
```bash
cat > /home/sara/sara-agent/sara-dashboard/frontend/.env << 'EOF'
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_SOCKET_URL=https://yourdomain.com
EOF

# Rebuild frontend with production URLs
cd /home/sara/sara-agent/sara-dashboard/frontend
npm run build
```

## 4. MongoDB Setup

### Create Database User
```bash
mongosh

use sara_dashboard

db.createUser({
  user: "sara_user",
  pwd: "your_secure_password",
  roles: [{ role: "readWrite", db: "sara_dashboard" }]
})

exit
```

Update `.env` with authenticated URI:
```
MONGODB_URI=mongodb://sara_user:your_secure_password@localhost:27017/sara_dashboard
```

### Seed Initial Data
```bash
cd /home/sara/sara-agent/sara-dashboard/backend
node scripts/seed.js
```

## 5. PM2 Process Management

### Create PM2 Ecosystem File
```bash
cat > /home/sara/sara-agent/ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'sara-voice-bot',
      script: 'main.py',
      interpreter: '/home/sara/sara-agent/venv/bin/python',
      cwd: '/home/sara/sara-agent',
      env: {
        FLASK_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      log_file: '/home/sara/sara-agent/logs/voice-bot.log',
      error_file: '/home/sara/sara-agent/logs/voice-bot-error.log',
      out_file: '/home/sara/sara-agent/logs/voice-bot-out.log'
    },
    {
      name: 'sara-dashboard-api',
      script: 'server.js',
      cwd: '/home/sara/sara-agent/sara-dashboard/backend',
      env: {
        NODE_ENV: 'production',
        PORT: 5000
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      log_file: '/home/sara/sara-agent/logs/dashboard-api.log',
      error_file: '/home/sara/sara-agent/logs/dashboard-api-error.log',
      out_file: '/home/sara/sara-agent/logs/dashboard-api-out.log'
    }
  ]
};
EOF
```

### Create Logs Directory
```bash
mkdir -p /home/sara/sara-agent/logs
```

### Start Services
```bash
cd /home/sara/sara-agent
pm2 start ecosystem.config.js

# Check status
pm2 status

# View logs
pm2 logs

# Save PM2 process list (auto-restart on reboot)
pm2 save

# Setup PM2 startup script
pm2 startup systemd -u sara --hp /home/sara
# Run the command it outputs as root
```

### PM2 Commands Reference
```bash
pm2 list                    # List all processes
pm2 logs                    # View all logs
pm2 logs sara-voice-bot     # View specific logs
pm2 restart all             # Restart all processes
pm2 restart sara-voice-bot  # Restart specific process
pm2 stop all                # Stop all
pm2 delete all              # Remove all processes
pm2 monit                   # Real-time monitoring
```

## 6. Apache Reverse Proxy

### Create Apache Config
```bash
sudo nano /etc/apache2/sites-available/sara.conf
```

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    
    # Redirect HTTP to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</VirtualHost>

<VirtualHost *:443>
    ServerName yourdomain.com
    ServerAlias www.yourdomain.com
    
    # SSL Configuration (Let's Encrypt will add this)
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/yourdomain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/yourdomain.com/privkey.pem
    
    # Security Headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    
    # React Frontend (Static Files)
    DocumentRoot /home/sara/sara-agent/sara-dashboard/frontend/build
    
    <Directory /home/sara/sara-agent/sara-dashboard/frontend/build>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
        
        # React Router - serve index.html for all routes
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteCond %{REQUEST_URI} !^/api
        RewriteCond %{REQUEST_URI} !^/voice
        RewriteCond %{REQUEST_URI} !^/socket.io
        RewriteRule . /index.html [L]
    </Directory>
    
    # Dashboard API Proxy
    ProxyPreserveHost On
    ProxyPass /api http://localhost:5000/api
    ProxyPassReverse /api http://localhost:5000/api
    
    # Socket.io Proxy (WebSocket support)
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/socket.io/(.*) ws://localhost:5000/socket.io/$1 [P,L]
    
    ProxyPass /socket.io http://localhost:5000/socket.io
    ProxyPassReverse /socket.io http://localhost:5000/socket.io
    
    # Voice Bot Proxy (Twilio Webhooks)
    ProxyPass /voice http://localhost:8080/voice
    ProxyPassReverse /voice http://localhost:8080/voice
    
    ProxyPass /process_speech http://localhost:8080/process_speech
    ProxyPassReverse /process_speech http://localhost:8080/process_speech
    
    ProxyPass /process_speech_realtime http://localhost:8080/process_speech_realtime
    ProxyPassReverse /process_speech_realtime http://localhost:8080/process_speech_realtime
    
    ProxyPass /status http://localhost:8080/status
    ProxyPassReverse /status http://localhost:8080/status
    
    ProxyPass /audio http://localhost:8081/audio
    ProxyPassReverse /audio http://localhost:8081/audio
    
    # Logging
    ErrorLog ${APACHE_LOG_DIR}/sara-error.log
    CustomLog ${APACHE_LOG_DIR}/sara-access.log combined
</VirtualHost>
```

### Enable Site
```bash
sudo a2ensite sara.conf
sudo a2dissite 000-default.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

## 7. SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-apache -y

# Get SSL Certificate
sudo certbot --apache -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically
# Test renewal:
sudo certbot renew --dry-run
```

## 8. Twilio Webhook Configuration

In your Twilio Console:

1. Go to **Phone Numbers** → **Manage** → **Active numbers**
2. Select your phone number
3. Under **Voice & Fax**, set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://yourdomain.com/voice?realtime=true`
   - **HTTP Method**: POST
4. Under **Call Status Changes**:
   - **URL**: `https://yourdomain.com/status`
5. Save

## 9. Maintenance & Monitoring

### Check Service Status
```bash
# PM2 processes
pm2 status

# Apache
sudo systemctl status apache2

# MongoDB
sudo systemctl status mongod
```

### View Logs
```bash
# Voice bot logs
pm2 logs sara-voice-bot --lines 100

# Dashboard API logs
pm2 logs sara-dashboard-api --lines 100

# Apache logs
sudo tail -f /var/log/apache2/sara-error.log
sudo tail -f /var/log/apache2/sara-access.log
```

### Restart Services
```bash
# Restart all PM2 processes
pm2 restart all

# Restart Apache
sudo systemctl restart apache2

# Restart MongoDB
sudo systemctl restart mongod
```

### Update Application
```bash
cd /home/sara/sara-agent

# Pull latest code
git pull origin main

# Activate Python venv
source venv/bin/activate

# Update Python dependencies
pip install -r requirements.txt

# Update backend dependencies
cd sara-dashboard/backend
npm install --production

# Rebuild frontend
cd ../frontend
npm install
npm run build

# Restart services
pm2 restart all
```

### Backup MongoDB
```bash
# Create backup
mongodump --db sara_dashboard --out /home/sara/backups/$(date +%Y%m%d)

# Restore backup
mongorestore --db sara_dashboard /home/sara/backups/YYYYMMDD/sara_dashboard
```

### Firewall Configuration
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## Quick Reference

### URLs After Deployment

| Service | URL |
|---------|-----|
| Dashboard | https://yourdomain.com |
| Dashboard API | https://yourdomain.com/api |
| Voice Webhook | https://yourdomain.com/voice |
| Status Webhook | https://yourdomain.com/status |

### Default Ports (Internal)

| Service | Port |
|---------|------|
| Voice Bot (Flask) | 8080 |
| Audio Server | 8081 |
| Dashboard API (Node) | 5000 |
| MongoDB | 27017 |

### PM2 Quick Commands

```bash
pm2 status          # Check status
pm2 logs            # View all logs
pm2 restart all     # Restart everything
pm2 monit           # Real-time monitor
```

---

## Troubleshooting

### Voice Bot Not Responding
1. Check PM2 status: `pm2 status`
2. Check logs: `pm2 logs sara-voice-bot`
3. Verify Twilio webhook URL is correct
4. Test webhook: `curl -X POST https://yourdomain.com/voice`

### Dashboard Not Loading
1. Check Apache is running: `sudo systemctl status apache2`
2. Check frontend build exists: `ls -la sara-dashboard/frontend/build`
3. Check API is responding: `curl http://localhost:5000/api/health`
4. Check Apache error log: `sudo tail -f /var/log/apache2/sara-error.log`

### MongoDB Connection Failed
1. Check MongoDB is running: `sudo systemctl status mongod`
2. Verify connection string in `.env`
3. Test connection: `mongosh "mongodb://localhost:27017/sara_dashboard"`

### WebSocket Not Working
1. Ensure Apache WebSocket modules are enabled: `sudo a2enmod proxy_wstunnel`
2. Check browser console for WebSocket errors
3. Verify CORS settings in dashboard backend `.env`


