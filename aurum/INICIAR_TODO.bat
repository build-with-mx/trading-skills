@echo off
cd /d "%~dp0"
echo Iniciando el equipo Aurum (7 bots)...
start "Guardian" cmd /k iniciar_guardian.bat
timeout /t 5 /nobreak >nul
start "Minero" cmd /k iniciar_minero.bat
timeout /t 60 /nobreak >nul
start "Contador" cmd /k iniciar_contador.bat
start "Vigia" cmd /k iniciar_vigia.bat
start "Sombra" cmd /k iniciar_sombra.bat
start "Explorador" cmd /k iniciar_explorador.bat
timeout /t 5 /nobreak >nul
start "Aurum" cmd /k iniciar_aurum.bat
echo Listo: Guardian, Minero, Contador, Vigia, Sombra, Explorador y Aurum en marcha.
