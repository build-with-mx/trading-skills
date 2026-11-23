---
name: estrategia-tendencia-donchian
description: "Estrategia de seguimiento de tendencia Donchian 20 en diario (activa en la demo de $100k en oro XAUUSD, Ethereum ETHUSD y Bitcoin BTCUSD; USDJPY y plata retirados por fallar fuera de muestra): entrar cuando el precio cierra en máximo/mínimo de 20 días, salir con el canal de 10 días. Reglas exactas, backtest de 5 años en 13 mercados, lote y revisión diaria. Usar cuando el usuario diga 'Donchian', 'seguimiento de tendencia', 'tortugas', 'estrategia de tendencia', 'yen', 'ethereum', 'cripto', o pida operar/revisar esta estrategia."
---

# Tendencia Donchian 20 — Oro, ETHUSD, BTCUSD (D1)

Español, corto. Estrategia de **pocas ganadoras grandes y muchas perdedoras pequeñas**: acierto típico 35-45%. Rachas de pérdidas son normales; la ganancia viene de pocas tendencias largas.

## Reglas exactas (velas D1 cerradas)
1. **Compra**: cierre > máximo de las 20 velas anteriores. **Venta**: cierre < mínimo de las 20 velas anteriores.
2. **Entrada**: a mercado en la siguiente apertura.
3. **SL inicial**: 2 × ATR(20) desde la entrada (fijo en el broker).
4. **Salida**: compra → cuando un cierre queda por debajo del mínimo de las últimas 10 velas; venta → cierre por encima del máximo de 10 velas. Cerrar en la siguiente apertura. Sin TP.
5. 1 posición por símbolo. No re-entrar el mismo día de una salida.
6. **Lote** (riesgo 1%):
   - **ETHUSD / BTCUSD**: $1 por 1.0 por lote, mín. 0.1, paso 0.1. lote = balance×1% / dist SL, redondeado abajo a 0.1. Si 0.1 lote arriesga más del % permitido, no operar.
   - **XAUUSD**: $100 por 1.0 por lote, mín. 0.01. La posición Donchian de oro **no lleva TP** (así se distingue de la ruptura asiática, que sí lo lleva).

## Validación (D1 Axi, nov-2021 → nov-2026, costo = 2× spread mediano)
| Mercado | Total Donchian 20 (ambos lados) | Robustez (N=20/30/40/55) | Años positivos | Riesgo con lote mín. hoy |
|---|---|---|---|---|
| **ETHUSD** | +10.5R (solo compras +12.7R) | 4/4 | **5/5** (ETH cayó −60% en el periodo: gana en ambos sentidos) | $22 |
| USDJPY ❌ retirado | +9.7R en 5 años, pero OOS −0.37R | 4/4 | 3/5 | — |
| XAGUSD ❌ retirada | +4.6R, inconsistente IS/OOS | 4/4 | 3/5 | — |
| BTCUSD | +9.4R | 4/4 | 3/5 | $718 (> 0.5% de $100k: se salta hasta que baje la volatilidad) |
| Oro (solo compras) | +16.7R | — | 5/5 | ver `laboratorio-estrategias` |
| EURUSD, GBPUSD, AUDUSD, US30, US2000, GER40 | negativa | 0/4 | — | ❌ No usar |
**Validación fuera de muestra (megalab, IS 60% / OOS 40%)**: oro 100% de variantes positivas en ambos periodos (OOS mediana +0.63R); ETH N=20 92%; BTC N=20 89%; **USDJPY 0% (IS +0.42R → OOS −0.37R) → retirado**; plata inconsistente → retirada.

Conclusión: la tendencia funciona en mercados con tendencias largas (yen, metales, cripto), no en índices de acciones ni en EUR/GBP/AUD.

## Versión H4 (estudio 23-nov)
Donchian en velas de 4 h (5 años): 100% de variantes OK en IS y OOS en oro, ETH y BTC (N=20-120, SL 2-3). **No se añade**: apuesta a la misma tendencia, mercado y dirección que la versión D1 → concentra riesgo en vez de diversificar. Candidata si se busca más frecuencia en una cuenta aparte.

## Advertencias
- **Swap no incluido**: las posiciones duran semanas; en cripto el swap de CFD puede ser alto. Revisar el swap real en la demo y descontarlo.
- Crypto cotiza el fin de semana: las señales del sábado/domingo se evalúan el domingo por la tarde.
- Estado: **backtest ✔ → demo**. Pasar a real solo tras 30+ operaciones en demo (tarda meses: ~8-12 operaciones/año por mercado).

## Revisión diaria (la hace la tarea "Estrategias diarias")
1. `get_mt5_candles` D1 ~60 días de XAUUSD, ETHUSD y BTCUSD.
2. Con posición: ¿cierre al otro lado del canal de 10? → `close_mt5_position`. Si no, mantener sin tocar.
3. Sin posición: ¿cierre fuera del canal de 20? → filtros (riesgo abierto total ≤ 2%, pérdida del día < 3%) → abrir con SL.

## Cuenta y riesgo actuales
- Demo MT5 **10076749** ($100k): riesgo **0.5%** por operación (sustituye al 1% de las fórmulas de lote), máx. 2% abierto total entre todas las estrategias.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Sin garantías; Claude no es asesor financiero.
