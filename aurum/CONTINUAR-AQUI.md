# CONTINUAR AQUÍ — estado del proyecto de trading (23-nov-2026)

> Documento de traspaso para el Proyecto de Claude. Léelo primero en cada conversación nueva junto con el PROMPT MAESTRO (instrucciones del proyecto). Responder siempre en español, corto y directo. Hora del usuario: Monterrey (UTC−6).

## 1. Dónde está todo
| Qué | Dónde |
|---|---|
| Código de Aurum (bots en Python) | GitHub `build-with-mx/trading-skills` → carpeta `aurum/` (versión **2.3**) |
| Simulador de broker y pruebas | mismo repo → `aurum-pruebas/` |
| Skills de trading (plugin `trading-pro` 1.15.0) | mismo repo → `plugins/trading-pro/` (instaladas en la cuenta del usuario) |
| Prompt maestro v1.3 | `aurum/PROMPT-MAESTRO.md` (también en las instrucciones del proyecto) |
| Informe completo del día de construcción | `INFORME-AURUM.md` (conocimiento del proyecto) |

## 2. Cuentas (Axi MT5)
| Cuenta | Uso | Permiso |
|---|---|---|
| Demo **10076749** ($100k) | Cuenta principal: Aurum / estrategias validadas | Operar con las reglas sin pedir confirmación |
| Demo **10076734** ($5k) | Solo el experimento "muchas operaciones" en USDJPY | Solo ese experimento |
| 60465719, 60465792, 60465885 (reales) | Del usuario | **Solo lectura.** Nada sin confirmación explícita en ese mensaje |

## 3. Aurum 2.3 — estrategias activas (7)
| Estrategia | Mercados | Año simulado 2026 |
|---|---|---|
| Ruptura asiática (H1) | Oro | +$35,357 (motor principal) |
| RSI(2) | US500, USTECH, US30, US2000 | +$3,058 |
| Donchian 20/10 | Oro, ETH, BTC | +$904 |
| NR7 | FTSE 100 (UK100) | +$870 |
| MACD | DAX (GER40) | +$670 |
| Cambio de mes | Oro | +$96 |
| MACD | Solana | +$9 (en observación) |

**Resultado de la simulación (un año real, al 1%):** $140,963 (+41%), caída máxima 8.2%, 0 errores.

**Eliminadas el 23-nov (a pedido del usuario: perdieron en 2026):** IBS, NR7 en GBPUSD y los 6 pares (USDCAD/USDCHF, LTC/BTC, US2000/US500, AUD/EUR, XAG/XPT, AUDJPY/USDJPY). Resistían en 5 años de backtest; se pueden reconsiderar con evidencia nueva.

**Reglas clave de 2.2–2.3:**
- Reserva de 1% de riesgo para la ruptura asiática: las demás no pueden llenar el tope de 3%.
- Autocontrol estadístico: z frente al backtest en 30 operaciones; −2 → mitad de riesgo; −3 → pausa de 30 días.
- Ejecutor: espera spread normal y reintenta recotizaciones.

## 4. Plan de riesgo
- Primera semana de Aurum en la PC: **1%** por operación, 3% abierto, stop diario −3%.
- Después: **2%** (en `aurum_config.json`: riesgo_por_operacion 0.02, riesgo_abierto_max 0.06, perdida_diaria_max 0.06, reservas_riesgo.ruptura_asiatica 0.02 y lo mismo en `topes_auditor`). Medido con bootstrap: año típico ~+40%, año malo ~−18% (si la ventaja en vivo es la mitad).
- 3% o más: NO (más de 50% de probabilidad de caer más de 40%).
- Retos de fondeo: siempre 1% (Copiador + Supervisor de fondeo).

## 5. Pendientes (en orden)
1. **Instalar Aurum 2.3 en la PC Windows del usuario** (está fuera de casa): Python 3 con "Add to PATH" → `pip install MetaTrader5` → MT5 con la demo 10076749 y Algo Trading encendido → descomprimir `aurum.zip` → `INICIAR_TODO.bat` → en Windows "Suspender: nunca". Telegram NO es necesario: todo se ve en `panel.html`. Opcional: Chrome Remote Desktop para verlo desde el celular.
2. Cuando Aurum corra: **pausar las tareas programadas** de la demo 10076749 (ruptura y estrategias diarias) para no duplicar operaciones.
3. Tras 1 semana sin problemas: subir a 2%.
4. Investigación: re-verificar los pares en el simulador (la versión en vivo no reproducía el backtest), diversificar para depender menos del oro.
5. Más adelante: reto de fondeo de $5k al 1% (estudio: 37 aprobados de 44 fechas de inicio en la simulación, 0 fallidos).

## 6. Tareas programadas (atadas al chat original)
| Tarea | Horario | Nota |
|---|---|---|
| Ruptura asiática oro (demo 100k) | cada hora :03, 07–16 UTC, lun–vie | Opera con Axi |
| Estrategias diarias (demo 100k) | 23:10 UTC dom–jue | IBS ya quitada |
| Experimento USDJPY (demo 5k) | cada hora :07, lun–vie | 20 ventas abiertas el 23-nov (~159.12 y ~159.07, SL y TP en el broker) |
| Investigación semanal | sábados 10:17 MTY | Independiente: sobrevive aunque se borre el chat |

⚠️ Las tres primeras **dependen del chat original**: si se borra, dejan de funcionar (la organización no permite conectar Axi a tareas independientes). En ese caso, la demo solo se opera cuando Aurum corra en la PC, o pidiéndole a Claude en el proyecto que revise y opere a mano.

## 7. Lecciones que no se deben olvidar
- Las reglas de capacidad (tope de riesgo, autocontrol) pueden costar más que cualquier estrategia: medirlas siempre en el simulador.
- Antes de comparar variantes, verificar que el simulador sea determinista (PYTHONHASHSEED=0) y no cambiar código mientras corren.
- El "efecto lunes" del S&P 500 es real pero delgado (~+0.035R tras swap): no se opera.
- Nada de martingala, grid sin SL ni promediar pérdidas. Todo con SL. No conectar cuentas a herramientas externas no verificadas.
