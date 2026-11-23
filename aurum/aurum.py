"""
AURUM — robot de trading autónomo para MetaTrader 5 (Windows).
Opera las estrategias validadas del plan (ruptura asiática del oro, Donchian, RSI(2), IBS) en la demo 10076749,
con gestión de riesgo, filtro de noticias, autocontrol por estrategia y configuración actualizable.

Instalación (una vez):  pip install MetaTrader5
Ejecutar:               python aurum.py
Detener:                Ctrl + C   (las posiciones conservan su Stop Loss / Take Profit)
Archivos que genera:    aurum_operaciones.csv, aurum_eventos.log, aurum_estado.json
"""
import csv
import json
import math
import os
import time
import urllib.request
from datetime import datetime, timedelta, timezone

try:
    import MetaTrader5 as mt5
except ImportError:  # permite probar la lógica de señales sin MetaTrader
    mt5 = None
try:
    from mensajero import enviar
except Exception:  # sin mensajero: solo pantalla
    def enviar(texto, origen="Aurum"):
        print(f"[{origen}] {texto}")

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_ESTADO = os.path.join(CARPETA, "aurum_estado.json")
RUTA_OPS = os.path.join(CARPETA, "aurum_operaciones.csv")
RUTA_LOG = os.path.join(CARPETA, "aurum_eventos.log")
VERSION = "1.1.0"
RUTA_ALTO = os.path.join(CARPETA, "aurum_ALTO.flag")


# ============================ utilidades ============================
def ahora_utc():
    return datetime.now(timezone.utc)


