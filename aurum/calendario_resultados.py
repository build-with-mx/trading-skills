"""
CALENDARIO DE RESULTADOS — vigila cuándo reportan resultados las empresas gigantes que mueven al Nasdaq y al S&P 500
(NVIDIA, Apple, Microsoft, Amazon, Alphabet, Meta, Tesla, Broadcom...).
  • Cada día a las 12:00 UTC revisa los próximos 7 días y te avisa de las que reportan, con fecha y si es antes de la
    apertura o después del cierre.
  • Si Aurum tiene posiciones abiertas en USTECH o US500 la víspera de un reporte gigante, te lo marca: es un riesgo de
    salto de precio (gap) que el Stop Loss no siempre cubre. No cierra nada: la estrategia se validó con esos días incluidos.
Escribe resultados_estado.json y resultados_reporte.md.
Ejecutar:  python calendario_resultados.py      (o  python calendario_resultados.py --ahora)
"""
import json
import os
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_ESTADO = os.path.join(CARPETA, "resultados_estado.json")
RUTA_REPORTE = os.path.join(CARPETA, "resultados_reporte.md")
URL = "https://api.nasdaq.com/api/calendar/earnings?date={}"
GIGANTES = {"NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon", "GOOGL": "Alphabet", "GOOG": "Alphabet",
            "META": "Meta", "TSLA": "Tesla", "AVGO": "Broadcom", "NFLX": "Netflix", "COST": "Costco", "AMD": "AMD", "JPM": "JPMorgan"}
HORARIO = {"time-pre-market": "antes de la apertura", "time-after-hours": "después del cierre", "time-not-supplied": "hora sin confirmar"}
INDICES = ("USTECH", "US500")


def descargar(dia):
    req = urllib.request.Request(URL.format(dia.isoformat()), headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


# ---------------- lógica pura ----------------
def gigantes_del_dia(datos, dia):
    filas = ((datos or {}).get("data") or {}).get("rows") or []
    vistos, out = set(), []
    for f in filas:
        s = (f.get("symbol") or "").upper()
        if s in GIGANTES and GIGANTES[s] not in vistos:
            vistos.add(GIGANTES[s])
            out.append({"fecha": dia.isoformat(), "simbolo": s, "empresa": GIGANTES[s], "horario": HORARIO.get(f.get("time"), "hora sin confirmar")})
    return out


def riesgo_posiciones(eventos, simbolos_abiertos, hoy):
    """Eventos de mañana (o de hoy después del cierre) con posiciones abiertas en índices."""
    if not any(s.startswith(i) for s in simbolos_abiertos for i in INDICES):
        return []
    manana = (hoy + timedelta(days=1)).isoformat()
    return [e for e in eventos if e["fecha"] == manana or (e["fecha"] == hoy.isoformat() and e["horario"] == "después del cierre")]


def ciclo(mt5, est):
    hoy = datetime.now(timezone.utc).date()
    eventos = []
    for k in range(8):
        d = hoy + timedelta(days=k)
        if d.weekday() >= 5:
            continue
        try:
            eventos += gigantes_del_dia(descargar(d), d)
        except Exception as e:
            print(f"Resultados: no pude leer {d}: {e!r}"[:150])
    abiertos = [p.symbol for p in (mt5.positions_get() or [])] if mt5 is not None else []
    riesgo = riesgo_posiciones(eventos, abiertos, hoy)
    lineas = ["# Resultados de empresas gigantes (próximos 7 días)", "", "| Fecha | Empresa | Horario |", "|---|---|---|"]
    lineas += [f"| {e['fecha']} | {e['empresa']} ({e['simbolo']}) | {e['horario']} |" for e in eventos] or ["| — | Ninguna | — |"]
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    if est.get("aviso") != hoy.isoformat():
        est["aviso"] = hoy.isoformat()
        if eventos:
            enviar("🏢 Resultados de gigantes esta semana:\n" + "\n".join(f"• {e['fecha']}: {e['empresa']} ({e['horario']})" for e in eventos), "Calendario de resultados")
        if riesgo:
            enviar("⚠️ Tienes posiciones en índices y reporta " + ", ".join(f"{e['empresa']} ({e['fecha']}, {e['horario']})" for e in riesgo)
                   + ". Puede haber salto de precio (gap). La estrategia se validó incluyendo estos días: no se cierra, solo te aviso.", "Calendario de resultados")
    est["eventos"] = eventos
    with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, indent=2, ensure_ascii=False)
    return eventos, riesgo


def main():
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            mt5 = None
    except ImportError:
        mt5 = None
    try:
        est = json.load(open(RUTA_ESTADO, encoding="utf-8"))
    except Exception:
        est = {}
    while True:
        ahora = datetime.now(timezone.utc)
        if "--ahora" in sys.argv or (ahora.hour >= 12 and est.get("aviso") != ahora.date().isoformat()):
            try:
                ciclo(mt5, est)
            except Exception as e:
                print(f"Resultados: error (sigo): {e!r}"[:200])
            if "--ahora" in sys.argv:
                return
        time.sleep(1800)


if __name__ == "__main__":
    main()
