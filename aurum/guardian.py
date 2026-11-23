"""
GUARDIÁN — freno de emergencia independiente de Aurum. Corre en su propia ventana.
Cada 10 segundos revisa la cuenta y actúa aunque Aurum falle:
  1. Posición sin Stop Loss  -> le pone un SL de emergencia (riesgo = riesgo_por_operacion) y avisa.
  2. Pérdida del día >= perdida_diaria_max  -> cierra TODO, bloquea nuevas entradas hasta mañana (UTC) y avisa.
  3. Caída desde el máximo de equity >= caida_maxima  -> cierra TODO, bloqueo TOTAL (lo quitas tú) y avisa.
  4. Riesgo abierto > riesgo_abierto_max + 0.5%  -> avisa.
  5. Lote anormal (riesgo de una posición > 2x lo permitido) -> avisa.
El bloqueo se comunica a Aurum con el archivo aurum_ALTO.flag (Aurum no abre nada mientras exista).
Ejecutar:  python guardian.py
"""
import json
import os
import time
from datetime import datetime, timezone

import MetaTrader5 as mt5

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_ESTADO = os.path.join(CARPETA, "guardian_estado.json")
RUTA_ALTO = os.path.join(CARPETA, "aurum_ALTO.flag")
RUTA_LATIDO = os.path.join(CARPETA, "guardian_latido.txt")


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def guardar(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2)


def log(msg):
    print(f"{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S} UTC | GUARDIÁN | {msg}")


def valor_por_precio(simbolo):
    i = mt5.symbol_info(simbolo)
    return i.trade_tick_value / i.trade_tick_size


def riesgo_posicion(p):
    if not p.sl:
        return None
    d = (p.price_open - p.sl) if p.type == mt5.POSITION_TYPE_BUY else (p.sl - p.price_open)
    return max(d, 0) * valor_por_precio(p.symbol) * p.volume


def cerrar_todo(motivo):
    for p in mt5.positions_get() or []:
        tick = mt5.symbol_info_tick(p.symbol)
        compra = p.type == mt5.POSITION_TYPE_BUY
        fm = mt5.symbol_info(p.symbol).filling_mode
        r = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
                            "type": mt5.ORDER_TYPE_SELL if compra else mt5.ORDER_TYPE_BUY,
                            "price": tick.bid if compra else tick.ask, "deviation": 50, "magic": p.magic,
                            "comment": "guardian_cierre",
                            "type_filling": mt5.ORDER_FILLING_FOK if fm & 1 else mt5.ORDER_FILLING_IOC if fm & 2 else mt5.ORDER_FILLING_RETURN})
        log(f"Cierre {p.symbol} #{p.ticket}: {'OK' if r and r.retcode == mt5.TRADE_RETCODE_DONE else 'ERROR ' + str(getattr(r, 'retcode', None))}")
    enviar(f"🛑 Cerré TODAS las posiciones. Motivo: {motivo}", "Guardián")


def poner_sl_emergencia(p, cfg):
    bal = mt5.account_info().balance
    riesgo = bal * cfg["riesgo_por_operacion"]
    dist = riesgo / (valor_por_precio(p.symbol) * p.volume)
    info = mt5.symbol_info(p.symbol)
    compra = p.type == mt5.POSITION_TYPE_BUY
    sl = round(p.price_open - dist if compra else p.price_open + dist, info.digits)
    tick = mt5.symbol_info_tick(p.symbol)
    actual = tick.bid if compra else tick.ask
    if (compra and sl >= actual) or (not compra and sl <= actual):  # ya pasó el nivel: cerrar
        cerrar_posicion = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
                                          "type": mt5.ORDER_TYPE_SELL if compra else mt5.ORDER_TYPE_BUY, "price": actual,
                                          "deviation": 50, "magic": p.magic, "comment": "guardian_sin_sl"})
        enviar(f"⚠️ {p.symbol} #{p.ticket} no tenía SL y ya perdía más del {cfg['riesgo_por_operacion']:.0%}: la cerré.", "Guardián")
        return
    r = mt5.order_send({"action": mt5.TRADE_ACTION_SLTP, "symbol": p.symbol, "position": p.ticket, "sl": sl, "tp": p.tp})
    ok = r and r.retcode == mt5.TRADE_RETCODE_DONE
    enviar(f"⚠️ {p.symbol} #{p.ticket} no tenía Stop Loss. {'Le puse' if ok else 'NO pude poner'} SL de emergencia en {sl} (riesgo ≈ ${riesgo:,.0f}).", "Guardián")


