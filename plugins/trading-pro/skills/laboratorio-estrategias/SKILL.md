---
name: laboratorio-estrategias
description: "Laboratorio para probar muchas estrategias a la vez en oro, Nasdaq y S&P (diario y H1): Donchian (tendencia), RSI(2) (reversión), ruptura del máximo/mínimo del día anterior y falsa ruptura asiática, con costos, bloques de tiempo y prueba de robustez. Incluye el registro de TODO lo probado y su veredicto. Usar cuando el usuario pida 'prueba más estrategias', 'qué más funciona', 'no solo Asia', 'busca otra estrategia', o antes de investigar algo para no repetir pruebas."
---

# Laboratorio de estrategias

Español, corto. Objetivo: encontrar ventajas **robustas**, no la mejor curva. Repetir pruebas cada 3-6 meses con datos nuevos.

## Método obligatorio
1. Datos: `get_mt5_candles` (D1 hasta 5 años; H1 hasta 1 año; M15 de 30 en 30 días). Salidas grandes se guardan en archivo.
2. Varios mercados a la vez: `python3 -I scripts/multi_mercado.py <carpeta_json>` (RSI2 + Donchian, robustez, años positivos y riesgo del lote mínimo). Un mercado: `python3 scripts/laboratorio.py diario --json D1.json --costo X` o `... h1 --csv H1.csv --costo X` (oro 0.3, USTECH 1.0, US500 0.6).
3. **Robustez**: variar cada parámetro ±1 paso. Aceptar solo si la mayoría de variantes es positiva y positiva en la mayoría de bloques. Elegir la configuración del **centro** de la zona estable, nunca la mejor.
4. **Control**: probar en otro mercado; si "funciona en todo", sospechar. Si funciona solo donde tiene lógica, mejor señal.
5. **Viabilidad**: comprobar que el lote mínimo cabe en 1% de riesgo (`get_mt5_available_markets`).
6. Si pasa → skill propia con `creador-skills-trading` (estado `backtest`) → demo 30-50 ops.

## Megalaboratorio (miles de variantes con validación fuera de muestra)
- `python3 -I scripts/megalab.py config.json resultados.csv` → prueba 7 familias D1 (RSI-k, Donchian, cruce de medias, Bollinger, ruptura N días con RR, rachas, momentum) + rupturas de sesión H1 + **150 estrategias al azar por mercado** como control. `config.json` = `{"d1": {"SIMB": [json_D1, digits]}, "h1": {"SIMB": [csv_H1, costo]}}`. Usa 4 núcleos; ~28k combinaciones en pocos minutos.
- `python3 -I scripts/analisis.py resultados.csv` → compara contra el azar y lista zonas robustas.
- **Regla de oro**: IS = primer 60% del tiempo (para elegir), OOS = último 40% (nunca se usa para elegir). Una zona (familia × mercado) se aprueba solo si ≥ 60% de sus variantes son positivas en IS **y** OOS (el azar logra ~25%) y la expectativa mediana es > +0.05R en ambos.

### Resultado 2026-11-23 (28,640 combinaciones, 16 mercados D1 de 5 años + 6 mercados H1 de 1 año)
- **Casi todo es ruido**: de las variantes elegidas por verse bien en IS, solo 57% siguió positiva en OOS (azar: 52%). Elegir "la mejor" de miles = elegir suerte.
- **Zonas aprobadas** (% variantes positivas IS y OOS): Donchian oro **100%**, RSI US500 **91%**, ruptura N días (RR) oro 91%, RSI USTECH 85%, Donchian ETH 78% (N=20: 92%), Donchian BTC 63% (N=20: 89%). La config exacta de RSI(2) de la skill es positiva en IS y OOS en US500, USTECH, US30 y US2000. Ruptura asiática oro: IS +0.24R, OOS +0.22R ✔.
- **Reprobadas que parecían buenas con los 5 años completos**: Donchian **USDJPY** (IS +0.42R → OOS −0.37R, 0%) y Donchian **plata** (IS negativa, OOS positiva: inconsistente) → retiradas de la demo.
- Peores zonas: Donchian en GBPUSD, US30, US2000, AUDUSD; Bollinger en USDCAD; rupturas de sesión H1 fuera del oro.

### Megalab 2 (2026-11-23, 3,712 combinaciones: IBS, cambio de mes, MACD, Supertrend, barra interior/NR7, squeeze)
`python3 -I scripts/megalab2.py config.json resultados2.csv` (mismo config; reusa megalab.py). Para comparar con el azar: unir sus filas con las filas `azar` de `resultados.csv` y pasar `analisis.py`.
- Aprobadas: IBS USTECH 100%, MACD GER40 94% (contradice Donchian GER40 0% → observación), Supertrend ETH 83% / BTC 80%, y en oro squeeze 100%, NR7 100%, cambio de mes 92%, MACD 80% → **todas en oro son la misma ventaja de tendencia**: no sumarlas.
- Rupturas por sesión (megalab H1): rango asiático oro 64%; **Londres** oro 28%, GER40 38%, GBP/EUR/JPY ≤ 3%; **Nueva York** oro 10%, USTECH 27% → ❌.
- Catálogo completo con veredictos y fuentes: skill `enciclopedia-estrategias`.

