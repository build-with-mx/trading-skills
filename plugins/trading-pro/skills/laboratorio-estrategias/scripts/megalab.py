#!/usr/bin/env python3
"""Megalaboratorio: miles de variantes de estrategias en muchos mercados, con validación fuera de muestra.
IS = primer 60% del tiempo (selección), OOS = último 40% (validación que nunca se usó para elegir).
Uso: python3 megalab.py config.json salida.csv     (config: {"d1": {"SIMB": [ruta_json, digits]}, "h1": {"SIMB": [ruta_csv, costo]}})"""
import json, csv, sys, random, itertools, statistics as st
from datetime import datetime
from multiprocessing import Pool

def sma(x, n):
    out=[None]*len(x); s=0.0
    for i,v in enumerate(x):
        s+=v
        if i>=n: s-=x[i-n]
        if i>=n-1: out[i]=s/n
    return out
def rsi(c, n):
    out=[None]*len(c); g=p=0.0
    for i in range(1,len(c)):
        d=c[i]-c[i-1]; up,dn=max(d,0),max(-d,0)
        if i<=n: g+=up/n; p+=dn/n
        else: g=(g*(n-1)+up)/n; p=(p*(n-1)+dn)/n
        if i>=n: out[i]=100.0 if p==0 else 100-100/(1+g/p)
    return out
def atr(h,l,c,n):
    tr=[h[0]-l[0]]+[max(h[i]-l[i],abs(h[i]-c[i-1]),abs(l[i]-c[i-1])) for i in range(1,len(c))]
    return sma(tr,n)
def rmax(x,n):  # max of previous n bars (excluding current)
    out=[None]*len(x)
    for i in range(n,len(x)): out[i]=max(x[i-n:i])
    return out
def rmin(x,n):
    out=[None]*len(x)
    for i in range(n,len(x)): out[i]=min(x[i-n:i])
    return out

class M:
    def __init__(s, t,o,h,l,c,cost):
        s.t,s.o,s.h,s.l,s.c,s.cost=t,o,h,l,c,cost; s.n=len(c); s._c={}
        s.a=atr(h,l,c,20)
    def g(s,k,f):
        if k not in s._c: s._c[k]=f()
        return s._c[k]

def sim(m, el, es, xl, xs, slm, rr=None, maxh=None):
    """el/es: entrada larga/corta (bool por vela, al cierre). xl/xs: salida por condición al cierre. Resultado en R."""
    o,h,l,c,a=m.o,m.h,m.l,m.c,m.a; ops=[]; i=0; n=m.n
    while i<n-1:
        s=1 if el[i] else -1 if es[i] else 0
        if not s or a[i] is None or a[i]<=0: i+=1; continue
        e=o[i+1]; d=slm*a[i]; sl=e-s*d; tp=e+s*rr*d if rr else None; j=i+1; r=None
        while j<n:
            if (s==1 and l[j]<=sl) or (s==-1 and h[j]>=sl): r=-1.0; break
            if tp is not None and ((s==1 and h[j]>=tp) or (s==-1 and l[j]<=tp)): r=rr; break
            if (xl[j] if s==1 else xs[j]) or (maxh and j-i>=maxh):
                if j+1<n: r=(o[j+1]-e)*s/d; j+=1
                else: r=(c[j]-e)*s/d
                break
            j+=1
        if r is None: r=(c[-1]-e)*s/d; j=n-1
        ops.append((m.t[i+1], r-m.cost/d)); i=j+1
    return ops

