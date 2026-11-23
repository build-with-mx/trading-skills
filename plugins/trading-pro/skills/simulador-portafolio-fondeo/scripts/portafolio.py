#!/usr/bin/env python3
"""Simulador de portafolio: combina las operaciones (en R) de varias estrategias validadas y estima
rendimiento, drawdown y probabilidad de pasar un reto de fondeo. Uso: python3 -I portafolio.py config.json"""
import sys, os, json, random, statistics as st
from collections import defaultdict
sys.path.insert(0, sys.argv[2] if len(sys.argv)>2 else os.path.dirname(os.path.abspath(__file__)))
import megalab as ML
cfg=json.load(open(sys.argv[1])); ML.init(cfg)
def d1(s): return ML.MK[("d1",s)]
EST={
 "RSI2 US500":  lambda: ML.fam_d1(d1("US500"),"rsi",(2,10,200,"sma5",2.5,"A")),
 "RSI2 USTECH": lambda: ML.fam_d1(d1("USTECH"),"rsi",(2,10,200,"sma5",2.5,"A")),
 "RSI2 US30":   lambda: ML.fam_d1(d1("US30"),"rsi",(2,10,200,"sma5",2.5,"A")),
 "RSI2 US2000": lambda: ML.fam_d1(d1("US2000"),"rsi",(2,10,200,"sma5",2.5,"A")),
 "Donchian oro":lambda: ML.fam_d1(d1("XAUUSD"),"donchian",(20,10,2,"A")),
 "Donchian ETH":lambda: ML.fam_d1(d1("ETHUSD"),"donchian",(20,10,2,"A")),
 "Donchian BTC":lambda: ML.fam_d1(d1("BTCUSD"),"donchian",(20,10,2,"A")),
 "Ruptura asiática oro": lambda: ML.sim_h1(ML.MK[("h1","XAUUSD")],0,6,10,1.5,2),
}
ops=[]; print(f"{'Estrategia':22} ops   total   exp/op   años")
for k,f in EST.items():
    o=f(); yrs=max((o[-1][0]-o[0][0]).days/365.25,0.1) if o else 1
    print(f"{k:22} {len(o):4} {sum(r for _,r in o):+7.1f}R {sum(r for _,r in o)/max(1,len(o)):+.2f}R  {yrs:.1f}")
    ops+= [(t,r,k) for t,r in o]
ops.sort()
RISK=float(os.environ.get("RIESGO","0.005"))
# curva de capital real (por fecha de entrada), riesgo fijo sobre capital actual
eq=1.0; pk=1.0; dd=0; por_anio=defaultdict(float); eq_anio={}
for t,r,k in ops:
    eq*= (1+RISK*r); pk=max(pk,eq); dd=max(dd,1-eq/pk); eq_anio[t.year]=eq
prev=1.0
print(f"\nPortafolio combinado, riesgo {RISK:.1%} por operación ({len(ops)} ops, {ops[0][0]:%Y-%m}→{ops[-1][0]:%Y-%m}):")
for y in sorted(eq_anio): print(f"  {y}: {eq_anio[y]/prev-1:+6.1%}"); prev=eq_anio[y]
yrs=(ops[-1][0]-ops[0][0]).days/365.25
print(f"  Total {eq-1:+.1%} | anual compuesto {eq**(1/yrs)-1:+.1%} | máx. caída {dd:.1%} | ~{len(ops)/yrs:.0f} operaciones/año")
# Monte Carlo de reto de fondeo: remuestrear operaciones en orden aleatorio
R=[r for _,r,_ in ops]; perday=len(ops)/(yrs*252)
def reto(obj=0.10, dd_max=0.10, dias=None, n=4000):
    ok=fail=0; dur=[]
    for _ in range(n):
        e=1.0; pk=1.0; k=0
        while True:
            e*=1+RISK*random.choice(R); k+=1; pk=max(pk,e)
            if e>=1+obj: ok+=1; dur.append(k/perday/21); break
            if e<=1-dd_max: fail+=1; break   # pérdida máx. estática desde el inicio
            if dias and k/perday>dias: break
    return ok/n, fail/n, (st.median(dur) if dur else float('nan'))
for obj,ddm,lbl in ((0.10,0.10,"Fase 1: +10% antes de −10%"),(0.05,0.10,"Fase 2: +5% antes de −10%"),(0.08,0.05,"Reto duro: +8% antes de −5%")):
    p,f,m=reto(obj,ddm); print(f"  {lbl:30} aprueba {p:5.1%} | quema {f:5.1%} | meses (mediana) {m:4.1f}")
