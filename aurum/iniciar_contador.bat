@echo off
title contador
cd /d "%~dp0"
:inicio
python contador.py
echo contador se detuvo. Reinicio en 15 segundos (cierra esta ventana para detenerlo del todo)...
timeout /t 15
goto inicio
