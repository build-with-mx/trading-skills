---
name: estrategia-rsi2-indices
description: "Estrategia de reversión a la media RSI(2) en índices de EE.UU. en diario (activa en demo: S&P 500 = US500 y Russell 2000 = US2000; Nasdaq y Dow validados pero el lote mínimo no cabe en $5k): comprar caídas cortas dentro de tendencia alcista y vender subidas cortas en tendencia bajista, salir al cruzar la media de 5 días. Reglas exactas, backtest de 5 años, tamaño de lote y cómo revisarla cada día. Usar cuando el usuario diga 'RSI2', 'RSI de 2', 'reversión en índices', 'estrategia del S&P', 'estrategia diaria', o pida operar/revisar esta estrategia."
---

# RSI(2) en índices — US500 y US2000 (D1)

Español, corto. Velas D1 de Axi: el día cierra a las 17:00 Nueva York (16:00 Monterrey en invierno de EE.UU., 15:00 en verano).

## Reglas exactas
Indicadores sobre velas D1 **cerradas**: SMA200 y SMA5 del cierre, RSI(2) de Wilder, ATR(20).
1. **Compra**: cierre > SMA200 **y** RSI(2) < 10.
2. **Venta**: cierre < SMA200 **y** RSI(2) > 90.
3. **Entrada**: a mercado en la apertura de la siguiente sesión.
4. **SL**: 2.5 × ATR(20) desde la entrada (fijo en el broker).
5. **Salida**: cuando una vela D1 cierra por encima de la SMA5 (compra) o por debajo (venta) → cerrar en la siguiente apertura. **Salida por tiempo**: tras 10 sesiones.
6. **Sin TP fijo**, sin break-even, sin trailing. 1 posición a la vez por símbolo.
7. **Lote** (US500 y US2000: $1 por punto por lote, mín. 0.1, paso 0.1): lote = (balance × 1%) / (distancia SL en puntos), redondeado **hacia abajo** a 0.1. Si da < 0.1 pero el riesgo con 0.1 lote es ≤ 1% del balance, usar 0.1; si 0.1 lote arriesga > 1%, **no operar**.

## Estado de validación: BACKTEST ✔ → demo
- **US500**, D1 Axi, nov-2021 → nov-2026, costo 0.6 puntos:
  - Configuración elegida (u=10, SL 2.5 ATR, ambos lados): 52 ops · acierto 78.8% · **+9.6R** · exp. +0.18R · PF 2.60 · máx. DD 2.3R · positiva en 4 de 5 años.
  - **Robustez: 24 de 24 variantes positivas** (umbral 5/10/15/20 × SL 2/2.5/3 ATR × ambos/solo compras).
- **US2000 (Russell 2000)**: +7.5R (52 ops), **12/12 variantes positivas, positiva en 5/5 años**. Riesgo con 0.1 lote hoy ≈ $16. → **Activa en demo**.
- **US30 (Dow)**: 12/12 variantes positivas, +4.7R, pero 0.1 lote arriesga ≈ $249 (5%) → no operable con $5k.
- **Otros mercados (5 años)**: GBPUSD 11/12 (+4.1R, 4/5 años) y USOIL 11/12 (+1.8R) → en observación; USDMXN 11/12 pero solo 3/5 años; EURUSD, AUDUSD, USDCAD, USDJPY, plata, ETH → no funciona. GER40 dudoso (7/12).
- **Correlación**: US500 y US2000 suelen dar señal los mismos días → con ambas abiertas el riesgo total es 2% (el máximo). No abrir una tercera.
- **USTECH (Nasdaq)**: 12 de 12 variantes positivas (+6 a +12.5R), pero con la volatilidad actual el SL (~2,400 pts) con el lote mínimo 0.1 arriesga ~$237 (≈5%) → **no operable con $5k**. Revisar si la cuenta crece o la volatilidad baja.
- **Oro**: no funciona (control negativo): es un patrón de índices de acciones.
- Riesgo real histórico con 0.1 lote en US500: mediana $16, máx. $55.
- Frecuencia: ~10 operaciones/año. Duración típica: 2-5 días.
- **No incluido en el backtest: swap** (costo por mantener posiciones de un día a otro). Revisarlo en la demo.

## Revisión diaria (la hace la tarea programada)
1. `get_mt5_candles` D1 de US500 y US2000 desde hace ~320 días (para SMA200).
2. Si hay posición US500 abierta: ¿la última vela cerró al otro lado de la SMA5, o pasaron 10 sesiones? → cerrar con `close_mt5_position`. Si no, mantener.
3. Si no hay posición: ¿señal en la última vela cerrada? → filtros (riesgo abierto total ≤ 2%, pérdida del día < 3%) → abrir con SL.
4. Reportar en una línea si no hay nada; con detalle si abre o cierra.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Una estrategia sin backtest + demo no se usa en real. Sin garantías; Claude no es asesor financiero.

## Lecciones aprendidas
- 2026-11-23 — Backtest robusto en US500 y USTECH; el tamaño mínimo de lote decide qué índice es operable con una cuenta pequeña.
