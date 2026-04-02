@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "API_PROJECT=%SCRIPT_DIR%src\SimuladorClinico.Api\SimuladorClinico.Api.csproj"

for /f "tokens=5" %%P in ('netstat -aon ^| findstr ":5070 .*LISTENING"') do (
    taskkill /PID %%P /F >nul 2>&1
)

if not exist "%API_PROJECT%" (
    echo [ERRO] Projeto da API nao encontrado em:
    echo %API_PROJECT%
    exit /b 1
)

echo Iniciando backend...
dotnet run --project "%API_PROJECT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERRO] O backend terminou com codigo %EXIT_CODE%.
)

exit /b %EXIT_CODE%