F=[False]
def fam_d1(m, fam, p):
    c=m.c; n=m.n; NO=[False]*n
    if fam=="rsi":
        k,thr,filt,ex,slm,lado=p
        r=m.g(("rsi",k),lambda:rsi(c,k)); f=m.g(("sma",filt),lambda:sma(c,filt)) if filt else None
        el=[r[i] is not None and r[i]<thr and (f is None or (f[i] is not None and c[i]>f[i])) for i in range(n)]
        es=NO if lado=="L" else [r[i] is not None and r[i]>100-thr and (f is None or (f[i] is not None and c[i]<f[i])) for i in range(n)]
        if ex=="rsi50": xl=[r[i] is not None and r[i]>50 for i in range(n)]; xs=[r[i] is not None and r[i]<50 for i in range(n)]
        else:
            q=int(ex[3:]); mm=m.g(("sma",q),lambda:sma(c,q))
            xl=[mm[i] is not None and c[i]>mm[i] for i in range(n)]; xs=[mm[i] is not None and c[i]<mm[i] for i in range(n)]
        return sim(m,el,es,xl,xs,slm,None,10)
    if fam=="donchian":
        N,xn,slm,lado=p
        hi=m.g(("rmax",N),lambda:rmax(m.h,N)); lo=m.g(("rmin",N),lambda:rmin(m.l,N))
        xhi=m.g(("rmax",xn),lambda:rmax(m.h,xn)); xlo=m.g(("rmin",xn),lambda:rmin(m.l,xn))
        el=[hi[i] is not None and c[i]>hi[i] for i in range(n)]
        es=NO if lado=="L" else [lo[i] is not None and c[i]<lo[i] for i in range(n)]
        xl=[xlo[i] is not None and c[i]<xlo[i] for i in range(n)]; xs=[xhi[i] is not None and c[i]>xhi[i] for i in range(n)]
        return sim(m,el,es,xl,xs,slm)
    if fam=="macross":
        fa,sl_,slm,lado=p
        f=m.g(("sma",fa),lambda:sma(c,fa)); s_=m.g(("sma",sl_),lambda:sma(c,sl_))
        up=[f[i] is not None and s_[i] is not None and f[i]>s_[i] for i in range(n)]
        el=[i>0 and up[i] and not up[i-1] and s_[i-1] is not None for i in range(n)]
        es=NO if lado=="L" else [i>0 and (not up[i]) and up[i-1] for i in range(n)]
        return sim(m,el,es,[not x for x in up],up,slm)
    if fam=="boll":
        per,dev,filt,slm,lado=p
        mid=m.g(("sma",per),lambda:sma(c,per))
        sd=m.g(("sd",per),lambda:[None if i<per-1 else st.pstdev(c[i-per+1:i+1]) for i in range(n)])
        f=m.g(("sma",filt),lambda:sma(c,filt)) if filt else None
        el=[mid[i] is not None and c[i]<mid[i]-dev*sd[i] and (f is None or (f[i] is not None and c[i]>f[i])) for i in range(n)]
        es=NO if lado=="L" else [mid[i] is not None and c[i]>mid[i]+dev*sd[i] and (f is None or (f[i] is not None and c[i]<f[i])) for i in range(n)]
        xl=[mid[i] is not None and c[i]>mid[i] for i in range(n)]; xs=[mid[i] is not None and c[i]<mid[i] for i in range(n)]
        return sim(m,el,es,xl,xs,slm,None,15)
    if fam=="ndayrr":
        N,slm,rr,lado=p
        hi=m.g(("rmax",N),lambda:rmax(m.h,N)); lo=m.g(("rmin",N),lambda:rmin(m.l,N))
        el=[hi[i] is not None and c[i]>hi[i] for i in range(n)]
        es=NO if lado=="L" else [lo[i] is not None and c[i]<lo[i] for i in range(n)]
        return sim(m,el,es,NO,NO,slm,rr,20)
    if fam=="streak":
        k,hold,filt,slm,lado=p
        f=m.g(("sma",filt),lambda:sma(c,filt)) if filt else None
        dn=[i>=k and all(c[i-j]<c[i-j-1] for j in range(k)) for i in range(n)]
        up=[i>=k and all(c[i-j]>c[i-j-1] for j in range(k)) for i in range(n)]
        el=[dn[i] and (f is None or (f[i] is not None and c[i]>f[i])) for i in range(n)]
        es=NO if lado=="L" else [up[i] and (f is None or (f[i] is not None and c[i]<f[i])) for i in range(n)]
        return sim(m,el,es,NO,NO,slm,None,hold)
    if fam=="mom":
        lb,slm,lado=p
        pos=[i>=lb and c[i]>c[i-lb] for i in range(n)]; neg=[i>=lb and c[i]<c[i-lb] for i in range(n)]
        el=[pos[i] and i>0 and not pos[i-1] for i in range(n)]
        es=NO if lado=="L" else [neg[i] and i>0 and not neg[i-1] for i in range(n)]
        return sim(m,el,es,[not x for x in pos],[not x for x in neg],slm)
    if fam=="azar":
        seed,prob,hold,slm=p; rnd=random.Random(seed)
        el=[False]*n; es=[False]*n
        for i in range(n):
            if rnd.random()<prob: (el if rnd.random()<0.5 else es)[i]=True
        return sim(m,el,es,NO,NO,slm,None,hold)

