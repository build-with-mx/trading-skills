#!/usr/bin/env python3
"""Perfil por hora (Monterrey, UTC-6) y por día: rango medio, % velas alcistas, movimiento neto medio.
Uso: python3 perfil.py velas_h1.csv  (CSV time,open,high,low,close en UTC)"""
import csv, sys, statistics as st
from datetime import datetime, timedelta
DIAS = ["lun","mar","mié","jue","vie","sáb","dom"]
rows = list(csv.DictReader(open(sys.argv[1])))
h, d = {}, {}
for r in rows:
    t = datetime.fromisoformat(r["time"]) - timedelta(hours=6)
    o, hi, lo, c = (float(r[k]) for k in ("open","high","low","close"))
    h.setdefault(t.hour, []).append((hi-lo, c-o))
    d.setdefault(t.weekday(), []).append((hi-lo, c-o))
tot = st.mean(x[0] for v in h.values() for x in v)
print(f"Rango H1 medio global: {tot:.2f}")
print("Hora MTY | rango medio | x global | % alcistas | neto medio")
for k in sorted(h):
    v = h[k]; rg = st.mean(x[0] for x in v)
    print(f"  {k:02d}h    | {rg:9.2f}  | {rg/tot:5.2f}x  | {sum(1 for x in v if x[1]>0)/len(v):6.1%}   | {st.mean(x[1] for x in v):+7.2f}  {'█'*int(rg/tot*10)}")
print("Día (velas H1) | % alcistas | neto medio/vela")
for k in sorted(d):
    v = d[k]; print(f"  {DIAS[k]}  | {sum(1 for x in v if x[1]>0)/len(v):6.1%} | {st.mean(x[1] for x in v):+.2f}")
