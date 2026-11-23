#!/usr/bin/env python3
"""Calculadora de riesgo para trading (oro / Nasdaq en Axi MT5). Solo librería estándar."""
import argparse
import math
import random

SIMBOLOS = {  # valor por 1.0 de movimiento de precio por 1 lote, lote mínimo/paso
    "XAUUSD": (100.0, 0.01),
    "USTECH": (1.0, 0.1),
    "NAS100.FS": (20.0, 0.1),
}


def lote(a):
    valor, paso = SIMBOLOS.get(a.simbolo.upper(), (a.valor, a.paso))
    if valor is None:
        raise SystemExit("Símbolo desconocido: pasa --valor y --paso")
    riesgo_usd = a.balance * a.riesgo / 100
    bruto = riesgo_usd / (a.sl * valor)
    final = math.floor(bruto / paso + 1e-9) * paso
    print(f"Riesgo: {a.balance} x {a.riesgo}% = ${riesgo_usd:.2f}")
    print(f"Lote bruto: {riesgo_usd:.2f} / ({a.sl} x {valor}) = {bruto:.4f}")
    if final < paso:
        print(f"Lote mínimo {paso} arriesgaría ${paso * a.sl * valor:.2f} (> permitido). NO OPERAR.")
    else:
        print(f"Lote: {final:.2f}  -> riesgo real ${final * a.sl * valor:.2f}")


def recuperar(a):
    p = a.perdida / 100
    print(f"Tras perder {a.perdida}% necesitas ganar {p / (1 - p) * 100:.1f}% para recuperar.")


def racha(a):
    q = 1 - a.acierto / 100
    n = a.operaciones
    esperada = math.log(n) / math.log(1 / q) if 0 < q < 1 else float("inf")
    print(f"Con {a.acierto}% de acierto en {n} operaciones, racha perdedora esperable ~{esperada:.0f} seguidas.")
    print(f"Con 1% de riesgo eso es un DD de ~{esperada:.0f}%. Prepárate para ello.")


def simular(balance, meta, riesgo, p, rr, ops, piso):
    b = balance
    for i in range(ops):
        b += b * riesgo * (rr if random.random() < p else -1)
        if b >= meta:
            return "meta", i + 1
        if b <= piso:
            return "ruina", i + 1
    return "nada", ops


def proyeccion(a):
    p, r = a.acierto / 100, a.riesgo / 100
    exp_r = p * a.rr - (1 - p)
    print(f"Expectativa: {p:.2f} x {a.rr} - {1 - p:.2f} = {exp_r:.2f} R por operación")
    if exp_r <= 0:
        print("Expectativa <= 0: sin ventaja, ninguna cantidad de riesgo llega a la meta de forma fiable.")
    piso = a.balance * (1 - a.dd_max / 100)
    max_ops = a.ops_mes * a.meses
    for riesgo in sorted({a.riesgo, 2.0, 3.0, 5.0}):
        res = [simular(a.balance, a.meta, riesgo / 100, p, a.rr, max_ops, piso) for _ in range(a.sims)]
        meta = [o for k, o in res if k == "meta"]
        ruina = sum(1 for k, _ in res if k == "ruina")
        med = sorted(meta)[len(meta) // 2] / a.ops_mes if meta else float("nan")
        print(f"Riesgo {riesgo:>4}%: llega a ${a.meta:,.0f} {len(meta) / a.sims:6.1%} | "
              f"cae {a.dd_max}% {ruina / a.sims:6.1%} | meses (mediana) {med:4.1f}")
    print(f"(Monte Carlo, {a.sims} simulaciones, horizonte {a.meses} meses. Supuestos fijos: la realidad varía.)")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("lote")
    s.add_argument("--balance", type=float, required=True)
    s.add_argument("--riesgo", type=float, default=1.0)
    s.add_argument("--sl", type=float, required=True, help="distancia al SL en precio")
    s.add_argument("--simbolo", default="XAUUSD")
    s.add_argument("--valor", type=float, default=None)
    s.add_argument("--paso", type=float, default=0.01)
    s.set_defaults(f=lote)
    s = sp.add_parser("recuperar")
    s.add_argument("--perdida", type=float, required=True)
    s.set_defaults(f=recuperar)
    s = sp.add_parser("racha")
    s.add_argument("--acierto", type=float, required=True)
    s.add_argument("--operaciones", type=int, default=100)
    s.set_defaults(f=racha)
    s = sp.add_parser("proyeccion")
    s.add_argument("--balance", type=float, required=True)
    s.add_argument("--meta", type=float, required=True)
    s.add_argument("--riesgo", type=float, default=1.0)
    s.add_argument("--acierto", type=float, required=True)
    s.add_argument("--rr", type=float, required=True)
    s.add_argument("--ops-mes", type=int, default=20)
    s.add_argument("--meses", type=int, default=24)
    s.add_argument("--dd-max", type=float, default=30.0)
    s.add_argument("--sims", type=int, default=3000)
    s.set_defaults(f=proyeccion)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
