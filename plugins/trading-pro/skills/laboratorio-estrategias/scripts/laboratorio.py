#!/usr/bin/env python3
"""Laboratorio multi-estrategia (sin dependencias). Resultados en R (riesgo inicial), con costo por operación.
Uso:
  python3 laboratorio.py diario --json velas_D1.json --costo 0.3            (Donchian 20/55, RSI2)
  python3 laboratorio.py h1 --csv velas_H1.csv --costo 0.3                   (máx/mín día anterior, falsa ruptura asiática)
JSON = salida de get_mt5_candles; CSV = time,open,high,low,close (UTC)."""
import json, csv, argparse
from datetime import datetime

def load_json(p):
    return [dict(t=datetime.fromisoformat(c["time"][:19]), o=c["open"], h=c["high"], l=c["low"], c=c["close"]) for c in json.load(open(p))]
def load_csv(p):
    return [dict(t=datetime.fromisoformat(r["time"][:19]), o=float(r["open"]), h=float(r["high"]), l=float(r["low"]), c=float(r["close"])) for r in csv.DictReader(open(p))]
def sma(x, n): return [None if i < n-1 else sum(x[i-n+1:i+1])/n for i in range(len(x))]
def atr(v, n=14):
    tr = [v[0]["h"]-v[0]["l"]] + [max(v[i]["h"]-v[i]["l"], abs(v[i]["h"]-v[i-1]["c"]), abs(v[i]["l"]-v[i-1]["c"])) for i in range(1, len(v))]
    return sma(tr, n)
def rsi(c, n):
    out=[None]*len(c); g=p=0.0
    for i in range(1,len(c)):
        d=c[i]-c[i-1]; up,dn=max(d,0),max(-d,0)
        if i<=n: g+=up/n; p+=dn/n
        else: g=(g*(n-1)+up)/n; p=(p*(n-1)+dn)/n
        if i>=n: out[i]=100 if p==0 else 100-100/(1+g/p)
    return out
def met(ops, bloques):
    if not ops: return "sin operaciones"
    r=[x[1] for x in ops]; g=[x for x in r if x>0]; pe=[x for x in r if x<=0]
    pf=sum(g)/-sum(pe) if pe and sum(pe) else 99
    eq=pk=dd=0
    for x in r: eq+=x; pk=max(pk,eq); dd=max(dd,pk-eq)
    t0,t1=ops[0][0],ops[-1][0]; paso=(t1-t0)/bloques; b=[0.0]*bloques
    for t,x in ops: b[min(int((t-t0)/paso),bloques-1)]+=x
    pos=sum(1 for x in b if x>0)
    return (f"ops={len(r):4} acierto={len(g)/len(r):5.1%} total={sum(r):+7.1f}R exp={sum(r)/len(r):+.2f}R PF={pf:4.2f} DD={dd:5.1f}R "
            f"| bloques +{pos}/{bloques}: " + " ".join(f"{x:+.1f}" for x in b))

# ---------- DIARIO ----------
def donchian(v, n, costo, lado):
    a=atr(v,20); ops=[]; pos=None
    for i in range(n, len(v)-1):
        if pos:
            s,e,d,t0=pos; sal=n//2
            lo=min(x["l"] for x in v[i-sal:i]); hi=max(x["h"] for x in v[i-sal:i])
            sl=e-s*2*d
            if (s==1 and v[i]["l"]<=sl) or (s==-1 and v[i]["h"]>=sl): ops.append((t0,-1-costo/(2*d))); pos=None; continue
            if (s==1 and v[i]["c"]<lo) or (s==-1 and v[i]["c"]>hi):
                ops.append((t0,(v[i+1]["o"]-e)*s/(2*d)-costo/(2*d))); pos=None
            continue
        hi=max(x["h"] for x in v[i-n:i]); lo=min(x["l"] for x in v[i-n:i])
        if a[i] is None: continue
        if v[i]["c"]>hi and lado in ("ambos","largo"): pos=(1,v[i+1]["o"],a[i],v[i+1]["t"])
        elif v[i]["c"]<lo and lado in ("ambos","corto"): pos=(-1,v[i+1]["o"],a[i],v[i+1]["t"])
    return ops
