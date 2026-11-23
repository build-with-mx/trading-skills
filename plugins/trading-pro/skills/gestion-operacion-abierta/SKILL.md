---
name: gestion-operacion-abierta
description: "Qué hacer con una operación ya abierta: break-even, cierres parciales, trailing stop, cerrar antes de noticias o del fin de semana, y cuándo NO tocarla. Incluye resultados medidos con datos reales. Usar cuando el usuario diga '¿muevo el stop?', '¿cierro?', '¿pongo break-even?', '¿tomo parcial?', 'voy ganando, qué hago', o haya posiciones abiertas que revisar."
---

# Gestión de la operación abierta

Español, corto. Regla madre: **gestionar según el plan de la estrategia, no según la emoción del momento.**

## Evidencia (ruptura asiática oro, H1, 182 ops, 1 año, Axi)
| Gestión | Total | Expectativa | Máx. DD |
|---|---|---|---|
| **Sin gestión (SL y TP fijos)** | **+31.9R** | **+0.18R** | **7.1R** |
| Break-even a +1R | +22.7R | +0.12R | 11.5R |
| Break-even a +1.5R | +28.8R | +0.16R | 10.9R |
| Parcial 50% a +1R + BE | +26.7R | +0.14R | 10.9R |
| Trailing 1.5× SL | +26.8R | +0.14R | 8.7R |
Conclusión: en estrategias con TP fijo probado, **mover el SL a break-even recorta ganadoras** que primero retroceden y luego llegan al TP. El "dolor" de ver una ganancia volver a cero cuesta menos que el BE sistemático. Sube el % de acierto pero baja el total.

## Reglas
1. **Si la estrategia tiene gestión definida y probada → seguirla al pie de la letra** (p. ej. ruptura asiática: no tocar).
2. Para operaciones sin estrategia probada (análisis discrecional): BE solo tras +1.5R **y** con nueva estructura a favor; nunca antes de +1R.
3. **Nunca** alejar el SL ni quitarlo. Nunca añadir a una perdedora.
4. Cerrar o reducir antes de: noticia de alto impacto (si la estrategia no las contempla), cierre del viernes si el swap/gap pesa, o si el escenario se invalidó (precio cierra más allá del nivel que justificó la entrada).
5. Cada cambio se anota en la bitácora con el motivo. Si no hay motivo escrito, no se cambia.
6. Si el usuario quiere tocar una operación por miedo o euforia → `psicologia-disciplina`.

## Probar una gestión nueva
Usar el backtest de `backtesting-estrategias` y comparar contra "sin gestión" con los mismos datos y walk-forward. Solo adoptar si mejora total **y** DD en la mayoría de bloques.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca modificar ni cerrar sin confirmación explícita del usuario en ese mensaje.
- Claude no es asesor financiero.
