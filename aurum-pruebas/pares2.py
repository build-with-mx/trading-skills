import sqlite3, math, statistics as st, itertools, random, sys
from collections import defaultdict
con=sqlite3.connect('datos.db')
def serie(s):
    f=con.execute("select time,close,spread from velas where simbolo=? and tf='D1' order by time",(s,)).fetchall()
    return {t:(c,sp) for t,c,sp in f}
PARES=[("US2000","US500"),("AUDUSD","EURUSD"),("EURUSD","GBPUSD"),("US500","USTECH"),("US30","US500"),("USTECH","US2000"),
("GER40","FRA40"),("EU50","GER40"),("UK100","EU50"),("FRA40","EU50"),("UK100","GER40"),("JPN225","AUS200"),("HK50","JPN225"),("US500","GER40"),("US500","UK100"),
("UKOIL","USOIL"),("XAUUSD","XAGUSD"),("XAUUSD","XPTUSD"),("XAGUSD","XPTUSD"),("COPPER.fs","XAGUSD"),
("EURJPY","GBPJPY"),("AUDJPY","EURJPY"),("AUDUSD","NZDUSD"),("USDCAD","USDCHF"),("EURGBP","EURUSD"),("NZDUSD","EURUSD"),("AUDJPY","USDJPY"),
("BTCUSD","ETHUSD"),("SOL-USD","ETHUSD"),("LTCUSD","BTCUSD"),("XRPUSD","BTCUSD")]
def preparar(a,b):
    A,B=serie(a),serie(b); ts=sorted(set(A)&set(B))
    la=[math.log(A[t][0]) for t in ts]; lb=[math.log(B[t][0]) for t in ts]
    costo=st.median(A[t][1]/A[t][0] for t in ts)*2+st.median(B[t][1]/B[t][0] for t in ts)*2
    return ts,la,lb,costo
def sim(ts,la,lb,costo,L,E,X,S,H,azar=None):
    n=len(ts); ops=[]; i=L
    sp=[la[k]-lb[k] for k in range(n)]
    while i<n-1:
        w=sp[i-L:i]; m=st.mean(w); sd=st.pstdev(w)
        if sd<=0: i+=1; continue
        z=(sp[i]-m)/sd
        if azar is not None:
            lado = azar.choice((1,-1)) if azar.random()<0.06 else 0
        else:
            lado = 1 if z<-E else -1 if z>E else 0   # 1 = comprar el ratio (A arriba / B abajo)
        if not lado: i+=1; continue
        e=sp[i]; d=(S-E)*sd; r=None
        for j in range(i+1,min(n,i+H+1)):
            mov=(sp[j]-e)*lado
            if mov<=-d: r=-1.0; break
            zj=(sp[j]-m)/sd
            if (lado==1 and zj>-X) or (lado==-1 and zj<X): r=mov/d; break
        if r is None: j=min(n-1,i+H); r=(sp[j]-e)*lado/d
        ops.append((ts[i],max(r,-1.5)-costo/d)); i=j+1
    return ops
def stats(ops,corte):
    a=[r for t,r in ops if t<corte]; b=[r for t,r in ops if t>=corte]
    return (len(a),st.mean(a) if a else 0,len(b),st.mean(b) if b else 0)
GRID=list(itertools.product((20,40,60,120),(1.5,2.0,2.5),(0.0,0.5),(3.0,3.5,4.0),(10,20)))
print(f"{len(GRID)} variantes por par × {len(PARES)} pares = {len(GRID)*len(PARES)}")
res={}
for a,b in PARES:
    ts,la,lb,costo=preparar(a,b); corte=ts[int(len(ts)*0.6)]
    filas=[]
    for p in GRID:
        n1,e1,n2,e2=stats(sim(ts,la,lb,costo,*p),corte)
        if n1>=15 and n2>=8: filas.append((p,n1,e1,n2,e2))
    rnd=random.Random(1); az=[]
    for k in range(60):
        p=GRID[k*5%len(GRID)]; n1,e1,n2,e2=stats(sim(ts,la,lb,costo,*p,azar=rnd),corte)
        if n1>=15 and n2>=8: az.append(e1>0 and e2>0)
    ok=sum(1 for f in filas if f[2]>0 and f[4]>0)/max(1,len(filas))
    mi=st.median(f[2] for f in filas) if filas else 0; mo=st.median(f[4] for f in filas) if filas else 0
    base=sum(az)/max(1,len(az))
    aprob= ok>=max(0.6,2*base) and mi>0.05 and mo>0.05
    rob=sorted([f for f in filas if f[2]>0 and f[4]>0], key=lambda f:min(f[2],f[4]), reverse=True)
    elegida=rob[len(rob)//4] if rob else None
    res[(a,b)]=(ok,mi,mo,base,aprob,elegida)
    print(f"{a}/{b:7} costo {costo*1e4:5.1f}pb | variantes OK {ok:4.0%} (azar {base:3.0%}) | mediana IS {mi:+.3f}R OOS {mo:+.3f}R | {'✅ APROBADA' if aprob else '❌'} {('robusta: L=%d E=%.1f X=%.1f S=%.1f H=%d  IS %d ops %+.2fR / OOS %d ops %+.2fR' % (elegida[0]+elegida[1:])) if aprob and elegida else ''}")
