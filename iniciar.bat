@echo off
chcp 65001 >nul
title Cotabot - robo de cotacao
cd /d "%~dp0"

echo ==========================================
echo   COTABOT - robo de cotacao (Magazine Luiza)
echo ==========================================
echo.

where claude >nul 2>nul
if errorlevel 1 (
    echo ERRO: Claude Code nao encontrado. Instale em https://claude.com/claude-code
    pause
    exit /b 1
)

rem Usa a conta Claude logada no Claude Code (o Chrome so conecta com ela, nao com chave de API)
set "ANTHROPIC_API_KEY="
set "ANTHROPIC_CUSTOM_HEADERS="

rem ---- Ambiente Python (so na primeira vez) ----
if not exist ".venv\Scripts\python.exe" (
    echo Preparando ambiente Python pela primeira vez...
    python -m venv .venv || (echo ERRO: Python nao encontrado. & pause & exit /b 1)
    ".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
)

if not exist "resultados" mkdir resultados
if not exist "words" mkdir words
del /q "resultados\*.json" 2>nul

rem ---- Texto dos itens ----
echo Cole a descricao do item e aperte Enter.
echo Pode colar varios itens, um por linha.
echo Quando terminar, aperte Enter numa linha vazia.
echo.
powershell -NoProfile -Command "$itens=@(); while(($l=Read-Host 'Item') -ne ''){ $itens+=$l.Trim() }; if($itens.Count -eq 0){ exit 1 }; [IO.File]::WriteAllLines((Join-Path (Get-Location) 'entrada.txt'), $itens, (New-Object Text.UTF8Encoding $false))"
if errorlevel 1 (
    echo Nenhum item informado. Saindo.
    pause
    exit /b 1
)

echo.
echo Deixe o Chrome aberto com a extensao Claude ativa.
echo O robo vai abrir uma aba propria. Nao feche essa aba.
echo.

claude "Leia o arquivo instrucoes_robo.md e execute a cotacao de todos os itens de entrada.txt seguindo exatamente essas instrucoes." --chrome --model sonnet --allowedTools "mcp__claude-in-chrome" "Read" "Write" "Bash(.venv\Scripts\python.exe gerar_word.py)" "PowerShell(.venv\Scripts\python.exe gerar_word.py)"

echo.
echo Words gerados na pasta: %~dp0words
start "" "%~dp0words"
pause
