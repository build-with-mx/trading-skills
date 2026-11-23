#!/usr/bin/env python3
"""Megalab 2: familias populares nuevas (IBS, cambio de mes, MACD, Supertrend, barra interior/NR7, squeeze).
Reusa el motor de megalab.py. Uso: python3 -I megalab2.py config.json resultados2.csv"""
import sys, os, json, csv, itertools
from datetime import timedelta
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import megalab as ML
from megalab import sma, M, sim, stats

def ema(x, n):
    out=[None]*len(x); k=2/(n+1); e=None
    for i,v in enumerate(x):
        e=v if e is None else e+k*(v-e); out[i]=e if i>=n-1 else None
    return out

def fam(m, f, p):
    o,h,l,c,n=m.o,m.h,m.l,m.c,m.n; NO=[False]*n
    if f=="ibs":
        thr,xt,filt,slm,lado=p
        ibs=[(c[i]-l[i])/(h[i]-l[i]) if h[i]>l[i] else 0.5 for i in range(n)]
        F=m.g(("sma",filt),lambda:sma(c,filt)) if filt else None
        okL=lambda i: F is None or (F[i] is not None and c[i]>F[i]); okS=lambda i: F is None or (F[i] is not None and c[i]<F[i])
        el=[ibs[i]<thr and okL(i) for i in range(n)]
        es=NO if lado=="L" else [ibs[i]>1-thr and okS(i) for i in range(n)]
        return sim(m,el,es,[ibs[i]>xt for i in range(n)],[ibs[i]<1-xt for i in range(n)],slm,None,5)
    if f=="tom":
        nlast,hold,slm=p
        d=[(t+timedelta(hours=3)).date() for t in m.t]  # fecha de sesión (la vela D1 de Axi abre a las 17:00 NY)
        el=[False]*n
        for i in range(n-nlast):
            if d[i+nlast].month!=d[i].month and all(d[i+k].month==d[i].month for k in range(nlast)): el[i]=True
        return sim(m,el,NO,NO,NO,slm,None,hold)
    if f=="macd":
        fa,sl_,sg,filt,slm,lado=p
        mc=m.g(("macd",fa,sl_),lambda:[None if a is None or b is None else a-b for a,b in zip(ema(c,fa),ema(c,sl_))])
        z=[0 if v is None else v for v in mc]; sig=m.g(("sig",fa,sl_,sg),lambda:ema(z,sg))
        up=[mc[i] is not None and sig[i] is not None and mc[i]>sig[i] for i in range(n)]
        F=m.g(("sma",filt),lambda:sma(c,filt)) if filt else None
        el=[i>0 and up[i] and not up[i-1] and (F is None or (F[i] is not None and c[i]>F[i])) for i in range(n)]
        es=NO if lado=="L" else [i>0 and not up[i] and up[i-1] and (F is None or (F[i] is not None and c[i]<F[i])) for i in range(n)]
        return sim(m,el,es,[not x for x in up],up,slm)
    if f=="supertrend":
        per,mult,slm,lado=p
        a=m.g(("atrN",per),lambda:ML.atr(h,l,c,per)); dirr=[0]*n; ub=lb=None; tr=1
        for i in range(n):
            if a[i] is None: continue
            mid=(h[i]+l[i])/2; bu=mid+mult*a[i]; bl=mid-mult*a[i]
            ub=bu if ub is None or bu<ub or c[i-1]>ub else ub
            lb=bl if lb is None or bl>lb or c[i-1]<lb else lb
            if tr==1 and c[i]<lb: tr=-1
            elif tr==-1 and c[i]>ub: tr=1
            dirr[i]=tr
        el=[i>0 and dirr[i]==1 and dirr[i-1]==-1 for i in range(n)]
        es=NO if lado=="L" else [i>0 and dirr[i]==-1 and dirr[i-1]==1 for i in range(n)]
        return sim(m,el,es,[x==-1 for x in dirr],[x==1 for x in dirr],slm)
    if f=="nr7":
        tipo,slm,rr,lado=p
        rg=[h[i]-l[i] for i in range(n)]
        if tipo=="inside": setup=[i>0 and h[i]<h[i-1] and l[i]>l[i-1] for i in range(n)]
        else: setup=[i>=6 and rg[i]==min(rg[i-6:i+1]) for i in range(n)]
        el=[i>0 and setup[i-1] and c[i]>h[i-1] for i in range(n)]
        es=NO if lado=="L" else [i>0 and setup[i-1] and c[i]<l[i-1] for i in range(n)]
        return sim(m,el,es,NO,NO,slm,rr,10)
    if f=="squeeze":
        per,kmult,slm,lado=p
        mid=m.g(("sma",per),lambda:sma(c,per)); a=m.g(("atrN",per),lambda:ML.atr(h,l,c,per))
        import statistics as st
        sd=m.g(("sd",per),lambda:[None if i<per-1 else st.pstdev(c[i-per+1:i+1]) for i in range(n)])
        sq=[mid[i] is not None and a[i] is not None and 2*sd[i]<kmult*a[i] for i in range(n)]
        el=[i>0 and sq[i-1] and c[i]>mid[i]+2*sd[i] for i in range(n)]
        es=NO if lado=="L" else [i>0 and sq[i-1] and c[i]<mid[i]-2*sd[i] for i in range(n)]
        return sim(m,el,es,[mid[i] is not None and c[i]<mid[i] for i in range(n)],[mid[i] is not None and c[i]>mid[i] for i in range(n)],slm)

def grids():
    G=[]
    G+=[("ibs",p) for p in itertools.product((0.1,0.2,0.3),(0.5,0.7),(0,200),(2,3),("A","L"))]
    G+=[("tom",p) for p in itertools.product((1,2,3,4),(3,5,7),(2,3))]
    G+=[("macd",p) for p in itertools.product((8,12),(21,26),(5,9),(0,200),(2,3),("A","L"))]
    G+=[("supertrend",p) for p in itertools.product((7,10,14),(2,2.5,3),(2,3),("A","L"))]
    G+=[("nr7",p) for p in itertools.product(("inside","nr7"),(1,1.5,2),(1,2,3),("A","L"))]
    G+=[("squeeze",p) for p in itertools.product((14,20),(1.5,2,2.5),(2,3),("A","L"))]
    return G

def run(task):
    s,f,p=task; m=ML.MK[("d1",s)]; ops=fam(m,f,p); split=m.t[int(m.n*0.6)]
    return ("d1",s,f,"|".join(map(str,p)))+stats(ops,split)
if __name__=="__main__":
    cfg=json.load(open(sys.argv[1])); cfg["h1"]={}
    tasks=[(s,f,p) for s in cfg["d1"] for f,p in grids()]
    print("combinaciones:",len(tasks),flush=True)
    with Pool(4,initializer=ML.init,initargs=(cfg,)) as pool, open(sys.argv[2],"w",newline="") as fo:
        w=csv.writer(fo); w.writerow(["tf","mercado","familia","params","n_is","exp_is","pf_is","n_oos","exp_oos","pf_oos"])
        for row in pool.imap_unordered(run,tasks,chunksize=10): w.writerow(row)
    print("listo")