def paso(info, cfg, g, est):
    """Una revisión completa del Guardián (se puede probar sin el bucle)."""
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if est["dia"] != hoy:  # nuevo día UTC
        est["dia"], est["balance_inicio_dia"] = hoy, info.balance
        if os.path.exists(RUTA_ALTO) and open(RUTA_ALTO).read().startswith("DIARIO"):
            os.remove(RUTA_ALTO)
            enviar("🟢 Nuevo día: quito el bloqueo diario. Aurum puede volver a operar.", "Guardián")
    est["pico_equity"] = max(est["pico_equity"], info.equity)

    # 1) posiciones sin SL
    for p in mt5.positions_get() or []:
        if not p.sl:
            poner_sl_emergencia(p, cfg)

    # 2) pérdida del día
    perdida_dia = (info.equity - est["balance_inicio_dia"]) / est["balance_inicio_dia"]
    if perdida_dia <= -cfg["perdida_diaria_max"] and not os.path.exists(RUTA_ALTO):
        with open(RUTA_ALTO, "w") as f:
            f.write(f"DIARIO {hoy} pérdida {perdida_dia:.2%}")
        cerrar_todo(f"pérdida del día {perdida_dia:.2%} (límite {cfg['perdida_diaria_max']:.0%})")

    # 3) caída desde el máximo
    caida = 1 - info.equity / est["pico_equity"]
    if caida >= g["caida_maxima"] and not (os.path.exists(RUTA_ALTO) and open(RUTA_ALTO).read().startswith("TOTAL")):
        with open(RUTA_ALTO, "w") as f:
            f.write(f"TOTAL caída {caida:.2%} desde ${est['pico_equity']:,.0f}. Borra este archivo para reanudar.")
        cerrar_todo(f"caída de {caida:.1%} desde el máximo (límite {g['caida_maxima']:.0%}). Bloqueo TOTAL: revisar con Claude.")

    # 4) y 5) riesgo abierto y lotes anormales
    riesgos = [(p, riesgo_posicion(p)) for p in mt5.positions_get() or []]
    total = sum(r or 0 for _, r in riesgos)
    if total > info.balance * (cfg["riesgo_abierto_max"] + 0.005):
        clave = f"riesgo_{hoy}_{int(total)}"
        if clave not in est["avisos"]:
            est["avisos"][clave] = 1
            enviar(f"⚠️ Riesgo abierto {total / info.balance:.1%} supera el máximo {cfg['riesgo_abierto_max']:.0%}.", "Guardián")
    for p, r in riesgos:
        if r and r > info.balance * cfg["riesgo_por_operacion"] * 2 and f"lote_{p.ticket}" not in est["avisos"]:
            est["avisos"][f"lote_{p.ticket}"] = 1
            enviar(f"⚠️ {p.symbol} #{p.ticket} arriesga ${r:,.0f} ({r / info.balance:.1%}), más del doble de lo permitido.", "Guardián")

    guardar(RUTA_ESTADO, est)
    with open(RUTA_LATIDO, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat())


def main():
    cfg = cargar(RUTA_CONFIG, None)
    g = cfg.get("guardian", {"caida_maxima": 0.10, "intervalo_seg": 10})
    if not mt5.initialize():
        raise SystemExit(f"No conecta con MetaTrader 5: {mt5.last_error()}")
    c = mt5.account_info()
    if c.login != cfg["cuenta_permitida"]:
        raise SystemExit(f"Cuenta {c.login} no es la vigilada ({cfg['cuenta_permitida']}).")
    est = cargar(RUTA_ESTADO, {"pico_equity": c.equity, "dia": "", "balance_inicio_dia": c.balance, "avisos": {}})
    enviar(f"🛡️ Guardián activo en la cuenta {c.login}. Equity ${c.equity:,.2f}.", "Guardián")
    desconectado_desde = None
    while True:
        try:
            cfg = cargar(RUTA_CONFIG, cfg)
            info = mt5.account_info()
            if info is None:
                desconectado_desde = desconectado_desde or time.time()
                if time.time() - desconectado_desde > 120:
                    enviar("🔌 Perdí conexión con MetaTrader 5 hace más de 2 minutos. Revisa la PC/VPS.", "Guardián")
                    desconectado_desde = time.time()
                mt5.initialize()
                time.sleep(10)
                continue
            desconectado_desde = None
            paso(info, cfg, g, est)
        except Exception as e:
            log(f"Error (sigo vigilando): {e!r}"[:200])
        time.sleep(g.get("intervalo_seg", 10))


if __name__ == "__main__":
    main()