def rsi2(v, costo, lado):
    c=[x["c"] for x in v]; m200=sma(c,200); m5=sma(c,5); r=rsi(c,2); a=atr(v,20); ops=[]; i=200
    while i < len(v)-1:
        s=0
        if lado in ("ambos","largo") and c[i]>m200[i] and r[i]<10: s=1
        elif lado in ("ambos","corto") and c[i]<m200[i] and r[i]>90: s=-1
        if not s: i+=1; continue
        e=v[i+1]["o"]; d=2.5*a[i]; sl=e-s*d; j=i+1; res=None
        while j < len(v)-1 and j-i <= 10:
            if (s==1 and v[j]["l"]<=sl) or (s==-1 and v[j]["h"]>=sl): res=-1; break
            if (s==1 and c[j]>m5[j]) or (s==-1 and c[j]<m5[j]) or j-i==10: res=(v[j+1]["o"]-e)*s/d; j+=1; break
            j+=1
        if res is None: res=(c[-1]-e)*s/d
        ops.append((v[i+1]["t"],res-costo/d)); i=j
    return ops

# ---------- H1 ----------
def por_dia(v):
    d={}
    for i,x in enumerate(v): d.setdefault(x["t"].date(),[]).append(i)
    return d
def salir(v,i,s,e,sl,tp,d,costo):
    for j in range(i,len(v)):
        if (s==1 and v[j]["l"]<=sl) or (s==-1 and v[j]["h"]>=sl): return j,(sl-e)*s/d-costo/d
        if (s==1 and v[j]["h"]>=tp) or (s==-1 and v[j]["l"]<=tp): return j,(tp-e)*s/d-costo/d
    return len(v)-1,(v[-1]["c"]-e)*s/d-costo/d
def pdhl(v,costo,rr=2,h0=7,h1=16):
    a=atr(v); dias=por_dia(v); ks=sorted(dias); ops=[]; fin=-1
    for k in range(1,len(ks)):
        prev=dias[ks[k-1]]; ph=max(v[i]["h"] for i in prev); pl=min(v[i]["l"] for i in prev)
        for i in dias[ks[k]]:
            if i<=fin or i>=len(v)-1 or a[i] is None or not (h0<=v[i]["t"].hour<h1): continue
            s=1 if v[i]["c"]>ph else -1 if v[i]["c"]<pl else 0
            if not s: continue
            e=v[i+1]["o"]; d=1.5*a[i]; fin,r=salir(v,i+1,s,e,e-s*d,e+s*rr*d,d,costo); ops.append((v[i+1]["t"],r)); break
    return ops
def falsa_asia(v,costo,rr=2,h0=6,h1=16):
    a=atr(v); dias=por_dia(v); ops=[]; fin=-1
    for k in sorted(dias):
        idx=dias[k]; rango=[i for i in idx if v[i]["t"].hour<6]
        if len(rango)<5: continue
        hi=max(v[i]["h"] for i in rango); lo=min(v[i]["l"] for i in rango); ext_h=hi; ext_l=lo
        for i in idx:
            if v[i]["t"].hour<h0 or i<=fin or i>=len(v)-1: continue
            if v[i]["t"].hour>=h1: break
            if v[i]["c"]>hi or v[i]["c"]<lo: break  # ruptura real: no hay falsa
            ext_h=max(ext_h,v[i]["h"]); ext_l=min(ext_l,v[i]["l"])
            s=-1 if v[i]["h"]>hi else 1 if v[i]["l"]<lo else 0
            if not s or a[i] is None: continue
            e=v[i+1]["o"]; sl=(ext_h if s==-1 else ext_l)-s*0.25*a[i]; d=(e-sl)*s
            if d<=0: break
            fin,r=salir(v,i+1,s,e,sl,e+s*rr*d,d,costo); ops.append((v[i+1]["t"],r)); break
    return ops

ap=argparse.ArgumentParser(); ap.add_argument("modo",choices=["diario","h1"]); ap.add_argument("--json"); ap.add_argument("--csv"); ap.add_argument("--costo",type=float,required=True)
A=ap.parse_args()
if A.modo=="diario":
    v=load_json(A.json); print(f"{len(v)} velas D1 {v[0]['t']:%Y-%m-%d} -> {v[-1]['t']:%Y-%m-%d} | comprar y mantener: {v[0]['c']:.0f} -> {v[-1]['c']:.0f} ({v[-1]['c']/v[0]['c']-1:+.0%})")
    for n in (20,55):
        for lado in ("ambos","largo"): print(f"Donchian {n:2} {lado:6}", met(donchian(v,n,A.costo,lado),5))
    for lado in ("ambos","largo"): print(f"RSI2      {lado:6}", met(rsi2(v,A.costo,lado),5))
else:
    v=load_csv(A.csv); print(f"{len(v)} velas H1 {v[0]['t']:%Y-%m-%d} -> {v[-1]['t']:%Y-%m-%d}")
    for rr in (1.5,2,3): print(f"Max/min dia anterior RR{rr}", met(pdhl(v,A.costo,rr),4))
    for rr in (1,1.5,2): print(f"Falsa ruptura asia  RR{rr}", met(falsa_asia(v,A.costo,rr),4))
