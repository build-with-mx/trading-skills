"""
ABOGADO DEL DIABLO — intenta ROMPER cada estrategia antes de que arriesgue dinero (y vuelve a atacar las activas).
Pruebas de estrés con las velas del Minero (datos.db):
  1. Costos ×2 y ×3: ¿sigue ganando si el spread/deslizamiento es el doble o el triple?
  2. Sin las 5 mejores operaciones: ¿depende de unos pocos golpes de suerte?
  3. Vecinos: ¿los parámetros de al lado también ganan? (si solo gana la combinación exacta, es sobreajuste)
  4. Estabilidad: divide la historia en 4 bloques; ¿gana en al menos 3?
  5. Bootstrap: probabilidad de que la expectativa real sea <= 0.
  6. Peor racha de pérdidas y caída máxima en R (para saber qué esperar).
Veredicto: RESISTE (pasa todo), DUDOSA (falla 1) o FRÁGIL (falla 2+). Una candidata FRÁGIL no debe pasar a la demo
aunque la Sombra la apruebe. Cada domingo 08:00 UTC; escribe abogado_reporte.md y te avisa.
Ejecutar:  python abogado_diablo.py      (o  python abogado_diablo.py --ahora)
"""
import json
import os
import random
import statistics as st
import sys
import time
from datetime import datetime, timezone

import lab_motor as L
from minero import leer_velas
from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CAND = os.path.join(CARPETA, "candidatos.json")
RUTA_REPORTE = os.path.join(CARPETA, "abogado_reporte.md")
RUTA_ESTADO = os.path.join(CARPETA, "abogado_estado.json")
# estrategias activas expresadas en el lenguaje del laboratorio
ACTIVAS = [("ruptura_asiatica", "XAUUSD", "H1", "sesion", (0, 6, 10, 1.5, 2))] + \
          [("donchian", s, "D1", "donchian", (20, 10, 2, "A")) for s in ("XAUUSD", "ETHUSD", "BTCUSD")] + \
          [("rsi2", s, "D1", "rsi", (2, 10, 200, "sma5", 2.5, "A")) for s in ("US500", "USTECH", "US30", "US2000")] + \
          [("ibs", s, "D1", "ibs", (0.2, 0.7, 200, 2, "A")) for s in ("USTECH", "US500")]


TENDENCIA = {"donchian", "macross", "ndayrr", "macd", "supertrend", "squeeze", "mom", "nr7"}


def exp(ops):
    return st.mean(r for _, r in ops) if ops else 0.0


def vecinos(familia, params, tf):
    grilla = L.grids_h1() if tf == "H1" else L.todas_las_grillas_d1()
    return [p for f, p in grilla if f == familia and p != tuple(params) and len(p) == len(params)
            and sum(1 for a, b in zip(p, params) if a != b) == 1]


def racha_y_caida(R):
    racha = peor = 0
    pico = eq = caida = 0.0
    for r in R:
        racha = racha + 1 if r < 0 else 0
        peor = max(peor, racha)
        eq += r
        pico = max(pico, eq)
        caida = max(caida, pico - eq)
    return peor, caida


def estresar(m, tf, familia, params, semilla=3):
    """Función pura sobre un objeto M del laboratorio. Devuelve dict con resultados y veredicto."""
    modo = "h1" if tf == "H1" else "d1"
    base = L.evaluar(m, modo, familia, tuple(params))
    if len(base) < 20:
        return {"n": len(base), "veredicto": "SIN DATOS SUFICIENTES"}
    costo = m.cost
    res = {"n": len(base), "exp": exp(base)}
    for k in (2, 3):
        m.cost = costo * k
        res[f"costo_x{k}"] = exp(L.evaluar(m, modo, familia, tuple(params)))
    m.cost = costo
    R = [r for _, r in base]
    res["sin_top5"] = st.mean(sorted(R)[:-5]) if len(R) > 10 else None
    vs = vecinos(familia, params, tf)
    if vs:
        res["vecinos_ok"] = sum(1 for p in vs if exp(L.evaluar(m, modo, familia, p)) > 0) / len(vs)
        res["n_vecinos"] = len(vs)
    q = len(base) // 4
    bloques = [base[i * q:(i + 1) * q] if i < 3 else base[3 * q:] for i in range(4)]
    res["bloques_ok"] = sum(1 for b in bloques if exp(b) > 0)
    rnd = random.Random(semilla)
    res["p_neg"] = sum(1 for _ in range(2000) if sum(rnd.choice(R) for _ in R) <= 0) / 2000
    res["peor_racha"], res["caida_R"] = racha_y_caida(R)
    fallas = []
    if res["costo_x2"] <= 0:
        fallas.append("no aguanta costos ×2")
    if res["sin_top5"] is not None and res["sin_top5"] <= 0:
        if familia in TENDENCIA:  # en seguimiento de tendencia es lo normal: pocas operaciones enormes pagan muchas pequeñas
            res["nota"] = "depende de sus 5 mejores operaciones (normal en tendencia; por eso nunca se le pone TP)"
        else:
            fallas.append("depende de sus 5 mejores operaciones")
    if res.get("vecinos_ok") is not None and res["vecinos_ok"] < 0.6:
        fallas.append(f"solo {res['vecinos_ok']:.0%} de los parámetros vecinos ganan")
    if res["bloques_ok"] < 3:
        fallas.append(f"gana en solo {res['bloques_ok']}/4 periodos")
    if res["p_neg"] > 0.10:
        fallas.append(f"{res['p_neg']:.0%} de probabilidad de que no tenga ventaja")
    res["fallas"] = fallas
    res["veredicto"] = "RESISTE" if not fallas else "DUDOSA" if len(fallas) == 1 else "FRÁGIL"
    return res


