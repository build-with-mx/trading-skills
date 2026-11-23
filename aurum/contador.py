"""
CONTADOR — registra y analiza todo lo que hace Aurum. Corre en su propia ventana.
Cada hora: lee el historial de MT5, guarda cada operación cerrada en aurum.db (SQLite) y genera contador_reporte.md
con estadísticas por estrategia (operaciones, acierto, resultado, R, expectativa, profit factor, caída máx., swap,
deslizamiento) y la comparación en vivo vs. backtest.
Cada día a las 22:05 UTC (≈ 4 pm Monterrey) manda el resumen a Telegram.
Ejecutar:  python contador.py        (o  python contador.py --una-vez  para generar el reporte y salir)
"""
import csv
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_ESTADO = os.path.join(CARPETA, "aurum_estado.json")
RUTA_OPS = os.path.join(CARPETA, "aurum_operaciones.csv")
RUTA_DB = os.path.join(CARPETA, "aurum.db")
RUTA_REPORTE = os.path.join(CARPETA, "contador_reporte.md")

# Expectativa por operación esperada según los backtests (para comparar en vivo vs. backtest)
BACKTEST_R = {"ruptura_asiatica": 0.22, "donchian": 0.30, "rsi2": 0.15, "ibs": 0.12}


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def estadisticas(ops):
    """ops: lista de dicts con 'neto' ($) y 'R'. Función pura (se puede probar sin MT5)."""
    if not ops:
        return None
    netos = [o["neto"] for o in ops]
    rs = [o["R"] for o in ops if o["R"] is not None]
    gan = sum(x for x in netos if x > 0)
    per = -sum(x for x in netos if x <= 0)
    eq = pico = caida = 0.0
    for x in netos:
        eq += x
        pico = max(pico, eq)
        caida = max(caida, pico - eq)
    return {"n": len(ops), "acierto": sum(1 for x in netos if x > 0) / len(ops), "total": sum(netos),
            "R_total": sum(rs), "expectativa_R": (sum(rs) / len(rs)) if rs else None,
            "pf": (gan / per) if per > 0 else float("inf"), "caida_max": caida,
            "swap": sum(o.get("swap", 0) for o in ops), "desliz_medio": None}


