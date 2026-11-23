# Pruebas del equipo Aurum (para Claude / desarrollo)
Broker MT5 simulado con velas reales (`datos.db` del Minero) para probar todo el equipo sin MetaTrader.
1. Copia la carpeta `aurum` como `equipo/` junto a estos archivos y pon un `datos.db` dentro.
2. `python prueba_general.py` → ~4 meses de operación real simulada (maestra $100k + copia $5k), errores por bot, fidelidad del Copiador.
3. `python estres.py` → posiciones sin SL, caída de −11%, riesgo manipulado, Algo Trading apagado.
4. `python riesgo_copia.py 0.01` → compara el riesgo de la cuenta copiada.
