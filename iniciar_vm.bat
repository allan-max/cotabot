@echo off
chcp 65001 >nul
title Cotabot - VM (Maestro)
cd /d "%~dp0"

rem Cotabot na VM: o gerenciador do Maestro chama a API pela rede (gerenciador\ponte_cotabot.py).
rem Precisa no .env desta pasta:
rem     COTABOT_HOST=0.0.0.0
rem     COTABOT_TOKEN=<o mesmo COTABOT_TOKEN do .env do gerenciador, 32+ caracteres>

where claude >nul 2>nul
if errorlevel 1 (
    echo ERRO: Claude Code nao encontrado. Instale e rode "claude" uma vez para logar na conta.
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Preparando ambiente Python pela primeira vez...
    python -m venv .venv || (echo ERRO: Python nao encontrado. & pause & exit /b 1)
)
".venv\Scripts\python.exe" -c "import openpyxl, PIL" 2>nul || ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt

echo Abrindo o Microsoft Edge (a extensao Claude precisa estar ativa e logada no claude.ai).
start "" msedge about:blank
echo Feche esta janela para parar o Cotabot.
echo.
".venv\Scripts\python.exe" cotabot_local.py
pause
