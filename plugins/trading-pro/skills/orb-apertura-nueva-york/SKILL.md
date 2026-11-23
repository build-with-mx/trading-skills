---
name: orb-apertura-nueva-york
description: "Opening Range Breakout (ORB) en la apertura de Nueva York (9:30 ET) para Nasdaq (USTECH) y oro: reglas, resultados del test con datos reales de Axi y script para re-probar. Usar cuando el usuario diga 'ORB', 'ruptura de la apertura', 'apertura de Nueva York', 'operar la apertura del Nasdaq', o pregunte por estrategias para el Nasdaq."
---

# ORB — Ruptura del rango de apertura de Nueva York

Español, corto. 9:30 ET = **7:30 Monterrey** (invierno de EE.UU., nov-mar) / **6:30** (verano). El script maneja el cambio de horario solo.

## Reglas probadas
1. Rango de apertura (OR) = máximo/mínimo de las primeras 15 o 30 min desde las 9:30 ET (velas M15).
2. Gatillo: primera vela M15 que **cierra** fuera del OR antes de las 11:30 ET. 1 operación por día.
3. Entrada: apertura de la vela siguiente.
4. SL: lado opuesto del OR, o punto medio del OR.
5. TP: 1R, 2R o cierre a las 15:45 ET.

## Estado: EN OBSERVACIÓN (Nasdaq) · DESCARTADA (oro) — 2026-11-23
- Datos: M15 Axi, 24-ago a 20-nov-2026 (65 días). Costos: USTECH 1.0 punto, oro 0.3.
- **Nasdaq**: mejor variante OR 15 min + SL en el medio + TP 2R → 59 ops, +8.2R, exp. +0.14R, PF 1.26. **Pero** todas las variantes perdieron en la 1ª mitad del periodo y ganaron en la 2ª (que coincidió con la caída fuerte de noviembre): depende del régimen, no es una ventaja estable. Muestra pequeña.
- **Oro**: 9 de 12 variantes negativas. Descartada.
- Próximo paso: repetir con más meses de M15 (pedir de 30 en 30 días con `get_mt5_candles`). Pasa a demo solo si es positiva en ≥ 3 de 4 bloques con ≥ 150 operaciones.

## Cómo re-probar
1. `get_mt5_candles` USTECH M15 en tramos de 30 días (la salida grande se guarda en archivos).
2. `python3 scripts/orb_test.py --costo 1.0 tramo1.json tramo2.json ...` (oro: `--costo 0.3`).
3. Leer total, expectativa y **1ª vs 2ª mitad**: si cambian de signo, no hay ventaja estable.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Una estrategia sin backtest + demo no se usa en real. Claude no es asesor financiero.
