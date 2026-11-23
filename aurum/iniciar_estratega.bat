@echo off
cd /d "%~dp0"
:loop
python estratega_metas.py
echo Estratega de metas se detuvo. Reinicio en 15 s...
timeout /t 15 /nobreak >nul
goto loop
