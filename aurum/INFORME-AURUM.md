# Informe de construcción de Aurum (lunes 23 de noviembre de 2026)

Meta: tener el mejor equipo de bots posible antes de las 4:00 pm (hora de Monterrey).

| Fase | Estado | Hora (MTY) | Versión |
|---|---|---|---|
| 4 · Metas y fondeo | ✅ Lista | 10:15 | 1.3 |
| 5 · Operación | ✅ Lista | 10:22 | 1.4 |
| 6 · Aprendizaje | ✅ Lista | 10:25 | 1.5 |
| 7 · Ejecución y análisis | ✅ Lista | 10:28 | 1.6 |
| 8 · Prueba general del equipo completo | ✅ Lista | 10:34 | 1.7 |
| 9 · Centralita, prompt maestro v1.2 y skills | ✅ Lista | 10:38 | 1.8 |
| 10 · Panel multicuenta | ✅ Lista | 10:40 | 1.9 |
| 11 · Revisión de código y prueba de un año completo | ✅ Lista | 10:41 | 1.9.1 |
| 12 · Muchas más estrategias (34 mercados) | ✅ Lista | 13:40 | 2.2 |
| 13 · Eliminar las que perdieron | ✅ Lista | 13:50 | 2.3 |
| 14 · Instalación en tu PC | ⏳ Te toca a ti (te guío) | — | 2.3 |

## Equipo actual: 23 bots
| # | Bot | Fase | Qué hace |
|---|---|---|---|
| 1 | Aurum | 1 | Opera las 4 estrategias validadas en la demo de $100k |
| 2 | Guardián | 1 | Freno de emergencia: SL faltantes, −3% diario y −10% total |
| 3 | Contador | 1 | Estadísticas en vivo frente al backtest |
| 4 | Mensajero | 1 | Envía los avisos a Telegram |
| 5 | Minero | 2 | Guarda las velas de 16 mercados |
| 6 | Vigía + Cazanoticias | 2 | Régimen, volatilidad, VIX, noticias, Fed, modo precaución |
| 7 | Explorador | 3 | Prueba unas 30,000 variantes cada sábado |
| 8 | Sombra | 3 | Practica en papel las estrategias candidatas |
| 9 | Estratega de metas | 4 | Mide el avance, calcula la probabilidad de llegar a la meta y protege lo ganado |
| 10 | Supervisor de fondeo | 4 | Hace cumplir las reglas del reto con margen |
| 11 | Copiador | 4 | Copia las operaciones de Aurum a cuentas de fondeo |
| 12 | Mecánico | 5 | Avisa si un bot se congela o si Algo Trading se apaga |
| 13 | Respaldo | 5 | Copia de seguridad diaria (últimos 14 días) |
| 14 | Panel | 5 | Tablero `panel.html` que se actualiza cada minuto |
| 15 | Auditor | 6 | Revisa cada hora que se cumplan las reglas, sin confiar en ningún otro bot |
| 16 | Archivista | 6 | Guarda el contexto de cada operación y lleva un diario profesional |
| 17 | Profesor | 6 | Cada domingo compara los resultados en vivo con el backtest y escribe las lecciones |
| 18 | Abogado del diablo | 6 | Intenta romper cada estrategia con pruebas de estrés |
| 19 | Ejecutor inteligente | 7 | Evita entrar con el spread disparado y reintenta si el broker recotiza |
| 20 | Estacional | 7 | Busca patrones de calendario (mes, día de la semana, cambio de mes) |
| 21 | Analista COT | 7 | Mide el posicionamiento de los grandes especuladores según la CFTC |
| 22 | Calendario de resultados | 7 | Avisa cuándo reportan NVIDIA, Apple, Microsoft y otras gigantes |
| 23 | Centralita | 9 | Controlas todo desde Telegram: `/estado`, `/pausa`, `/reanudar`, `/cerrar_todo CONFIRMO` |

