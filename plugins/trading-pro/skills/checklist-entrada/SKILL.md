---
name: checklist-entrada
description: "Checklist con puntuación antes de abrir cualquier operación (oro, Nasdaq u otro): contexto, nivel, gatillo, riesgo, noticias y estado mental. Da un puntaje 0-10 y un veredicto (operar / esperar / no operar). Usar cuando el usuario diga '¿entro?', '¿compro o vendo?', 'voy a abrir una operación', 'revisa mi entrada', o antes de que Claude ejecute una operación en la demo."
---

# Checklist de entrada

Filtro obligatorio antes de cada operación. Evita las entradas impulsivas, que son las que más dinero cuestan. Español, corto.

## Pasos
1. Datos en vivo: `get_mt5_quote`, `get_mt5_candles` (H4 y H1 + temporalidad de entrada), `get_mt5_positions`, `get_account`. Noticias del día (web).
2. Puntuar cada punto (sí = puntos, no = 0):

| # | Criterio | Pts |
|---|---|---|
| 1 | A favor de la tendencia de H4 (o reversión con razón clara en nivel mayor) | 2 |
| 2 | Entrada en nivel clave (S/R, máx/mín diario, número redondo, zona de liquidez) | 2 |
| 3 | Gatillo confirmado en vela cerrada (patrón, ruptura+retesteo, cruce) | 1 |
| 4 | R:B ≥ 1:2 hasta el siguiente obstáculo real | 1 |
| 5 | SL por estructura/ATR, lote calculado a ≤1% (`gestion-riesgo-avanzada`) | 1 |
| 6 | Sin noticia de alto impacto en ±30 min (`calendario-macro-noticias`) | 1 |
| 7 | Sesión con liquidez (Londres o NY) y spread normal | 1 |
| 8 | Estado mental OK: sin pérdidas seguidas hoy, sin prisa ni revancha | 1 |

**Bloqueantes** (cualquiera = NO OPERAR sin importar el puntaje): sin SL · riesgo > 1% · stop diario alcanzado · riesgo abierto total > 2% · operación de revancha.

3. Veredicto: **8-10 operar** · **6-7 esperar mejor precio/confirmación** · **≤5 no operar**.

## Formato de salida
```
Símbolo / dirección: ...
Puntaje: X/10 (lista de ✔/✘ por criterio)
Bloqueantes: ninguno | ...
Plan: entrada · SL · TP · lote · riesgo $
Veredicto: ...
```
Si el usuario quiere entrar con puntaje bajo, decirlo con claridad una vez y respetar su decisión (en real, sin ejecutar nada sin su confirmación explícita).

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Nunca inventar precios: consultarlos en vivo. Sin garantías; Claude no es asesor financiero.
