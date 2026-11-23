@echo off
title minero
cd /d "%~dp0"
:inicio
python minero.py
echo minero se detuvo. Reinicio en 15 segundos (cierra esta ventana para detenerlo del todo)...
timeout /t 15
goto inicio