def grids_d1():
    G=[]
    for p in itertools.product((2,3,4),(5,10,15,20,25),(0,100,200),("sma3","sma5","sma10","rsi50"),(2,3),("A","L")): G.append(("rsi",p))
    for N in (10,15,20,30,40,55,70,100):
        for xn in sorted({max(2,N//4),max(2,N//2),N}):
            for slm in (1.5,2,3):
                for lado in ("A","L"): G.append(("donchian",(N,xn,slm,lado)))
    for fa,sl_ in ((5,20),(5,50),(10,50),(10,100),(20,50),(20,100),(20,200),(50,100),(50,200),(10,200)):
        for slm in (2,3):
            for lado in ("A","L"): G.append(("macross",(fa,sl_,slm,lado)))
    for p in itertools.product((10,20),(1.5,2,2.5),(0,200),(2,3),("A","L")): G.append(("boll",p))
    for p in itertools.product((5,10,20),(1,1.5,2),(1,2,3),("A","L")): G.append(("ndayrr",p))
    for p in itertools.product((2,3,4,5),(1,3,5),(0,200),(2,3),("A","L")): G.append(("streak",p))
    for p in itertools.product((20,60,120,250),(2,3),("A","L")): G.append(("mom",p))
    for seed in range(150): G.append(("azar",(seed,0.03,(1,3,5,10)[seed%4],(2,3)[seed%2])))
    return G

# ---------- H1: ruptura de rango por sesión ----------
def sim_h1(m, rs, rl, ew, slm, rr):
    o,h,l,c,a,t=m.o,m.h,m.l,m.c,m.a,m.t; ops=[]; byd={}
    for i,x in enumerate(t): byd.setdefault(x.date(),[]).append(i)
    fin=-1
    for d,idx in byd.items():
        rng=[i for i in idx if rs<=t[i].hour<rs+rl]
        if len(rng)<rl: continue
        hi=max(h[i] for i in rng); lo=min(l[i] for i in rng)
        for i in idx:
            if i<=fin or i>=m.n-1: continue
            hr=t[i].hour
            if hr<rs+rl: continue
            if hr>=rs+rl+ew: break
            s=1 if c[i]>hi else -1 if c[i]<lo else 0
            if not s or a[i] is None: continue
            e=o[i+1]; dd=slm*a[i]; sl=e-s*dd; tp=e+s*rr*dd; r=None
            for j in range(i+1,m.n):
                if (s==1 and l[j]<=sl) or (s==-1 and h[j]>=sl): r=-1.0; break
                if (s==1 and h[j]>=tp) or (s==-1 and l[j]<=tp): r=rr; break
            if r is None: r=(c[-1]-e)*s/dd; j=m.n-1
            ops.append((t[i+1], r-m.cost/dd)); fin=j; break
    return ops
def grids_h1():
    return [("sesion",p) for p in itertools.product((0,2,4,6,7,8,12,13,14),(1,2,3,4,6),(3,6,10),(1,1.5,2),(1,1.5,2,3)) if p[0]+p[1]+p[2]<=23]

def stats(ops, split):
    def one(x):
        if not x: return 0,0.0,0.0
        r=[v for _,v in x]; g=sum(v for v in r if v>0); p=-sum(v for v in r if v<=0)
        return len(r), sum(r)/len(r), (g/p if p>0 else 99.0)
    a=[o for o in ops if o[0]<split]; b=[o for o in ops if o[0]>=split]
    return one(a)+one(b)

MK={}
def init(cfg):
    global MK
    for s,(path,dg) in cfg["d1"].items():
        raw=json.load(open(path)); pt=10**-dg; cost=2*sorted(x["spread"] for x in raw)[len(raw)//2]*pt
        MK[("d1",s)]=M([datetime.fromisoformat(x["time"][:19]) for x in raw],[x["open"] for x in raw],[x["high"] for x in raw],[x["low"] for x in raw],[x["close"] for x in raw],cost)
    for s,(path,cost) in cfg.get("h1",{}).items():
        rows=list(csv.DictReader(open(path)))
        MK[("h1",s)]=M([datetime.fromisoformat(r["time"][:19]) for r in rows],*[[float(r[k]) for r in rows] for k in ("open","high","low","close")],cost)
        MK[("h1",s)].a=atr(MK[("h1",s)].h,MK[("h1",s)].l,MK[("h1",s)].c,14)
def run(task):
    tf,s,fam,p=task; m=MK[(tf,s)]
    ops=fam_d1(m,fam,p) if tf=="d1" else sim_h1(m,*p)
    split=m.t[int(m.n*0.6)]
    return (tf,s,fam,"|".join(map(str,p)))+stats(ops,split)
if __name__=="__main__":
    cfg=json.load(open(sys.argv[1])); init(cfg)
    tasks=[("d1",s,f,p) for s in cfg["d1"] for f,p in grids_d1()]+[("h1",s,f,p) for s in cfg.get("h1",{}) for f,p in grids_h1()]
    print("combinaciones:",len(tasks),flush=True)
    with Pool(4,initializer=init,initargs=(cfg,)) as pool, open(sys.argv[2],"w",newline="") as fo:
        w=csv.writer(fo); w.writerow(["tf","mercado","familia","params","n_is","exp_is","pf_is","n_oos","exp_oos","pf_oos"])
        for k,row in enumerate(pool.imap_unordered(run,tasks,chunksize=20)):
            w.writerow(row)
            if k%2000==0: print(k,flush=True)
    print("listo")