def cargar_m(simbolo, tf):
    v = leer_velas(simbolo, tf)
    if not v:
        return None
    t, o, h, l, c, costo = v
    m = L.M(t, o, h, l, c, costo)
    if tf == "H1":
        m.a = L.atr(h, l, c, 14)
    return m


def revisar():
    objetivos = [("ACTIVA " + n, s, tf, f, p) for n, s, tf, f, p in ACTIVAS]
    cand = json.load(open(RUTA_CAND, encoding="utf-8")) if os.path.exists(RUTA_CAND) else []
    objetivos += [(f"candidata {c['familia']}", c["simbolo"], c["tf"], c["familia"], tuple(c["params"]))
                  for c in cand if c.get("estado") in ("sombra", "aprobada_papel")]
    filas, avisos, estado = [], [], {}
    for nombre, s, tf, fam, p in objetivos:
        m = cargar_m(s, tf)
        if m is None:
            continue
        r = estresar(m, tf, fam, p)
        clave = f"{nombre}|{s}|{tf}"
        estado[clave] = r
        if r["veredicto"] == "SIN DATOS SUFICIENTES":
            continue
        top5 = "—" if r["sin_top5"] is None else f"{r['sin_top5']:+.2f}R"
        vec = "—" if r.get("vecinos_ok") is None else f"{r['vecinos_ok']:.0%}"
        filas.append(f"| {nombre} | {s} {tf} | {r['n']} | {r['exp']:+.2f}R | {r['costo_x2']:+.2f}R | {top5} | {vec} | {r['bloques_ok']}/4 | "
                     f"{r['p_neg']:.0%} | {r['peor_racha']} / {r['caida_R']:.1f}R | **{r['veredicto']}** {'; '.join(r['fallas'] + ([r['nota']] if r.get('nota') else []))} |")
        if r["veredicto"] == "FRÁGIL" or (nombre.startswith("ACTIVA") and r["veredicto"] != "RESISTE"):
            avisos.append(f"{nombre} {s} {tf}: {r['veredicto']} — {'; '.join(r['fallas'])}")
    ahora = datetime.now(timezone.utc)
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write(f"# Abogado del diablo — {ahora:%Y-%m-%d %H:%M} UTC\n\n"
                "| Estrategia | Mercado | Ops | Exp. | Costos ×2 | Sin top 5 | Vecinos OK | Bloques + | P(sin ventaja) | Peor racha / caída | Veredicto |\n"
                "|---|---|---|---|---|---|---|---|---|---|---|\n" + "\n".join(filas))
    with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
        json.dump({"actualizado": ahora.isoformat(), "resultados": estado}, f, indent=2, ensure_ascii=False, default=str)
    resumen = f"😈 Abogado del diablo: ataqué {len(filas)} estrategias. " + (
        "Todas resistieron." if not avisos else f"{len(avisos)} con problemas:\n• " + "\n• ".join(avisos[:10]))
    enviar(resumen, "Abogado del diablo")
    return filas, avisos


def main():
    hecho = None
    while True:
        ahora = datetime.now(timezone.utc)
        if "--ahora" in sys.argv or (ahora.weekday() == 6 and ahora.hour == 8 and hecho != ahora.date()):
            try:
                revisar()
                hecho = ahora.date()
            except Exception as e:
                print(f"Abogado del diablo: error (sigo): {e!r}"[:200])
            if "--ahora" in sys.argv:
                return
        time.sleep(600)


if __name__ == "__main__":
    main()
