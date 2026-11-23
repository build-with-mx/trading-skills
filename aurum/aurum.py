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
from ejecutor import Ejecutor

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
VERSION = "2.3.0"
RUTA_ALTO = os.path.join(CARPETA, "aurum_ALTO.flag")
RUTA_PAUSA = os.path.join(CARPETA, "aurum_PAUSA.flag")  # pausa manual (Centralita /pausa)
RUTA_VIGIA = os.path.join(CARPETA, "vigia_estado.json")
RUTA_METAS = os.path.join(CARPETA, "metas_estado.json")
RUTA_SENALES = os.path.join(CARPETA, "senales_maestro.jsonl")  # para el Copiador
RUTA_VIVAS = os.path.join(CARPETA, "maestro_vivas.json")


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


def publicar_senal(**ev):
    """Añade un evento (ABRIR/CERRAR) a senales_maestro.jsonl para que los Copiadores lo repliquen."""
    try:
        ev["t"] = ahora_utc().isoformat()
        with open(RUTA_SENALES, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass


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


def senal_lab(familia, params, t, o, h, l, c):
    """Señales de cualquier familia del laboratorio con la MISMA lógica que se validó (lab_motor).
    Captura lo que la familia le pasaría al simulador: entradas/salidas por vela, multiplicador de SL, TP y tiempo máximo."""
    import lab_motor as L
    cap = {}

    def captura(m, el, es, xl, xs, slm, rr=None, maxh=None):
        cap.update(el=el, es=es, xl=xl, xs=xs, slm=slm, rr=rr, maxh=maxh, a=m.a)
        return []
    original = L.sim
    L.sim = captura
    try:
        L.evaluar(L.M(t, o, h, l, c, 0.0), "d1", familia, tuple(params))
    finally:
        L.sim = original
    if familia == "tom" and cap:
        # el laboratorio mira la fecha de la vela que está nlast sesiones adelante; en vivo se sabe con el calendario
        # (días hábiles que le quedan al mes después de hoy). Los festivos pueden mover 1 día la entrada.
        hoy = (t[-1] + timedelta(hours=3)).date()
        quedan, d = 0, hoy + timedelta(days=1)
        while d.month == hoy.month:
            quedan += d.weekday() < 5
            d += timedelta(days=1)
        cap["el"] = cap["el"][:-1] + [quedan == params[0] - 1]
    return cap


def spread_par(da, db):
    """Serie log(A) - log(B) en las velas D1 comunes (mismo tiempo). Devuelve (tiempos, serie)."""
    cb = {b["time"]: b["close"] for b in db}
    ts = [b["time"] for b in da if b["time"] in cb]
    ca = {b["time"]: b["close"] for b in da}
    return ts, [math.log(ca[t]) - math.log(cb[t]) for t in ts]


def senal_par(da, db, p):
    """Par de reversión del ratio: z del spread frente a sus últimas L velas (sin la actual).
    Devuelve (lado, z, media, desv, spread_actual) con lado 1 = comprar A y vender B, −1 = al revés; o None."""
    ts, sp = spread_par(da, db)
    if len(sp) < p["L"] + 1:
        return None
    w = sp[-p["L"] - 1:-1]
    m = sum(w) / len(w)
    sd = (sum((x - m) ** 2 for x in w) / len(w)) ** 0.5
    if sd <= 0:
        return None
    z = (sp[-1] - m) / sd
    if abs(z) >= p["S"]:
        return None  # el ratio ya pasó su propio stop: entrar ahí sería empezar perdiendo
    lado = 1 if z < -p["E"] else -1 if z > p["E"] else 0
    return (lado, z, m, sd, sp[-1]) if lado else None


def salida_par(sp_actual, pos, p, sesiones):
    """pos: {lado, e, m, sd}. Motivo de salida o None: vuelta a la media, stop del spread o tiempo."""
    z = (sp_actual - pos["m"]) / pos["sd"]
    if (sp_actual - pos["e"]) * pos["lado"] <= -(p["S"] - p["E"]) * pos["sd"]:
        return "stop del spread"
    if (pos["lado"] == 1 and z > -p["X"]) or (pos["lado"] == -1 and z < p["X"]):
        return "volvió a la media"
    if sesiones >= p["H"]:
        return f"{p['H']} sesiones"
    return None


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
        self.ejecutor = Ejecutor()

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

    def riesgo_de(self, p):
        """Riesgo real de una posición. En los pares el SL del broker es solo de emergencia (muy lejano): cuenta el stop del ratio."""
        par = self.cfg["estrategias"].get("par_ratio", {})
        if p.magic == par.get("magic") and str(p.ticket) in self.estado["riesgos"]:
            return self.estado["riesgos"][str(p.ticket)]
        if not p.sl:
            return 0.0
        d = (p.price_open - p.sl) if p.type == mt5.POSITION_TYPE_BUY else (p.sl - p.price_open)
        return max(d, 0) * self.valor_por_precio(p.symbol) * p.volume

    def riesgo_abierto(self):
        return sum(self.riesgo_de(p) for p in mt5.positions_get() or [])

    def limite_riesgo(self, estrategia):
        """Riesgo abierto máximo para esta estrategia: el total menos lo reservado a OTRAS estrategias sin posición abierta."""
        bal = mt5.account_info().balance
        limite = bal * self.cfg["riesgo_abierto_max"]
        for otra, frac in self.cfg.get("reservas_riesgo", {}).items():
            if otra != estrategia and not self.posiciones(otra):
                limite -= bal * frac
        return limite

    def riesgo_grupo(self, simbolo):
        """(nombre, riesgo abierto del grupo, máximo $) del grupo correlacionado del símbolo, o None."""
        bal = mt5.account_info().balance
        for nombre, g in self.cfg.get("grupos_riesgo", {}).items():
            if simbolo in g["simbolos"]:
                total = sum(self.riesgo_de(p) for p in mt5.positions_get() or [] if p.symbol in g["simbolos"])
                return nombre, total, bal * g["max"]
        return None

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
        """Abre la operación. Devuelve "posponer" si el Ejecutor pide esperar (spread anormal)."""
        e = self.cfg["estrategias"][estrategia]
        bal = mt5.account_info().balance
        riesgo = bal * self.cfg["riesgo_por_operacion"]
        if cargar_json(RUTA_VIGIA, {}).get("modo_precaucion"):
            riesgo *= 0.5  # el Vigía activó la revisión profunda
            motivo += " [modo precaución: riesgo a la mitad]"
        if estrategia in self.estado.get("reducidas", []):
            riesgo *= 0.5
            motivo += " [autocontrol: riesgo a la mitad]"
        f_meta = min(1.0, float(cargar_json(RUTA_METAS, {}).get("factor_riesgo", 1.0)))  # el Estratega solo lo baja
        if f_meta < 1.0:
            riesgo *= f_meta
            motivo += f" [Estratega de metas: riesgo ×{f_meta:g}]"
        if self.riesgo_abierto() + riesgo > self.limite_riesgo(estrategia) * 1.0001:
            log("Sin espacio de riesgo: no abro", estrategia=estrategia, simbolo=simbolo)
            return
        g = self.riesgo_grupo(simbolo)
        if g and g[1] + riesgo > g[2] * 1.0001:
            log("Grupo correlacionado lleno: no abro", estrategia=estrategia, simbolo=simbolo, grupo=g[0])
            return
        lote = self.lote_para_riesgo(simbolo, dist_sl, riesgo)
        if lote <= 0:
            log("El lote mínimo arriesga demasiado: no abro", estrategia=estrategia, simbolo=simbolo)
            return
        entrar, nota = self.ejecutor.puede_entrar(mt5, f"{estrategia}:{simbolo}", simbolo)
        if not entrar:
            log("Ejecutor: entrada pospuesta", estrategia=estrategia, simbolo=simbolo, motivo=nota)
            return "posponer"
        if nota:
            motivo += f" [{nota}]"
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
        r = Ejecutor.enviar(mt5, req, direccion)  # reintenta si el broker recotiza
        if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
            log("Error al abrir", estrategia=estrategia, simbolo=simbolo, retcode=getattr(r, "retcode", None), error=mt5.last_error())
            enviar(f"❗ No pude abrir {estrategia} en {simbolo} (código {getattr(r, 'retcode', None)})")
            return
        p_real = mt5.positions_get(ticket=r.order)
        if p_real:  # SL/TP reales (pudieron moverse si hubo recotización)
            sl, tp = p_real[0].sl, p_real[0].tp
        riesgo_real = abs(r.price - sl) * self.valor_por_precio(simbolo) * lote
        publicar_senal(accion="ABRIR", id=r.order, estrategia=estrategia, simbolo=simbolo, direccion=direccion, precio=r.price,
                       sl_dist=abs(r.price - sl), tp_dist=abs(tp - r.price) if tp else 0.0, magic=e["magic"])
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
        publicar_senal(accion="CERRAR", id=p.ticket, estrategia=estrategia, simbolo=p.symbol, motivo=motivo)
        registrar_operacion(accion="CERRAR", estrategia=estrategia, simbolo=p.symbol, direccion="COMPRA" if es_compra else "VENTA",
                            lote=p.volume, precio=r.price, resultado_usd=round(p.profit + p.swap, 2), motivo=motivo)
        log("CERRADA", ticket=p.ticket, estrategia=estrategia, resultado=round(p.profit + p.swap, 2), motivo=motivo)
        enviar(f"{'✅' if p.profit + p.swap > 0 else '🔻'} CERRADA {estrategia}: {p.symbol} {p.volume} lotes · resultado {p.profit + p.swap:+,.2f}$ · {motivo}")

    # ---------- pares (reversión del ratio) ----------
    def ciclo_pares(self, bloqueado, noticia):
        e = self.cfg["estrategias"].get("par_ratio")
        if not e:
            return
        pares = self.estado.setdefault("pares", {})
        for par in e["pares"]:
            p = {**e, **par}  # cada par con sus propios parámetros (L, E, X, S, H)
            a, b = par["a"], par["b"]
            clave = f"{a}/{b}"
            pos = pares.get(clave)
            # si el broker cerró una pata (SL de emergencia), cierro la otra de inmediato
            if pos:
                vivas = [t for t in pos["tickets"] if mt5.positions_get(ticket=t)]
                if len(vivas) < 2:
                    for t in vivas:
                        for p in mt5.positions_get(ticket=t) or []:
                            self.cerrar(p, "par_ratio", "la otra pata del par se cerró")
                    pares.pop(clave)
                    continue
            if not (self.mercado_abierto(a) and self.mercado_abierto(b)):
                continue
            da, db = self.barras(a, mt5.TIMEFRAME_D1, p["L"] + 30), self.barras(b, mt5.TIMEFRAME_D1, p["L"] + 30)
            if not da or not db or not self.nueva_barra(f"par:{clave}:D1", da):
                continue
            if pos:
                pos["sesiones"] = pos.get("sesiones", 0) + 1
                _, sp = spread_par(da, db)
                motivo = salida_par(sp[-1], pos, p, pos["sesiones"])
                if motivo:
                    for t in pos["tickets"]:
                        for p in mt5.positions_get(ticket=t) or []:
                            self.cerrar(p, "par_ratio", motivo)
                    pares.pop(clave)
                continue
            if bloqueado or noticia or not self.activa("par_ratio"):
                continue
            sen = senal_par(da, db, p)
            if sen:
                self.abrir_par(clave, a, b, sen, da, db, p)

    def abrir_par(self, clave, a, b, sen, da, db, e):
        lado, z, m, sd, sp = sen
        bal = mt5.account_info().balance
        riesgo = bal * self.cfg["riesgo_por_operacion"] * e.get("factor_riesgo", 1.0)
        if cargar_json(RUTA_VIGIA, {}).get("modo_precaucion"):
            riesgo *= 0.5
        riesgo *= min(1.0, float(cargar_json(RUTA_METAS, {}).get("factor_riesgo", 1.0)))
        if "par_ratio" in self.estado.get("reducidas", []):
            riesgo *= 0.5
        d = (e["S"] - e["E"]) * sd                      # distancia del stop en el spread (log)
        nocional = riesgo / d                           # $ por pata: una pérdida de d en el spread ≈ riesgo
        patas = []
        for sim, direccion, velas in ((a, lado, da), (b, -lado, db)):
            info, tick = mt5.symbol_info(sim), mt5.symbol_info_tick(sim)
            precio = tick.ask if direccion == 1 else tick.bid
            lote = math.floor(nocional / (self.valor_por_precio(sim) * precio) / info.volume_step + 1e-9) * info.volume_step
            dist_sl = e["sl_pata_atr"] * atr(velas, 20)
            if lote < info.volume_min:
                log("Par: el lote mínimo no cabe en el riesgo", par=clave, simbolo=sim)
                return
            patas.append((sim, direccion, round(min(lote, info.volume_max), 2), precio, dist_sl, info))
        riesgo_patas = riesgo  # el riesgo real del par es el stop del ratio (el SL de cada pata es de emergencia)
        if self.riesgo_abierto() + riesgo_patas > self.limite_riesgo("par_ratio") * 1.0001:
            log("Par: sin espacio de riesgo", par=clave)
            return
        g = self.riesgo_grupo(a)
        if g and g[1] + riesgo_patas > g[2] * 1.0001:
            log("Par: grupo correlacionado lleno", par=clave, grupo=g[0])
            return
        if self.cfg.get("solo_observar"):
            log("SEÑAL PAR (modo observar)", par=clave, lado=lado, z=round(z, 2))
            return
        tickets = []
        for sim, direccion, lote, precio, dist_sl, info in patas:
            sl = round(precio - direccion * dist_sl, info.digits)
            req = {"action": mt5.TRADE_ACTION_DEAL, "symbol": sim, "volume": lote, "price": precio, "sl": sl, "tp": 0.0,
                   "type": mt5.ORDER_TYPE_BUY if direccion == 1 else mt5.ORDER_TYPE_SELL, "deviation": 30,
                   "magic": e["magic"], "comment": f"aurum_par_{clave}"[:31], "type_time": mt5.ORDER_TIME_GTC, "type_filling": self.filling(sim)}
            r = Ejecutor.enviar(mt5, req, direccion)
            if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
                log("Par: error al abrir una pata: deshago el par", par=clave, simbolo=sim, retcode=getattr(r, "retcode", None))
                for t in tickets:
                    for p in mt5.positions_get(ticket=t) or []:
                        self.cerrar(p, "par_ratio", "no se pudo abrir la otra pata")
                enviar(f"❗ No pude abrir el par {clave} (código {getattr(r, 'retcode', None)}). No quedó nada abierto.")
                return
            tickets.append(r.order)
            self.estado["riesgos"][str(r.order)] = riesgo / 2
            publicar_senal(accion="ABRIR", id=r.order, estrategia="par_ratio", simbolo=sim, direccion=direccion, precio=r.price,
                           sl_dist=dist_sl, tp_dist=0.0, magic=e["magic"])
            registrar_operacion(accion="ABRIR", estrategia="par_ratio", simbolo=sim, direccion="COMPRA" if direccion == 1 else "VENTA",
                                lote=lote, precio_pedido=precio, precio=r.price, sl=sl, tp=0.0, riesgo_usd=round(riesgo / 2, 2),
                                motivo=f"par {clave} z={z:+.2f}")
        self.estado["pares"][clave] = {"lado": lado, "e": sp, "m": m, "sd": sd, "tickets": tickets, "sesiones": 0}
        guardar_json(RUTA_ESTADO, self.estado)
        log("PAR ABIERTO", par=clave, lado=lado, z=round(z, 2), riesgo=round(riesgo, 2))
        enviar(f"🟢 PAR ABIERTO {clave}: {'COMPRA ' + a + ' / VENTA ' + b if lado == 1 else 'VENTA ' + a + ' / COMPRA ' + b} "
               f"(ratio a {z:+.1f} desviaciones). Riesgo ${riesgo:,.0f}. Sale cuando el ratio vuelva a la media.")

    # ---------- autocontrol ----------
    def revisar_autocontrol(self):
        """Autocontrol estadístico (v2.1): compara las últimas N operaciones en vivo con lo que promete el backtest.
        z = (suma real − suma esperada) / (desviación × √N).  z < −2 → riesgo a la mitad;  z < −3 → pausa 30 días
        (vuelve sola, a medio riesgo). Una racha mala normal ya NO apaga una estrategia buena."""
        ac = self.cfg.get("autocontrol", {})
        n = ac.get("ultimas_operaciones", 30)
        deals = mt5.history_deals_get(ahora_utc() - timedelta(days=365), datetime.now() + timedelta(days=1)) or []
        bal = mt5.account_info().balance
        reducidas = self.estado.setdefault("reducidas", [])
        desde = self.estado.setdefault("pausa_desde", {})
        hoy = ahora_utc()
        for nombre in list(self.estado["pausadas"]):  # las pausas vencen solas a los 30 días
            if nombre in desde and hoy - datetime.fromisoformat(desde[nombre]) > timedelta(days=ac.get("dias_pausa", 30)):
                self.estado["pausadas"].remove(nombre)
                desde.pop(nombre)
                if nombre not in reducidas:
                    reducidas.append(nombre)
                enviar(f"▶️ {nombre} vuelve a operar tras su pausa, con riesgo a la mitad hasta que se recupere.")
        for nombre, e in self.cfg["estrategias"].items():
            cierres = [d for d in deals if d.magic == e["magic"] and d.entry == mt5.DEAL_ENTRY_OUT][-n:]
            if len(cierres) < min(n, 20):
                continue
            R = [(d.profit + d.swap + d.commission) / (self.estado["riesgos"].get(str(d.position_id)) or bal * self.cfg["riesgo_por_operacion"])
                 for d in cierres]
            m = len(R)
            media = sum(R) / m
            sd = max((sum((x - media) ** 2 for x in R) / (m - 1)) ** 0.5, 0.5)
            esperado = e.get("exp_backtest", 0.1)
            z = (sum(R) - esperado * m) / (sd * m ** 0.5)
            if z < ac.get("z_pausa", -3.0) and nombre not in self.estado["pausadas"]:
                self.estado["pausadas"].append(nombre)
                desde[nombre] = hoy.isoformat()
                log("AUTOCONTROL: pausa (rinde muy por debajo del backtest)", estrategia=nombre, z=round(z, 2), suma_R=round(sum(R), 1))
                enviar(f"⏸️ Pausé {nombre} 30 días: sus últimas {m} operaciones suman {sum(R):+.1f}R, {abs(z):.1f} desviaciones por debajo "
                       f"de lo esperado (eso ya no parece mala suerte). Revísala con Claude.")
            elif z < ac.get("z_reducir", -2.0) and nombre not in reducidas and nombre not in self.estado["pausadas"]:
                reducidas.append(nombre)
                log("AUTOCONTROL: riesgo a la mitad", estrategia=nombre, z=round(z, 2))
                enviar(f"🔻 {nombre} rinde por debajo de lo esperado ({sum(R):+.1f}R en {m} ops, z {z:+.1f}): le bajo el riesgo a la mitad.")
            elif z >= -1.0 and nombre in reducidas:
                reducidas.remove(nombre)
                enviar(f"✅ {nombre} se recuperó (z {z:+.1f}): vuelve a su riesgo normal.")
        guardar_json(RUTA_ESTADO, self.estado)

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
        guardar_json(RUTA_VIVAS, {"t": ahora_utc().isoformat(), "ids": [p.ticket for p in mt5.positions_get() or []]})
        self.ejecutor.muestrear(mt5, sorted({s for e in self.cfg["estrategias"].values() for s in e["simbolos"]}))
        self.actualizar_config()
        self.actualizar_noticias()
        self.calcular_offset()
        cfg = self.cfg
        bal = mt5.account_info().balance
        if self.resultado_hoy() <= -bal * cfg["perdida_diaria_max"]:
            hoy = ahora_utc().date().isoformat()
            if self.estado.get("stop_diario_avisado") != hoy:
                self.estado["stop_diario_avisado"] = hoy
                log("Stop diario alcanzado: no abro nada más hoy", resultado=round(self.resultado_hoy(), 2))
                enviar(f"⛔ Stop diario: hoy se perdió {self.resultado_hoy():+,.2f}$ (límite {cfg['perdida_diaria_max']:.0%}). No abro más hasta mañana.")
            return  # stop diario: no se abre nada más hoy
        bloqueado = os.path.exists(RUTA_ALTO) or os.path.exists(RUTA_PAUSA)  # Guardián/Supervisor o tu /pausa: solo salidas
        candidatos = []
        noticia = self.bloqueo_noticias()

        # --- estrategias diarias: salidas y señales en cada vela D1 nueva ---
        for nombre in ("donchian", "rsi2", "ibs"):
            if nombre not in cfg["estrategias"]:
                continue  # estrategia eliminada de la configuración
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

        # --- estrategias del laboratorio (aprobadas por Explorador + Abogado del diablo) ---
        for nombre, e in cfg["estrategias"].items():
            if "familia_lab" not in e:
                continue
            for s in e["simbolos"]:
                if not self.mercado_abierto(s):
                    continue
                d1 = self.barras(s, mt5.TIMEFRAME_D1, 400)
                if len(d1) < 260 or not self.nueva_barra(f"{nombre}:{s}:D1", d1):
                    continue
                cap = senal_lab(e["familia_lab"], e["params"], [b["utc"].replace(tzinfo=None) for b in d1],
                                [b["open"] for b in d1], [b["high"] for b in d1], [b["low"] for b in d1], [b["close"] for b in d1])
                if not cap:
                    continue
                abiertas = self.posiciones(nombre, s)
                for p in abiertas:
                    direc = 1 if p.type == mt5.POSITION_TYPE_BUY else -1
                    if (cap["xl"][-1] if direc == 1 else cap["xs"][-1]) or (cap["maxh"] and self.sesiones_desde(d1, p) >= cap["maxh"]):
                        self.cerrar(p, nombre, "regla de salida")
                if abiertas or not self.activa(nombre) or not cap["a"][-1]:
                    continue
                lado = 1 if cap["el"][-1] else -1 if cap["es"][-1] else 0
                if lado:
                    d = cap["slm"] * cap["a"][-1]
                    candidatos.append((f"{nombre}:{s}", nombre, s, lado, d, cap["rr"] * d if cap["rr"] else 0.0, f"señal {e['familia_lab']}"))

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

        self.ciclo_pares(bloqueado, noticia)
        if bloqueado:
            if candidatos:
                log("Bloqueo o pausa activa: no abro nuevas", señales=len(candidatos))
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
            if self.abrir(nombre, s, d, sl, tp, motivo) == "posponer":  # el Ejecutor espera un spread normal
                self.estado["ultima_barra"].pop(f"ruptura:{s}:H1" if nombre == "ruptura_asiatica" else f"{nombre}:{s}:D1", None)
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
