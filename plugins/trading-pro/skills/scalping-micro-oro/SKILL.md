---
name: scalping-micro-oro
description: "Scalping y operaciones muy pequeñas y muy frecuentes en oro (XAUUSD M1): 'muchas operaciones de $2', 'ganar $300 en minutos', alta frecuencia. Contiene el resultado del test con datos reales (descartado por el spread), la matemática del costo por operación y el script para volver a probar. Usar cuando el usuario pida scalping, operar muy rápido, muchas operaciones pequeñas o ganar mucho en minutos."
---

# Scalping micro en oro (XAUUSD M1)

Español, corto y directo. **Estado: DESCARTADA** (2026-11-23). No ejecutar en demo ni en real salvo que un nuevo test la apruebe.

## Por qué no funciona (matemática)
- Cada operación paga el **spread** (≈0.16 en oro en Axi) = **$1.60 a 0.1 lote** / $0.16 a 0.01 lote.
- Para ganar "$2 netos" a 0.1 lote el precio debe moverse 0.36 a favor; pero si pierdes, pierdes el SL **más** el spread. Con ~50% de acierto, cada operación pierde en promedio ≈ el spread.
- 150 operaciones × $1.60 de spread = **−$240 garantizados** solo en costos, antes de acertar o fallar.
- Además Claude ejecuta vía herramientas (segundos por llamada) y las tareas programadas corren como mucho cada hora: no es infraestructura de alta frecuencia. Los que ganan con HFT tienen servidores junto al broker, costos casi cero y ventaja de microsegundos.

## Test con datos reales
- XAUUSD M1 Axi, 9-20 nov 2026 (13,727 velas, 11 días). Spread mediano 0.16; rango mediano de vela M1 1.74.
- Señales: cruce EMA 9/21, pullback a EMA21 con tendencia, RSI(7) 20/80, y **entradas al azar** como referencia. TP/SL de 0.2 a 2.0.
- Resultado: **todas negativas**, acierto ≈ 50% (igual que el azar), entre −$0.36 y −$2.71 por operación a 0.1 lote; **−$193 a −$1,748** en 11 días. Ninguna señal superó al azar → sin ventaja.

## Cómo responder al usuario
1. Explicar la matemática del spread con sus números (lote que quiera usar).
2. Mostrar que lo que da "miles en minutos" es **capital grande con riesgo pequeño** (cuenta de fondeo: 1% de $100k = $1,000), no muchas operaciones pequeñas.
3. Redirigir a estrategias con ventaja medida (`estrategia-ruptura-asiatica-oro`) y a `cuentas-fondeo-prop`.

## Cómo volver a probar (si cambian costos o hay idea nueva)
1. `get_mt5_candles` XAUUSD period M1 (máx. 30 días por llamada); la salida se guarda en archivo.
2. `python3 scripts/scalp_test.py <archivo.json>`. Para una idea nueva, añadir una función `sig_<nombre>(i)` y su fila en la lista.
3. Solo es candidata si supera claramente al AZAR **después del spread**, en ≥ 300 operaciones y en al menos 2 periodos distintos. Luego `backtesting-estrategias` y demo.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Una estrategia sin backtest + demo no se usa en real. Claude no es asesor financiero.
