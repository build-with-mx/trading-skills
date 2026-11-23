"""Bot base para MT5 (Windows). Cruce de medias en XAUUSD H1. SOLO DEMO por defecto.
Requisitos: pip install MetaTrader5 pandas ; terminal MT5 abierto, logueado y con Algo Trading activado."""
import csv
import math
import time
from datetime import datetime, date

import MetaTrader5 as mt5
import pandas as pd

# ---------------- Configuración ----------------
SIMBOLO = "XAUUSD"
TIMEFRAME = mt5.TIMEFRAME_H1
RIESGO_PCT = 1.0          # % del balance por operación
STOP_DIARIO_PCT = 3.0     # deja de operar si pierde esto en el día
MAX_OPS_DIA = 3
ATR_SL = 1.5              # SL = 1.5 x ATR(14)
RR = 2.0                  # TP = 2 x SL
HORAS_UTC = range(7, 20)  # solo opera entre 07:00 y 19:59 UTC
MAGIC = 260001
SOLO_DEMO = True
LOG = "bot_log.csv"


def log(evento, **datos):
    with open(LOG, "a", newline="") as f:
        csv.writer(f).writerow([datetime.now().isoformat(timespec="seconds"), evento, datos])
    print(evento, datos)


def velas(n=200):
    df = pd.DataFrame(mt5.copy_rates_from_pos(SIMBOLO, TIMEFRAME, 1, n))  # 1 = solo velas cerradas
    df["tr"] = pd.concat([df.high - df.low, (df.high - df.close.shift()).abs(),
                          (df.low - df.close.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = df.tr.rolling(14).mean()
    return df


def senal(df):
    """Devuelve 1 (compra), -1 (venta) o 0. Reemplaza esta función con tu estrategia."""
    rapida, lenta = df.close.rolling(20).mean(), df.close.rolling(50).mean()
    if rapida.iloc[-2] <= lenta.iloc[-2] and rapida.iloc[-1] > lenta.iloc[-1]:
        return 1
    if rapida.iloc[-2] >= lenta.iloc[-2] and rapida.iloc[-1] < lenta.iloc[-1]:
        return -1
    return 0


def calcular_lote(dist_sl):
    info, cuenta = mt5.symbol_info(SIMBOLO), mt5.account_info()
    valor_por_precio = info.trade_tick_value / info.trade_tick_size  # $ por 1.0 de precio por lote
    lote = cuenta.balance * RIESGO_PCT / 100 / (dist_sl * valor_por_precio)
    lote = math.floor(lote / info.volume_step) * info.volume_step
    return round(lote, 2) if lote >= info.volume_min else 0.0


def resultado_hoy():
    desde = datetime.combine(date.today(), datetime.min.time())
    deals = mt5.history_deals_get(desde, datetime.now()) or []
    mios = [d for d in deals if d.magic == MAGIC]
    return sum(d.profit + d.commission + d.swap for d in mios), len([d for d in mios if d.entry == 0])


def puede_operar():
    if datetime.utcnow().hour not in HORAS_UTC:
        return False
    if mt5.positions_get(symbol=SIMBOLO):
        return False
    pnl, ops = resultado_hoy()
    if pnl <= -mt5.account_info().balance * STOP_DIARIO_PCT / 100:
        log("stop_diario", pnl=pnl)
        return False
    return ops < MAX_OPS_DIA


def abrir(direccion, atr):
    tick = mt5.symbol_info_tick(SIMBOLO)
    precio = tick.ask if direccion == 1 else tick.bid
    dist = ATR_SL * atr
    lote = calcular_lote(dist)
    if lote == 0:
        log("lote_insuficiente", dist=dist)
        return
    digitos = mt5.symbol_info(SIMBOLO).digits
    req = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": SIMBOLO, "volume": lote,
        "type": mt5.ORDER_TYPE_BUY if direccion == 1 else mt5.ORDER_TYPE_SELL,
        "price": precio,
        "sl": round(precio - direccion * dist, digitos),
        "tp": round(precio + direccion * dist * RR, digitos),
        "deviation": 20, "magic": MAGIC, "comment": "bot_base",
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC,
    }
    r = mt5.order_send(req)
    if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
        log("error_orden", retcode=getattr(r, "retcode", None), error=mt5.last_error())
    else:
        log("orden_abierta", dir=direccion, lote=lote, precio=r.price, sl=req["sl"], tp=req["tp"])


def main():
    if not mt5.initialize():
        raise SystemExit(f"No conecta con MT5: {mt5.last_error()}")
    cuenta = mt5.account_info()
    if SOLO_DEMO and cuenta.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        mt5.shutdown()
        raise SystemExit("La cuenta NO es demo. Bot detenido por seguridad.")
    mt5.symbol_select(SIMBOLO, True)
    log("inicio", cuenta=cuenta.login, balance=cuenta.balance)
    ultima = None
    try:
        while True:
            df = velas()
            vela = df.time.iloc[-1]
            if vela != ultima:  # evalúa una vez por vela cerrada
                ultima = vela
                s = senal(df)
                if s and puede_operar():
                    abrir(s, df.atr.iloc[-1])
            time.sleep(30)
    except KeyboardInterrupt:
        log("detenido")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
