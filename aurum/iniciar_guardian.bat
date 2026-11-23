@echo off
title guardian
cd /d "%~dp0"
:inicio
python guardian.py
echo guardian se detuvo. Reinicio en 15 segundos (cierra esta ventana para detenerlo del todo)...
timeout /t 15
goto inicio
