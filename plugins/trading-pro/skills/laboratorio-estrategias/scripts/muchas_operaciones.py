#!/usr/bin/env python3
"""Prueba 'abrir muchas y cerrar cuando hay ganancia'. Cada hora abre una posición de 1 unidad (precio),
la cierra cuando gana >= TP (en múltiplos de ATR H1). Sin SL o con SL. Mide ganancia realizada, pérdida flotante,
peor caída de capital (realizado + flotante) y posiciones abiertas a la vez."""
import csv, sys, random
def load(p):
    r=list(csv.DictReader(open(p))); return [(x['time'],float(x['open']),float(x['high']),float(x['low']),float(x['close'])) for x in r]
def atr(v,n=14):
    tr=[v[0][2]-v[0][3]]+[max(v[i][2]-v[i][3],abs(v[i][2]-v[i-1][4]),abs(v[i][3]-v[i-1][4])) for i in range(1,len(v))]
    out=[None]*len(v); s=0
    for i,x in enumerate(tr):
        s+=x
        if i>=n: s-=tr[i-n]
        if i>=n-1: out[i]=s/n
    return out
def run(v,cost,tpk,slk,modo,cada=1,seed=1):
    rnd=random.Random(seed); a=atr(v); ema=None; k=2/51
    abiertas=[]; real=0; wins=losses=0; peor=0; pico=0; maxab=0; perd_max=0
    for i in range(20,len(v)-1):
        t,o,h,l,c=v[i]; ema=c if ema is None else ema+k*(c-ema)
        # gestionar abiertas con la vela i
        quedan=[]
        for (s,e,tp,sl) in abiertas:
            if sl is not None and ((s==1 and l<=sl) or (s==-1 and h>=sl)):
                pnl=(sl-e)*s-cost; real+=pnl; losses+=1; perd_max=min(perd_max,pnl); continue
            if (s==1 and h>=tp) or (s==-1 and l<=tp):
                pnl=(tp-e)*s-cost; real+=pnl; wins+=1; continue
            quedan.append((s,e,tp,sl))
        abiertas=quedan
        flot=sum((c-e)*s for s,e,_,_ in abiertas)
        eq=real+flot; pico=max(pico,eq); peor=min(peor,eq-pico); maxab=max(maxab,len(abiertas))
        if i%cada==0 and a[i]:
            s = rnd.choice((1,-1)) if modo=="azar" else (1 if c>ema else -1)
            e=v[i+1][1]; d=a[i]
            abiertas.append((s,e,e+s*tpk*d,(e-s*slk*d) if slk else None))
    flot=sum((v[-1][4]-e)*s for s,e,_,_ in abiertas)
    return dict(cerradas=wins+losses, acierto=wins/max(1,wins+losses), real=real, flot=flot, total=real+flot, peor=peor, maxab=maxab, abiertas=len(abiertas))
for nom,p,cost,val in (("ORO",sys.argv[1],0.3,100),("NASDAQ",sys.argv[2],1.6,1)):
    v=load(p); print(f"===== {nom}: 1 posición nueva cada hora durante 1 año ({len(v)} velas). Resultados en $ con 0.01 lote oro / 1 lote USTECH por posición")
    m=1 if nom=="ORO" else 1
    for modo in ("azar","tendencia"):
        for tpk,slk in ((0.25,None),(0.5,None),(1,None),(0.5,3),(1,1),(2,1)):
            r=run(v,cost,tpk,slk,modo)
            f=0.01*val if nom=="ORO" else 1  # $ por 1.0 de precio
            lbl=f"TP {tpk}xATR {'SIN SL' if slk is None else f'SL {slk}xATR'}"
            print(f" {modo:9} {lbl:22} cerradas {r['cerradas']:5} acierto {r['acierto']:5.1%} | realizado ${r['real']*f:+9,.0f} | flotante final ${r['flot']*f:+9,.0f} | TOTAL ${r['total']*f:+9,.0f} | peor caída ${r['peor']*f:+9,.0f} | hasta {r['maxab']:4} abiertas a la vez")
