@echo off
title sombra
cd /d "%~dp0"
:inicio
python sombra.py
echo sombra se detuvo. Reinicio en 15 segundos (cierra esta ventana para detenerlo del todo)...
timeout /t 15
goto inicio