### Estudio 2 (23-nov, 3:30 am)
- **IBS** (0.2/0.7/SMA200/SL2): USTECH 100%, US500 67% → ✅ demo (`estrategia-ibs-indices`). Solo 19-26% de sus entradas coinciden con RSI(2) → operaciones nuevas. US30 IS≈0 y US2000 17% → ❌.
- **Donchian H4**: 100% en oro/ETH/BTC, pero duplica la exposición de Donchian D1 → documentado, no añadido.

### Estudio 3 (23-nov, 5:30 am)
- Ruptura asiática oro + filtros: tendencia D1 (SMA50/200) y volatilidad (percentil ATR) → ninguno mejora en IS y OOS a la vez; positiva en todos los regímenes → **sin filtro**.
- RSI(2) GBPUSD 34% y USOIL 22% de variantes OK fuera de muestra → ❌ descartadas (de "observación" a descartadas).
- Swap: ver sección en `gestion-riesgo-avanzada`; cripto ~0.1R por operación de 20 días → medir en la demo.

### Prueba "muchas operaciones y cerrar con ganancia" (23-nov)
`python3 -I scripts/muchas_operaciones.py oro_h1.csv nasdaq_h1.csv` — abre 1 posición por hora y la cierra al llegar a TP (k×ATR), con o sin SL.
- **Sin SL**: 100% de cierres en ganancia, pero las perdedoras quedan abiertas: oro total −$25k a −$124k, caída −$36k a −$146k; Nasdaq caída −$57k a −$386k (liquidación segura en $100k). Hasta 265 posiciones abiertas a la vez.
- **Con SL**: resultado ≈ azar o negativo (spread). USDJPY: todas las variantes con SL negativas en IS y OOS; la menos mala (tendencia EMA50, TP 1 ATR, SL 2 ATR) −$82 a −$545/año con 0.01 lote por posición.
- Veredicto ❌. Se corre como **experimento en vivo** en la demo 10076734 ($5k) a pedido del usuario, separado de la demo principal.

## Registro de pruebas (actualizar siempre)
| Estrategia | Mercado | Datos | Resultado | Veredicto |
|---|---|---|---|---|
| Ruptura asiática H1 | Oro | 1 año | +32.9R, 4/4 bloques, 16/18 variantes + | ✅ **Demo en curso** |
| Ruptura asiática H1 | Nasdaq | 1 año | 18/18 variantes − | ❌ |
| **RSI(2) D1** | **US500** | 5 años | +9.6R, 24/24 variantes +, DD 2.3R | ✅ **Demo** |
| **RSI(2) D1** | **US2000** | 5 años | +7.5R, 12/12 variantes +, 5/5 años | ✅ **Demo** |
| RSI(2) D1 | US30 | 5 años | 12/12 +, pero lote mín. ≈ 5% de riesgo | ⏸️ No operable con $5k |
| RSI(2) D1 | GBPUSD / USOIL | 5 años | 11/12 + con 5 años completos, pero fuera de muestra 34% / 22% (= azar) | ❌ Descartadas (estudio 3) |
| RSI(2) D1 | EURUSD, AUDUSD, USDCAD, USDJPY, XAG, ETH | 5 años | ≤ 6/12 | ❌ |
| Donchian 20 D1 | USDJPY | 5 años | +9.7R en total, pero OOS −0.37R (0% de variantes OK fuera de muestra) | ❌ Retirada (megalab) |
| **Donchian 20 D1** | **ETHUSD** | 5 años | +10.5R, 4/4 +, 5/5 años (ETH −60%) | ✅ **Demo** |
| Donchian 20 D1 | XAGUSD | 5 años | IS negativa / OOS positiva: inconsistente | ❌ Retirada (megalab) |
| Donchian 20 D1 | BTCUSD | 5 años | 89% variantes OK en IS y OOS; lote mín. $718 | ✅ Demo (se salta si el lote mín. > 0.5%) |
| **Donchian 20 D1** | **Oro** | 5 años | **100% variantes OK en IS y OOS** | ✅ **Demo** |
| Donchian D1 | EURUSD, GBPUSD, AUDUSD, US30, US2000, GER40 | 5 años | 0/4 | ❌ |
| RSI(2) D1 | Nasdaq | 5 años | 12/12 variantes +, pero lote mín. = ~5% de riesgo | ⏸️ No operable con $5k |
| RSI(2) D1 | Oro | 5 años | ≈ 0 | ❌ |
| Máx/mín del día anterior H1 (RR 1.5) | Oro | 1 año | +17 a +33R según horario, 3/4 bloques (1er bloque −) | 🔎 Observación; correlacionada con la ruptura asiática |
| Máx/mín del día anterior H1 | Nasdaq | 1 año | negativa | ❌ |
| Donchian 20 solo compras D1 | Oro | 5 años | +16.7R, 5/5 años, solo 22 ops; oro alcista en el periodo | 🔎 Observación (sesgo de mercado alcista) |
| Donchian 55 D1 | Oro | 5 años | +44R pero 37R vienen de un solo año | ❌ Depende de un outlier |
| Donchian 20/55 solo compras D1 | Nasdaq | 5 años | +9 a +11R, pocas ops | 🔎 Observación |
| Ruptura asiática H1 | EURUSD / GBPUSD / GER40 / USDJPY | 1 año | robustez 7/18, 5/18, 12/18 (exp. +0.03R), 2/18 (−31R) | ❌ Solo funciona en oro |
| Máx/mín día anterior H1 | EURUSD / GBPUSD / GER40 / USDJPY | 1 año | inestable: bloques cambian de signo | ❌ |
| Falsa ruptura asiática H1 | Oro | 1 año | un bloque explica todo, DD 17-28R | ❌ |
| Falsa ruptura asiática H1 | Nasdaq | 1 año | −29 a −40R | ❌ |
| ORB Nueva York M15 | Nasdaq | 3 meses | +8R pero cambia de signo entre mitades | 🔎 Observación |
| ORB Nueva York M15 | Oro | 3 meses | mayoría negativa | ❌ |
| Scalping M1 (4 señales) | Oro | 11 días | todas negativas, = azar | ❌ |

