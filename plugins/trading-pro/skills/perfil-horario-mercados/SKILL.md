---
name: perfil-horario-mercados
description: "Perfil de volatilidad por hora y día para oro (XAUUSD) y Nasdaq (USTECH) en hora de Monterrey: cuándo se mueve más el mercado, cuándo está muerto, y cómo usarlo para elegir horario, tamaño de SL y evitar entradas malas. Usar cuando el usuario pregunte '¿a qué hora opero?', '¿cuándo se mueve más el oro/Nasdaq?', 'mejor horario', o al planear una sesión."
---

# Perfil horario de oro y Nasdaq

Español, corto. Horas en **Monterrey (UTC-6)**. Calculado con 1 año de velas H1 de Axi (nov-2025 a nov-2026). Aproximado: las horas de EE.UU. se corren 1 h en su horario de verano (mar-nov).

## Oro (rango H1 medio global ≈ 21)
| Horario MTY | Actividad | Uso |
|---|---|---|
| 19:00 (apertura Asia) | 1.4× | Salto de apertura; no perseguir |
| 22:00-04:00 | 0.6-0.9× | Tranquilo: se forma el rango asiático |
| **06:00-09:00** | **1.2-1.5×** (máx. 7-8 h) | Datos de EE.UU. + apertura NY: la acción principal |
| 11:00-16:00 | 0.7-0.9× | Bajo: rupturas tardías fallan más |

## Nasdaq (rango H1 medio global ≈ 98 puntos)
| Horario MTY | Actividad | Uso |
|---|---|---|
| 21:00-05:00 | 0.6-0.8× | Muerto: spread caro relativo al movimiento |
| **07:00-09:00** | **1.7-2.1×** (máx. 8 h) | Apertura NY: casi todo el movimiento del día |
| 10:00-13:00 | 1.1-1.3× | Medio |
| 14:00 en adelante | 0.8-1.0× | Bajo |

## Lo que NO dice
- Ninguna hora ni día tiene sesgo alcista/bajista útil: todos rondan 45-55% de velas alcistas. **No** operar por "a esta hora sube".
- Sirve para **cuándo** operar y **qué tan amplio** poner el SL (más actividad → SL por ATR más amplio, lote menor).

## Cómo actualizarlo
`get_mt5_candles` H1 hasta 1 año → CSV `time,open,high,low,close` → `python3 scripts/perfil.py archivo.csv`. Repetir cada 6 meses.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Claude no es asesor financiero.
