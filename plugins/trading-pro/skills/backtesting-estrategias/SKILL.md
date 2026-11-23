---
name: backtesting-estrategias
description: "Probar estrategias de trading con datos históricos antes de arriesgar dinero: descargar velas de MT5 (Axi), correr un backtest en Python, medir acierto, R medio, expectativa, profit factor y drawdown, y validar con walk-forward. Usar cuando el usuario diga 'prueba esta estrategia', 'backtest', '¿funciona esta idea?', '¿esta estrategia gana?', o antes de pasar una estrategia a demo/real."
---

# Backtesting de estrategias

Sin backtest no hay ventaja comprobada. Foco XAUUSD / USTECH. Español, corto y directo.

## Flujo
1. **Definir reglas exactas** (sin ambigüedad): entrada, SL, TP, filtros, horario, máx. operaciones/día. Si la regla no se puede programar, no se puede probar: pedir precisión.
2. **Datos**: `get_mt5_candles` (símbolo, temporalidad, rango). Guardar a CSV con columnas `time,open,high,low,close` en el scratchpad. Mínimo ~300 operaciones o 1-2 años de datos; si el conector limita el rango, pedir varias ventanas y unirlas.
3. **Correr** `python3 scripts/backtest.py --csv datos.csv --estrategia <nombre> [parámetros]` (ruta relativa a esta skill). Estrategias incluidas:
   - `cruce_medias` (`--rapida 20 --lenta 50`)
   - `ruptura_rango` (`--hora-inicio 0 --hora-fin 7`, rompe el rango asiático)
   - `rsi_reversion` (`--rsi-bajo 30 --rsi-alto 70`)
   Horas en **UTC** (las velas de Axi vienen en UTC; Monterrey = UTC-6). Convertir el JSON de `get_mt5_candles` a CSV con un mini script (`time[:19],open,high,low,close`). Si la salida es enorme, se guarda en archivo: leerla desde ahí con Python.
   Comunes: `--atr-sl 1.5 --rr 2 --costo 0.3` (spread+comisión en precio). Para una estrategia nueva, añadir una función `senal_<nombre>` en el script siguiendo el patrón y probarla.
4. **Walk-forward**: `--walk 4` divide en 4 bloques; la estrategia debe ser rentable en la mayoría, no solo en total.
5. **Informe**: operaciones, % acierto, R medio, expectativa (R), profit factor, máx. drawdown (R), racha perdedora máx., resultado por bloque. Veredicto: `descartar` / `afinar` / `pasar a demo`.

## Criterios para pasar a demo
- ≥ 100 operaciones, expectativa > 0.15R tras costos, profit factor > 1.3, rentable en ≥ 3 de 4 bloques walk-forward, DD máx. tolerable a 1% de riesgo.
- Luego 30-50 operaciones en demo con resultados similares antes de pensar en real.

## Trampas a evitar (avisar siempre)
- **Sobreoptimización**: probar 50 combinaciones y quedarse con la mejor = curva que no se repite. Pocos parámetros, valores redondos.
- **Sesgo de anticipación**: usar datos de la vela que aún no cerró. El script entra en la apertura de la vela siguiente.
- **Ignorar costos**: el spread del oro come mucho en scalping.
- **Muestra pequeña**: 20 operaciones no prueban nada.
- Si SL y TP se tocan en la misma vela, el script asume SL (conservador).

## Al terminar
Si la estrategia pasa, proponer guardarla como skill con `creador-skills-trading` (estado `backtest` + métricas).

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Resultados pasados no garantizan resultados futuros. Claude no es asesor financiero.
