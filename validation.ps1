# Validation Script for Integration Safety
# Run this before merging any feature branch

Write-Host "Running pre-merge validation..." -ForegroundColor Cyan

# Check Python imports
Write-Host "Checking Python imports..." -ForegroundColor Yellow
python -c 'import sys; sys.path.append(\"src\"); from enhanced_hindi_tts import EnhancedHindiTTS'
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python import check failed!" -ForegroundColor Red
    exit 1
}

# Check TTS file hash
Write-Host "Checking TTS file integrity..." -ForegroundColor Yellow
$TTS_HASH = git hash-object src/enhanced_hindi_tts.py
Write-Host "Current TTS hash: $TTS_HASH" -ForegroundColor Green

# Check syntax errors
Write-Host "Checking for Python syntax errors..." -ForegroundColor Yellow
$pythonFiles = Get-ChildItem -Path "src" -Filter "*.py" -File
foreach ($file in $pythonFiles) {
    python -m py_compile $file.FullName 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Syntax error in $($file.Name)" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Validation passed!" -ForegroundColor Green
