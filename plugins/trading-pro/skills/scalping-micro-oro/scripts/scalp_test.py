#!/usr/bin/env python3
"""Prueba de scalping en M1 con spread real. Uso: python3 scalp_test.py velas_m1.json (JSON de get_mt5_candles, period M1).
Señales: cruce EMA9/21, pullback a EMA21 con tendencia EMA50, RSI(7) 20/80 y entradas al AZAR como referencia.
Si una señal no supera al AZAR, no tiene ventaja."""
import json,sys,random,statistics as st
d=json.load(open(sys.argv[1]))
o=[c['open'] for c in d];h=[c['high'] for c in d];l=[c['low'] for c in d];c=[c_['close'] for c_ in d]
sp=[x['spread']/100 for x in d]
n=len(d);dias=len({x['time'][:10] for x in d})
print(f"velas M1={n} dias={dias} spread mediano={st.median(sp):.2f} rango M1 mediano={st.median([h[i]-l[i] for i in range(n)]):.2f}")
def ema(v,k):
    a=2/(k+1);out=[v[0]]
    for x in v[1:]: out.append(out[-1]+a*(x-out[-1]))
    return out
def rsi(v,k=7):
    out=[50]*len(v);g=p=0
    for i in range(1,len(v)):
        dd=v[i]-v[i-1];g=(g*(k-1)+max(dd,0))/k;p=(p*(k-1)+max(-dd,0))/k
        out[i]=100-100/(1+g/p) if p else 100
    return out
e9,e21,e50=ema(c,9),ema(c,21),ema(c,50);r=rsi(c)
def sig_cross(i): return 1 if e9[i-1]<=e21[i-1] and e9[i]>e21[i] else -1 if e9[i-1]>=e21[i-1] and e9[i]<e21[i] else 0
def sig_pull(i):
    if e21[i]>e50[i] and l[i]<=e21[i]<c[i] and c[i]>o[i]: return 1
    if e21[i]<e50[i] and h[i]>=e21[i]>c[i] and c[i]<o[i]: return -1
    return 0
def sig_rsi(i): return 1 if r[i-1]<20<=r[i] else -1 if r[i-1]>80>=r[i] else 0
def sig_break(i):
    if i<16: return 0
    hh=max(h[i-15:i]);ll=min(l[i-15:i])
    return 1 if c[i]>hh else -1 if c[i]<ll else 0
random.seed(1)
def sig_rand(i): return random.choice([1,-1]) if random.random()<0.05 else 0
def run(sig,tp,sl):
    res=[];i=60
    while i<n-1:
        s=sig(i)
        if not s: i+=1;continue
        j=i+1;spr=sp[j];e=o[j]
        # precios del grafico = bid; compra paga spread al entrar, venta al salir
        if s==1: tpp,slp=e+spr+tp-spr, e+spr-sl-spr  # ganancia neta = tp - spr
        r_=None
        while j<n:
            hs = (l[j]<=e-sl) if s==1 else (h[j]>=e+sl)
            ht = (h[j]>=e+tp) if s==1 else (l[j]<=e-tp)
            if hs and ht: r_=(tp-spr) if random.random()<0.5 else (-sl-spr);break
            if hs: r_=-sl-spr;break
            if ht: r_=tp-spr;break
            j+=1
        if r_ is None: break
        res.append(r_);i=j+1
    return res
print(f"{'senal':<9}{'TP/SL':>8}{'ops':>6}{'ops/dia':>8}{'acierto':>8}{'$ medio/op @0.1lot':>20}{'total $ @0.1lot':>16}")
for name,sg in [('cruce',sig_cross),('pullback',sig_pull),('rsi',sig_rsi),('AZAR',sig_rand)]:
    for tp,sl in [(0.2,0.2),(0.3,0.3),(0.5,0.5),(1,1),(2,2)]:
        res=run(sg,tp,sl)
        if not res: continue
        w=sum(1 for x in res if x>0)/len(res)
        print(f"{name:<9}{f'{tp}/{sl}':>8}{len(res):>6}{len(res)/dias:>8.0f}{w:>8.0%}{st.mean(res)*10:>20.2f}{sum(res)*10:>16.0f}")
