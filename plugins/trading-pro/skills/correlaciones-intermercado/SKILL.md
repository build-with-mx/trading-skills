---
name: correlaciones-intermercado
description: "Relaciones entre mercados que mueven al oro y al Nasdaq: dólar (DXY), rendimientos de bonos y tasas reales, petróleo, VIX, bitcoin, plata y otros índices. Cómo leerlas antes de operar, cómo detectar riesgo correlacionado y cuándo se rompen. Usar cuando el usuario pregunte '¿por qué sube/baja el oro?', '¿qué mueve al Nasdaq?', 'el dólar', 'los bonos', o antes de abrir oro y Nasdaq a la vez."
---

# Correlaciones intermercado

Español, corto. Son tendencias, no leyes: se rompen en pánicos y cambios de régimen.

## Mapa
| Mercado | Oro | Nasdaq | Lectura |
|---|---|---|---|
| Dólar (DXY) ↑ | ↓ fuerte | ↓ leve | El oro cotiza en USD |
| Rendimiento 10 años / tasas reales ↑ | ↓ fuerte | ↓ (tecnológicas sensibles a tasas) | Costo de oportunidad |
| Expectativa de alzas de la Fed ↑ | ↓ | ↓ | Mueve dólar y rendimientos a la vez |
| VIX (miedo) ↑ | ↑ normal / ↓ en liquidaciones | ↓ | En pánicos se vende todo para cubrir margen |
| Petróleo ↑ | ↑ leve (inflación) | ↓ leve | |
| Plata | Muy positiva | — | Confirma o contradice al oro |
| S&P 500 / Dow | — | Muy positiva | El Nasdaq amplifica al S&P |
| Bitcoin | Débil | Positiva (apetito de riesgo) | |

## Rutina antes de operar
1. Revisar en la web (o en `get_mt5_available_markets` si Axi los ofrece: buscar USDX/DXY, US10Y, VIX, XAGUSD, US500) la dirección del día del dólar, rendimientos y VIX.
2. Si el sesgo de la operación va **contra** el dólar y las tasas a la vez → bajar puntaje en `checklist-entrada` (criterio de contexto).
3. Oro y Nasdaq abiertos a la vez: si ambos dependen del mismo motor (p. ej. la Fed), sumar el riesgo como una sola posición (máx. 2% total).

## Régimen reciente (actualizar)
- Nov-2026: Fed con sesgo de alzas + dólar fuerte → oro en mínimos de 14 meses; venta fuerte de tecnológicas. En la semana del 17-20 nov oro y Nasdaq cayeron **juntos** (liquidaciones): la correlación inversa clásica oro/acciones se rompió.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Nunca inventar datos: consultarlos en vivo. Claude no es asesor financiero.
