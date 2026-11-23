"""
EXPLORADOR — busca estrategias nuevas cada semana con el filtro anti-suerte.
1. Lee las velas de datos.db (las guarda el Minero).
2. Prueba ~1,500 variantes diarias por mercado (13 familias) y ~1,400 de ruptura por sesión en H1, más 150 estrategias al AZAR por mercado.
3. Elige con el primer 60% del tiempo y valida en el 40% final. Aprueba una zona (familia × mercado) solo si >= 60% de sus
   variantes ganan en ambos periodos (el azar logra ~25%) y la expectativa mediana es > +0.05R en ambos.
4. De cada zona aprobada toma una variante ROBUSTA (no la mejor) y comprueba que el lote mínimo quepa en el riesgo.
5. Las nuevas entran a candidatos.json en estado "sombra": la Sombra las practica en papel antes de cualquier dinero.
Ejecutar:  python explorador.py            (espera al sábado 06:00 UTC; si no hay candidatos.json, explora al arrancar)
           python explorador.py --ahora    (explora ya y termina)
"""
import json
import os
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from multiprocessing import Pool

import lab_motor as L
from minero import leer_velas
from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_CAND = os.path.join(CARPETA, "candidatos.json")
RUTA_RES = os.path.join(CARPETA, "explorador_ultimo.json")

# posición del multiplicador de SL (en ATR) dentro de los parámetros de cada familia
POS_SL = {"rsi": 4, "donchian": 2, "macross": 2, "boll": 3, "ndayrr": 1, "streak": 3, "mom": 1, "ibs": 3, "tom": 2,
          "macd": 4, "supertrend": 2, "nr7": 1, "squeeze": 2, "sesion": 3}
# estrategias que Aurum ya opera (familia, símbolo) → no se proponen otra vez
YA_ACTIVAS = {"ruptura_asiatica": "sesion", "donchian": "donchian", "rsi2": "rsi", "ibs": "ibs"}

# tipo de ventaja de cada familia: dos estrategias del mismo tipo en el mismo mercado suelen ser la MISMA apuesta
TIPO = {"donchian": "tendencia", "macross": "tendencia", "ndayrr": "tendencia", "macd": "tendencia", "supertrend": "tendencia",
        "squeeze": "tendencia", "mom": "tendencia", "nr7": "tendencia", "sesion": "ruptura_intradia",
        "rsi": "reversion", "ibs": "reversion", "boll": "reversion", "streak": "reversion", "tom": "calendario"}

_DATOS = {}


def estrategias_activas(cfg):
    """(familia del laboratorio, símbolo) de lo que Aurum ya opera."""
    activas = {(YA_ACTIVAS[n], s) for n, e in cfg["estrategias"].items() if n in YA_ACTIVAS and e.get("activa") for s in e["simbolos"]}
    activas |= {(e["familia_lab"], s) for e in cfg["estrategias"].values() if e.get("familia_lab") and e.get("activa") for s in e["simbolos"]}
    return activas


def _init(universo):
    for tf, simbolos in universo.items():
        for s in simbolos:
            v = leer_velas(s, tf)
            if v:
                t, o, h, l, c, costo = v
                m = L.M(t, o, h, l, c, costo)
                if tf == "H1":
                    m.a = L.atr(h, l, c, 14)
                _DATOS[(tf, s)] = m


def _probar(tarea):
    tf, s, fam, p = tarea
    m = _DATOS[(tf, s)]
    ops = L.evaluar(m, "h1" if tf == "H1" else "d1", fam if fam != "azar" else "azar", p)
    corte = m.t[int(m.n * 0.6)]
    return (tf, s, fam, p) + L.stats(ops, corte)


