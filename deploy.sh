#!/bin/bash

# SARA Deployment Script
# Usage: ./deploy.sh [setup|start|stop|restart|logs|status|update]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_DIR/logs"

echo -e "${BLUE}══════════════════════════════════════════${NC}"
echo -e "${BLUE}       SARA AI Calling Agent Deployer      ${NC}"
echo -e "${BLUE}══════════════════════════════════════════${NC}"

# Ensure logs directory exists
mkdir -p "$LOGS_DIR"

case "$1" in
    setup)
        echo -e "${YELLOW}🔧 Setting up SARA...${NC}"
        
        # Python setup
        echo -e "${BLUE}📦 Setting up Python environment...${NC}"
        if [ ! -d "venv" ]; then
            python3 -m venv venv
        fi
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        
        # Backend setup
        echo -e "${BLUE}📦 Installing backend dependencies...${NC}"
        cd "$PROJECT_DIR/sara-dashboard/backend"
        npm install --production
        
        # Frontend setup
        echo -e "${BLUE}📦 Building frontend...${NC}"
        cd "$PROJECT_DIR/sara-dashboard/frontend"
        npm install
        npm run build
        
        echo -e "${GREEN}✅ Setup complete!${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo "1. Configure your .env files"
        echo "2. Run: ./deploy.sh start"
        ;;
        
    start)
        echo -e "${YELLOW}🚀 Starting SARA services...${NC}"
        cd "$PROJECT_DIR"
        pm2 start ecosystem.config.js
        pm2 save
        echo -e "${GREEN}✅ Services started!${NC}"
        pm2 status
        ;;
        
    stop)
        echo -e "${YELLOW}🛑 Stopping SARA services...${NC}"
        pm2 stop all
        echo -e "${GREEN}✅ Services stopped!${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}🔄 Restarting SARA services...${NC}"
        pm2 restart all
        echo -e "${GREEN}✅ Services restarted!${NC}"
        pm2 status
        ;;
        
    logs)
        if [ -z "$2" ]; then
            pm2 logs
        else
            pm2 logs "$2"
        fi
        ;;
        
    status)
        echo -e "${BLUE}📊 Service Status:${NC}"
        pm2 status
        echo ""
        echo -e "${BLUE}📈 Process Details:${NC}"
        pm2 describe sara-voice-bot | head -30
        ;;
        
    update)
        echo -e "${YELLOW}📥 Updating SARA...${NC}"
        
        # Pull latest code
        git pull origin main
        
        # Update Python dependencies
        source venv/bin/activate
        pip install -r requirements.txt
        
        # Update backend
        cd "$PROJECT_DIR/sara-dashboard/backend"
        npm install --production
        
        # Rebuild frontend
        cd "$PROJECT_DIR/sara-dashboard/frontend"
        npm install
        npm run build
        
        # Restart services
        cd "$PROJECT_DIR"
        pm2 restart all
        
        echo -e "${GREEN}✅ Update complete!${NC}"
        ;;
        
    monit)
        pm2 monit
        ;;
        
    *)
        echo -e "${YELLOW}Usage:${NC} ./deploy.sh {setup|start|stop|restart|logs|status|update|monit}"
        echo ""
        echo "Commands:"
        echo "  setup    - Initial setup (install dependencies, build frontend)"
        echo "  start    - Start all services with PM2"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - View logs (optional: logs <app-name>)"
        echo "  status   - Show service status"
        echo "  update   - Pull latest code and restart"
        echo "  monit    - Open PM2 real-time monitor"
        exit 1
        ;;
esac

