@echo off
cd /d "%~dp0"
echo Iniciando el equipo Aurum: Guardian, Contador y Aurum...
start "Guardian" cmd /k iniciar_guardian.bat
timeout /t 5 /nobreak >nul
start "Contador" cmd /k iniciar_contador.bat
timeout /t 3 /nobreak >nul
start "Aurum" cmd /k iniciar_aurum.bat
echo Listo. Se abrieron 3 ventanas. Para detener todo, cierralas.
