# Aurum 1.3 — equipo de bots de trading

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

## El equipo (fases 2 y 3)
| Bot | Archivo | Qué hace |
|---|---|---|
| **Minero** ⛏️ | `minero.py` | Guarda las velas D1 (~5 años) y H1 (~1 año) de 16 mercados en `datos.db` y las actualiza cada 6 h |
| **Vigía** 🔭 | `vigia.py` | Cada 15 min: régimen (tendencia/rango), volatilidad (ATR vs media), VIX, noticias de alto impacto (resumen diario 6 am MTY) y comunicados de la Fed (**Cazanoticias**). Si hay volatilidad > 2×, 3+ estrategias perdiendo el mismo día o la cuenta cae −2% en el día → **modo precaución**: Aurum arriesga la mitad hasta el día siguiente |
| **Explorador** 🔬 | `explorador.py` | Cada sábado (y al arrancar si no hay candidatos) prueba ~30,000 variantes de 14 familias en todos los mercados con validación fuera de muestra y control al azar. Las zonas robustas entran a `candidatos.json`, marcadas si repiten una ventaja ya activa |
| **Sombra** 👻 | `sombra.py` | Practica en papel, en vivo, cada candidata. Te avisa cuando una **aprueba** (≥ 20 ops, o ≥ 10 ops y 90 días, con expectativa > 0 y ≥ 50% del backtest) o se **descarta**. Ninguna pasa a dinero sin que tú y Claude la agreguen |

## El equipo (fase 4: metas y cuentas de fondeo)
| Bot | Archivo | Qué hace |
|---|---|---|
| **Estratega de metas** 🎯 | `estratega_metas.py` | Cada hora mide el avance hacia la meta (bloque `metas`), estima con 3,000 simulaciones la probabilidad de lograrla y las semanas que faltan, y **baja el riesgo a la mitad** cuando ya llevas el 80% del camino o consumiste la mitad del margen de pérdida. **Nunca lo sube.** Resumen los domingos |
| **Supervisor de fondeo** 🏢 | `supervisor_fondeo.py` | Hace cumplir las reglas de la empresa de fondeo **con margen**: al 50% de un límite (diario o total) deja de abrir; al 80% **cierra todo** antes de que la empresa te descalifique. También: objetivo alcanzado → para; consistencia; cierre antes de noticias o del fin de semana si la empresa lo pide |
| **Copiador** 📡 | `copiador.py` | Copia las operaciones de Aurum a otra cuenta (un reto de fondeo, otra demo) con el riesgo de **esa** cuenta. No persigue el precio (señal de más de 10 min o precio movido > 25% del SL → no copia) |

### Cómo conectar una cuenta de fondeo (cuando la compres)
1. Instala el **MetaTrader 5 de la empresa de fondeo** (es un segundo programa, aparte del de Axi) e inicia sesión en el reto.
2. Copia `copiador_ejemplo.json` como `copiador_fondeo1.json` y rellena: ruta del `terminal`, número de `cuenta`, nombres de los símbolos de esa empresa (`mapa_simbolos`), y las **reglas exactas** del reto en `fondeo` y `metas`.
3. Un reto es una cuenta **real**: el Copiador solo opera si pones `"permitir_cuenta_real": true` **y** creas tú el archivo `AUTORIZO_<número de cuenta>.txt` con la palabra `AUTORIZO`. Es tu firma: sin ella no se mueve.
4. Doble clic en **`iniciar_fondeo.bat`** → abre Supervisor, Estratega y Copiador de esa cuenta. (Para otra cuenta: `iniciar_fondeo.bat copiador_fondeo2.json`.)
5. Aurum debe seguir corriendo en la demo: es la cuenta maestra que genera las señales.

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
Doble clic en **`INICIAR_TODO.bat`**: se abren 8 ventanas (Guardián, Minero, Contador, Vigía, Sombra, Explorador, Estratega y Aurum). La primera vez el Minero tarda ~1 minuto en llenar `datos.db` y el Explorador hará su primera búsqueda (unos minutos). Si alguno se cae, se reinicia solo a los 15 segundos. **Deja las ventanas abiertas** (puedes minimizarlas) y que la PC no se suspenda.
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
- `vigia_reporte.md`, `sombra_reporte.md`, `candidatos.json`, `explorador_ultimo.json` — inteligencia, práctica en papel y exploración.
- `datos.db` — velas guardadas por el Minero.
- `metas_estado.json` — avance, probabilidad y factor de riesgo del Estratega.
- `senales_maestro.jsonl`, `maestro_vivas.json` — señales que Aurum publica para los Copiadores.

## Cómo se actualiza
Claude investiga estrategias y, cuando una nueva pasa las pruebas, te envía un `aurum_config.json` nuevo (o una nueva versión de `aurum.py`). Reemplaza el archivo y reinicia Aurum. Más adelante se puede activar la descarga automática desde GitHub (`config_remota`).

**Importante:** mientras Aurum opere la demo 10076749, avisa a Claude para que pause sus tareas programadas en esa cuenta y no se dupliquen operaciones.
