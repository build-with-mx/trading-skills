@echo off
REM Uso: iniciar_fondeo.bat copiador_fondeo1.json  (abre Supervisor de fondeo, Estratega y Copiador de esa cuenta)
cd /d "%~dp0"
set CFG=%1
if "%CFG%"=="" set CFG=copiador_fondeo1.json
if not exist "%CFG%" (echo Falta %CFG%. Copia copiador_ejemplo.json y rellenalo. & pause & exit /b)
start "Supervisor %CFG%" cmd /k bucle.bat supervisor_fondeo.py %CFG%
timeout /t 5 /nobreak >nul
start "Estratega %CFG%" cmd /k bucle.bat estratega_metas.py %CFG%
start "Copiador %CFG%" cmd /k bucle.bat copiador.py %CFG%
echo Listo: Supervisor, Estratega y Copiador de %CFG% en marcha.
