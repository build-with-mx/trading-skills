---
name: revision-semanal-trading
description: "Revisión semanal (o mensual) del trading: descarga el historial de MT5, calcula estadísticas (acierto, R, expectativa, profit factor, drawdown, por símbolo, día y hora), compara con el plan y saca 3 acciones concretas. Usar cuando el usuario diga 'revisa mi semana', '¿cómo voy?', 'estadísticas', 'resumen del mes', o los viernes/fines de semana."
---

# Revisión semanal

Lo que no se mide no mejora. Cuenta por defecto: demo MT5 10076734. Español, corto.

## Pasos
1. `get_account` (balance, equity) y `get_mt5_order_history` + `get_mt5_fills` del periodo.
2. Guardar las operaciones cerradas en CSV (scratchpad) con columnas: `cierre,simbolo,direccion,lotes,profit` (profit neto con comisión y swap). Si el usuario dio su riesgo por operación, añadir columna `riesgo` en $; si no, usar 1% del balance inicial del periodo.
3. Correr `python3 scripts/estadisticas.py --csv ops.csv --balance-inicial <X>` (ruta relativa a esta skill).
4. Revisar con el usuario cumplimiento del plan: ¿todas con SL? ¿respetó stop diario? ¿operaciones fuera del plan?
5. Progreso hacia la meta (de $5,000 a $15,000): % recorrido y ritmo.

## Formato de salida
1. **Números**: balance, P/L $, % semana, operaciones, % acierto, expectativa (R), PF, máx. DD.
2. **Qué funcionó** (mejor símbolo/hora/día).
3. **Qué costó** (peor símbolo/hora, errores de conducta).
4. **3 acciones** concretas para la próxima semana (p. ej. "no operar oro antes de las 7:00", "máx. 2 operaciones/día").
5. Si sale una lección durable, proponer añadirla a "Lecciones aprendidas" de `trading-completo`.

Con pocas operaciones (< 20) avisar que las estadísticas aún no son significativas.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: solo lectura salvo confirmación explícita del usuario.
- Claude no es asesor financiero.
