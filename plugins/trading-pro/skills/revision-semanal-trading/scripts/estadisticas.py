#!/usr/bin/env python3
"""Estadísticas de trading desde CSV: cierre,simbolo,direccion,lotes,profit[,riesgo]."""
import argparse
import csv
from collections import defaultdict
from datetime import datetime

DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]


def resumen(ps):
    gan = [p for p in ps if p > 0]
    per = [p for p in ps if p <= 0]
    pf = sum(gan) / abs(sum(per)) if per and sum(per) else float("inf")
    return len(ps), (len(gan) / len(ps) if ps else 0), sum(ps), pf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--balance-inicial", type=float, required=True)
    ap.add_argument("--riesgo-pct", type=float, default=1.0)
    ap.add_argument("--meta", type=float, default=15000)
    ap.add_argument("--utc-offset", type=int, default=-6, help="Monterrey = -6")
    a = ap.parse_args()
    ops = list(csv.DictReader(open(a.csv, newline="")))
    if not ops:
        raise SystemExit("Sin operaciones.")
    riesgo_def = a.balance_inicial * a.riesgo_pct / 100
    filas = []
    for o in ops:
        t = datetime.fromisoformat(o["cierre"].replace("Z", "")[:19])
        p = float(o["profit"])
        r = p / float(o.get("riesgo") or riesgo_def)
        filas.append((t, o["simbolo"], o["direccion"], p, r))
    filas.sort()
    ps = [f[3] for f in filas]
    rs = [f[4] for f in filas]
    n, ac, tot, pf = resumen(ps)
    eq = pico = a.balance_inicial
    dd = 0.0
    racha = rmax = 0
    for p in ps:
        eq += p
        pico = max(pico, eq)
        dd = max(dd, (pico - eq) / pico)
        racha = racha + 1 if p <= 0 else 0
        rmax = max(rmax, racha)
    print(f"Operaciones: {n} | Acierto: {ac:.1%} | P/L: ${tot:+,.2f} ({tot / a.balance_inicial:+.2%})")
    print(f"Expectativa: {sum(rs) / n:+.2f}R | Total: {sum(rs):+.1f}R | PF: {pf:.2f} | Máx DD: {dd:.1%} | Racha perdedora: {rmax}")
    print(f"Balance final: ${eq:,.2f} | Progreso a ${a.meta:,.0f}: {(eq - 5000) / (a.meta - 5000):.1%} (desde $5,000)")
    if n < 20:
        print("Aviso: menos de 20 operaciones, estadísticas poco significativas.")
    for nombre, clave in [("Símbolo", lambda f: f[1]), ("Dirección", lambda f: f[2]),
                          ("Día", lambda f: DIAS[f[0].weekday()]),
                          ("Hora Monterrey", lambda f: f"{(f[0].hour + a.utc_offset) % 24:02d}h")]:
        g = defaultdict(list)
        for f in filas:
            g[clave(f)].append(f[3])
        print(f"\nPor {nombre}:")
        for k, v in sorted(g.items(), key=lambda kv: -sum(kv[1])):
            n2, ac2, t2, _ = resumen(v)
            print(f"  {k:<10} ops={n2:<3} acierto={ac2:6.1%} P/L=${t2:+,.2f}")


if __name__ == "__main__":
    main()