## Fase 5: qué se probó
- **Mecánico:** detectó un bot con 60 minutos sin latido y avisó solo una vez, sin repetir. Muestra correctamente los bots que no tienen datos.
- **Respaldo:** creó el zip con las bases de datos copiadas de forma segura. Se comprobó que **no** incluye `telegram.json` ni los archivos AUTORIZO.
- **Panel:** se ve bien en computadora y en celular, en modo claro y oscuro.

## Fase 6: qué se probó
- **Auditor:** con posiciones trampa detectó los 6 problemas: una posición sin SL, una que arriesgaba de más, una de origen desconocido, una duplicada, el riesgo total excedido y el deslizamiento de $2.12 de nuestra compra de oro de esta mañana. También detectó una configuración manipulada al 5%.
- **Archivista y Profesor:** con 60 operaciones simuladas, guardaron el contexto, unieron cada contexto con su resultado y separaron una estrategia "dentro de lo esperado" de otra "en pérdida, vigilar".

## 😈 Hallazgo real del Abogado del diablo (datos reales de Axi)
| Estrategia | Operaciones | Expectativa | Costos ×2 | Periodos ganadores | Probabilidad de no tener ventaja | Veredicto |
|---|---|---|---|---|---|---|
| Ruptura asiática (oro) | 195 | +0.23R | +0.22R | 4 de 4 | 1% | ✅ RESISTE |
| RSI(2) (S&P 500) | 52 | +0.19R | +0.18R | 4 de 4 | 0% | ✅ RESISTE |
| IBS (S&P 500) | 128 | +0.12R | +0.12R | 4 de 4 | 0% | ✅ RESISTE |
| Donchian (oro) | 38 | +0.31R | +0.30R | 3 de 4 | 16% | ⚠️ DUDOSA |
| Donchian (Ethereum) | 54 | +0.24R | +0.23R | 4 de 4 | 17% | ⚠️ DUDOSA |

**Qué significa:** las tres estrategias de reversión y la ruptura son sólidas. Donchian gana, pero con pocas operaciones: hay entre 16% y 17% de probabilidad de que su ventaja sea suerte. **Recomendación:** mantener Donchian, que el Profesor la vigile y, si se compra un reto de fondeo, darle prioridad a la ruptura, a RSI(2) y a IBS.

## Fase 7: qué se probó
- **Ejecutor:** en el *rollover*, con un spread 4 veces mayor de lo normal, **esperó**. Con el spread normal entró, y cuando el broker recotizó reintentó moviendo el SL y el TP con el precio, así que el riesgo quedó en $1,000 exactos (1%). La señal se publicó para el Copiador.
- **Estacional:** con datos reales de Axi. Corregí un desfase: las velas diarias abren a las 22:00 UTC del día anterior, por eso el viernes aparecía como "domingo".
- **COT y Calendario de resultados:** probé la lógica con datos en el formato oficial de la CFTC y de Nasdaq. Este servidor tiene esos sitios bloqueados, así que la descarga real se probará en tu PC.

## 📅 Hallazgo del Estacional (datos reales)
- **El S&P 500 sube +0.18% de media los lunes** (t = 3.2, evidencia fuerte; los demás días son ruido). Incluye el salto del fin de semana. Queda anotado como hipótesis para el Explorador; **no** se opera hasta que pase el filtro anti-suerte.
- Noviembre no tiene un patrón fiable en ningún mercado: solo hay 5 años de datos y todo es ruido.

## 🧪 Fase 8: prueba general del equipo completo
Todo el equipo operó **4 meses de velas reales de Axi** (23 jul – 20 nov 2026) contra un MetaTrader simulado, con la cuenta maestra de $100k y una cuenta copiada de $5k.

