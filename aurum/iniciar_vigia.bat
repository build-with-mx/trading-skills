@echo off
title vigia
cd /d "%~dp0"
:inicio
python vigia.py
echo vigia se detuvo. Reinicio en 15 segundos (cierra esta ventana para detenerlo del todo)...
timeout /t 15
goto inicio
