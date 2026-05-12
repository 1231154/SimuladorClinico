# Start Python AI Service
# This script starts the FastAPI-based AI service with LangChain

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "SimuladorClinico - Python AI Service" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$pythonDir = Join-Path $rootDir "python"

# Check Python installation
Write-Host "[*] Checking Python installation..." -ForegroundColor Yellow
$pythonRoot = Join-Path $env:LOCALAPPDATA "Programs\Python"
$preferredFolders = @(
    (Join-Path $pythonRoot "Python312"),
    (Join-Path $pythonRoot "Python313"),
    (Join-Path $pythonRoot "Python314")
)

$pythonExe = $null
foreach ($folderPath in $preferredFolders) {
    $candidate = Join-Path $folderPath "python.exe"
    if (Test-Path $candidate) {
        $pythonExe = $candidate
        Write-Host "[OK] Found Python in: $folderPath" -ForegroundColor Green
        break
    }
}

if (-not $pythonExe) {
    $pythonFolders = Get-ChildItem $pythonRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^Python\d+' } | Sort-Object Name -Descending
    foreach ($folder in $pythonFolders) {
        $candidate = Join-Path $folder.FullName "python.exe"
        if (Test-Path $candidate) {
            $pythonExe = $candidate
            Write-Host "[OK] Found Python in: $($folder.FullName)" -ForegroundColor Green
            break
        }
    }
}

if (-not $pythonExe) {
    Write-Host "[!] Python not found. Please install Python 3.10+" -ForegroundColor Red
    exit 1
}

$pythonVersion = & $pythonExe --version 2>&1
Write-Host "[OK] Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment if not exists
$venvPath = Join-Path $pythonDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[*] Creating Python virtual environment..." -ForegroundColor Yellow
    & $pythonExe -m venv $venvPath
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[*] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path (Join-Path $venvPath "Scripts") "Activate.ps1"
& $activateScript

# Install requirements
Write-Host "[*] Checking and installing dependencies..." -ForegroundColor Yellow
$requirementsFile = Join-Path $pythonDir "requirements.txt"
if (Test-Path $requirementsFile) {
    & $pythonExe -m pip install -q -r $requirementsFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "[!] Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[!] requirements.txt not found" -ForegroundColor Red
    exit 1
}

# Check Ollama availability
Write-Host "[*] Checking Ollama availability..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "[OK] Ollama is running" -ForegroundColor Green
} catch {
    Write-Host "[!] Warning: Ollama is not responding on localhost:11434" -ForegroundColor Yellow
    Write-Host "[!] Make sure Ollama is running: ollama run mistral:latest" -ForegroundColor Yellow
}

# Start the service
Write-Host ""
Write-Host "[*] Starting Python AI Service on port 5555..." -ForegroundColor Yellow
Write-Host "[*] API docs available at http://localhost:5555/docs" -ForegroundColor Cyan
Write-Host "[*] Press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host ""

Push-Location $pythonDir
& $pythonExe main.py
Pop-Location

Write-Host ""
Write-Host "[!] Python AI Service stopped" -ForegroundColor Yellow






