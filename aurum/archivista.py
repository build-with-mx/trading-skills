"""
ARCHIVISTA — guarda el CONTEXTO de cada operación en el momento en que Aurum la abre, para poder aprender después
("¿la ruptura gana más con volatilidad alta?", "¿Donchian pierde en rango?").
  • Lee las aperturas que Aurum publica (senales_maestro.jsonl) y anota: régimen y volatilidad del mercado (Vigía),
    VIX, modo precaución, factor de riesgo de metas, hora y día de la semana.
  • Lo guarda en aurum.db → tabla "contexto" (clave = número de posición, la misma que usa el Contador).
  • Escribe diario_operaciones.md: el diario de trading que llevaría un profesional (contexto + resultado).
Ejecutar:  python archivista.py      (o  python archivista.py --una-vez)
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

from copiador import leer_senales

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(CARPETA, "aurum.db")
RUTA_SENALES = os.path.join(CARPETA, "senales_maestro.jsonl")
RUTA_ESTADO = os.path.join(CARPETA, "archivista_estado.json")
RUTA_DIARIO = os.path.join(CARPETA, "diario_operaciones.md")
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def cargar(nombre, defecto):
    try:
        with open(os.path.join(CARPETA, nombre), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def contexto_de(ev, vigia, metas):
    """Función pura: arma el registro de contexto de una apertura."""
    t = datetime.fromisoformat(ev["t"])
    m = vigia.get("mercados", {}).get(ev["simbolo"], {})
    return {"posicion": int(ev["id"]), "hora_utc": t.isoformat(), "estrategia": ev["estrategia"], "simbolo": ev["simbolo"],
            "direccion": "COMPRA" if ev["direccion"] == 1 else "VENTA", "regimen": m.get("regimen", "?"),
            "volatilidad": m.get("volatilidad", "?"), "atr_ratio": m.get("atr_ratio"), "tendencia_20d": m.get("tendencia_20d", "?"),
            "vix": vigia.get("vix"), "precaucion": int(bool(vigia.get("modo_precaucion"))),
            "factor_meta": metas.get("factor_riesgo", 1.0), "hora": t.hour, "dia": DIAS[t.weekday()]}


def crear_tabla(con):
    con.execute("""CREATE TABLE IF NOT EXISTS contexto (posicion INTEGER PRIMARY KEY, hora_utc TEXT, estrategia TEXT, simbolo TEXT,
                   direccion TEXT, regimen TEXT, volatilidad TEXT, atr_ratio REAL, tendencia_20d TEXT, vix REAL, precaucion INTEGER,
                   factor_meta REAL, hora INTEGER, dia TEXT)""")


def guardar(regs):
    con = sqlite3.connect(RUTA_DB)
    crear_tabla(con)
    con.executemany("""INSERT OR REPLACE INTO contexto VALUES (:posicion,:hora_utc,:estrategia,:simbolo,:direccion,:regimen,:volatilidad,
                       :atr_ratio,:tendencia_20d,:vix,:precaucion,:factor_meta,:hora,:dia)""", regs)
    con.commit()
    con.close()


def escribir_diario():
    con = sqlite3.connect(RUTA_DB)
    crear_tabla(con)
    try:
        filas = con.execute("""SELECT c.hora_utc, c.estrategia, c.simbolo, c.direccion, c.regimen, c.volatilidad, c.vix, c.precaucion,
                                      o.neto, o.R, o.cerrada FROM contexto c LEFT JOIN operaciones o ON o.posicion = c.posicion
                               ORDER BY c.hora_utc DESC LIMIT 200""").fetchall()
    except sqlite3.OperationalError:  # el Contador aún no creó "operaciones"
        filas = [r + (None, None, None) for r in con.execute("""SELECT hora_utc, estrategia, simbolo, direccion, regimen, volatilidad, vix,
                 precaucion FROM contexto ORDER BY hora_utc DESC LIMIT 200""").fetchall()]
    con.close()
    lineas = ["# Diario de operaciones (Archivista)", "", "| Abierta (UTC) | Estrategia | Mercado | Dir. | Régimen | Volatilidad | VIX | Precaución | Resultado |",
              "|---|---|---|---|---|---|---|---|---|"]
    for h, e, s, d, reg, vol, vix, pre, neto, R, cerr in filas:
        res = "abierta" if neto is None else f"{neto:+,.2f}$ ({R:+.2f}R)"
        lineas.append(f"| {h[:16]} | {e} | {s} | {d} | {reg} | {vol} | {vix or '—'} | {'sí' if pre else 'no'} | {res} |")
    with open(RUTA_DIARIO, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))


def ciclo(est):
    eventos, est["byte"] = leer_senales(RUTA_SENALES, est.get("byte", 0))
    regs = [contexto_de(ev, cargar("vigia_estado.json", {}), cargar("metas_estado.json", {})) for ev in eventos if ev.get("accion") == "ABRIR"]
    if regs:
        guardar(regs)
    if regs or est.get("diario") != datetime.now(timezone.utc).strftime("%Y-%m-%d %H"):
        if os.path.exists(RUTA_DB):
            escribir_diario()
        est["diario"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H")
    with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f)


def main():
    est = cargar("archivista_estado.json", {"byte": 0})
    while True:
        try:
            ciclo(est)
        except Exception as e:
            print(f"Archivista: error (sigo): {e!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(10)


if __name__ == "__main__":
    main()
