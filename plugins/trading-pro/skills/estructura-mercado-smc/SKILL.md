---
name: estructura-mercado-smc
description: "Leer la estructura del mercado y conceptos de liquidez (Smart Money Concepts): tendencia por máximos y mínimos, BOS, CHoCH, barridas de liquidez, zonas de oferta/demanda, order blocks y FVG, con criterios objetivos y sus límites. Usar cuando el usuario mencione SMC, ICT, order block, liquidez, BOS, CHoCH, FVG, 'estructura', o pida un análisis técnico de oro o Nasdaq."
---

# Estructura de mercado y liquidez (SMC)

Español, corto, explicando cada término la primera vez. **Advertencia honesta**: SMC es un lenguaje para describir el precio, no una ventaja comprobada por sí solo. Cada patrón que se quiera operar debe pasar por `backtesting-estrategias`.

## Definiciones objetivas (para que sean medibles)
- **Swing alto/bajo**: vela con máximo (mínimo) mayor (menor) que las 2 velas a cada lado.
- **Tendencia alcista**: último swing alto > anterior y último swing bajo > anterior. Bajista: al revés. Si no, **rango**.
- **BOS (ruptura de estructura)**: cierre de vela más allá del último swing a favor de la tendencia → continuación.
- **CHoCH (cambio de carácter)**: cierre más allá del último swing **en contra** de la tendencia → posible giro (necesita confirmación).
- **Barrida de liquidez**: la mecha supera un máximo/mínimo obvio (diario, asiático, doble techo) y la vela **cierra de vuelta** dentro.
- **Zona de oferta/demanda / order block**: última vela contraria antes de un movimiento impulsivo que hizo BOS.
- **FVG (hueco de valor)**: en 3 velas, el máximo de la 1ª no toca el mínimo de la 3ª (o al revés).

## Rutina de análisis multi-temporalidad
1. **D1/H4**: tendencia y niveles mayores (máx/mín diario y semanal, zonas).
2. **H1**: estructura actual, liquidez cercana (máx/mín asiático, del día anterior).
3. **M15**: gatillo (CHoCH tras barrida, o BOS + retroceso a zona).
4. Dar el análisis como **escenarios** con niveles concretos (consultados en vivo con `get_mt5_candles`), nunca como certeza.

## Uso con lo ya probado
- Los extremos del **rango asiático** son liquidez obvia: una barrida seguida de cierre dentro del rango es la idea opuesta a `estrategia-ruptura-asiatica-oro`. Candidata a backtest ("falsa ruptura asiática").
- Antes de operar un setup SMC: `checklist-entrada` y riesgo 1%.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Una estrategia sin backtest + demo no se usa en real. Claude no es asesor financiero.
