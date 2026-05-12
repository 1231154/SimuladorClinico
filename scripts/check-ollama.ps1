<#
Check Ollama local setup:
- Verifica se o comando `ollama` está disponível
- Verifica se o modelo configurado está presente (ollama list)
- Tenta uma chamada HTTP simples ao endpoint local para garantir que responde
#>
param(
    [string]$ModelName = $null,
    [string]$HostUrl = $null,
    [int]$TimeoutSec = 10
)

if (-not $ModelName) { $ModelName = $env:OLLAMA_MODEL; if (-not $ModelName) { $ModelName = "mistral:latest" } }
if (-not $HostUrl) { $HostUrl = $env:OLLAMA_HOST; if (-not $HostUrl) { $HostUrl = "http://localhost:11434" } }

function Write-Err($msg) { Write-Host $msg -ForegroundColor Red }
function Write-Ok($msg) { Write-Host $msg -ForegroundColor Green }

Write-Host "Verificando ambiente Ollama..."

# Check if ollama command exists
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Err "Comando 'ollama' não encontrado no PATH. Por favor instala o Ollama: https://ollama.com/docs/installation"
    exit 2
}
Write-Ok "Comando 'ollama' encontrado."

# Check model present via ollama list
Write-Host "Verificando se o modelo '$ModelName' está disponível localmente (ollama list)..."
try {
    $list = & ollama list 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Err "Falha a executar 'ollama list':`n$list"
    }
    else {
        if ($list -match [regex]::Escape($ModelName)) {
            Write-Ok "Modelo '$ModelName' encontrado localmente."
        }
        else {
            Write-Host "Modelo '$ModelName' NÃO encontrado localmente." -ForegroundColor Yellow
            Write-Host "Executa './scripts/bootstrap-dev.ps1 -ModelName $ModelName' para fazer o pull do modelo." -ForegroundColor Cyan
        }
    }
}
catch {
    Write-Err "Erro a correr 'ollama list': $_"
}

# Test HTTP endpoint
Write-Host "Testando endpoint HTTP em $HostUrl (timeout ${TimeoutSec}s)..."
$testBody = @{ model = $ModelName; prompt = "Test"; max_tokens = 16 } | ConvertTo-Json
try {
    $resp = Invoke-RestMethod -Uri "$HostUrl/api/generate" -Method Post -Body $testBody -ContentType "application/json" -ErrorAction Stop
    Write-Ok "Endpoint HTTP respondeu."
}
catch {
    Write-Host "Não foi possível contactar o endpoint HTTP em $Host." -ForegroundColor Yellow
    Write-Host "Isto pode ser normal se o Ollama não estiver a expor a API HTTP no host/porta definidos." -ForegroundColor Yellow
    Write-Host "Tenta: ollama run $ModelName ou verifica a documentação do Ollama para expor a API local." -ForegroundColor Cyan
}

Write-Host "Check concluído."


