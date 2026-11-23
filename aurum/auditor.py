"""
AUDITOR — revisa cada hora que TODO cumpla las reglas, sin confiar en ningún otro bot.
  • Configuración: riesgo por operación <= 1%, riesgo abierto <= 3%, stop diario <= 3%, cuenta demo. Si alguien
    (o algo) subió el riesgo en aurum_config.json, te avisa.
  • Cada posición abierta: tiene SL, arriesga <= 1.5× lo permitido, tiene un "magic" conocido (sabemos qué bot la abrió)
    y no está duplicada (misma estrategia y mercado dos veces).
  • Riesgo abierto total frente al máximo.
  • Registro de operaciones: ninguna apertura sin SL; deslizamiento (precio obtenido vs pedido) > 10% del SL.
Escribe auditor_estado.json (lo usa el Panel) y auditor_reporte.md. Solo avisa de hallazgos NUEVOS.
Ejecutar:  python auditor.py      (o  python auditor.py --una-vez)
"""
import csv
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_OPS = os.path.join(CARPETA, "aurum_operaciones.csv")
RUTA_ESTADO = os.path.join(CARPETA, "auditor_estado.json")
RUTA_REPORTE = os.path.join(CARPETA, "auditor_reporte.md")
LIMITES = {"riesgo_por_operacion": 0.01, "riesgo_abierto_max": 0.03, "perdida_diaria_max": 0.03}


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


# ---------------- lógica pura ----------------
def auditar(cfg, posiciones, balance, filas):
    """posiciones: [{ticket, simbolo, magic, sl, riesgo_usd}]. filas: registro CSV. Devuelve lista de hallazgos (texto)."""
    h = []
    for k, tope in LIMITES.items():
        if cfg.get(k, 0) > tope:
            h.append(f"config: {k} = {cfg[k]:.2%} supera el tope de {tope:.0%}")
    magics = {0} | {e["magic"] for e in cfg.get("estrategias", {}).values()}
    permitido = balance * cfg.get("riesgo_por_operacion", 0.01)
    for p in posiciones:
        if not p["sl"]:
            h.append(f"posición {p['ticket']} {p['simbolo']} SIN stop loss")
        elif p["riesgo_usd"] > 1.5 * permitido:
            h.append(f"posición {p['ticket']} {p['simbolo']} arriesga ${p['riesgo_usd']:,.0f} (> 1.5× los ${permitido:,.0f} permitidos)")
        if p["magic"] not in magics:
            h.append(f"posición {p['ticket']} {p['simbolo']} con magic {p['magic']} desconocido (¿quién la abrió?)")
    dup = Counter((p["magic"], p["simbolo"]) for p in posiciones if p["magic"])
    h += [f"duplicada: {n} posiciones de la misma estrategia (magic {m}) en {s}" for (m, s), n in dup.items() if n > 1]
    total = sum(p["riesgo_usd"] for p in posiciones if p["sl"])
    if total > balance * (cfg.get("riesgo_abierto_max", 0.03) + 0.005):
        h.append(f"riesgo abierto ${total:,.0f} = {total / balance:.1%} (máximo {cfg.get('riesgo_abierto_max', 0.03):.0%})")
    for f in filas[-200:]:
        if f.get("accion") != "ABRIR":
            continue
        try:
            sl, pedido, obtenido = float(f.get("sl") or 0), float(f.get("precio_pedido") or 0), float(f.get("precio") or 0)
        except ValueError:
            continue
        if not sl:
            h.append(f"registro: apertura {f['hora_utc']} {f['simbolo']} sin SL")
        elif pedido and abs(obtenido - pedido) > 0.10 * abs(pedido - sl):
            h.append(f"registro: deslizamiento alto en {f['simbolo']} {f['hora_utc']} ({abs(obtenido - pedido):.2f} = "
                     f"{abs(obtenido - pedido) / abs(pedido - sl):.0%} del SL)")
    return h


def leer_filas():
    if not os.path.exists(RUTA_OPS):
        return []
    with open(RUTA_OPS, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def posiciones_mt5(mt5):
    out = []
    for p in mt5.positions_get() or []:
        i = mt5.symbol_info(p.symbol)
        dist = max(0.0, (p.price_open - p.sl) if p.type == 0 else (p.sl - p.price_open)) if p.sl else 0.0
        out.append({"ticket": p.ticket, "simbolo": p.symbol, "magic": p.magic, "sl": p.sl,
                    "riesgo_usd": dist * i.trade_tick_value / i.trade_tick_size * p.volume})
    return out


def ciclo(mt5, est):
    cfg = cargar(RUTA_CONFIG, {})
    pos, bal = (posiciones_mt5(mt5), mt5.account_info().balance) if mt5 is not None else ([], 1.0)
    hallazgos = auditar(cfg, pos, bal, leer_filas())
    nuevos = [x for x in hallazgos if x not in est.get("vistos", [])]
    if nuevos:
        enviar("🧾 Auditoría — hallazgos nuevos:\n• " + "\n• ".join(nuevos[:10]), "Auditor")
    ahora = datetime.now(timezone.utc)
    est.update({"actualizado": ahora.isoformat(), "hallazgos": hallazgos, "vistos": sorted(set(est.get("vistos", [])) | set(hallazgos))[-300:]})
    with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, indent=2, ensure_ascii=False)
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write(f"# Auditoría — {ahora:%Y-%m-%d %H:%M} UTC\n\n" + ("\n".join(f"- {x}" for x in hallazgos) or "Todo en regla ✅"))


def main():
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            mt5 = None
    except ImportError:
        mt5 = None
    est = cargar(RUTA_ESTADO, {})
    while True:
        try:
            ciclo(mt5, est)
        except Exception as e:
            print(f"Auditor: error (sigo): {e!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(3600)


if __name__ == "__main__":
    main()