def desliz_por_estrategia():
    """Deslizamiento = precio ejecutado vs precio pedido, en la dirección desfavorable (de aurum_operaciones.csv)."""
    res = {}
    if not os.path.exists(RUTA_OPS):
        return res
    with open(RUTA_OPS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("accion") != "ABRIR" or not r.get("precio_pedido"):
                continue
            d = (float(r["precio"]) - float(r["precio_pedido"])) * (1 if r["direccion"] == "COMPRA" else -1)
            res.setdefault(r["estrategia"], []).append(d)
    return {k: sum(v) / len(v) for k, v in res.items()}


def leer_cierres(mt5, cfg, estado):
    """Agrupa los deals de MT5 por posición y devuelve las operaciones cerradas."""
    magics = {e["magic"]: n for n, e in cfg["estrategias"].items()}
    adoptadas = estado.get("adoptadas", {})
    riesgos = estado.get("riesgos", {})
    deals = mt5.history_deals_get(datetime.now() - timedelta(days=400), datetime.now() + timedelta(days=1)) or []
    por_pos = {}
    for d in deals:
        if d.position_id:
            por_pos.setdefault(d.position_id, []).append(d)
    bal = mt5.account_info().balance
    ops = []
    for pid, ds in por_pos.items():
        entrada = [d for d in ds if d.entry == mt5.DEAL_ENTRY_IN]
        salida = [d for d in ds if d.entry == mt5.DEAL_ENTRY_OUT]
        if not entrada or not salida:
            continue
        e0 = entrada[0]
        estr = magics.get(e0.magic) or adoptadas.get(str(pid)) or ("experimento" if e0.magic else "manual")
        neto = sum(d.profit + d.swap + d.commission for d in salida) + sum(d.commission for d in entrada)
        riesgo = riesgos.get(str(pid)) or riesgos.get(str(e0.order)) or bal * cfg["riesgo_por_operacion"]
        ops.append({"posicion": pid, "estrategia": estr, "simbolo": e0.symbol, "direccion": "COMPRA" if e0.type == mt5.DEAL_TYPE_BUY else "VENTA",
                    "lote": e0.volume, "entrada": e0.price, "salida": salida[-1].price,
                    "abierta": datetime.fromtimestamp(e0.time, timezone.utc).isoformat(), "cerrada": datetime.fromtimestamp(salida[-1].time, timezone.utc).isoformat(),
                    "neto": neto, "swap": sum(d.swap for d in salida), "R": neto / riesgo if riesgo else None})
    return ops


def guardar_db(ops):
    con = sqlite3.connect(RUTA_DB)
    con.execute("""CREATE TABLE IF NOT EXISTS operaciones (posicion INTEGER PRIMARY KEY, estrategia TEXT, simbolo TEXT,
                   direccion TEXT, lote REAL, entrada REAL, salida REAL, abierta TEXT, cerrada TEXT, neto REAL, swap REAL, R REAL)""")
    con.executemany("""INSERT OR REPLACE INTO operaciones VALUES (:posicion,:estrategia,:simbolo,:direccion,:lote,:entrada,:salida,
                       :abierta,:cerrada,:neto,:swap,:R)""", ops)
    con.commit()
    con.close()


def reporte(ops, cuenta):
    desl = desliz_por_estrategia()
    lineas = [f"# Reporte del Contador — {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC",
              f"Cuenta {cuenta.login} · Balance ${cuenta.balance:,.2f} · Equity ${cuenta.equity:,.2f}", "",
              "| Estrategia | Ops | Acierto | Resultado $ | R total | Expectativa R (vivo) | Expectativa R (backtest) | PF | Caída máx $ | Swap $ | Desliz. medio |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    resumen = []
    for estr in sorted({o["estrategia"] for o in ops}):
        s = estadisticas([o for o in ops if o["estrategia"] == estr])
        exp = f"{s['expectativa_R']:+.2f}" if s["expectativa_R"] is not None else "—"
        bt = f"{BACKTEST_R[estr]:+.2f}" if estr in BACKTEST_R else "—"
        d = f"{desl[estr]:+.4f}" if estr in desl else "—"
        lineas.append(f"| {estr} | {s['n']} | {s['acierto']:.0%} | {s['total']:+,.2f} | {s['R_total']:+.1f} | {exp} | {bt} | {s['pf']:.2f} | {s['caida_max']:,.0f} | {s['swap']:+,.2f} | {d} |")
        resumen.append(f"• {estr}: {s['n']} ops, {s['acierto']:.0%} acierto, {s['total']:+,.0f}$ ({s['R_total']:+.1f}R)")
    t = estadisticas(ops)
    if t:
        lineas += ["", f"**Total**: {t['n']} operaciones · acierto {t['acierto']:.0%} · {t['total']:+,.2f} $ · swap {t['swap']:+,.2f} $"]
    lineas += ["", "Notas: con menos de 30 operaciones por estrategia, las cifras todavía no son significativas.",
               "Si una estrategia rinde < 50% de su backtest tras 30+ operaciones → revisarla con Claude."]
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    return resumen, t


def ciclo(mt5, enviar_resumen):
    cfg = cargar(RUTA_CONFIG, None)
    estado = cargar(RUTA_ESTADO, {})
    ops = leer_cierres(mt5, cfg, estado)
    guardar_db(ops)
    cuenta = mt5.account_info()
    resumen, t = reporte(ops, cuenta)
    if enviar_resumen:
        hoy = datetime.now(timezone.utc).date().isoformat()
        de_hoy = [o for o in ops if o["cerrada"].startswith(hoy)]
        th = estadisticas(de_hoy)
        texto = (f"📊 Resumen del día\nBalance ${cuenta.balance:,.2f} · Equity ${cuenta.equity:,.2f}\n"
                 f"Hoy: {th['n'] if th else 0} cerradas, {th['total'] if th else 0:+,.2f}$\n"
                 f"Posiciones abiertas: {len(mt5.positions_get() or [])}\n" + "\n".join(resumen[:10]))
        enviar(texto, "Contador")


def main():
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f"No conecta con MetaTrader 5: {mt5.last_error()}")
    if "--una-vez" in sys.argv:
        ciclo(mt5, False)
        print(f"Reporte generado: {RUTA_REPORTE}")
        return
    enviar("📊 Contador activo: reporte cada hora y resumen diario a las 22:05 UTC.", "Contador")
    ultimo_resumen = None
    while True:
        try:
            ahora = datetime.now(timezone.utc)
            toca = ahora.hour == 22 and ahora.minute >= 5 and ultimo_resumen != ahora.date()
            ciclo(mt5, toca)
            if toca:
                ultimo_resumen = ahora.date()
        except Exception as e:
            print(f"Contador: error (sigo): {e!r}"[:200])
        time.sleep(3600 if datetime.now(timezone.utc).hour != 21 else 300)


if __name__ == "__main__":
    main()
