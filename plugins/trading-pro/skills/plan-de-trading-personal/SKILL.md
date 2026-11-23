---
name: plan-de-trading-personal
description: "El plan de trading del usuario en un solo lugar: metas, cuentas, estrategias activas y su estado, reglas de riesgo, horario, rutina, criterios para pasar de demo a real y a cuentas de fondeo. Usar cuando el usuario pregunte '¿cuál es mi plan?', '¿qué estrategias uso?', '¿cuándo paso a real?', 'mis reglas', o cuando haya que decidir algo importante sobre su trading."
---

# Plan de trading personal

Español, corto. Es la referencia que manda sobre cualquier impulso del momento. Actualizar con el usuario cuando cambie algo (fecha al final).

## Meta
- **Demo MT5 10076749 (Axi, $100,000)** = ensayo de cuenta de fondeo: riesgo **1% por operación** (decidido el 23-nov con delegación del usuario), máx. **3% abierto**, stop diario 3%. Objetivo tipo reto: +10% sin caer más de 10% desde el máximo.
- La demo 10076734 ($5,000) solo corre el **experimento de muchas operaciones** en USDJPY, separado de la demo principal.
- Después: cuenta de fondeo (capital ajeno) y, cuando haya resultados, cuenta real con confirmación explícita en cada operación.

## Estrategias
| Estrategia | Mercado | Estado | Opera |
|---|---|---|---|
| Ruptura asiática (`estrategia-ruptura-asiatica-oro`) | Oro H1 | Backtest ✔ → **demo en curso** | Tarea horaria 1:03-10:03 MTY, lun-vie |
| RSI(2) (`estrategia-rsi2-indices`) | US500, US2000, USTECH, US30 D1 | Backtest ✔ → **demo en curso** | Tarea "Estrategias diarias" 17:10 MTY, dom-jue |
| IBS (`estrategia-ibs-indices`) | USTECH, US500 D1 | Backtest ✔ → **demo en curso** | Tarea "Estrategias diarias" 17:10 MTY, dom-jue |
| Tendencia Donchian 20 (`estrategia-tendencia-donchian`) | Oro, ETHUSD, BTCUSD D1 | Backtest ✔ → **demo en curso** | Tarea "Estrategias diarias" 17:10 MTY, dom-jue |
| ORB Nueva York (`orb-apertura-nueva-york`) | Nasdaq M15 | En observación | No |
| Máx/mín día anterior, Donchian | Oro / índices | En observación (`laboratorio-estrategias`) | No |
| Scalping M1 (`scalping-micro-oro`) | Oro | Descartada | No |
| Ruptura asiática en Nasdaq | Nasdaq | Descartada | No |
| Experimento muchas operaciones (pedido del usuario) | USDJPY H1 en **demo 10076734 ($5k)** | ❌ en backtest; se mide en vivo | Tarea horaria :07, lun-vie: 0.01 lote, tendencia EMA50, TP 1 ATR, SL 2 ATR, máx. 10 abiertas, se detiene en −10% |
| Investigación semanal | — | Sábados 10:17 MTY | Propone nuevas |

## Reglas de riesgo (no negociables)
1% por operación en la demo de $100k · 3% abierto total · stop diario 3% · semanal 6% (→ bajar a 0.5%) · siempre SL · sin martingala · sin promediar pérdidas.

## Rutina
- Diario: reportes de la tarea en el chat; revisar noticias (`calendario-macro-noticias`).
- Viernes/sábado: `revision-semanal-trading` + investigación.
- Cada 3 meses: re-backtest de las estrategias activas con datos nuevos.

## Criterios para avanzar
- **Demo → fondeo**: ≥ 50 operaciones de estrategias probadas, expectativa > 0, DD máx. < 10%, ≥ 4 semanas, reglas respetadas.
- **Fondeo/real**: riesgo 0.5-1%, confirmación explícita del usuario en cada operación real.
- Una estrategia nueva entra al plan solo tras backtest + 30-50 operaciones en demo.

## Historial de cambios
- 2026-11-23 (mañana): primera operación de la ruptura asiática (compra oro 0.30 @3661.53); experimento de muchas operaciones en la demo de $5k; el usuario tiene posiciones manuales sin SL en su cuenta real 60465719 (recomendado poner SL; Claude no opera cuentas reales sin confirmación explícita).
- 2026-11-23 (estudio 3): ruptura asiática se mantiene sin filtros; RSI(2) en GBPUSD y petróleo descartados; medir el swap real de cada posición (cripto es caro).
- 2026-11-23 (madrugada): riesgo a 1% por operación y 3% abierto (delegación del usuario); se añade IBS en USTECH y US500; Donchian H4 estudiado y no añadido.
- 2026-11-23: megalab de 28,640 combinaciones con validación fuera de muestra → Donchian: fuera USDJPY y plata, entra oro.
- 2026-11-23: nueva demo 10076749 de $100k (ensayo de fondeo), riesgo 0.5%; se añaden USTECH y US30 (RSI2) y XAGUSD y BTCUSD (Donchian), que no cabían en $5k.
- 2026-11-23: investigación en 13 mercados → añadidos RSI(2) en US2000 y Donchian en USDJPY y ETHUSD a la demo.
- 2026-11-23: añadida RSI(2) en US500 a demo (Nasdaq no operable: lote mínimo ≈5% de riesgo).
- 2026-11-23: plan creado. Tarea diaria discrecional pausada para test limpio de la ruptura asiática. Órdenes pendientes canceladas; demo en $5,000.

## Reglas de seguridad (heredadas)
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Sin garantías; Claude no es asesor financiero.
