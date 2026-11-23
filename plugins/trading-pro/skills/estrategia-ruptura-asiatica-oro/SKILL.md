---
name: estrategia-ruptura-asiatica-oro
description: "Estrategia de ruptura del rango asiático en oro (XAUUSD, H1): marcar máximo y mínimo de 00:00-06:00 UTC, operar la primera vela H1 que cierre fuera del rango, SL 1.5×ATR y TP 2R. Incluye reglas exactas, horarios en hora de Monterrey, resultados de backtest y cómo ejecutarla o revisarla. Usar cuando el usuario diga 'ruptura asiática', 'rango asiático', 'estrategia del oro', '¿hay setup de ruptura hoy?', o pida operar/revisar esta estrategia."
---

# Ruptura del rango asiático — Oro (XAUUSD H1)

Español, corto y directo. Las velas de Axi vienen en **UTC**; Monterrey = UTC-6 todo el año.

## Reglas exactas
1. **Rango**: máximo y mínimo de las velas H1 que abren de **00:00 a 05:00 UTC** (inclusive) = **18:00 a 23:59 Monterrey** de la noche anterior.
2. **Ventana de entrada**: de **06:00 a 15:59 UTC** (00:00 a 09:59 Monterrey). Después, no hay entrada ese día.
3. **Gatillo**: la **primera** vela H1 que **cierra** por encima del máximo → compra; por debajo del mínimo → venta. Solo **1 operación por día**.
4. **Entrada**: a mercado en la apertura de la vela siguiente.
5. **SL**: 1.5 × ATR(14) de H1, medido desde la entrada.
6. **TP**: 2 × distancia del SL (2R). Sin gestión adicional (así se probó).
7. **Lote**: 1% de riesgo → `python3 ../gestion-riesgo-avanzada/scripts/riesgo.py lote --balance <B> --sl <dist_SL> --simbolo XAUUSD`.
8. **Filtros obligatorios**: sin noticia de alto impacto USD en la siguiente hora (`calendario-macro-noticias`); pasar el `checklist-entrada` (los bloqueantes mandan).

## Cómo revisarla en vivo
1. `get_mt5_candles` XAUUSD H1 desde las 00:00 UTC de hoy (y ~20 velas previas para el ATR).
2. Calcular máximo/mínimo del rango, ATR(14), y si ya hubo una vela cerrada fuera del rango después de las 06:00 UTC.
3. Responder: rango (máx/mín), estado (`esperando` / `gatillo compra` / `gatillo venta` / `ya operada hoy` / `ventana cerrada`), y si hay gatillo: entrada, SL, TP, lote y riesgo en $.
4. En la **demo 10076749** puede ejecutarse según las reglas de `trading-completo`. En **real**: solo con confirmación explícita del usuario.

## Estado de validación
- **Estado: backtest** (falta demo). Próximo paso: 30-50 operaciones en demo con registro.
- Datos: XAUUSD H1 Axi, 23-nov-2025 a 20-nov-2026 (5,886 velas), costo 0.3 por operación (spread real mediano ≈ 0.13).
- **Resultado**: 182 ops · acierto 39.6% · **+32.9R** · expectativa **+0.18R** · PF 1.30 · máx. DD 7.1R · racha perdedora máx. 6.
- **Walk-forward** (4 trimestres): +7.7R, +6.8R, +6.7R, +11.7R → positiva en los 4.
- **Robustez**: 16 de 18 combinaciones vecinas (SL 1-2 ATR, RR 1.5-3, fin de rango 6-7 UTC) dieron positivo; las de SL 1×ATR son las débiles. Se eligió una configuración del centro de la zona estable, **no** la mejor del grid (evitar sobreoptimización).
- **Debilidad**: con RR 2, casi toda la ganancia vino de **ventas** (+32.5R) y las compras quedaron en cero (+0.5R). El oro bajó en el periodo (4,075 → 3,540). En un año alcista el resultado podría ser peor. Con RR 3 ambas direcciones fueron positivas: candidata a probar en demo como variante.
- **Nasdaq (USTECH)**: la misma lógica **perdió** en las 18 combinaciones (−6R a −38R). **No usar en Nasdaq.**
- Fecha última revisión: 2026-11-23. Repetir el backtest cada 3 meses con datos nuevos (`backtesting-estrategias`, `--estrategia ruptura_rango --hora-fin 6 --atr-sl 1.5 --rr 2 --costo 0.3 --walk 4`).

## Expectativas realistas
- Rachas de 6+ pérdidas seguidas son normales (≈6% de DD a 1% de riesgo).
- ~15 operaciones/mes. A +0.18R y 1% de riesgo ≈ +2-3% mensual **si** el comportamiento pasado se mantiene, lo cual no está garantizado.

## Cuenta y riesgo actuales
- Demo MT5 **10076749** ($100k): riesgo **0.5%** por operación (sustituye al 1% de las fórmulas de lote), máx. 2% abierto total entre todas las estrategias.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Nunca inventar precios: consultarlos en vivo. Sin garantías; Claude no es asesor financiero.
- Una estrategia sin backtest + demo no se usa en real.

## Lecciones aprendidas
- 2026-11-23 — Backtest inicial: robusta en oro, negativa en Nasdaq; ganancia concentrada en ventas con RR 2.
- 2026-11-23 — Primera operación en demo: 1:00 MTY la vela tocó 3,637 pero cerró dentro del rango (falsa ruptura evitada por la regla de cierre); 7:00 MTY cerró en 3,654.51 → compra 0.30 @3661.53 (deslizamiento de $2: riesgo real 1.06%). La entrada a mercado en movimientos rápidos puede salir peor que el ask leído: dejar margen.
