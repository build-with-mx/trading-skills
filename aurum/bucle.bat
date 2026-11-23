@echo off
REM Ejecuta un bot y lo reinicia si se cae. Uso: bucle.bat script.py [argumentos]
cd /d "%~dp0"
:loop
python %*
echo %1 se detuvo. Reinicio en 15 s...
timeout /t 15 /nobreak >nul
goto loop
