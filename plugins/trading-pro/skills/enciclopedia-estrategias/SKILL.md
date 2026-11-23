---
name: enciclopedia-estrategias
description: "Enciclopedia de las estrategias de trading más usadas hoy (2026) con veredicto basado en pruebas reales con datos de Axi y en la evidencia publicada: tendencia, reversión, rupturas por sesión (Asia, Londres, Nueva York), ICT/SMC (Silver Bullet, FVG, killzones), scalping, IBS, cambio de mes, MACD, Supertrend, barra interior/NR7, squeeze, grid/martingala, IA, carry, deriva nocturna. Usar cuando el usuario pregunte '¿funciona la estrategia X?', '¿qué estrategias existen?', 'vi esta estrategia en YouTube', 'estrategias actuales', o antes de investigar una estrategia nueva."
---

# Enciclopedia de estrategias (actualizada 2026-11-23)

Español, corto. Cada fila combina **(1) qué dice la evidencia publicada** y **(2) nuestro test con datos de Axi** (D1 5 años en 16 mercados, H1 1 año en 6 mercados; 32,352 combinaciones; elegidas con el primer 60% del tiempo y validadas en el 40% final; comparadas contra 2,400 estrategias al azar que logran ~25%). "% OK" = porcentaje de variantes positivas en ambos periodos.

## Veredictos
| Estrategia | Evidencia publicada | Nuestro test | Veredicto |
|---|---|---|---|
| **Tendencia (Donchian, Supertrend, MACD; D1 y H4)** | Fuerte: base de los fondos CTA; funciona por horizonte medio/largo | Oro Donchian 100%, MACD 80%, squeeze 100%; ETH/BTC Donchian ~90%, Supertrend 80%+ ; **USDJPY 0%**, GBP/EUR/AUD/índices de acciones malos | ✅ en oro y cripto · ❌ en divisas e índices de acciones |
| RSI(2) en GBPUSD / petróleo | — | Validación fuera de muestra: GBPUSD 34%, USOIL 22% (= azar) | ❌ (con 5 años completos parecían buenas) |
| **Reversión RSI(2) / IBS en índices** | Media-fuerte: IBS estudiado (Pagonidis 2013); en vivo rinde ~la mitad que en backtest | RSI US500 91%, USTECH 85%; **IBS USTECH 100%**, US500 67% (IBS añadido a la demo el 23-nov; 75-80% de sus entradas no coinciden con RSI2) | ✅ en índices de EE.UU. · ❌ en oro, divisas |
| **Ruptura rango asiático** | Mixta (blogs con resultados inestables) | Oro 64% (config. activa: IS +0.24R, OOS +0.22R); GER40 14%, GBP/EUR/JPY < 10%. Filtros de tendencia (SMA50/200) o de volatilidad: no mejoran en ambos periodos | ✅ solo oro, sin filtros |
| **Ruptura de Londres** (muy vendida) | Débil: tests de 10-18 años sin ventaja estable | Oro 28%, GER40 38%, GBP 2%, EUR 2%, JPY 3% | ❌ |
| **Ruptura apertura Nueva York / ORB** | Débil-mixta | Oro 10%, USTECH 27%, EUR 11% | ❌ (Nasdaq en observación) |
| **ICT / SMC** (Silver Bullet, FVG, killzones, order blocks) | Muy débil: sin estudios independientes; un test FVG+killzone en GBPUSD 2016-2026 perdió −30% | Falsa ruptura asiática (barrida de liquidez) ❌ | ❌ como sistema; útil solo como lenguaje |
| **Scalping M1** | El spread domina | Todas negativas, = azar | ❌ |
| **Cambio de mes (turn of month)** | Efecto académico conocido en acciones | Oro 92% (sesgo alcista del periodo), GER40 62%, índices EE.UU. ≤ 42% | 🔎 observación |
| **MACD en GER40** | — | 94% (pero Donchian en GER40 0%: contradictorio) | 🔎 observación |
| **Barra interior / NR7** | Escasa | Oro 100% (misma ventaja de tendencia del oro), GBP 61%; índices 0% | 🔎 / ❌ |
| **Bollinger reversión, rachas, momentum simple** | Mixta | Sin zonas robustas | ❌ |
| **Grid / martingala** (muchos EAs de oro) | Riesgo de ruina; la mayoría de prop firms los prohíbe o vigila | No se prueba: viola las reglas de riesgo | ❌ prohibido |
| **IA / machine learning "milagro"** | Backtests sin validar; un portafolio en vivo de pocos meses no prueba nada | — | ❌ salvo validación fuera de muestra |
| **Deriva nocturna (overnight drift)** | NY Fed: existió 1998-2020; se debilitó; difícil de capturar neto de costos | No testeable con D1 de Axi (el día cierra 17:00 NY) | ❌ |
| **Carry trade** | Documentado; índice de carry de Bloomberg +18% en 2025, pero "gana despacio y pierde de golpe" (desarme del yen ago-2024; Banque de France: medir por unidad de volatilidad) | No testeable sin historial de swaps de Axi | 🔎 no prioritario: riesgo de crash, swaps de CFD retail reducen el diferencial |

## Lecciones generales
1. La ventaja depende del **mercado**: tendencia en oro/cripto, reversión en índices de acciones. La misma estrategia falla en otro mercado.
2. Varias "estrategias distintas" en oro (Donchian, MACD, squeeze, NR7, cambio de mes) **son la misma ventaja** (tendencia del oro): no sumarlas como si fueran independientes, el riesgo se concentra.
3. Con miles de pruebas, las ganadoras por suerte abundan: exigir validación fuera de muestra y vecinos robustos (`laboratorio-estrategias`).
4. Desconfiar de backtests de vendedores, de periodos cortos (2020-2025 = oro solo subió) y de cualquier promesa de ganancia.

## Fuentes principales
- Carry y swaps: Banque de France (carry y volatilidad), Advisor Perspectives/Bloomberg (carry 2025), Oanda e IG (financiamiento CFD), Axi (fees).
- IBS: Pagonidis (2013) "The IBS Effect"; Quantified Strategies; J. Kinlay (2019).
- Deriva nocturna: Boyarchenko, Larsen y Whelan, NY Fed Staff Report 917; Liberty Street Economics.
- ICT/FVG: Backtrex (FVG + killzone GBPUSD 2016-2026).
- Rupturas en oro: blogs MQL5 (190 tests en 10 años; 288 versiones en 18 años) — fuente comercial.
- Tendencia/CTA 2026: LPL Research, CFA Institute (ene-2026), Bloomberg (22-ene-2026).
- Prop firms y martingala: guías de PropFirmMap, FundedTrading (comerciales; verificar reglas de cada firma).

## Cómo usarla
- Si el usuario trae una estrategia: buscarla aquí; si no está o cambió, probarla con `laboratorio-estrategias` (megalab + filtro anti-suerte) y **añadir la fila**.
- Una estrategia pasa a demo solo con ✅ y aprobación del usuario.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación (0.5% en la demo de $100k), 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Sin garantías; Claude no es asesor financiero.
