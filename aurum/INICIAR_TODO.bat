@echo off
cd /d "%~dp0"
echo Iniciando el equipo Aurum (15 bots)...
start "Guardian" cmd /k iniciar_guardian.bat
timeout /t 5 /nobreak >nul
start "Minero" cmd /k iniciar_minero.bat
timeout /t 60 /nobreak >nul
start "Contador" cmd /k iniciar_contador.bat
start "Vigia" cmd /k iniciar_vigia.bat
start "Sombra" cmd /k iniciar_sombra.bat
start "Explorador" cmd /k iniciar_explorador.bat
start "Estratega" cmd /k iniciar_estratega.bat
start "Mecanico" cmd /k iniciar_mecanico.bat
start "Respaldo" cmd /k iniciar_respaldo.bat
start "Panel" cmd /k iniciar_panel.bat
start "Auditor" cmd /k iniciar_auditor.bat
start "Archivista" cmd /k iniciar_archivista.bat
start "Profesor" cmd /k iniciar_profesor.bat
start "Abogado del diablo" cmd /k iniciar_abogado_diablo.bat
timeout /t 5 /nobreak >nul
start "Aurum" cmd /k iniciar_aurum.bat
echo Listo: Guardian, Minero, Contador, Vigia, Sombra, Explorador, Estratega, Mecanico, Respaldo, Panel, Auditor, Archivista, Profesor, Abogado del diablo y Aurum en marcha. Abre panel.html para ver todo. Cuenta de fondeo: iniciar_fondeo.bat.
