"""
PROFESOR — cada domingo estudia los resultados reales y escribe las lecciones de la semana.
  • Por estrategia: expectativa en vivo frente al backtest con su margen de error (no se asusta por 5 pérdidas seguidas,
    pero detecta cuando la diferencia ya no es mala suerte):
       - "ventaja confirmada en vivo": con >= 20 operaciones, incluso el peor caso razonable (−2 errores estándar) es > 0
       - "deterioro probable": con >= 20 operaciones, incluso el mejor caso razonable (+2 errores estándar) queda por debajo del backtest
       - probabilidad (bootstrap) de que la expectativa real sea <= 0
  • Por contexto (datos del Archivista): ¿gana más en tendencia o en rango? ¿con volatilidad alta o normal? ¿qué día?
    Solo saca conclusiones con >= 10 operaciones en cada grupo; si no, lo dice.
  • Agrega todo a profesor_lecciones.md (memoria permanente del equipo) y te manda el resumen.
  • NO cambia la configuración: propone. Los cambios los decides tú con Claude.
Ejecutar:  python profesor.py      (o  python profesor.py --ahora)
"""
import os
import random
import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(CARPETA, "aurum.db")
RUTA_LECCIONES = os.path.join(CARPETA, "profesor_lecciones.md")
BACKTEST_R = {"ruptura_asiatica": 0.22, "donchian": 0.30, "rsi2": 0.15, "ibs": 0.12}
try:  # cada estrategia puede declarar su expectativa de backtest en aurum_config.json ("exp_backtest")
    import json as _json
    _cfg = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "aurum_config.json"), encoding="utf-8"))
    BACKTEST_R.update({n: e["exp_backtest"] for n, e in _cfg.get("estrategias", {}).items() if "exp_backtest" in e})
except Exception:
    pass
MIN_GRUPO = 10


# ---------------- lógica pura ----------------
def prob_negativa(R, sims=3000, semilla=11):
    rnd = random.Random(semilla)
    n = len(R)
    return sum(1 for _ in range(sims) if sum(rnd.choice(R) for _ in range(n)) <= 0) / sims


def diagnostico(R, bt):
    n = len(R)
    if n < 5:
        return {"n": n, "veredicto": "muy pocas operaciones", "exp": st.mean(R) if R else 0.0}
    exp, se = st.mean(R), st.stdev(R) / n ** 0.5
    if n >= 20 and exp - 2 * se > 0:
        v = "ventaja confirmada en vivo"
    elif n >= 20 and exp + 2 * se < bt:
        v = "deterioro probable: rinde menos que el backtest más allá de la mala suerte"
    elif n >= 20 and exp <= 0:
        v = "VIGILAR: en pérdida, aunque todavía compatible con el backtest (puede ser mala racha)"
    else:
        v = "dentro de lo esperado" if exp - 2 * se <= bt <= exp + 2 * se else "por encima de lo esperado" if exp > bt else "por debajo, aún compatible con mala suerte"
    return {"n": n, "exp": exp, "se": se, "bt": bt, "p_neg": prob_negativa(R), "veredicto": v}


def por_grupo(filas, clave):
    """filas: dicts con R y la clave. Devuelve {grupo: (n, exp)} y la conclusión (o None si faltan datos)."""
    g = defaultdict(list)
    for f in filas:
        g[f[clave]].append(f["R"])
    res = {k: (len(v), st.mean(v)) for k, v in g.items()}
    validos = {k: v for k, v in res.items() if v[0] >= MIN_GRUPO}
    if len(validos) < 2:
        return res, None
    mejor = max(validos, key=lambda k: validos[k][1])
    peor = min(validos, key=lambda k: validos[k][1])
    if validos[mejor][1] - validos[peor][1] < 0.3:
        return res, None
    return res, f"rinde mejor con {clave} = {mejor} ({validos[mejor][1]:+.2f}R, {validos[mejor][0]} ops) que con {peor} ({validos[peor][1]:+.2f}R, {validos[peor][0]} ops)"


def leccion(filas_por_estrategia, contexto_por_estrategia):
    txt, alertas = [], []
    for e, R in filas_por_estrategia.items():
        d = diagnostico(R, BACKTEST_R.get(e, 0.1))
        if d["n"] < 5:
            txt.append(f"- **{e}**: {d['n']} operaciones, aún muy pocas para opinar.")
            continue
        txt.append(f"- **{e}**: {d['n']} ops, {d['exp']:+.2f}R por operación (±{2 * d['se']:.2f}) vs backtest {d['bt']:+.2f}R → "
                   f"**{d['veredicto']}**. Probabilidad de que en realidad pierda: {d['p_neg']:.0%}.")
        if d["veredicto"].startswith("deterioro"):
            alertas.append(f"{e}: {d['veredicto']}. Propuesta: bajar su riesgo a la mitad y revisarla con Claude.")
        for clave in ("regimen", "volatilidad", "dia"):
            _, concl = por_grupo(contexto_por_estrategia.get(e, []), clave)
            if concl:
                txt.append(f"  - {concl}. (Hipótesis: hay que confirmarla fuera de muestra antes de usarla como filtro.)")
    return txt, alertas


# ---------------- ejecución ----------------
def estudiar():
    if not os.path.exists(RUTA_DB):
        return None
    con = sqlite3.connect(RUTA_DB)
    ops = con.execute("SELECT posicion, estrategia, R FROM operaciones WHERE R IS NOT NULL ORDER BY cerrada").fetchall()
    try:
        ctx = con.execute("SELECT o.estrategia, o.R, c.regimen, c.volatilidad, c.dia FROM operaciones o JOIN contexto c ON c.posicion = o.posicion").fetchall()
    except sqlite3.OperationalError:
        ctx = []
    con.close()
    R = defaultdict(list)
    for _, e, r in ops:
        R[e].append(r)
    C = defaultdict(list)
    for e, r, reg, vol, dia in ctx:
        C[e].append({"R": r, "regimen": reg, "volatilidad": vol, "dia": dia})
    txt, alertas = leccion(R, C)
    ahora = datetime.now(timezone.utc)
    seccion = [f"\n## Semana del {ahora:%Y-%m-%d}", f"Operaciones cerradas en total: {len(ops)}"] + (txt or ["- Aún no hay operaciones cerradas."])
    if alertas:
        seccion += ["", "**Propuestas:**"] + [f"- {a}" for a in alertas]
    nuevo = not os.path.exists(RUTA_LECCIONES)
    with open(RUTA_LECCIONES, "a", encoding="utf-8") as f:
        if nuevo:
            f.write("# Lecciones del Profesor\nMemoria permanente: lo que el equipo aprende de sus operaciones reales.\n")
        f.write("\n".join(seccion) + "\n")
    enviar("🎓 Lección de la semana:\n" + "\n".join(t.replace("**", "") for t in txt[:12]) +
           ("\n\n⚠️ " + "\n⚠️ ".join(alertas) if alertas else ""), "Profesor")
    return seccion


def main():
    hecho = None
    while True:
        ahora = datetime.now(timezone.utc)
        if "--ahora" in sys.argv or (ahora.weekday() == 6 and ahora.hour == 9 and hecho != ahora.date()):
            try:
                estudiar()
                hecho = ahora.date()
            except Exception as e:
                print(f"Profesor: error (sigo): {e!r}"[:200])
            if "--ahora" in sys.argv:
                return
        time.sleep(600)


if __name__ == "__main__":
    main()
