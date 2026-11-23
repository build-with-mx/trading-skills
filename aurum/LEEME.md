# Aurum — robot de trading autónomo

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

## Instalación (una sola vez)
1. Instala **Python 3** desde https://www.python.org/downloads/ — marca **"Add Python to PATH"**.
2. Abre la terminal (tecla Windows → escribe `cmd` → Enter) y ejecuta:
   ```
   pip install MetaTrader5
   ```
3. Descomprime esta carpeta `aurum` en tu PC (por ejemplo en el Escritorio).
4. Abre **MetaTrader 5 de escritorio**, inicia sesión en la **demo 10076749** y pulsa el botón **"Algo Trading"** (debe quedar en verde).

## Arrancar
En la terminal:
```
cd Desktop\aurum
python aurum.py
```
Verás mensajes como `Aurum 1.0.0 iniciado`. **Deja la ventana abierta** (puedes minimizarla). La PC no debe apagarse ni suspenderse mientras opere.

**Primera vez (opcional, recomendado):** abre `aurum_config.json` y pon `"solo_observar": true` durante unas horas: Aurum registrará las señales sin operar. Luego vuelve a `false`.

## Detener
Pulsa **Ctrl + C** en la terminal. Las posiciones abiertas conservan su Stop Loss y Take Profit.

## Archivos que genera (mándaselos a Claude para revisar)
- `aurum_operaciones.csv` — cada apertura y cierre.
- `aurum_eventos.log` — todo lo que hace y por qué (señales, bloqueos por noticias, errores).
- `aurum_estado.json` — memoria interna (no lo edites).

## Cómo se actualiza
Claude investiga estrategias y, cuando una nueva pasa las pruebas, te envía un `aurum_config.json` nuevo (o una nueva versión de `aurum.py`). Reemplaza el archivo y reinicia Aurum. Más adelante se puede activar la descarga automática desde GitHub (`config_remota`).

**Importante:** mientras Aurum opere la demo 10076749, avisa a Claude para que pause sus tareas programadas en esa cuenta y no se dupliquen operaciones.
