---
name: gestion-riesgo-avanzada
description: "Gestión de riesgo y matemáticas del trading: cálculo de lote, riesgo por operación, drawdown, cuánto hace falta para recuperar pérdidas, rachas perdedoras, interés compuesto y proyecciones realistas hacia una meta. Usar cuando el usuario pregunte '¿cuántos lotes?', '¿cuánto arriesgo?', '¿en cuánto tiempo llego a X?', 'quiero ganar más rápido', o quiera subir el riesgo."
---

# Gestión de riesgo avanzada

El riesgo es lo único que el trader controla. Foco: XAUUSD y USTECH en Axi MT5. Español, corto y directo.

## Calculadora
`python3 scripts/riesgo.py` (ruta relativa a esta skill). Subcomandos:
- `lote --balance 5000 --riesgo 1 --sl 4.5 --simbolo XAUUSD` → lote redondeado hacia abajo.
- `recuperar --perdida 20` → % necesario para volver al punto de partida.
- `racha --acierto 45 --operaciones 100` → racha perdedora esperable.
- `proyeccion --balance 5000 --meta 15000 --riesgo 1 --acierto 45 --rr 2 --ops-mes 20` → meses estimados y simulación Monte Carlo (prob. de llegar a la meta vs. de caer 30%).
Mostrar siempre el cálculo al usuario, no solo el resultado.

## Valores por símbolo (verificar con get_mt5_available_markets si cambia)
| Símbolo | Valor por 1.0 de precio por lote | Lote mín./paso |
|---|---|---|
| XAUUSD | $100 | 0.01 |
| USTECH | $1 por punto | 0.1 |
| NAS100.fs | $20 por punto | verificar |

## Reglas
- 1% por operación (0.5% en racha de 3 pérdidas o tras DD > 6%). 2% abierto total. Stop diario 3%, semanal 6%.
- Oro + Nasdaq a la vez = riesgo correlacionado: sumar como si fuera una sola posición.
- SL por estructura o 1-1.5× ATR(14) de la temporalidad de entrada; nunca por "lo que me alcanza".
- Si el lote mínimo supera el riesgo permitido → no operar ese setup.

## "Quiero dinero más rápido" — respuesta honesta
Mostrar con la calculadora la tabla de recuperación y una simulación a 1% vs 3% vs 5% de riesgo:
| Pérdida | Ganancia necesaria para recuperar |
|---|---|
| 10% | 11% |
| 20% | 25% |
| 30% | 43% |
| 50% | 100% |
Con más riesgo la meta llega antes **solo si nada sale mal**; la probabilidad de quemar la cuenta crece mucho más rápido. Las vías reales para acelerar: 1) mejorar la expectativa (mejores setups, menos operaciones malas), 2) consistencia en demo, 3) capital ajeno vía cuentas de fondeo (ver skill `cuentas-fondeo-prop`), 4) aportar capital propio. Nunca recomendar subir el riesgo por prisa.

## Métricas clave
- Expectativa (R) = %acierto × R medio ganador − %fallo × R medio perdedor. Si ≤ 0, no hay ventaja: no escalar.
- Profit factor = ganancias brutas / pérdidas brutas (> 1.3 aceptable, > 1.7 bueno).
- Escalar riesgo solo con 50+ operaciones de expectativa positiva y DD controlado.

## Costos de swap (financiamiento nocturno)
- Cada posición que pasa la noche paga (o cobra) swap. Fórmula típica: **valor de la posición × tasa anual / 365** por noche. Fin de semana = swap triple: en divisas y metales suele cobrarse el **miércoles**; en índices y cripto, el **viernes** (varía por broker: comprobar en MT5).
- En Axi: la tasa está en el campo **"Swap"** de la especificación del símbolo en MT5 (Market Watch → Especificación). Se aplica alrededor de las 17:00 de Nueva York. Las cuentas sin swap cobran a cambio una comisión de mantenimiento.
- **Cripto es caro**: referencias públicas de ~25% anual (≈0.07% del valor por día). Ejemplo: venta ETH 2.2 lotes (~$3,800 de valor) ≈ $2.6/día → en 20 días ≈ $50 ≈ 0.1R de una operación de $500 de riesgo. Con una ventaja de +0.2 a +0.3R por operación, el swap puede comerse un tercio.
- **Regla**: para estrategias que mantienen días o semanas (Donchian, RSI2, IBS), anotar el swap real cobrado en cada cierre y restarlo en la revisión semanal; si en cripto el swap supera ~0.1R por operación de media, reevaluar.
- Fuentes: [Axi – fees and charges](https://www.axi.com/int/fees-and-charges), [Axi – swaps en CFDs](https://www.axi.com/int/zendesk-faqs/cfds/are-there-any-swaps-or-overnight-fees-for-holding-a-cfd-position), [Oanda – financing costs](https://oanda.com/au-en/trading/financing-costs), [IG – overnight funding](https://www.ig.com/en/help-and-support/cfds/fees-and-charges/why-is-overnight-funding-charged-and-how-is-it-calculated-), [Blueberry – swap triple](https://intercom.help/blueberry-global/en/articles/12007870-why-are-swap-rates-tripled-on-wednesdays-and-fridays).

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Nunca inventar precios: consultarlos en vivo. Sin garantías; Claude no es asesor financiero.
