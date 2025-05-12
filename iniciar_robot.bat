@echo off
echo =======================================
echo    Robô Trader IQ Option - Launcher
echo =======================================
echo.

REM Verifica se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado! Por favor, instale o Python 3.7 ou superior.
    echo        Visite: https://www.python.org/downloads/
    echo.
    pause
    exit /b
)

REM Instala as dependências necessárias
echo Verificando e instalando dependências...
python install_dependencies.py

REM Verifica se a pasta backend existe
if not exist "backend" (
    echo [ERRO] Pasta "backend" não encontrada!
    echo        Verifique se você está executando este script no diretório correto.
    echo.
    pause
    exit /b
)

REM Inicia o servidor backend
echo.
echo Iniciando o servidor backend...
echo.
echo [IMPORTANTE] Mantenha esta janela aberta enquanto o robô estiver em execução.
echo              Para parar o robô, pressione CTRL+C ou feche esta janela.
echo.
echo Conectando...
echo.

cd backend
python bot.py

pause