## Efecto lunes (23-nov-2026)
El Estacional marcó al S&P 500: +0.18% de media los lunes (t = 3.2). Prueba: comprar al cierre del viernes, salir al cierre del lunes, SL 2×ATR20, costo 2× spread:
| Mercado | Lunes IS | Lunes OOS | Acierto | Otros días |
|---|---|---|---|---|
| US500 | +0.04R | +0.08R | 62% | entre −0.03R y +0.02R |
| GER40 | +0.01R | +0.04R | 55% | entre −0.02R y +0.03R |
| Oro / ETH | sin efecto | | | |
**Veredicto: real pero delgado.** El swap triple del fin de semana (~0.02R en US500) lo deja en ~+0.035R por operación. No se opera solo; queda **en observación** (posible filtro: preferir entradas largas de RSI2/IBS en viernes).

## Exploración de 34 mercados (23-nov-2026)
Datos: 34 mercados D1 de Axi (5 años): índices EE.UU./Europa/Asia, metales, energía, 13 divisas y 6 criptos.
- **Explorador**: 52,392 variantes → 23 zonas aprobadas (el azar logra 20%).
- **Abogado del diablo** (costos ×2, sin top 5, vecinos, 4 periodos, bootstrap):
  - **RESISTEN y diversifican (activas en Aurum 2.2)**: NR7 UK100 (+0.48R, 45 ops), NR7 GBPUSD (+0.29R), MACD GER40 (+0.17R), MACD SOL-USD (+0.46R), cambio de mes en oro (+0.24R).
  - **RESISTEN pero repiten la ventaja de Donchian en el mismo mercado** (no se agregan): ndayrr/macd/nr7/squeeze en oro, squeeze en ETH, supertrend en SOL.
  - **DUDOSAS**: boll EU50, squeeze SOL, macd XAGUSD, supertrend ETH. **FRÁGIL**: supertrend BTC.
- **Pares (familia nueva, reversión del ratio, 31 pares × 144 variantes)**: 7 aprobados, 6 RESISTEN (USDCAD/USDCHF +0.37R, LTC/BTC +0.36R, US2000/US500 +0.31R, AUD/EUR +0.25R, XAG/XPT +0.32R, AUDJPY/USDJPY +0.89R); AUDJPY/EURJPY FRÁGIL. **Ojo**: la versión en vivo no reproduce el backtest en el simulador de 2026 → apagados hasta re-verificar.
- **Lección de portafolio**: con muchas estrategias diarias, el tope de riesgo abierto dejaba fuera a la ruptura asiática (la mejor). Una **reserva de 1%** para ella llevó el año simulado de +3% (caída 16%) a +37% (caída 9%).
- **Lección de autocontrol**: "−8R en 20 operaciones" se dispara por azar en una estrategia de 37% de acierto con 2R. Usar z frente al backtest.

## Ideas en cola
Ruptura de Londres en oro (08:00 UTC) · RSI(2) en GBPUSD y USOIL a demo cuando haya margen de riesgo · Donchian en plata/BTC si la cuenta crece · Donchian en cartera (oro + índices) · filtro de volatilidad (ATR alto/bajo) sobre la ruptura asiática · días posteriores a gaps del lunes.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Resultados pasados no garantizan resultados futuros. Claude no es asesor financiero.
