import sys, json
RDIR=sys.argv[1]  # carpeta con los JSON de get_mt5_candles D1 (ajustar el mapa U con los nombres de archivo)
sys.argv=['x','diario','--costo','1']
exec(open('laboratorio.py').read().split("ap=argparse.ArgumentParser()")[0])
R=RDIR
def rsi2v(v,costo,umbral,slm,lado="ambos"):
    c=[x["c"] for x in v]; m200=sma(c,200); m5=sma(c,5); r=rsi(c,2); a=atr(v,20); ops=[]; i=200
    while i<len(v)-1:
        s=0
        if lado in("ambos","largo") and c[i]>m200[i] and r[i]<umbral: s=1
        elif lado in("ambos","corto") and c[i]<m200[i] and r[i]>100-umbral: s=-1
        if not s: i+=1; continue
        e=v[i+1]["o"]; d=slm*a[i]; sl=e-s*d; j=i+1; res=None
        while j<len(v)-1 and j-i<=10:
            if (s==1 and v[j]["l"]<=sl) or (s==-1 and v[j]["h"]>=sl): res=-1; break
            if (s==1 and c[j]>m5[j]) or (s==-1 and c[j]<m5[j]) or j-i==10: res=(v[j+1]["o"]-e)*s/d; j+=1; break
            j+=1
        if res is None: res=(c[-1]-e)*s/d
        ops.append((v[i+1]["t"],res-costo/d)); i=j
    return ops
def tot(o): return sum(r for _,r in o)
def blq(o,n=5):
    if not o: return 0
    t0,t1=o[0][0],o[-1][0]; p=(t1-t0)/n or 1; b=[0]*n
    for t,r in o: b[min(int((t-t0)/p),n-1)]+=r
    return sum(1 for x in b if x>0)
# symbol: file, digits, contract, profit-ccy factor to USD (approx), minlot
U={"EURUSD":("cfzfc3",5,100000,1,0.01),"GBPUSD":("75ugi9",5,100000,1,0.01),"USDJPY":("u35c42",3,100000,"inv",0.01),
"AUDUSD":("1r404j",5,100000,1,0.01),"USDCAD":("ptvq54",5,100000,"inv",0.01),"USDMXN":("80qo4t",5,100000,"inv",0.01),
"XAGUSD":("02qb9i",3,5000,1,0.01),"USOIL":("fghjh8",3,10,1,0.1),"US30":("xwbxqn",2,1,1,0.1),"US2000":("epi53g",2,1,1,0.1),
"GER40":("1sibm3",2,1,1.08,0.1),"BTCUSD":("s1k25q",2,1,1,0.1),"ETHUSD":("ud9g7p",3,1,1,0.1)}
import glob
print(f"{'Mercado':8}|{'Compra/mant.':>12}|{'RSI2 base':>10}|{'RSI2 rob.':>9}|{'blq':>4}|{'Don20':>7}|{'Don20L':>7}|{'Don rob.':>8}|{'blq':>4}| riesgo min lote (RSI2 / Don)")
for s,(k,dg,cs,fx,ml) in U.items():
    f=glob.glob(f"{R}/*{k}.txt")[0]; raw=json.load(open(f)); v=load_json(f)
    pt=10**-dg; sp=sorted(x["spread"] for x in raw)[len(raw)//2]*pt; costo=2*sp
    bh=v[-1]["c"]/v[0]["c"]-1
    base=rsi2v(v,costo,10,2.5); grid=[tot(rsi2v(v,costo,u,m)) for u in (5,10,15,20) for m in (2,2.5,3)]
    d20=donchian(v,20,costo,"ambos"); d20l=donchian(v,20,costo,"largo")
    dg_=[tot(donchian(v,n,costo,"ambos")) for n in (20,30,40,55)]
    a=atr(v,20)[-1]; px=v[-1]["c"]; usd=(1/px if fx=="inv" else fx)
    r_rsi=ml*cs*2.5*a*usd; r_don=ml*cs*2*a*usd
    print(f"{s:8}|{bh:+11.0%} |{tot(base):+7.1f}R ({len(base):2})|{sum(1 for x in grid if x>0):3}/12 |{blq(base)}/5|{tot(d20):+6.1f}R|{tot(d20l):+6.1f}R|{sum(1 for x in dg_ if x>0):3}/4   |{blq(d20)}/5 | ${r_rsi:5.0f} / ${r_don:5.0f}")