def explorar(cfg):
    universo = cfg["universo"]
    _init(universo)
    tareas = []
    for (tf, s) in _DATOS:
        if tf == "D1":
            tareas += [("D1", s, f, p) for f, p in L.todas_las_grillas_d1()]
        else:
            tareas += [("H1", s, f, p) for f, p in L.grids_h1()]
    if not tareas:
        return [], 0.0, 0
    enviar(f"🔬 Explorador: empiezo a probar {len(tareas):,} variantes en {len(_DATOS)} series de datos.", "Explorador")
    with Pool(max(1, (os.cpu_count() or 2) - 1), initializer=_init, initargs=(universo,)) as pool:
        filas = pool.map(_probar, tareas, chunksize=25)

    ok = lambda r: r[4] >= 20 and r[7] >= 12  # n_is, n_oos
    azar = [r for r in filas if r[2] == "azar" and ok(r)]
    base = sum(1 for r in azar if r[5] > 0 and r[8] > 0) / max(1, len(azar))
    zonas = defaultdict(list)
    for r in filas:
        if r[2] != "azar" and ok(r):
            zonas[(r[0], r[1], r[2])].append(r)
    activas = estrategias_activas(cfg)
    aprobadas = []
    for (tf, s, fam), xs in zonas.items():
        if len(xs) < 8:
            continue
        ambos = sum(1 for x in xs if x[5] > 0 and x[8] > 0) / len(xs)
        med_is, med_oos = st.median(x[5] for x in xs), st.median(x[8] for x in xs)
        if ambos >= max(0.6, 2 * base) and med_is > 0.05 and med_oos > 0.05:
            robustas = sorted([x for x in xs if x[5] > 0 and x[8] > 0], key=lambda x: min(x[5], x[8]), reverse=True)
            elegida = robustas[len(robustas) // 4]  # cuartil superior, no la mejor (evita sobreoptimizar)
            aprobadas.append({"tf": tf, "simbolo": s, "familia": fam, "params": list(elegida[3]), "zona_ok": round(ambos, 2),
                              "exp_is": round(elegida[5], 3), "exp_oos": round(elegida[8], 3), "n_is": elegida[4], "n_oos": elegida[7],
                              "ya_activa": (fam, s) in activas})
    return aprobadas, base, len(filas)


def lote_cabe(cand, cfg):
    """Comprueba con MetaTrader que el lote mínimo no arriesgue más del riesgo permitido (si MT5 está disponible)."""
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            return None
        info = mt5.symbol_info(cand["simbolo"])
        m = _DATOS[(cand["tf"], cand["simbolo"])]
        a = [x for x in m.a if x][-1]
        dist = cand["params"][POS_SL[cand["familia"]]] * a
        riesgo_min = info.volume_min * dist * info.trade_tick_value / info.trade_tick_size
        return riesgo_min <= mt5.account_info().balance * cfg["riesgo_por_operacion"]
    except Exception:
        return None


def main():
    cfg = json.load(open(RUTA_CONFIG, encoding="utf-8"))
    while True:
        ahora = datetime.now(timezone.utc)
        toca = "--ahora" in sys.argv or not os.path.exists(RUTA_CAND) or (ahora.weekday() == 5 and ahora.hour == 6)
        if toca:
            cfg = json.load(open(RUTA_CONFIG, encoding="utf-8"))
            aprobadas, base, total = explorar(cfg)
            if total == 0:  # el Minero aún no guardó datos: reintentar en 10 minutos
                print("Explorador: todavía no hay velas en datos.db; reintento en 10 minutos.")
                time.sleep(600)
                continue
            cand = json.load(open(RUTA_CAND, encoding="utf-8")) if os.path.exists(RUTA_CAND) else []
            ids = {c["id"] for c in cand}
            nuevas = []
            activas = estrategias_activas(cfg)
            for a in aprobadas:
                a["id"] = f"{a['familia']}:{a['simbolo']}:{a['tf']}:{'|'.join(map(str, a['params']))}"
                if a["ya_activa"] or a["id"] in ids or any(c["familia"] == a["familia"] and c["simbolo"] == a["simbolo"] for c in cand):
                    continue
                a["tipo"] = TIPO.get(a["familia"], "otro")
                tipos_activos = {TIPO.get(f) for f, sim in activas if sim == a["simbolo"]}
                a["diversifica"] = a["tipo"] not in tipos_activos
                a["lote_cabe"] = lote_cabe(a, cfg)
                a.update({"estado": "sombra" if a["lote_cabe"] is not False else "no_cabe_lote", "fecha_alta": ahora.isoformat()})
                cand.append(a)
                nuevas.append(a)
            json.dump(cand, open(RUTA_CAND, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            json.dump({"fecha": ahora.isoformat(), "variantes": total, "azar_ambos": base, "zonas_aprobadas": aprobadas},
                      open(RUTA_RES, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
            txt = "\n".join(f"• {n['familia']} en {n['simbolo']} ({n['tf']}): {n['zona_ok']:.0%} de variantes OK, OOS {n['exp_oos']:+.2f}R → {n['estado']}{'' if n['diversifica'] else ' (misma ventaja que una activa)'}" for n in nuevas[:15])
            enviar(f"🔬 Exploración terminada: {total:,} variantes, {len(aprobadas)} zonas aprobadas (azar: {base:.0%}).\n"
                   f"Nuevas candidatas a práctica en papel: {len(nuevas)}\n{txt or '— ninguna nueva esta semana'}", "Explorador")
            if "--ahora" in sys.argv:
                return
            time.sleep(3700)
        time.sleep(600)


if __name__ == "__main__":
    main()
