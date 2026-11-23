---
name: bot-mt5-python
description: "Crear, explicar y depurar bots de trading en Python con la librería MetaTrader5 (Windows): conectar al terminal, leer precios y velas, calcular lote, enviar órdenes con SL/TP, gestionar posiciones y registrar todo. Usar cuando el usuario diga 'hazme un bot', 'automatizar mi estrategia', 'script de MT5', 'error en MetaTrader5 python', o quiera aprender Python para trading."
---

# Bots MT5 con Python

El usuario aprende Python con la librería `MetaTrader5` en **Windows** (la librería solo funciona en Windows con el terminal MT5 abierto). Explicar línea por línea si lo pide; código simple antes que elegante. Español.

## Reglas para todo bot
1. **Solo cuenta demo** por defecto: el bot verifica `account_info().trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO` y se detiene si no lo es. Quitar esa protección solo si el usuario lo pide explícitamente, tras validar en demo.
2. Siempre SL y TP en la orden. Lote calculado por riesgo (1%), nunca fijo a ciegas.
3. Límites internos: máx. operaciones/día, stop diario 3%, una posición por símbolo, horario de operación.
4. `magic` number propio para identificar sus órdenes. Registro (log) a archivo CSV de cada acción.
5. Manejar errores: revisar `retcode` de `order_send` y `mt5.last_error()`.
6. Una estrategia va al bot **después** de pasar `backtesting-estrategias`.

## Plantilla
`templates/bot_base.py`: bot de cruce de medias en XAUUSD H1 con todas las protecciones. Para otra estrategia, reemplazar solo la función `senal()`. Entregar el archivo completo al usuario (en /home/user) e indicar:
```
pip install MetaTrader5 pandas
python bot_base.py
```
con MT5 abierto y logueado en la demo, y "Algo Trading" activado.

## Errores comunes
| Síntoma | Causa / solución |
|---|---|
| `initialize() failed` | MT5 cerrado, otra ruta de instalación (`mt5.initialize(path=...)`), o Python de 32 bits |
| retcode 10027 | "Algo Trading" desactivado en el terminal |
| retcode 10030 | `type_filling` no soportado: probar `ORDER_FILLING_IOC` o `FOK` |
| retcode 10016 | SL/TP inválidos: muy cerca (ver `trade_stops_level`) o del lado equivocado |
| retcode 10014 | Volumen inválido: redondear a `volume_step` y respetar `volume_min` |
| símbolo None | `mt5.symbol_select("XAUUSD", True)` y verificar el nombre exacto en Axi |

## Alternativa sin Windows
Claude puede gestionar la demo directamente con el conector Axi (get_mt5_candles, open_mt5_position, etc.) y tareas programadas, sin bot propio.

## Reglas de seguridad (heredadas)
- Riesgo máx. 1% por operación, 2% abierto total, stop diario 3%. Siempre con Stop Loss.
- Cuentas reales: nunca operar sin confirmación explícita del usuario en ese mensaje.
- Sin garantías; Claude no es asesor financiero.
