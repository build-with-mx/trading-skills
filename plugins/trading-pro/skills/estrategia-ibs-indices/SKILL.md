---
name: estrategia-ibs-indices
description: "Estrategia IBS (Internal Bar Strength) diaria en índices de EE.UU. (activa en la demo de $100k: Nasdaq USTECH y S&P 500 US500): comprar cuando el día cierra cerca de su mínimo dentro de tendencia alcista y vender cuando cierra cerca de su máximo en tendencia bajista; salir cuando el cierre vuelve a la parte alta/baja de la vela. Reglas exactas, validación fuera de muestra, solapamiento con RSI(2) y lote. Usar cuando el usuario diga 'IBS', 'internal bar strength', 'fuerza de la vela', o pida operar/revisar esta estrategia."
---

# IBS en índices — USTECH y US500 (D1)

Español, corto. IBS = (cierre − mínimo) / (máximo − mínimo) de la vela diaria: 0 = cerró en el mínimo, 1 = cerró en el máximo. Efecto documentado: Pagonidis (2013), "The IBS Effect: Mean Reversion in Equity ETFs".

## Reglas exactas (velas D1 cerradas de Axi)
1. **Compra**: IBS < 0.2 **y** cierre > SMA200.
2. **Venta**: IBS > 0.8 **y** cierre < SMA200.
3. **Entrada**: a mercado en la siguiente apertura.
4. **SL**: 2 × ATR(20) (fijo en el broker). Sin TP.
5. **Salida**: compra → cuando una vela cierra con IBS > 0.7; venta → IBS < 0.3; o a las 5 sesiones. Cerrar en la siguiente apertura.
6. **Un solo trade por índice**: si ya hay una posición de RSI(2) en ese índice, no abrir IBS (RSI(2) tiene prioridad).
7. **Lote**: $1 por punto por lote, mín. 0.1, paso 0.1 → lote = balance × riesgo% / dist SL, redondeado abajo; si 0.1 lote arriesga más que el % permitido, no operar.

## Validación (D1 Axi, nov-2021 → nov-2026; IS = primer 60%, OOS = último 40%)
| Índice | Variantes OK en IS y OOS | Config. elegida (0.2 / 0.7 / SMA200 / SL 2 / ambos) | Ops en 5 años |
|---|---|---|---|
| **USTECH** | **100%** | IS +0.09R, OOS +0.15R | 135 |
| **US500** | 67% | IS +0.10R, OOS +0.15R | 125 |
| US30 | 60% (IS ≈ 0) | IS −0.01R, OOS +0.11R | ❌ no se usa |
| US2000 | 17% | — | ❌ no se usa |
- **Independencia**: solo 19-26% de las entradas IBS coinciden (±2 días) con RSI(2) → aporta operaciones nuevas (~25 al año por índice).
- Advertencia de la literatura: en vivo suele rendir ~50-55% del backtest.
- Estado: **backtest ✔ → demo** (añadida a la tarea "Estrategias diarias" el 23-nov-2026).

## Reglas de seguridad (heredadas)
- Riesgo según el plan vigente (demo $100k: 1% por operación, 3% abierto total, stop diario 3%). Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Sin garantías; Claude no es asesor financiero.
