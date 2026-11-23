exec(open("pares2.py").read().split("GRID=list")[0])
import random, statistics as st
VALS=[(20,40,60,120),(1.5,2.0,2.5),(0.0,0.5),(3.0,3.5,4.0),(10,20)]
CAND={("US2000","US500"):(40,2.0,0.5,3.5,20),("AUDUSD","EURUSD"):(40,2.0,0.5,3.5,20),("XAGUSD","XPTUSD"):(40,2.0,0.5,4.0,20),
      ("AUDJPY","EURJPY"):(40,2.5,0.0,3.0,10),("USDCAD","USDCHF"):(20,2.0,0.0,3.0,20),("AUDJPY","USDJPY"):(40,2.5,0.5,3.0,10),("LTCUSD","BTCUSD"):(40,2.0,0.5,3.0,10)}
for (a,b),P in CAND.items():
    ts,la,lb,costo=preparar(a,b)
    ops=sim(ts,la,lb,costo,*P); R=[r for _,r in ops]
    c2=st.mean(r for _,r in sim(ts,la,lb,costo*2,*P))
    top=st.mean(sorted(R)[:-5]); q=len(ops)//4
    bl=[st.mean(r for _,r in ops[k*q:(k+1)*q if k<3 else len(ops)]) for k in range(4)]
    rnd=random.Random(3); pneg=sum(1 for _ in range(3000) if sum(rnd.choice(R) for _ in R)<=0)/3000
    vec=[]
    for pos,vals in enumerate(VALS):
        for v in vals:
            if v==P[pos]: continue
            p=list(P); p[pos]=v; o=sim(ts,la,lb,costo,*p); vec.append(bool(o) and st.mean(r for _,r in o)>0)
    fallas=[]
    if c2<=0: fallas.append("costos×2")
    if top<=0: fallas.append("top5")
    if sum(vec)/len(vec)<0.6: fallas.append("vecinos")
    if sum(1 for x in bl if x>0)<3: fallas.append("periodos")
    if pneg>0.10: fallas.append("bootstrap")
    v="RESISTE" if not fallas else "DUDOSA" if len(fallas)==1 else "FRÁGIL"
    print(f"{a}/{b:7} {len(R):3d} ops | exp {st.mean(R):+.2f}R | costos×2 {c2:+.2f} | sin top5 {top:+.2f} | periodos +{sum(1 for x in bl if x>0)}/4 | vecinos {sum(vec)}/{len(vec)} | P(suerte) {pneg:.0%} → {v} {' '.join(fallas)}")
