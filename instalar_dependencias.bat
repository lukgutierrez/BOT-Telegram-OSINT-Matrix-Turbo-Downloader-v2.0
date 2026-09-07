@echo off
title INSTALADOR DE REQUISITOS (@lukgtz)
color 0E
chcp 65001 > nul
cls
echo ========================================================
echo   INSTALADOR DE DEPENDENCIAS - TELEGRAM OSINT MATRIX
echo   Creado por: @lukgtz (Luciano Gutierrez - Salta, Arg)
echo ========================================================
echo.
echo [1/4] Verificando instalacion de Python...
python --version
if errorlevel 1 (
    echo.
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Descarga e instala Python 3.10+ desde https://www.python.org/downloads/
    pause
    exit /b
)
echo.
echo [2/4] Creando entorno virtual (venv)...
if not exist venv (
    python -m venv venv
    echo Entorno virtual 'venv' creado con exito.
) else (
    echo El entorno virtual 'venv' ya existe.
)
echo.
echo [3/4] Instalando librerias desde requirements.txt...
call .\venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo [4/4] Verificando archivo de configuracion .env...
if not exist .env (
    copy .env.example .env
    echo.
    echo [AVISO] Se creo el archivo '.env' a partir de '.env.example'.
    echo Por favor abre '.env' y coloca tus claves de https://my.telegram.org
) else (
    echo El archivo '.env' ya esta configurado.
)
echo.
echo ========================================================
echo   INSTALACION COMPLETADA CON EXITO
echo   Ahora puedes hacer doble clic en 'iniciar_web.bat'
echo ========================================================
pause