| Resultado | Dato |
|---|---|
| Errores de los bots | **0** (encontré y corregí 1 en el Archivista) |
| Operaciones de Aurum | 67 (ruptura 51, IBS 9, RSI2 5, Donchian 2) |
| Cuenta maestra $100k | **+7.7%** en 4 meses ($107,705) |
| Riesgo de cada entrada | entre $994 y $1,097, cerca del 1% |
| Fidelidad del Copiador | **56 de 56 copias idénticas** (misma hora, dirección y precio) |
| Falsas alarmas | 0 (el Guardián y el Auditor no molestaron sin motivo) |

**Pruebas de estrés (catástrofes a propósito):**
| Catástrofe | Reacción |
|---|---|
| 5 lotes de oro sin SL | El Guardián puso SL de emergencia con riesgo de 1% |
| La cuenta cae 11% | El Guardián cerró todo y bloqueó; Aurum **no abrió nada** |
| Alguien sube el riesgo a 5% | El Auditor lo detectó |
| Algo Trading apagado | El Mecánico avisó |

**Decisión para el reto de fondeo (con datos):**
| Riesgo en la cuenta de $5k | Señales copiadas | Resultado en 4 meses | Peor caída |
|---|---|---|---|
| 0.5% | 56 de 69 | +4.2% | 2.2% |
| **1%** ✅ | **67 de 69** | **+7.6%** | **4.2%** |

Con 0.5%, el lote mínimo del oro (0.01) no cabe en 1 de cada 5 señales. Ahora el Copiador usa **1%** por defecto, y el Estratega lo baja solo a 0.5% cuando te acercas al objetivo o al límite. Ojo: es un solo periodo de 4 meses; el resultado real puede ser mejor o peor.

## 📟 Fase 9: control desde el celular y lo aprendido
**Centralita (Telegram):**
- Probé los 8 comandos. `/cerrar_todo` pide confirmación y solo actúa en la demo de Aurum.
- Solo obedece a **tu** chat.
- `/reanudar` **no** quita los bloqueos de seguridad.
- En la simulación, durante una pausa de 10 días, Aurum abrió **0** operaciones.

**Hueco de seguridad corregido:** si había una pausa manual, el stop diario de −3% del Guardián no se activaba. Ahora la pausa usa su propio archivo y el stop diario siempre funciona.

**Efecto lunes en el S&P 500 (investigación completa):** es real, porque gana en ambos periodos (+0.04R y +0.08R) con 62% de acierto. Pero es delgado: después del swap del fin de semana quedan unos +0.035R por operación, así que **no se opera**. Queda en observación.

**Prompt maestro v1.2:** incluye el equipo de 23 bots, los veredictos del Abogado del diablo, el riesgo de 1% para retos y nuevas reglas: nunca esquivar al Guardián, al Supervisor ni al Auditor, y nunca crear el archivo AUTORIZO por ti.

**Skills (trading-pro 1.14.0):** Donchian, laboratorio y fondeo ya tienen los hallazgos de hoy.

## 📊 Fase 10: Panel multicuenta
- El Panel ahora muestra **todas tus cuentas de fondeo** en una tabla: balance, equity, copias abiertas, progreso hacia la meta, probabilidad de lograrla y si están bloqueadas.
- También muestra los veredictos del Abogado del diablo, el posicionamiento COT y los resultados de empresas gigantes de la semana.
- Corregí una tabla que se salía de la pantalla. Verifiqué que en computadora y en celular la página no se desplaza hacia los lados.

## 🔍 Fase 11: revisión de código y prueba de un año completo
**Error corregido en el Ejecutor:** recordaba para siempre cuándo empezó a esperar una señal. Si la señal volvía días después, creía que ya había esperado más de 3 horas y entraba aunque el spread estuviera disparado. Ya está corregido y probado.

**El equipo completo operando 11 meses de datos reales (dic 2025 – nov 2026):**
| Dato | Resultado |
|---|---|
| Errores de los bots | 0 |
| Operaciones | 191 (ruptura 148, IBS 21, RSI2 11, Donchian 11) |
| Cuenta maestra $100k | Balance **+22.7%**, equity **+28.7%** |
| Peor caída | **9.7%** (feb–abr 2026, racha mala de la ruptura asiática en oro) |
| Copiador | **175 de 175** copias idénticas |

