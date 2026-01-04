@echo off
setlocal enabledelayedexpansion

REM SARA Deployment Script for Windows
REM Usage: deploy.bat [setup|start|stop|restart|logs|status|update]

echo ======================================
echo    SARA AI Calling Agent Deployer
echo ======================================

if not exist logs mkdir logs

if "%1"=="" goto usage
if "%1"=="setup" goto setup
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="status" goto status
if "%1"=="update" goto update
if "%1"=="monit" goto monit
goto usage

:setup
echo [Setup] Setting up SARA...

echo [Setup] Creating Python virtual environment...
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo [Setup] Installing backend dependencies...
cd sara-dashboard\backend
call npm install --production

echo [Setup] Building frontend...
cd ..\frontend
call npm install
call npm run build

cd ..\..
echo [SUCCESS] Setup complete!
echo.
echo Next steps:
echo 1. Configure your .env files
echo 2. Run: deploy.bat start
goto end

:start
echo [Start] Starting SARA services...
call pm2 start ecosystem.config.js
call pm2 save
echo [SUCCESS] Services started!
call pm2 status
goto end

:stop
echo [Stop] Stopping SARA services...
call pm2 stop all
echo [SUCCESS] Services stopped!
goto end

:restart
echo [Restart] Restarting SARA services...
call pm2 restart all
echo [SUCCESS] Services restarted!
call pm2 status
goto end

:logs
if "%2"=="" (
    call pm2 logs
) else (
    call pm2 logs %2
)
goto end

:status
echo [Status] Service Status:
call pm2 status
goto end

:update
echo [Update] Updating SARA...
git pull origin main

call venv\Scripts\activate.bat
pip install -r requirements.txt

cd sara-dashboard\backend
call npm install --production

cd ..\frontend
call npm install
call npm run build

cd ..\..
call pm2 restart all
echo [SUCCESS] Update complete!
goto end

:monit
call pm2 monit
goto end

:usage
echo Usage: deploy.bat {setup^|start^|stop^|restart^|logs^|status^|update^|monit}
echo.
echo Commands:
echo   setup    - Initial setup (install dependencies, build frontend)
echo   start    - Start all services with PM2
echo   stop     - Stop all services
echo   restart  - Restart all services
echo   logs     - View logs (optional: logs ^<app-name^>)
echo   status   - Show service status
echo   update   - Pull latest code and restart
echo   monit    - Open PM2 real-time monitor
goto end

:end
endlocal


