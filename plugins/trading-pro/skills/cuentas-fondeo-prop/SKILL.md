---
name: cuentas-fondeo-prop
description: "Cuentas de fondeo (prop firms): cómo funcionan los retos, reglas típicas (objetivo, pérdida diaria y máxima, días mínimos, consistencia, noticias), cómo elegir una, plan de riesgo para pasar el reto y señales de alerta de empresas poco fiables. Usar cuando el usuario quiera más capital, pregunte por FTMO/fondeo/prop firm/challenge, o diga que quiere ganar más sin arriesgar más de su dinero."
---

# Cuentas de fondeo (prop firms)

La forma legítima de operar con más capital sin arriesgar más dinero propio: se paga una cuota por un reto en demo; si se aprueba, la empresa da una cuenta (normalmente simulada) y comparte ganancias (70-90% para el trader). Español, corto.

## Antes de recomendarlo (honestidad)
- La mayoría de quienes intentan retos no los pasan. La cuota es una pérdida probable si no hay consistencia previa.
- Requisito sugerido: 50+ operaciones en demo con expectativa positiva y DD máx. < 8% siguiendo las reglas de esta biblioteca.
- Verificar siempre en la web las reglas **actuales** de la empresa (cambian a menudo) y que acepte residentes de México, la plataforma MT5 y los símbolos (oro, Nasdaq).

## Reglas típicas (varían por empresa: confirmar)
| Regla | Rango típico |
|---|---|
| Objetivo fase 1 / fase 2 | 8-10% / 4-5% |
| Pérdida diaria máx. | 4-5% (ojo: a veces sobre equity, incluye flotante) |
| Pérdida total máx. | 8-10% (estática o "trailing") |
| Días mínimos | 0-5 |
| Regla de consistencia | ningún día > 30-50% del beneficio total |
| Noticias / fin de semana | a veces prohibido mantener posiciones |

## Plan para pasar el reto
- Riesgo 0.5-1% por operación (nunca más): con DD máx. 10% eso son 10-20 pérdidas de margen.
- Stop diario propio = la mitad del límite de la empresa (si es 5%, parar en 2-2.5%).
- Sin prisa: el tiempo suele ser ilimitado; quemar la cuenta por intentar pasar en 3 días es el error #1.
- Tras llegar al objetivo, dejar de operar (o el mínimo exigido).
- Usar `gestion-riesgo-avanzada` (proyección con `--dd-max` igual al de la empresa) para estimar probabilidad de pasar.

## Señales de alerta (empresa poco fiable)
Promesas de ganancias garantizadas, reglas ocultas o ambiguas sobre pagos, sin historial verificable de pagos, cambios de reglas retroactivos, muchas quejas recientes de pagos negados, presión para comprar rápido "con descuento que vence hoy". Revisar reseñas recientes (Trustpilot, foros) antes de pagar.

## Estudio 23-nov-2026: el camino con $50–100
**Con $100 en una cuenta propia no cabe ninguna estrategia de Aurum**: el lote mínimo arriesga demasiado (riesgo con lote mínimo y ATR actual):

| Estrategia | Riesgo con lote mínimo | $100 | $5,000 | $10,000 | $100,000 |
|---|---|---|---|---|---|
| Ruptura asiática oro (0.01) | $33 | ❌ 33% | ✅ 0.7% | ✅ 0.3% | ✅ |
| Donchian oro (0.01) | $194 | ❌ | ❌ 3.9% | ⚠️ 1.9% | ✅ |
| Donchian ETH (0.1) | $22 | ❌ 22% | ✅ 0.4% | ✅ | ✅ |
| Donchian BTC (0.1) | $574 | ❌ | ❌ 11% | ❌ 5.7% | ✅ |
| RSI2/IBS S&P 500 (0.1) | $40 | ❌ 40% | ✅ 0.8% | ✅ | ✅ |
| RSI2 Russell 2000 (0.1) | $11 | ❌ 11% | ✅ 0.2% | ✅ | ✅ |
| RSI2/IBS Nasdaq, RSI2 Dow (0.1) | $237–249 | ❌ | ❌ ~5% | ❌ ~2.5% | ✅ |
| Experimento USDJPY (0.01) | $2.4 | ❌ 2.4% | ✅ | ✅ | ✅ |
(Recalcular con el ATR del momento: la volatilidad cambia estos números.)

**Conclusión**: con $50–100 el mejor uso es **un reto de fondeo de $5k–10k** (Aurum puede operar 5 de 9 estrategias en $5k), no una cuenta propia.

### Precios de referencia 2026 (fuentes de afiliados; verificar en la web de cada firma antes de pagar)
| Firma | Cuenta | Precio aprox. | Notas |
|---|---|---|---|
| FundingPips 2-Step Pro | $5k | ~$29 | MT5; verificar reglas de EA |
| IC Funded | $5k | ~$30 | sin límite de tiempo (según fuente) |
| FundedNext Stellar Lite | $5k | ~$33 | regla de consistencia 40%; EA posiblemente con complemento pagado |
| The5ers High Stakes | $5k | ~$35 | consistencia 50%; restricciones de noticias |
| GOAT Funded Trader | $5k | ~$36 | MT5 |
| Audacity Capital | $10k | ~$68–79 | |
| FTMO 1-Step / 2-Step | $10k | ~$89–102 | permite EAs (no en cuentas Aggressive cerca de noticias); sin consistencia en estándar |
- **Pendiente antes de comprar**: confirmar que aceptan residentes de **México**, que permiten **EAs/robots** en la cuenta elegida, reglas de noticias y de consistencia, y pérdida diaria (si se mide sobre equity).
- Aurum en un reto: riesgo 0.5–1%, desactivar estrategias cuyo lote mínimo no quepa, filtro de noticias activo.
- Fuentes: TradingPilot, VettedPropFirms, FundingPips blog, BrokerAnalysis, BestProps, PropFirmMap, FundedTrading, Audacity Capital (guías comerciales/afiliados).

### VPS (para que Aurum funcione 24 h)
- Axi no da VPS gratis: **acredita hasta ~$35–36 al mes** del VPS de terceros (ForexVPS / CNS) a quien opere **más de 20 lotes al mes** (fuente: página de VPS de Axi). Planes desde ~$35/mes. Alternativa: VPS Windows genérico más barato (verificar precio).

## Prueba general con el equipo Aurum (23-nov-2026)
Simulación de 4 meses con velas reales (23 jul – 20 nov 2026): la demo maestra de $100k operó y el Copiador replicó en una cuenta de $5k.
| Riesgo en $5k | Señales copiadas | Resultado | Peor caída |
|---|---|---|---|
| 0.5% | 56 de 69 | +4.2% | 2.2% |
| **1%** | **67 de 69** | **+7.6%** | **4.2%** |
- Con 0.5% en $5k, el **lote mínimo del oro (0.01)** arriesga más de lo permitido en 1 de cada 5 señales: se pierden operaciones. Usar **1%** y dejar que el Estratega de metas lo baje a 0.5% cerca del objetivo o del límite.
- Supervisor de fondeo: bloquea entradas al 50% de cualquier límite y **cierra todo al 80%**, antes de que la empresa descalifique.
- Es un solo periodo de 4 meses: el resultado puede ser mejor o peor. Pasar el checklist del prompt maestro antes de comprar.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Claude no recomienda una empresa concreta como garantizada; Claude no es asesor financiero.
