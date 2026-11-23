#!/usr/bin/env python3
"""Analiza resultados del megalab: separa ventaja real de suerte.
Uso: python3 analisis.py resultados.csv"""
import csv, sys, statistics as st
from collections import defaultdict
rows=list(csv.DictReader(open(sys.argv[1])))
for r in rows:
    for k in ("n_is","n_oos"): r[k]=int(r[k])
    for k in ("exp_is","pf_is","exp_oos","pf_oos"): r[k]=float(r[k])
def ok(r,ni=20,no=12): return r["n_is"]>=ni and r["n_oos"]>=no
reales=[r for r in rows if r["familia"]!="azar" and ok(r)]; azar=[r for r in rows if r["familia"]=="azar" and ok(r)]
print(f"Combinaciones con suficientes operaciones: {len(reales)} reales, {len(azar)} al azar (de {len(rows)})")
def tasa(xs,f): return sum(1 for x in xs if f(x))/max(1,len(xs))
for nom,xs in (("REALES",reales),("AZAR",azar)):
    sel=[x for x in xs if x["exp_is"]>0.1 and x["pf_is"]>1.2]
    print(f"{nom:6}: positivas en IS {tasa(xs,lambda x:x['exp_is']>0):.0%} | en OOS {tasa(xs,lambda x:x['exp_oos']>0):.0%} | "
          f"elegidas por IS: {len(sel)} → siguen positivas en OOS {tasa(sel,lambda x:x['exp_oos']>0):.0%} (exp OOS media {st.mean([x['exp_oos'] for x in sel]) if sel else 0:+.3f}R)")
# zonas robustas: familia x mercado x tf
g=defaultdict(list)
for r in reales: g[(r["tf"],r["mercado"],r["familia"])].append(r)
base=tasa(azar,lambda x:x["exp_is"]>0 and x["exp_oos"]>0)
print(f"\nReferencia AZAR: {base:.0%} de variantes positivas en IS y OOS a la vez")
res=[]
for k,xs in g.items():
    if len(xs)<8: continue
    both=tasa(xs,lambda x:x["exp_is"]>0 and x["exp_oos"]>0)
    med_oos=st.median(x["exp_oos"] for x in xs); med_is=st.median(x["exp_is"] for x in xs)
    res.append((both,med_oos,med_is,len(xs),k))
res.sort(reverse=True)
print("\nTOP zonas robustas (familia x mercado): % variantes positivas en IS y OOS | exp mediana IS / OOS | nº variantes")
for both,mo,mi,n,k in res[:30]:
    marca="✅" if both>=max(0.6,2*base) and mo>0.05 and mi>0.05 else "  "
    print(f"{marca} {k[0]} {k[1]:7} {k[2]:9} {both:5.0%} | IS {mi:+.2f}R  OOS {mo:+.2f}R | {n}")
print("\nPEORES zonas (evitar):")
for both,mo,mi,n,k in sorted(res)[:8]: print(f"   {k[0]} {k[1]:7} {k[2]:9} {both:5.0%} | IS {mi:+.2f}R OOS {mo:+.2f}R")
# mejores variantes dentro de zonas robustas
print("\nMejor variante (centro) por zona aprobada:")
for both,mo,mi,n,k in res:
    if not (both>=max(0.6,2*base) and mo>0.05 and mi>0.05): continue
    xs=sorted(g[k],key=lambda x:(min(x["exp_is"],x["exp_oos"])),reverse=True)
    x=xs[len(xs)//10]  # percentil 90, no la mejor
    print(f"   {k[1]:7} {k[2]:9} params={x['params']:22} IS n={x['n_is']} {x['exp_is']:+.2f}R PF {x['pf_is']:.2f} | OOS n={x['n_oos']} {x['exp_oos']:+.2f}R PF {x['pf_oos']:.2f}")
