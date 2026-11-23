#!/usr/bin/env python3
"""Backtester simple en R (sin dependencias). CSV: time,open,high,low,close.
Entrada en la apertura de la vela siguiente a la señal. SL por ATR, TP = rr * SL.
Si SL y TP se tocan en la misma vela, se asume SL (conservador)."""
import argparse
import csv
from datetime import datetime


def cargar(ruta):
    velas = []
    with open(ruta, newline="") as f:
        for r in csv.DictReader(f):
            t = r["time"]
            try:
                ts = datetime.fromtimestamp(float(t))
            except ValueError:
                ts = datetime.fromisoformat(t.replace("Z", "").replace(" ", "T"))
            velas.append({"t": ts, **{k: float(r[k]) for k in ("open", "high", "low", "close")}})
    return velas


def sma(v, n):
    out, s = [None] * len(v), 0.0
    for i, x in enumerate(v):
        s += x
        if i >= n:
            s -= v[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def atr(velas, n=14):
    tr = [velas[0]["high"] - velas[0]["low"]]
    for i in range(1, len(velas)):
        h, l, pc = velas[i]["high"], velas[i]["low"], velas[i - 1]["close"]
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sma(tr, n)


def rsi(c, n=14):
    out = [None] * len(c)
    g = p = 0.0
    for i in range(1, len(c)):
        d = c[i] - c[i - 1]
        up, dn = max(d, 0), max(-d, 0)
        if i <= n:
            g += up / n
            p += dn / n
            if i == n:
                out[i] = 100 - 100 / (1 + g / p) if p else 100
        else:
            g = (g * (n - 1) + up) / n
            p = (p * (n - 1) + dn) / n
            out[i] = 100 - 100 / (1 + g / p) if p else 100
    return out


# --- Señales: devuelven lista de +1 (compra), -1 (venta), 0 por vela (calculada al cierre) ---
def senal_cruce_medias(velas, a):
    c = [v["close"] for v in velas]
    f, s = sma(c, a.rapida), sma(c, a.lenta)
    out = [0] * len(velas)
    for i in range(1, len(velas)):
        if None in (f[i], s[i], f[i - 1], s[i - 1]):
            continue
        if f[i - 1] <= s[i - 1] and f[i] > s[i]:
            out[i] = 1
        elif f[i - 1] >= s[i - 1] and f[i] < s[i]:
            out[i] = -1
    return out


def senal_ruptura_rango(velas, a):
    out = [0] * len(velas)
    dia, hi, lo, usado = None, None, None, False
    for i, v in enumerate(velas):
        d, h = v["t"].date(), v["t"].hour
        if d != dia:
            dia, hi, lo, usado = d, None, None, False
        if a.hora_inicio <= h < a.hora_fin:
            hi = v["high"] if hi is None else max(hi, v["high"])
            lo = v["low"] if lo is None else min(lo, v["low"])
        elif h >= a.hora_fin and hi is not None and not usado and h < a.hora_corte:
            if v["close"] > hi:
                out[i], usado = 1, True
            elif v["close"] < lo:
                out[i], usado = -1, True
    return out


def senal_rsi_reversion(velas, a):
    r = rsi([v["close"] for v in velas])
    out = [0] * len(velas)
    for i in range(1, len(velas)):
        if r[i] is None or r[i - 1] is None:
            continue
        if r[i - 1] < a.rsi_bajo <= r[i]:
            out[i] = 1
        elif r[i - 1] > a.rsi_alto >= r[i]:
            out[i] = -1
    return out


def simular(velas, senales, a):
    at = atr(velas)
    ops, i = [], 0
    while i < len(velas) - 1:
        s = senales[i]
        if s == 0 or at[i] is None:
            i += 1
            continue
        e = velas[i + 1]["open"] + s * a.costo / 2
        dist = a.atr_sl * at[i]
        sl, tp = e - s * dist, e + s * dist * a.rr
        j, r = i + 1, None
        while j < len(velas):
            v = velas[j]
            toca_sl = v["low"] <= sl if s == 1 else v["high"] >= sl
            toca_tp = v["high"] >= tp if s == 1 else v["low"] <= tp
            if toca_sl:
                r = -1 - (a.costo / 2) / dist
                break
            if toca_tp:
                r = a.rr - (a.costo / 2) / dist
                break
            j += 1
        if r is None:
            r = s * (velas[-1]["close"] - e) / dist
            j = len(velas) - 1
        ops.append({"t": velas[i + 1]["t"], "dir": s, "r": r})
        i = j + 1  # una operación a la vez
    return ops


def metricas(ops):
    if not ops:
        return "sin operaciones"
    rs = [o["r"] for o in ops]
    gan = [r for r in rs if r > 0]
    per = [r for r in rs if r <= 0]
    eq = pico = dd = 0.0
    racha = rmax = 0
    for r in rs:
        eq += r
        pico = max(pico, eq)
        dd = max(dd, pico - eq)
        racha = racha + 1 if r <= 0 else 0
        rmax = max(rmax, racha)
    pf = sum(gan) / abs(sum(per)) if per and sum(per) else float("inf")
    return (f"ops={len(rs)} acierto={len(gan) / len(rs):.1%} total={sum(rs):+.1f}R "
            f"expectativa={sum(rs) / len(rs):+.3f}R PF={pf:.2f} maxDD={dd:.1f}R racha_perd={rmax}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--estrategia", required=True, choices=["cruce_medias", "ruptura_rango", "rsi_reversion"])
    ap.add_argument("--atr-sl", type=float, default=1.5)
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--costo", type=float, default=0.0, help="spread+comisión en unidades de precio")
    ap.add_argument("--walk", type=int, default=1)
    ap.add_argument("--rapida", type=int, default=20)
    ap.add_argument("--lenta", type=int, default=50)
    ap.add_argument("--hora-inicio", type=int, default=0)
    ap.add_argument("--hora-fin", type=int, default=7)
    ap.add_argument("--hora-corte", type=int, default=16)
    ap.add_argument("--rsi-bajo", type=float, default=30)
    ap.add_argument("--rsi-alto", type=float, default=70)
    a = ap.parse_args()
    velas = cargar(a.csv)
    ops = simular(velas, globals()["senal_" + a.estrategia](velas, a), a)
    print(f"{a.estrategia} | {len(velas)} velas {velas[0]['t']} -> {velas[-1]['t']}")
    print("TOTAL:", metricas(ops))
    if a.walk > 1 and ops:
        n = len(velas) // a.walk
        for k in range(a.walk):
            t0 = velas[k * n]["t"]
            t1 = velas[min((k + 1) * n, len(velas)) - 1]["t"]
            print(f"Bloque {k + 1} ({t0:%Y-%m-%d}..{t1:%Y-%m-%d}):", metricas([o for o in ops if t0 <= o["t"] <= t1]))


if __name__ == "__main__":
    main()
