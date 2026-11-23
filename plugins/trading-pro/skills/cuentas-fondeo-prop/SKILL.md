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

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Claude no recomienda una empresa concreta como garantizada; Claude no es asesor financiero.
