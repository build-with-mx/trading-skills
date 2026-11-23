@echo off
title aurum
cd /d "%~dp0"
:inicio
python aurum.py
echo aurum se detuvo. Reinicio en 15 segundos (cierra esta ventana para detenerlo del todo)...
timeout /t 15
goto inicio
