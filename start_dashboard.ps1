# Sara Dashboard Starter
# This script starts MongoDB, seeds the database, and launches the dashboard

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "     SARA DASHBOARD STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if MongoDB is running
Write-Host "1. Checking MongoDB..." -ForegroundColor Yellow
$mongoProcess = Get-Process -Name mongod -ErrorAction SilentlyContinue

if ($null -eq $mongoProcess) {
    Write-Host "   ❌ MongoDB is not running!" -ForegroundColor Red
    Write-Host "   Please start MongoDB first:" -ForegroundColor Yellow
    Write-Host "   - Open Command Prompt as Administrator" -ForegroundColor White
    Write-Host "   - Run: net start MongoDB" -ForegroundColor White
    Write-Host "   OR run: mongod" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Start dashboard anyway? (y/n)"
    if ($continue -ne "y") {
        exit
    }
} else {
    Write-Host "   ✅ MongoDB is running" -ForegroundColor Green
}

# Navigate to backend directory
Write-Host "`n2. Navigating to backend directory..." -ForegroundColor Yellow
Set-Location -Path "sara-dashboard\backend"

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "   ⚠️  node_modules not found. Installing dependencies..." -ForegroundColor Yellow
    npm install
}

# Seed the database
Write-Host "`n3. Seeding database (creating admin user)..." -ForegroundColor Yellow
node scripts\seed.js

# Start the backend server
Write-Host "`n4. Starting backend server on port 5000..." -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to stop`n" -ForegroundColor Gray

$env:NODE_ENV="development"
npm start