⚠️ **Lección importante:** al 1%, el portafolio llegó a caer casi 10%, que es el límite típico de un reto. Por eso el Supervisor y el Estratega no son opcionales en una cuenta de fondeo.

**¿Cuántas veces pasa un reto de $5k?** (+8% objetivo, −10% total, −5% diario; empezando en 44 fechas distintas del año)
| Riesgo | Pasa | Falla | Días medianos para pasar |
|---|---|---|---|
| 0.5% | 26 | 0 | 138 |
| **1% con protecciones** ✅ | **37** | **0** | **56** |
| 1.5% con protecciones | 38 | 3 | 28 |
Las fechas que no aparecen no terminaron porque se acabaron los datos. **Se queda 1%:** con 1.5% ya hay retos perdidos.

**¿En qué podría estar equivocado?** Es un solo año, las ventanas se solapan y el resultado depende mucho del oro. No incluye el ~10% de señales donde el lote mínimo no cabe ni el costo del reto. **No es una garantía:** es la mejor evidencia que hay hoy.

## 🎯 Qué sigue (tú eliges)
1. **Instalar Aurum en tu PC hoy**: te guío paso a paso (Python, Telegram, `INICIAR_TODO.bat`). Es lo que más acerca el resultado real.
2. **Elegir la empresa de fondeo**: comparo precios y reglas actuales para el reto de $5k que mejor encaje con estos números.
3. **Más investigación**: que el Explorador pruebe nuevas familias de estrategias para diversificar y depender menos del oro.

## 🚀 Fase 12 (en curso): muchas más estrategias
**Datos:** descargué 30 mercados nuevos de Axi, con 5 años de velas diarias cada uno. Ya son **34 mercados**: índices de EE.UU., Europa y Asia, oro, plata, platino, cobre, petróleos, gas, 13 divisas y 6 criptos.

**Búsqueda:**
| Prueba | Variantes | Aprobadas por el filtro anti-suerte |
|---|---|---|
| Explorador (13 familias × 34 mercados) | 52,392 | 23 zonas (el azar logra 20%) |
| Pares (familia nueva: reversión del ratio) | 4,464 | 7 de 31 pares |

**Abogado del diablo** (solo entra lo que RESISTE y diversifica):
| Nueva estrategia | Mercado | Ops en 5 años | Expectativa | Prob. de suerte |
|---|---|---|---|---|
| Par USD/CAD contra USD/CHF | Divisas | 89 | +0.37R | 3% |
| Par Litecoin contra Bitcoin | Cripto | 87 | +0.36R | 2% |
| Par Russell 2000 contra S&P 500 | Índices | 52 | +0.31R | 3% |
| Par AUD/USD contra EUR/USD | Divisas | 51 | +0.25R | 6% |
| Par plata contra platino | Metales | 46 | +0.32R | 3% |
| Par AUD/JPY contra USD/JPY | Divisas | 45 | +0.89R | 2% |
| NR7 (ruptura tras día estrecho) | FTSE 100 | 45 | +0.48R | 2% |
| NR7 | GBP/USD | 47 | +0.29R | 8% |
| MACD | DAX | 44 | +0.17R | 3% |
| MACD | Solana | 51 | +0.46R | 3% |
| Cambio de mes | Oro | 59 | +0.24R | 3% |

Con estas, Aurum pasa de **4 estrategias en 10 mercados a 15 estrategias en 23 mercados**.

**Cómo entran en Aurum (2.2):** Aurum ahora usa el motor del laboratorio directamente. Comprobé que en vivo da **las mismas entradas que el backtest** (35/35, 41/41 y 45/45; en el cambio de mes, 45/46 por un festivo). Desde ahora, cualquier estrategia que aprueben el Explorador y el Abogado se activa en Aurum solo con la configuración. Los pares arrancan con riesgo a la mitad hasta tener 20 operaciones en vivo.

