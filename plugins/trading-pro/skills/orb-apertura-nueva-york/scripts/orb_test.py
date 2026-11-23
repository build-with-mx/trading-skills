#!/usr/bin/env python3
"""Opening Range Breakout (apertura NY 9:30 ET) en velas M15 de Axi (UTC). Maneja horario de verano con zoneinfo.
Uso: python3 orb_test.py --costo 1.0 archivo1.json [archivo2.json ...]"""
import json, sys, argparse, statistics as st
from datetime import datetime, time
from zoneinfo import ZoneInfo
NY = ZoneInfo("America/New_York")
ap = argparse.ArgumentParser(); ap.add_argument("--costo", type=float, required=True); ap.add_argument("files", nargs="+")
a = ap.parse_args()
vel = {}
for f in a.files:
    for c in json.load(open(f)):
        t = datetime.fromisoformat(c["time"]).astimezone(NY)
        vel[t] = (c["open"], c["high"], c["low"], c["close"])
dias = {}
for t in sorted(vel):
    if t.weekday() < 5: dias.setdefault(t.date(), []).append((t, *vel[t]))

def run(or_min, sl_mode, rr, corte=time(11, 30), salida=time(15, 45)):
    res = []
    for d, vs in dias.items():
        ini = time(9, 30); n = or_min // 15
        orv = [v for v in vs if v[0].time() >= ini][:n]
        if len(orv) < n or orv[0][0].time() != ini: continue
        hi = max(v[2] for v in orv); lo = min(v[3] for v in orv)
        resto = [v for v in vs if v[0] > orv[-1][0]]
        for i, v in enumerate(resto[:-1]):
            if v[0].time() >= corte: break
            s = 1 if v[4] > hi else -1 if v[4] < lo else 0
            if not s: continue
            e = resto[i + 1][1]
            stop = (lo if s == 1 else hi) if sl_mode == "opuesto" else (hi + lo) / 2
            dist = (e - stop) * s
            if dist <= 0: break
            tp = e + s * dist * rr if rr else None
            r = None
            for w in resto[i + 1:]:
                if (w[3] <= stop) if s == 1 else (w[2] >= stop): r = -1; break
                if tp and ((w[2] >= tp) if s == 1 else (w[3] <= tp)): r = rr; break
                if w[0].time() >= salida: r = (w[4] - e) * s / dist; break
            if r is None: r = (resto[-1][4] - e) * s / dist
            res.append((d, r - a.costo / dist))
            break
    return res

def met(rs):
    if not rs: return "sin ops"
    x = [r for _, r in rs]; g = [r for r in x if r > 0]; p = [r for r in x if r <= 0]
    pf = sum(g) / -sum(p) if p and sum(p) else 99
    eq = pk = dd = 0
    for r in x: eq += r; pk = max(pk, eq); dd = max(dd, pk - eq)
    return f"ops={len(x):3} acierto={len(g)/len(x):5.1%} total={sum(x):+6.1f}R exp={sum(x)/len(x):+.2f}R PF={pf:4.2f} DD={dd:4.1f}R"
print(f"Dias: {len(dias)}  {min(dias)} -> {max(dias)}")
for om in (15, 30):
    for slm in ("opuesto", "medio"):
        for rr in (1, 2, 0):
            rs = run(om, slm, rr)
            mitad = len(rs) // 2
            print(f"OR={om}m SL={slm:7} TP={'cierre' if not rr else str(rr)+'R':6} {met(rs)} | 1a mitad {sum(r for _,r in rs[:mitad]):+5.1f}R  2a mitad {sum(r for _,r in rs[mitad:]):+5.1f}R")
