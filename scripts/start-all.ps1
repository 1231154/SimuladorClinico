# Script para iniciar Backend (.NET), Frontend (React/Vite), Python AI Service e Ollama simultaneamente
# Uso: ./scripts/start-all.ps1

$rootPath = Split-Path -Parent $PSScriptRoot
$apiPath = Join-Path $rootPath "src\SimuladorClinico.Api"
$webPath = Join-Path $rootPath "src\SimuladorClinico.Web"
$pythonDir = Join-Path $rootPath "python"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Iniciador Completo - SimuladorClinico" -ForegroundColor Cyan
Write-Host "  Ollama + Python AI + Backend + Frontend" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Ollama esta instalado
Write-Host "[1/4] Verificando Ollama..." -ForegroundColor Yellow
try {
    $ollamaExists = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollamaExists) {
        Write-Host "[!] Ollama nao encontrado! Instale de: https://ollama.com/download" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Ollama encontrado" -ForegroundColor Green
} catch {
    Write-Host "[!] Erro ao verificar Ollama: $_" -ForegroundColor Red
    exit 1
}

# Verificar se Python esta instalado
Write-Host "[2/4] Verificando Python..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue

if (-not $pythonCmd) {
    # Procurar Python em localizacao do Microsoft Store
    $msStorePythonPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python"
    $pythonDirs = Get-ChildItem $msStorePythonPath -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "Python\d+" } | Sort-Object Name -Descending

    if ($pythonDirs.Count -gt 0) {
        $pythonFolder = $pythonDirs[0]
        $pythonExe = Join-Path $pythonFolder.FullName "python.exe"

        if (Test-Path $pythonExe) {
            Write-Host "[OK] Python encontrado em: $($pythonFolder.FullName)" -ForegroundColor Green
            # Adicionar ao PATH da sessao atual
            $env:PATH = "$($pythonFolder.FullName);$($pythonFolder.FullName)\Scripts;$env:PATH"
        } else {
            Write-Host "[!] Python nao encontrado! Instale de https://www.python.org/downloads/" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[!] Python nao encontrado! Instale de https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[OK] Python encontrado" -ForegroundColor Green
}

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
        break
    }
}

if (-not $pythonExe) {
    $pythonFolders = Get-ChildItem $pythonRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^Python\d+' } | Sort-Object Name -Descending
    foreach ($folder in $pythonFolders) {
        $candidate = Join-Path $folder.FullName "python.exe"
        if (Test-Path $candidate) {
            $pythonExe = $candidate
            break
        }
    }
}

if (-not $pythonExe) {
    Write-Host "[!] Nao foi possivel localizar python.exe instalado" -ForegroundColor Red
    exit 1
}

# Verificar se o modelo Mistral esta disponivel
Write-Host "[3/4] Verificando modelo Mistral..." -ForegroundColor Yellow
$modelList = ollama list 2>$null | Out-String
if ($modelList -notlike "*mistral*") {
    Write-Host "[!] Modelo Mistral nao encontrado. A fazer pull..." -ForegroundColor Yellow
    ollama pull mistral:latest
} else {
    Write-Host "[OK] Modelo Mistral disponivel" -ForegroundColor Green
}

Write-Host ""
Write-Host "Iniciando servicos..." -ForegroundColor Cyan
Write-Host ""

# 1. Iniciar Ollama em nova janela
Write-Host "[->] Abrindo Ollama em nova janela..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "ollama serve" -WindowStyle Normal

# Aguardar um pouco para Ollama iniciar
Start-Sleep -Seconds 3

# 2. Iniciar Python AI Service em nova janela
Write-Host "[->] Abrindo Python AI Service em nova janela..." -ForegroundColor Yellow
$pythonCommand = @"
`$env:PATH = '$($env:PATH)'
Set-Location '$pythonDir'
if (-not (Test-Path 'venv')) {
    Write-Host 'Criando ambiente virtual Python...' -ForegroundColor Yellow
    & '$pythonExe' -m venv venv
}
& '.\venv\Scripts\Activate.ps1'
if (-not (Test-Path 'venv\Lib\site-packages\fastapi')) {
    Write-Host 'Instalando dependencias Python...' -ForegroundColor Yellow
    & '$pythonExe' -m pip install -q -r requirements.txt
}
Write-Host 'Iniciando Python AI Service em http://localhost:5555...' -ForegroundColor Green
& '$pythonExe' main.py
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $pythonCommand -WindowStyle Normal

# Aguardar um pouco para Python iniciar
Start-Sleep -Seconds 5

# 3. Iniciar API .NET em nova janela
Write-Host "[->] Abrindo Backend (.NET API) em nova janela..." -ForegroundColor Yellow
$apiCommand = @"
Set-Location '$apiPath'
Write-Host 'Iniciando API em http://localhost:5070...' -ForegroundColor Green
dotnet run --configuration Debug
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiCommand -WindowStyle Normal

# Aguardar um pouco para a API iniciar
Start-Sleep -Seconds 4

# 4. Iniciar Frontend em nova janela
Write-Host "[->] Abrindo Frontend (React/Vite) em nova janela..." -ForegroundColor Yellow
$webCommand = @"
Set-Location '$webPath'
if (-not (Test-Path 'node_modules')) {
    Write-Host 'Instalando dependencias npm...' -ForegroundColor Yellow
    npm install
}
Write-Host 'Iniciando Vite Dev Server em http://localhost:5173...' -ForegroundColor Green
npm run dev
"@
Start-Process powershell -ArgumentList "-NoExit", "-Command", $webCommand -WindowStyle Normal

Write-Host ""
Write-Host "[OK] Todos os servicos foram iniciados!" -ForegroundColor Green
Write-Host ""
Write-Host "Enderecos:" -ForegroundColor Cyan
Write-Host "  Frontend:      http://localhost:5173" -ForegroundColor Green
Write-Host "  Backend:       http://localhost:5070" -ForegroundColor Green
Write-Host "  Python AI:     http://localhost:5555" -ForegroundColor Green
Write-Host "  Ollama:        http://localhost:11434" -ForegroundColor Green
Write-Host ""
Write-Host "Dicas:" -ForegroundColor Cyan
Write-Host "  * Abriram 4 janelas PowerShell separadas" -ForegroundColor Gray
Write-Host "  * Fechar qualquer janela para parar esse servico" -ForegroundColor Gray
Write-Host "  * Aguarde 15-20 segundos ate tudo estar pronto" -ForegroundColor Gray
Write-Host "  * API Python Docs: http://localhost:5555/docs" -ForegroundColor Gray
Write-Host ""










