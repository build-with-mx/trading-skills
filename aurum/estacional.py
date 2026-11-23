"""
ESTACIONAL — estudia los patrones de calendario de cada mercado con las velas del Minero (datos.db):
  • Rendimiento medio por MES y por DÍA DE LA SEMANA, con su t-estadístico (¿es real o ruido?).
  • Efecto "cambio de mes" (último día + primeros 3 días hábiles) frente al resto del mes.
  • Cada lunes manda la nota del mes en curso: "Diciembre: el S&P 500 subió 4 de 5 años (+1.2% medio), evidencia débil".
Importante: con ~5 años de datos, un mes tiene solo 5 observaciones. Por eso el Estacional NO opera ni filtra nada:
informa, y marca como "evidencia fuerte" solo lo que tiene |t| >= 2 con suficientes datos. Sus ideas pasan al Explorador.
Escribe estacional_reporte.md.
Ejecutar:  python estacional.py      (o  python estacional.py --ahora)
"""
import json
import os
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from minero import leer_velas
from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_REPORTE = os.path.join(CARPETA, "estacional_reporte.md")
MESES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def tstat(x):
    if len(x) < 3 or st.pstdev(x) == 0:
        return 0.0
    return st.mean(x) / (st.stdev(x) / len(x) ** 0.5)


def estudiar(t, c):
    """Función pura. t: fechas (datetime) de velas D1; c: cierres. Devuelve dict con meses, días y cambio de mes."""
    # las velas diarias de Axi abren a las 17:00 de Nueva York (21-22 UTC del día ANTERIOR): las llevo a su día de sesión
    t = [f + timedelta(hours=6) for f in t]
    ret = [(t[i], c[i] / c[i - 1] - 1) for i in range(1, len(c))]
    # mensual: rendimiento de cada mes calendario completo
    ultimo_por_mes = {}
    for f, x in zip(t, c):
        ultimo_por_mes[(f.year, f.month)] = x
    claves = sorted(ultimo_por_mes)
    por_mes = defaultdict(list)
    for a, b in zip(claves, claves[1:]):
        por_mes[b[1]].append(ultimo_por_mes[b] / ultimo_por_mes[a] - 1)
    meses = {m: {"n": len(v), "media": st.mean(v), "sube": sum(1 for r in v if r > 0), "t": tstat(v)} for m, v in por_mes.items()}
    por_dia = defaultdict(list)
    for f, r in ret:
        por_dia[f.weekday()].append(r)
    dias = {d: {"n": len(v), "media": st.mean(v), "t": tstat(v)} for d, v in por_dia.items() if len(v) > 20}
    # cambio de mes: último día hábil del mes + primeros 3
    idx_mes = defaultdict(list)
    for i, (f, r) in enumerate(ret):
        idx_mes[(f.year, f.month)].append(i)
    tom = set()
    meses_ord = sorted(idx_mes)
    for k, mm in enumerate(meses_ord):
        tom.update(idx_mes[mm][:3])
        if k + 1 < len(meses_ord):
            tom.add(idx_mes[mm][-1])
    dentro = [ret[i][1] for i in tom]
    fuera = [ret[i][1] for i in range(len(ret)) if i not in tom]
    cambio = {"dentro": st.mean(dentro) if dentro else 0.0, "fuera": st.mean(fuera) if fuera else 0.0,
              "t": (st.mean(dentro) - st.mean(fuera)) / ((st.pvariance(dentro) / len(dentro) + st.pvariance(fuera) / len(fuera)) ** 0.5)
              if len(dentro) > 5 and len(fuera) > 5 else 0.0}
    return {"meses": meses, "dias": dias, "cambio_mes": cambio}


def fuerza(t, n):
    return "evidencia fuerte" if abs(t) >= 2 and n >= 8 else "evidencia débil" if abs(t) >= 1 else "ruido"


def nota_del_mes(simbolo, res, mes):
    m = res["meses"].get(mes)
    if not m:
        return None
    return (f"{simbolo}: en {MESES[mes]} subió {m['sube']} de {m['n']} años ({m['media']:+.1%} de media) → {fuerza(m['t'], m['n'])}")


def generar(simbolos):
    ahora = datetime.now(timezone.utc)
    lineas = [f"# Estacional — {ahora:%Y-%m-%d} (datos D1 del Minero)", "",
              "Con ~5 años, cada mes tiene ~5 observaciones: casi todo es *evidencia débil*. Solo se informa; no se opera.", ""]
    notas = []
    for s in simbolos:
        v = leer_velas(s, "D1")
        if not v or len(v[4]) < 300:
            continue
        res = estudiar(v[0], v[4])
        n = nota_del_mes(s, res, ahora.month)
        if n:
            notas.append(n)
        lineas += [f"## {s}", "| Mes | Años | Sube | Media | t | Lectura |", "|---|---|---|---|---|---|"]
        lineas += [f"| {MESES[m]} | {x['n']} | {x['sube']} | {x['media']:+.2%} | {x['t']:+.1f} | {fuerza(x['t'], x['n'])} |" for m, x in sorted(res["meses"].items())]
        lineas += ["", "| Día | Días | Media | t | Lectura |", "|---|---|---|---|---|"]
        lineas += [f"| {DIAS[d]} | {x['n']} | {x['media']:+.3%} | {x['t']:+.1f} | {fuerza(x['t'], 30)} |" for d, x in sorted(res["dias"].items())]
        cm = res["cambio_mes"]
        lineas += ["", f"Cambio de mes: {cm['dentro']:+.3%} por día dentro vs {cm['fuera']:+.3%} fuera (t {cm['t']:+.1f}, {fuerza(cm['t'], 30)})", ""]
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    return notas


def main():
    hecho = None
    while True:
        ahora = datetime.now(timezone.utc)
        if "--ahora" in sys.argv or (ahora.weekday() == 0 and ahora.hour == 11 and hecho != ahora.date()):
            try:
                cfg = json.load(open(RUTA_CONFIG, encoding="utf-8"))
                notas = generar(cfg["universo"]["D1"])
                hecho = ahora.date()
                if notas:
                    enviar(f"📅 Estacionalidad de {MESES[ahora.month]} (solo informativa):\n• " + "\n• ".join(notas), "Estacional")
            except Exception as e:
                print(f"Estacional: error (sigo): {e!r}"[:200])
            if "--ahora" in sys.argv:
                return
        time.sleep(600)


if __name__ == "__main__":
    main()
