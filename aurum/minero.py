"""
MINERO — descarga y guarda las velas de todos los mercados del universo en datos.db (SQLite).
Las actualiza cada 6 horas. Explorador y Sombra leen de aquí.
Ejecutar:  python minero.py           (o  python minero.py --una-vez)
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_DB = os.path.join(CARPETA, "datos.db")
CANTIDAD = {"D1": 1400, "H1": 6500}


def conectar_db():
    con = sqlite3.connect(RUTA_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS velas (simbolo TEXT, tf TEXT, time INTEGER, open REAL, high REAL, low REAL,
                   close REAL, spread REAL, PRIMARY KEY (simbolo, tf, time))""")
    return con


def leer_velas(simbolo, tf):
    """Para Explorador/Sombra: devuelve (tiempos, o, h, l, c, costo) con costo = 2 × spread mediano."""
    con = conectar_db()
    filas = con.execute("SELECT time, open, high, low, close, spread FROM velas WHERE simbolo=? AND tf=? ORDER BY time", (simbolo, tf)).fetchall()
    con.close()
    if not filas:
        return None
    sp = sorted(f[5] for f in filas)[len(filas) // 2]
    t = [datetime.fromtimestamp(f[0], timezone.utc).replace(tzinfo=None) for f in filas]
    return t, [f[1] for f in filas], [f[2] for f in filas], [f[3] for f in filas], [f[4] for f in filas], 2 * sp


def actualizar(mt5, cfg):
    con = conectar_db()
    tfs = {"D1": mt5.TIMEFRAME_D1, "H1": mt5.TIMEFRAME_H1}
    # la hora de las velas de MT5 es la del servidor: la paso a UTC
    tick = mt5.symbol_info_tick("XAUUSD")
    offset = round((tick.time - time.time()) / 3600) if tick and abs(time.time() - tick.time) < 3 * 3600 + 120 else 0
    total = 0
    for tf, simbolos in cfg["universo"].items():
        for s in simbolos:
            mt5.symbol_select(s, True)
            r = mt5.copy_rates_from_pos(s, tfs[tf], 1, CANTIDAD[tf])
            if r is None or len(r) == 0:
                print(f"Minero: sin datos de {s} {tf}")
                continue
            punto = mt5.symbol_info(s).point
            filas = [(s, tf, int(x["time"]) - offset * 3600, float(x["open"]), float(x["high"]), float(x["low"]),
                      float(x["close"]), float(x["spread"]) * punto) for x in r]
            con.executemany("INSERT OR REPLACE INTO velas VALUES (?,?,?,?,?,?,?,?)", filas)
            total += len(filas)
    con.commit()
    con.close()
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC | Minero: {total} velas actualizadas en datos.db")


def main():
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f"No conecta con MetaTrader 5: {mt5.last_error()}")
    while True:
        cfg = json.load(open(RUTA_CONFIG, encoding="utf-8"))
        try:
            actualizar(mt5, cfg)
        except Exception as e:
            print(f"Minero: error (sigo): {e!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(6 * 3600)


if __name__ == "__main__":
    main()