**Reglas que estorbaban, corregidas (tenías razón):**
1. **Autocontrol:** la regla vieja ("pausar si pierde 8R en 20 operaciones") **apagó para siempre la ruptura asiática** después de una racha mala normal. Ahora compara con lo que promete el backtest: con 2 desviaciones por debajo baja el riesgo a la mitad, con 3 pausa 30 días, y se recupera sola.
2. **Espacio de riesgo:** las estrategias diarias ocupaban el 3% durante días y la ruptura (la mejor) se quedaba fuera. Ahora se le **reserva 1%**, sin subir el 3% total.
3. **Grupos correlacionados:** límite al riesgo conjunto de los índices de EE.UU., porque caen juntos.

## ✅ Resultado final de la fase 12 (simulación de un año real, dic 2025 – nov 2026)
| Configuración | Balance | Caída máx. |
|---|---|---|
| Antes de hoy (4 estrategias, sin reserva, autocontrol viejo) | $103,010 | 16.1% |
| **Aurum 2.2 (la que instalas)**: 9 estrategias, reserva para la ruptura, autocontrol nuevo, al 1% | **$136,667 (+37%)** | **9.0%** |

Pruebas finales: **0 errores** en el año completo. Las 4 pruebas de estrés quedaron contenidas: SL de emergencia, bloqueo total por −11%, riesgo manipulado y Algo Trading apagado.

**Riesgo (medido, no adivinado):**
| Riesgo/operación | Año típico* | Año malo* | Prob. de caída > 40% |
|---|---|---|---|
| 1% | +21% | −8% | 0.3% |
| **2%** ✅ | **+40%** | **−18%** | **18%** |
| 3% | +55% | −31% | 55% ❌ |

\*Suponiendo que en vivo la ventaja sea la mitad que en la simulación (lo prudente).

**Plan:** 1 semana al 1% en tu PC para comprobar que todo funciona; después, **2%**. Los retos de fondeo siempre al 1%.

**Pares:** los 6 resisten en 5 años de backtest, pero la versión en vivo no reproduce el backtest en el simulador de 2026. Encontré y corregí una causa (se reabrían con el ratio ya pasado de su stop), pero **quedan apagados** hasta verificarlo. No enciendo nada que no pase el simulador.

**¿En qué podría estar equivocado?**
- Es un solo año de simulación y la ruptura asiática pone casi todo el resultado (+$32,577). Si el oro cambia de comportamiento, el portafolio lo sentirá.
- Las 5 estrategias nuevas operan poco (1–4 veces en el año): su aporte real se verá en meses.
- NR7 en GBP/USD perdió en este año (−$5,168) aunque resiste en 5 años. El autocontrol nuevo la frenará sola si sigue así.

## 🧹 Fase 13: fuera lo que pierde (a pedido tuyo)
| Eliminada | Por qué |
|---|---|
| 6 pares | Perdieron en todas las simulaciones (−$4,500 a −$22,000) |
| NR7 en GBP/USD | Perdió en todas (−$4,000 a −$7,800) |
| IBS (Nasdaq y S&P) | Perdió en 5 de 6 (−$1,000 a −$4,600) |

**Aurum 2.3 = 7 estrategias** (ruptura asiática, Donchian, RSI2, NR7 en FTSE, MACD en DAX, MACD en Solana, cambio de mes en oro). Año simulado: **$140,963 (+41%), caída máxima 8.2%, 0 errores.** Todas las que quedan ganaron.

Nota: el Explorador y el Abogado del diablo pueden volver a proponer alguna si en el futuro su evidencia mejora. Nada se pierde: queda registrado.

## Seguridad (sin cambios)
- Aurum solo opera la demo 10076749.
- Las cuentas reales solo se usan con tu firma (`AUTORIZO_<cuenta>.txt`).
- Ningún bot puede subir el riesgo: el Estratega y el Vigía solo pueden bajarlo.
