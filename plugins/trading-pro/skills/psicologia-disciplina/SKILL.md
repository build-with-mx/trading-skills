---
name: psicologia-disciplina
description: "Psicología y disciplina del trader: detectar tilt, revancha, FOMO, sobreoperar, prisa por ganar; rutina antes/después de operar y reglas de parada. Usar cuando el usuario muestre frustración o euforia, diga 'quiero recuperar', 'quiero dinero rápido', 'perdí otra vez', 'voy a doblar el lote', 'estoy enojado', o tras 2+ pérdidas seguidas."
---

# Psicología y disciplina

La mayoría de las cuentas se pierden por conducta, no por falta de estrategia. Tono: directo, con empatía, sin sermones. Una advertencia clara basta; luego respetar la decisión. Español.

## Señales de alerta (detectarlas en lo que escribe el usuario o en el historial)
| Señal | Ejemplo | Respuesta |
|---|---|---|
| Revancha | "tengo que recuperar lo de hoy" | Proponer parar; el mercado no sabe que perdiste |
| Prisa / dinero rápido | "quiero llegar ya a la meta" | Mostrar riesgo de ruina con `gestion-riesgo-avanzada` |
| Subir lote tras pérdidas | "voy con 1 lote ahora" | Bloqueante: el riesgo vuelve a ≤1% |
| FOMO | "se está yendo sin mí" | El precio ya se movió; esperar retroceso o siguiente setup |
| Mover/quitar SL | "le doy más espacio" | El SL marca dónde la idea está equivocada; no se aleja |
| Sobreoperar | > 3-4 operaciones/día sin plan | Límite diario |
| Euforia | racha ganadora → más riesgo | Mismo riesgo; las rachas terminan |

## Reglas de parada
- 2 pérdidas seguidas → pausa de 1 hora y repasar checklist.
- 3 pérdidas en el día o -3% → se acabó el día.
- -6% en la semana → riesgo a 0.5% hasta recuperar la mitad.
- Enojo, cansancio, alcohol, prisa → no operar.

## Rutina
- **Antes** (5 min): ¿cómo me siento 1-10? ¿noticias? ¿niveles marcados? ¿cuál es mi máximo de pérdida hoy?
- **Durante**: solo setups del plan; checklist antes de cada entrada.
- **Después**: anotar en la bitácora si respetó el plan (sí/no), emoción dominante, una lección.

## Sobre "ganar dinero rápido"
Explicar con calma: lo que hace crecer una cuenta es una ventaja pequeña repetida muchas veces con riesgo bajo. La prisa no hace aparecer operaciones mejores, solo más y más grandes. Vías legítimas para acelerar: mejorar la estrategia (backtest), consistencia, cuentas de fondeo (`cuentas-fondeo-prop`), aportar capital. Si el usuario necesita dinero con urgencia para gastos, decir con tacto que el trading no es una fuente fiable para eso.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Claude no es psicólogo ni asesor financiero.
