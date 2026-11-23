# Aurum 1.1 — equipo de bots de trading

Opera solo, 24/5, en tu **demo MT5 10076749** las estrategias que pasaron el filtro anti-suerte:

| Estrategia | Mercados | Revisa |
|---|---|---|
| Ruptura asiática | Oro (XAUUSD) | Cada vela de 1 hora |
| Donchian (tendencia) | Oro, Ethereum, Bitcoin | Cada vela diaria |
| RSI(2) (reversión) | S&P 500, Nasdaq, Dow, Russell 2000 | Cada vela diaria |
| IBS (reversión) | Nasdaq, S&P 500 | Cada vela diaria |

**Protecciones incluidas**
- Solo opera la cuenta **10076749 en modo demo**: si detecta otra cuenta (por ejemplo la real), no arranca.
- Riesgo de **1% por operación**, máximo **3% abierto** entre todas, **stop diario de −3%**.
- **Filtro de noticias**: no abre 30 min antes ni después de noticias de alto impacto de EE.UU. (calendario de Forex Factory).
- **Autocontrol**: si una estrategia suma menos de −8R en sus últimas 20 operaciones en vivo, se pausa sola.
- Todas las operaciones con **Stop Loss** en el broker.
- **Adopta** las posiciones que Claude ya abrió (oro con TP = ruptura; oro/ETH/BTC sin TP = Donchian) y las gestiona.

## El equipo (fase 1)
| Bot | Archivo | Qué hace |
|---|---|---|
| **Aurum** (director/operador) | `aurum.py` | Opera las estrategias y te avisa de cada apertura y cierre |
| **Guardián** 🛡️ | `guardian.py` | Freno de emergencia independiente: pone SL a posiciones que no lo tengan, cierra todo si el día pierde −3% (bloquea hasta mañana) o si la cuenta cae −10% desde su máximo (bloqueo total), avisa de riesgo o lotes anormales y de desconexiones de MT5 |
| **Contador** 📊 | `contador.py` | Registra cada operación en `aurum.db`, genera `contador_reporte.md` cada hora (por estrategia: acierto, R, expectativa vivo vs backtest, swap, deslizamiento) y te manda un resumen diario |
| **Mensajero** 📱 | `mensajero.py` | Envía todos los avisos a tu Telegram |

## Instalación (una sola vez)
1. Instala **Python 3** desde https://www.python.org/downloads/ — marca **"Add Python to PATH"**.
2. Abre la terminal (tecla Windows → escribe `cmd` → Enter) y ejecuta:
   ```
   pip install MetaTrader5
   ```
3. Descomprime esta carpeta `aurum` en tu PC (por ejemplo en el Escritorio).
4. Abre **MetaTrader 5 de escritorio**, inicia sesión en la **demo 10076749** y pulsa el botón **"Algo Trading"** (debe quedar en verde).

## Telegram (5 minutos, recomendado)
1. En Telegram busca **@BotFather** → escribe `/newbot` → ponle nombre (p. ej. "Mi Aurum") → copia el **token** que te da.
2. Abre el chat de tu nuevo bot y escríbele "hola".
3. En la terminal, dentro de la carpeta aurum:  `python obtener_chat_id.py`  → pega el token. Se crea `telegram.json`.
4. Prueba:  `python mensajero.py`  → debe llegarte un mensaje al celular.
**No compartas `telegram.json` con nadie** (contiene la llave de tu bot).

## Arrancar
Doble clic en **`INICIAR_TODO.bat`**: se abren 3 ventanas (Guardián, Contador y Aurum). Si alguno se cae, se reinicia solo a los 15 segundos. **Deja las ventanas abiertas** (puedes minimizarlas) y que la PC no se suspenda.
(Manual: `python guardian.py`, `python contador.py`, `python aurum.py` en ventanas separadas.)

### Si el Guardián bloquea
Se crea el archivo `aurum_ALTO.flag`: Aurum deja de abrir operaciones (sí gestiona las salidas). El bloqueo diario se quita solo al día siguiente (UTC). El bloqueo TOTAL (caída de −10%) lo quitas tú borrando ese archivo, **después de revisarlo con Claude**.

**Primera vez (opcional, recomendado):** abre `aurum_config.json` y pon `"solo_observar": true` durante unas horas: Aurum registrará las señales sin operar. Luego vuelve a `false`.

## Detener
Cierra las ventanas (o Ctrl + C en cada una). Las posiciones abiertas conservan su Stop Loss y Take Profit.

## Archivos que genera (mándaselos a Claude para revisar)
- `aurum_operaciones.csv` — cada apertura y cierre.
- `aurum_eventos.log` — todo lo que hace y por qué (señales, bloqueos por noticias, errores).
- `aurum_estado.json`, `guardian_estado.json` — memoria interna (no los edites).
- `contador_reporte.md` y `aurum.db` — estadísticas del Contador.

## Cómo se actualiza
Claude investiga estrategias y, cuando una nueva pasa las pruebas, te envía un `aurum_config.json` nuevo (o una nueva versión de `aurum.py`). Reemplaza el archivo y reinicia Aurum. Más adelante se puede activar la descarga automática desde GitHub (`config_remota`).

**Importante:** mientras Aurum opere la demo 10076749, avisa a Claude para que pause sus tareas programadas en esa cuenta y no se dupliquen operaciones.