def log(msg, **datos):
    linea = f"{ahora_utc():%Y-%m-%d %H:%M:%S} UTC | {msg}" + (f" | {datos}" if datos else "")
    print(linea)
    with open(RUTA_LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def registrar_operacion(**d):
    nuevo = not os.path.exists(RUTA_OPS)
    campos = ["hora_utc", "accion", "estrategia", "simbolo", "direccion", "lote", "precio_pedido", "precio", "sl", "tp", "riesgo_usd", "resultado_usd", "motivo"]
    with open(RUTA_OPS, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        if nuevo:
            w.writeheader()
        w.writerow({k: d.get(k, "") for k in campos} | {"hora_utc": f"{ahora_utc():%Y-%m-%d %H:%M:%S}"})


def cargar_json(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def guardar_json(ruta, datos):
    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    os.replace(tmp, ruta)


# ============================ indicadores (puros) ============================
def sma(valores, n):
    return sum(valores[-n:]) / n if len(valores) >= n else None


def atr(barras, n):
    """ATR simple de los últimos n True Range."""
    if len(barras) < n + 1:
        return None
    tr = []
    for i in range(len(barras) - n, len(barras)):
        h, l, pc = barras[i]["high"], barras[i]["low"], barras[i - 1]["close"]
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(tr) / n


def rsi_wilder(cierres, n):
    if len(cierres) < n + 2:
        return None, None
    g = p = 0.0
    prev = None
    for i in range(1, len(cierres)):
        d = cierres[i] - cierres[i - 1]
        up, dn = max(d, 0.0), max(-d, 0.0)
        if i <= n:
            g += up / n
            p += dn / n
        else:
            g = (g * (n - 1) + up) / n
            p = (p * (n - 1) + dn) / n
        if i >= n:
            val = 100.0 if p == 0 else 100 - 100 / (1 + g / p)
            if i == len(cierres) - 2:
                prev = val
            last = val
    return last, prev


def ibs(barra):
    rango = barra["high"] - barra["low"]
    return (barra["close"] - barra["low"]) / rango if rango > 0 else 0.5


# ============================ señales (puras) ============================
def senal_ruptura_asiatica(barras_h1_utc, p):
    """barras con 'utc' (datetime). Devuelve (dir, sl_dist, tp_dist, info) si la ÚLTIMA vela cerrada es el gatillo."""
    if len(barras_h1_utc) < 30:
        return None
    ultima = barras_h1_utc[-1]
    dia = ultima["utc"].date()
    hoy = [b for b in barras_h1_utc if b["utc"].date() == dia]
    rango = [b for b in hoy if p["rango_inicio_utc"] <= b["utc"].hour < p["rango_fin_utc"]]
    if len(rango) < (p["rango_fin_utc"] - p["rango_inicio_utc"]) - 1:
        return None
    hi, lo = max(b["high"] for b in rango), min(b["low"] for b in rango)
    for b in hoy:
        if not (p["rango_fin_utc"] <= b["utc"].hour < p["ventana_fin_utc"]):
            continue
        d = 1 if b["close"] > hi else -1 if b["close"] < lo else 0
        if d:
            if b is not ultima:
                return None  # la ruptura del día ya ocurrió antes
            a = atr(barras_h1_utc, p["atr_periodo"])
            if not a:
                return None
            sl = p["sl_atr"] * a
            return d, sl, sl * p["tp_r"], {"rango": [hi, lo], "cierre": b["close"], "atr": round(a, 3)}
    return None


def senal_donchian_entrada(d1, p):
    n = p["entrada"]
    if len(d1) < n + 2:
        return None
    previo = d1[-n - 1:-1]
    c = d1[-1]["close"]
    a = atr(d1, p["atr_periodo"])
    if c > max(b["high"] for b in previo):
        return 1, p["sl_atr"] * a
    if c < min(b["low"] for b in previo):
        return -1, p["sl_atr"] * a
    return None


def donchian_salida(d1, p, direccion):
    n = p["salida"]
    previo = d1[-n - 1:-1]
    c = d1[-1]["close"]
    return (direccion == 1 and c < min(b["low"] for b in previo)) or (direccion == -1 and c > max(b["high"] for b in previo))


def senal_rsi2_entrada(d1, p):
    cierres = [b["close"] for b in d1]
    s200 = sma(cierres, p["sma_tendencia"])
    r, _ = rsi_wilder(cierres, p["rsi_periodo"])
    if s200 is None or r is None:
        return None
    a = atr(d1, p["atr_periodo"])
    if cierres[-1] > s200 and r < p["umbral"]:
        return 1, p["sl_atr"] * a
    if cierres[-1] < s200 and r > 100 - p["umbral"]:
        return -1, p["sl_atr"] * a
    return None


def rsi2_salida(d1, p, direccion, sesiones):
    cierres = [b["close"] for b in d1]
    s5 = sma(cierres, p["sma_salida"])
    return sesiones >= p["max_sesiones"] or (direccion == 1 and cierres[-1] > s5) or (direccion == -1 and cierres[-1] < s5)


def senal_ibs_entrada(d1, p):
    cierres = [b["close"] for b in d1]
    s200 = sma(cierres, p["sma_tendencia"])
    if s200 is None:
        return None
    v = ibs(d1[-1])
    a = atr(d1, p["atr_periodo"])
    if v < p["entrada"] and cierres[-1] > s200:
        return 1, p["sl_atr"] * a
    if v > 1 - p["entrada"] and cierres[-1] < s200:
        return -1, p["sl_atr"] * a
    return None


def ibs_salida(d1, p, direccion, sesiones):
    v = ibs(d1[-1])
    return sesiones >= p["max_sesiones"] or (direccion == 1 and v > p["salida"]) or (direccion == -1 and v < 1 - p["salida"])


# ============================ MetaTrader ============================
class Aurum:
    def __init__(self):
        self.cfg = cargar_json(RUTA_CONFIG, None)
        if not self.cfg:
            raise SystemExit("No encuentro aurum_config.json junto a aurum.py")
        self.estado = cargar_json(RUTA_ESTADO, {"adoptadas": {}, "riesgos": {}, "pausadas": [], "ultima_barra": {}})
        self.offset_h = 0
        self.noticias = []
        self.noticias_hora = None
        self.config_hora = None

    # ---------- conexión y seguridad ----------
    def conectar(self):
        if not mt5.initialize():
            raise SystemExit(f"No conecta con MetaTrader 5: {mt5.last_error()}")
        c = mt5.account_info()
        if c.login != self.cfg["cuenta_permitida"] or c.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            mt5.shutdown()
            raise SystemExit(f"Cuenta {c.login} NO permitida. Aurum solo opera la DEMO {self.cfg['cuenta_permitida']}.")
        for e in self.cfg["estrategias"].values():
            for s in e["simbolos"]:
                mt5.symbol_select(s, True)
        self.calcular_offset()
        log(f"Aurum {VERSION} iniciado", cuenta=c.login, balance=c.balance, offset_servidor_h=self.offset_h)
        enviar(f"🚀 Aurum {VERSION} iniciado en la cuenta {c.login}. Balance ${c.balance:,.2f}.")

    def calcular_offset(self):
        """Las velas de MT5 vienen en hora del servidor; calculo su diferencia con UTC."""
        tick = mt5.symbol_info_tick("XAUUSD")
        if tick and abs(time.time() - tick.time) < 3 * 3600 + 120:
            self.offset_h = round((tick.time - time.time()) / 3600)

    def mercado_abierto(self, simbolo):
        """True si hubo cotización en los últimos 3 minutos (la hora del tick viene en hora del servidor)."""
        tick = mt5.symbol_info_tick(simbolo)
        return bool(tick) and (time.time() + self.offset_h * 3600 - tick.time) < 180

    def barras(self, simbolo, tf, n):
        r = mt5.copy_rates_from_pos(simbolo, tf, 1, n)  # 1 = solo velas cerradas
        if r is None or len(r) == 0:
            return []
        return [{"time": int(x["time"]), "open": float(x["open"]), "high": float(x["high"]), "low": float(x["low"]),
                 "close": float(x["close"]), "utc": datetime.fromtimestamp(int(x["time"]), timezone.utc) - timedelta(hours=self.offset_h)}
                for x in r]

    # ---------- configuración actualizable ----------
    def actualizar_config(self):
        if self.config_hora and ahora_utc() - self.config_hora < timedelta(hours=1):
            return
        self.config_hora = ahora_utc()
        rem = self.cfg.get("config_remota", {})
        url = rem.get("url")
        if url:
            try:
                req = urllib.request.Request(url)
                token = os.environ.get(rem.get("token_variable_entorno", ""), "")
                if token:
                    req.add_header("Authorization", f"Bearer {token}")
                nueva = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
                if nueva.get("cuenta_permitida") == self.cfg["cuenta_permitida"] and "estrategias" in nueva and nueva.get("version") != self.cfg.get("version"):
                    guardar_json(RUTA_CONFIG, nueva)
                    log("Configuración actualizada desde remoto", de=self.cfg.get("version"), a=nueva.get("version"))
                    self.cfg = nueva
                    return
            except Exception as e:
                log("No pude descargar la configuración remota (sigo con la local)", error=str(e)[:120])
        self.cfg = cargar_json(RUTA_CONFIG, self.cfg)

    # ---------- noticias ----------
    def actualizar_noticias(self):
        fn = self.cfg.get("filtro_noticias", {})
        if not fn.get("activo"):
            self.noticias = []
            return
        if self.noticias_hora and ahora_utc() - self.noticias_hora < timedelta(hours=1):
            return
        self.noticias_hora = ahora_utc()
        try:
            datos = json.loads(urllib.request.urlopen(fn["url"], timeout=20).read().decode())
            ev = []
            for x in datos:
                if x.get("country") in fn["monedas"] and x.get("impact") in fn["impacto"]:
                    ev.append((datetime.fromisoformat(x["date"]).astimezone(timezone.utc), x.get("title", "")))
            self.noticias = ev
            log("Calendario de noticias cargado", eventos_alto_impacto=len(ev))
        except Exception as e:
            log("No pude cargar el calendario de noticias", error=str(e)[:120])

    def bloqueo_noticias(self):
        fn = self.cfg.get("filtro_noticias", {})
        t = ahora_utc()
        for cuando, titulo in self.noticias:
            if cuando - timedelta(minutes=fn.get("minutos_antes", 30)) <= t <= cuando + timedelta(minutes=fn.get("minutos_despues", 30)):
                return titulo
        return None

    # ---------- riesgo ----------
    def valor_por_precio(self, simbolo):
        i = mt5.symbol_info(simbolo)
        return i.trade_tick_value / i.trade_tick_size

    def lote_para_riesgo(self, simbolo, dist, riesgo_usd):
        i = mt5.symbol_info(simbolo)
        v = self.valor_por_precio(simbolo)
        bruto = riesgo_usd / (dist * v)
        lote = math.floor(bruto / i.volume_step + 1e-9) * i.volume_step
        if lote < i.volume_min:
            if i.volume_min * dist * v <= riesgo_usd:
                lote = i.volume_min
            else:
                return 0.0
        return round(min(lote, i.volume_max), 2)

    def riesgo_abierto(self):
        total = 0.0
        for p in mt5.positions_get() or []:
            if p.sl:
                d = (p.price_open - p.sl) if p.type == mt5.POSITION_TYPE_BUY else (p.sl - p.price_open)
                total += max(d, 0) * self.valor_por_precio(p.symbol) * p.volume
        return total

    def resultado_hoy(self):
        desde = datetime.combine(ahora_utc().date(), datetime.min.time())
        deals = mt5.history_deals_get(desde, datetime.now() + timedelta(days=1)) or []
        return sum(d.profit + d.swap + d.commission for d in deals if d.entry == mt5.DEAL_ENTRY_OUT)

    # ---------- posiciones por estrategia ----------
    def estrategia_de(self, p):
        for nombre, e in self.cfg["estrategias"].items():
            if p.magic == e["magic"]:
                return nombre
        return self.estado["adoptadas"].get(str(p.ticket))

    def adoptar_posiciones(self):
        """Adopta posiciones abiertas antes por Claude (magic 0): oro con TP = ruptura; Donchian sin TP; índices = rsi2."""
        don = self.cfg["estrategias"]["donchian"]["simbolos"]
        for p in mt5.positions_get() or []:
            if p.magic != 0 or str(p.ticket) in self.estado["adoptadas"]:
                continue
            if p.symbol == "XAUUSD" and p.tp:
                e = "ruptura_asiatica"
            elif p.symbol in don and not p.tp:
                e = "donchian"
            elif p.symbol in self.cfg["estrategias"]["rsi2"]["simbolos"]:
                e = "rsi2"
            else:
                continue
            self.estado["adoptadas"][str(p.ticket)] = e
            log("Posición adoptada", ticket=p.ticket, simbolo=p.symbol, estrategia=e)
        guardar_json(RUTA_ESTADO, self.estado)

    def posiciones(self, estrategia, simbolo=None):
        return [p for p in (mt5.positions_get() or []) if self.estrategia_de(p) == estrategia and (simbolo is None or p.symbol == simbolo)]

    def sesiones_desde(self, d1, p):
        return sum(1 for b in d1 if b["time"] >= p.time)

    # ---------- órdenes ----------
    def filling(self, simbolo):
        fm = mt5.symbol_info(simbolo).filling_mode
        return mt5.ORDER_FILLING_FOK if fm & 1 else mt5.ORDER_FILLING_IOC if fm & 2 else mt5.ORDER_FILLING_RETURN

    def abrir(self, estrategia, simbolo, direccion, dist_sl, dist_tp, motivo):
        e = self.cfg["estrategias"][estrategia]
        bal = mt5.account_info().balance
        riesgo = bal * self.cfg["riesgo_por_operacion"]
        if self.riesgo_abierto() + riesgo > bal * self.cfg["riesgo_abierto_max"]:
            log("Sin espacio de riesgo: no abro", estrategia=estrategia, simbolo=simbolo)
            return
        lote = self.lote_para_riesgo(simbolo, dist_sl, riesgo)
        if lote <= 0:
            log("El lote mínimo arriesga demasiado: no abro", estrategia=estrategia, simbolo=simbolo)
            return
        tick = mt5.symbol_info_tick(simbolo)
        info = mt5.symbol_info(simbolo)
        precio = tick.ask if direccion == 1 else tick.bid
        sl = round(precio - direccion * dist_sl, info.digits)
        tp = round(precio + direccion * dist_tp, info.digits) if dist_tp else 0.0
        if self.cfg.get("solo_observar"):
            log("SEÑAL (modo observar, sin operar)", estrategia=estrategia, simbolo=simbolo, dir=direccion, lote=lote, sl=sl, tp=tp)
            return
        req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": simbolo, "volume": lote,
               "type": mt5.ORDER_TYPE_BUY if direccion == 1 else mt5.ORDER_TYPE_SELL, "price": precio,
               "sl": sl, "tp": tp, "deviation": 30, "magic": e["magic"], "comment": f"aurum_{estrategia}"[:31],
               "type_time": mt5.ORDER_TIME_GTC, "type_filling": self.filling(simbolo)}
        r = mt5.order_send(req)
        if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
            log("Error al abrir", estrategia=estrategia, simbolo=simbolo, retcode=getattr(r, "retcode", None), error=mt5.last_error())
            enviar(f"❗ No pude abrir {estrategia} en {simbolo} (código {getattr(r, 'retcode', None)})")
            return
        riesgo_real = abs(r.price - sl) * self.valor_por_precio(simbolo) * lote
        self.estado["riesgos"][str(r.order)] = riesgo_real
        guardar_json(RUTA_ESTADO, self.estado)
        registrar_operacion(accion="ABRIR", estrategia=estrategia, simbolo=simbolo, direccion="COMPRA" if direccion == 1 else "VENTA",
                            lote=lote, precio_pedido=precio, precio=r.price, sl=sl, tp=tp, riesgo_usd=round(riesgo_real, 2), motivo=motivo)
        log("ABIERTA", estrategia=estrategia, simbolo=simbolo, dir=direccion, lote=lote, precio=r.price, sl=sl, tp=tp)
        enviar(f"🟢 ABIERTA {estrategia}: {'COMPRA' if direccion == 1 else 'VENTA'} {simbolo} {lote} lotes @ {r.price}\nSL {sl} · TP {tp or '—'} · riesgo ${riesgo_real:,.0f}")

    def cerrar(self, p, estrategia, motivo):
        if self.cfg.get("solo_observar"):
            log("CIERRE (modo observar, sin operar)", ticket=p.ticket, motivo=motivo)
            return
        tick = mt5.symbol_info_tick(p.symbol)
        es_compra = p.type == mt5.POSITION_TYPE_BUY
        req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
               "type": mt5.ORDER_TYPE_SELL if es_compra else mt5.ORDER_TYPE_BUY, "price": tick.bid if es_compra else tick.ask,
               "deviation": 30, "magic": p.magic, "comment": "aurum_cierre", "type_time": mt5.ORDER_TIME_GTC,
               "type_filling": self.filling(p.symbol)}
        r = mt5.order_send(req)
        if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
            log("Error al cerrar", ticket=p.ticket, retcode=getattr(r, "retcode", None), error=mt5.last_error())
            return
        registrar_operacion(accion="CERRAR", estrategia=estrategia, simbolo=p.symbol, direccion="COMPRA" if es_compra else "VENTA",
                            lote=p.volume, precio=r.price, resultado_usd=round(p.profit + p.swap, 2), motivo=motivo)
        log("CERRADA", ticket=p.ticket, estrategia=estrategia, resultado=round(p.profit + p.swap, 2), motivo=motivo)
        enviar(f"{'✅' if p.profit + p.swap > 0 else '🔻'} CERRADA {estrategia}: {p.symbol} {p.volume} lotes · resultado {p.profit + p.swap:+,.2f}$ · {motivo}")

    # ---------- autocontrol ----------
    def revisar_autocontrol(self):
        ac = self.cfg.get("autocontrol", {})
        n, limite = ac.get("ultimas_operaciones", 20), ac.get("pausar_si_suma_R_menor_que", -8.0)
        deals = mt5.history_deals_get(ahora_utc() - timedelta(days=365), datetime.now() + timedelta(days=1)) or []
        bal = mt5.account_info().balance
        for nombre, e in self.cfg["estrategias"].items():
            cierres = [d for d in deals if d.magic == e["magic"] and d.entry == mt5.DEAL_ENTRY_OUT][-n:]
            if len(cierres) < n:
                continue
            suma_r = sum((d.profit + d.swap + d.commission) / (bal * self.cfg["riesgo_por_operacion"]) for d in cierres)
            if suma_r < limite and nombre not in self.estado["pausadas"]:
                self.estado["pausadas"].append(nombre)
                guardar_json(RUTA_ESTADO, self.estado)
                log("AUTOCONTROL: estrategia pausada por mal rendimiento en vivo", estrategia=nombre, suma_R=round(suma_r, 1))
                enviar(f"⏸️ Pausé la estrategia {nombre}: sus últimas {n} operaciones suman {suma_r:+.1f}R. Revísala con Claude.")

    def activa(self, nombre):
        return self.cfg["estrategias"][nombre].get("activa") and nombre not in self.estado["pausadas"]

    # ---------- ciclo principal ----------
    def nueva_barra(self, clave, barras):
        if not barras:
            return False
        t = barras[-1]["time"]
        if self.estado["ultima_barra"].get(clave) == t:
            return False
        self.estado["ultima_barra"][clave] = t
        return True

    def ciclo(self):
        self.actualizar_config()
        self.actualizar_noticias()
        self.calcular_offset()
        cfg = self.cfg
        bal = mt5.account_info().balance
        if self.resultado_hoy() <= -bal * cfg["perdida_diaria_max"]:
            return  # stop diario: no se abre nada más hoy
        bloqueado = os.path.exists(RUTA_ALTO)  # el Guardián frenó: solo se gestionan salidas
        candidatos = []
        noticia = self.bloqueo_noticias()

        # --- estrategias diarias: salidas y señales en cada vela D1 nueva ---
        for nombre in ("donchian", "rsi2", "ibs"):
            e = cfg["estrategias"][nombre]
            for s in e["simbolos"]:
                if not self.mercado_abierto(s):
                    continue  # se evaluará cuando abra la sesión
                d1 = self.barras(s, mt5.TIMEFRAME_D1, 260)
                if not self.nueva_barra(f"{nombre}:{s}:D1", d1):
                    continue
                abiertas = self.posiciones(nombre, s)
                for p in abiertas:
                    direc = 1 if p.type == mt5.POSITION_TYPE_BUY else -1
                    ses = self.sesiones_desde(d1, p)
                    salir = (donchian_salida(d1, e, direc) if nombre == "donchian" else
                             rsi2_salida(d1, e, direc, ses) if nombre == "rsi2" else ibs_salida(d1, e, direc, ses))
                    if salir:
                        self.cerrar(p, nombre, "regla de salida")
                if abiertas or not self.activa(nombre):
                    continue
                if nombre == "ibs" and self.posiciones("rsi2", s):
                    continue
                sen = (senal_donchian_entrada(d1, e) if nombre == "donchian" else
                       senal_rsi2_entrada(d1, e) if nombre == "rsi2" else senal_ibs_entrada(d1, e))
                if sen:
                    candidatos.append((f"{nombre}:{s}", nombre, s, sen[0], sen[1], 0.0, "señal D1"))

        # --- ruptura asiática del oro en cada vela H1 nueva ---
        e = cfg["estrategias"]["ruptura_asiatica"]
        for s in e["simbolos"]:
            if not self.mercado_abierto(s):
                continue
            h1 = self.barras(s, mt5.TIMEFRAME_H1, 72)
            if not self.nueva_barra(f"ruptura:{s}:H1", h1) or not self.activa("ruptura_asiatica"):
                continue
            sen = senal_ruptura_asiatica(h1, e)
            ya_hoy = any(self.estrategia_de(p) == "ruptura_asiatica" for p in (mt5.positions_get(symbol=s) or []))
            tick = mt5.symbol_info_tick(s)
            if sen and not ya_hoy and (tick.ask - tick.bid) <= e["spread_max"]:
                if noticia:
                    log("Señal de ruptura bloqueada por noticia", noticia=noticia)
                else:
                    candidatos.append((f"ruptura_asiatica:{s}", "ruptura_asiatica", s, sen[0], sen[1], sen[2], f"ruptura {sen[3]}"))

        if bloqueado:
            if candidatos:
                log("Guardián activo (aurum_ALTO.flag): no abro nuevas", señales=len(candidatos))
            guardar_json(RUTA_ESTADO, self.estado)
            return
        # --- abrir por prioridad ---
        orden = cfg.get("prioridad", [])
        candidatos.sort(key=lambda c: orden.index(c[0]) if c[0] in orden else -1)
        for _, nombre, s, d, sl, tp, motivo in candidatos:
            if noticia and nombre != "ruptura_asiatica":
                log("Entrada pospuesta por noticia", estrategia=nombre, simbolo=s, noticia=noticia)
                self.estado["ultima_barra"].pop(f"{nombre}:{s}:D1", None)  # reintentar en el siguiente ciclo
                continue
            self.abrir(nombre, s, d, sl, tp, motivo)
        guardar_json(RUTA_ESTADO, self.estado)

    def correr(self):
        self.conectar()
        self.adoptar_posiciones()
        ultimo_autocontrol = None
        try:
            while True:
                try:
                    self.ciclo()
                    if not ultimo_autocontrol or ahora_utc() - ultimo_autocontrol > timedelta(hours=6):
                        self.revisar_autocontrol()
                        ultimo_autocontrol = ahora_utc()
                except Exception as e:
                    log("Error en el ciclo (sigo funcionando)", error=repr(e)[:200])
                    if not mt5.terminal_info():
                        mt5.initialize()
                time.sleep(15)
        except KeyboardInterrupt:
            log("Aurum detenido por el usuario")
        finally:
            mt5.shutdown()


if __name__ == "__main__":
    if mt5 is None:
        raise SystemExit("Falta la librería MetaTrader5. Instálala con:  pip install MetaTrader5")
    Aurum().correr()
