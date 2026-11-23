# Pruebas del equipo Aurum (para Claude / desarrollo)
Broker MT5 simulado con velas reales (`datos.db` del Minero) para probar todo el equipo sin MetaTrader.
1. Copia la carpeta `aurum` como `equipo/` junto a estos archivos y pon un `datos.db` dentro.
2. `python prueba_general.py` → ~4 meses de operación real simulada (maestra $100k + copia $5k), errores por bot, fidelidad del Copiador.
3. `python estres.py` → posiciones sin SL, caída de −11%, riesgo manipulado, Algo Trading apagado.
4. `python riesgo_copia.py 0.01` → compara el riesgo de la cuenta copiada.

## Desde 2.2
- `variante.sh NOMBRE PAR RESERVA LAB` (con variables RIESGO, ABIERTO, DIARIA) → un año completo con una configuración; resultado determinista (PYTHONHASHSEED=0).
- `base_sim.py` arma el código de simulación en un solo texto parcheable (para rastrear señales).
- `pares2.py` / `estres_pares2.py` → búsqueda y estrés de la familia de pares (necesitan un datos.db con los 34 mercados).
- Pendiente: los pares en vivo no reproducen su backtest en 2026 (ver `_estado` de par_ratio en aurum_config.json).
