@echo off
title explorador
cd /d "%~dp0"
:inicio
python explorador.py
echo explorador se detuvo. Reinicio en 15 segundos (cierra esta ventana para detenerlo del todo)...
timeout /t 15
goto inicio
