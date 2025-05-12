@echo off
echo =====================================
echo   Iniciar Servidor pelo VS Code
echo =====================================
echo.

REM Verifica se o Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado! Instale o Python 3.7+ e tente novamente.
    echo.
    pause
    exit /b
)

REM Instala ou atualiza a biblioteca iqoptionapi antes de iniciar
echo Verificando/Atualizando biblioteca IQOptionAPI...
python -m pip install -U git+https://github.com/iqoptionapi/iqoptionapi.git

REM Vai para a pasta backend e inicia o servidor
cd backend
echo Iniciando o servidor no diretório: %cd%
echo.
echo Para conectar com a interface, abra o arquivo:
echo frontend/index.html
echo.
echo Iniciando o servidor com modo de debug...
echo.
set PYTHONPATH=%PYTHONPATH%;..
python bot.py --debug --auto-update-pairs

pause
