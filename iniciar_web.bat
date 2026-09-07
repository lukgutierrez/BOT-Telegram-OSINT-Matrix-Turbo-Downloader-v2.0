@echo off
title TELEGRAM OSINT MATRIX - CONSOLA WEB (@lukgtz)
color 0A
chcp 65001 > nul
cls
echo ========================================================
echo   TELEGRAM OSINT RECON MATRIX - CONSOLA WEB
echo   Creado por: @lukgtz (Luciano Gutierrez - Salta, Arg)
echo ========================================================
echo.
echo [INFO] Iniciando servidor t?ctico Streamlit...
echo [INFO] Se abrir? tu navegador en http://localhost:8501
echo.
python -m streamlit run app_web.py
pause
