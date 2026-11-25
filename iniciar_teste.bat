@echo off
chcp 65001 >nul
title Cotabot - teste local
cd /d "%~dp0"

where claude >nul 2>nul
if errorlevel 1 (
    echo ERRO: Claude Code nao encontrado. Instale em https://claude.com/claude-code
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    echo Preparando ambiente Python pela primeira vez...
    python -m venv .venv || (echo ERRO: Python nao encontrado. & pause & exit /b 1)
)
".venv\Scripts\python.exe" -c "import openpyxl, PIL" 2>nul || ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt

echo O robo usa o Microsoft Edge com a extensao Claude ativa e logada no claude.ai.
echo A pagina de teste vai abrir no Edge. Feche esta janela para parar o robo.
echo.
".venv\Scripts\python.exe" cotabot_local.py --abrir-pagina
pause
