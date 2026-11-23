"""
COPIADOR — copia las operaciones de Aurum (cuenta maestra) a otra cuenta MT5: un reto de fondeo, otra demo, etc.
Cómo funciona:
  • Aurum escribe cada apertura y cierre en senales_maestro.jsonl y la lista de posiciones vivas en maestro_vivas.json.
  • Cada Copiador (uno por cuenta, con su propio archivo de configuración y su propio MetaTrader 5 instalado) lee esas
    señales y las replica con SU riesgo, calculado sobre SU balance. El SL y el TP van en el broker desde el primer segundo.
  • No persigue el precio: si la señal tiene más de 10 minutos o el precio ya se movió más de 25% del SL, no copia.
  • Respeta su archivo de bloqueo (lo escribe el Supervisor de fondeo) y el factor de riesgo del Estratega de metas.
SEGURIDAD
  • Solo opera la cuenta indicada en "cuenta". Si es una cuenta REAL (un reto de fondeo lo es), además exige
    "permitir_cuenta_real": true  Y  un archivo AUTORIZO_<cuenta>.txt creado por ti con la palabra AUTORIZO.
    Sin las dos cosas no abre nada. Claude nunca crea ese archivo: lo creas tú.
Ejecutar:  python copiador.py copiador_fondeo1.json
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_SENALES = os.path.join(CARPETA, "senales_maestro.jsonl")
RUTA_VIVAS = os.path.join(CARPETA, "maestro_vivas.json")
RUTA_VIGIA = os.path.join(CARPETA, "vigia_estado.json")
MAX_EDAD_SENAL = timedelta(minutes=10)
MAX_DESVIO_SL = 0.25


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def ruta(nombre):
    return nombre if os.path.isabs(nombre) else os.path.join(CARPETA, nombre)


# ---------------- lógica pura (probada sin MT5) ----------------
def leer_senales(ruta_jsonl, desde_byte):
    """Devuelve (eventos nuevos, nueva posición en bytes). Ignora líneas incompletas (Aurum podría estar escribiendo)."""
    if not os.path.exists(ruta_jsonl):
        return [], 0
    with open(ruta_jsonl, "rb") as f:
        tam = os.path.getsize(ruta_jsonl)
        if desde_byte > tam:  # el archivo se reinició
            desde_byte = 0
        f.seek(desde_byte)
        datos = f.read()
    eventos, usados = [], 0
    for linea in datos.split(b"\n")[:-1]:  # la última parte (sin \n) puede estar incompleta
        usados += len(linea) + 1
        try:
            eventos.append(json.loads(linea.decode("utf-8")))
        except Exception:
            pass
    return eventos, desde_byte + usados


def decidir_copia(ev, cfg, ahora, precio_actual):
    """None si se copia; si no, el motivo para no copiar."""
    if ev["estrategia"] not in cfg.get("estrategias", []):
        return "estrategia no incluida en este copiador"
    if ahora - datetime.fromisoformat(ev["t"]) > MAX_EDAD_SENAL:
        return "señal vieja (no persigo el precio)"
    if abs(precio_actual - ev["precio"]) > MAX_DESVIO_SL * ev["sl_dist"]:
        return f"el precio ya se movió {abs(precio_actual - ev['precio']):.2f} (> {MAX_DESVIO_SL:.0%} del SL)"
    return None


def factor_riesgo(cfg, metas, vigia):
    f = min(1.0, float(metas.get("factor_riesgo", 1.0)))  # el Estratega solo puede BAJAR el riesgo
    if vigia.get("modo_precaucion"):
        f *= 0.5
    return f


def copias_huerfanas(copias, vivas, ahora, abiertas_desde):
    """Copias cuya posición maestra ya no existe (cerró por SL/TP en el maestro). Solo si la foto del maestro es reciente."""
    if not vivas or ahora - datetime.fromisoformat(vivas["t"]) > timedelta(minutes=3):
        return []
    ids = set(map(str, vivas["ids"]))
    return [mid for mid in copias if mid not in ids and ahora - abiertas_desde.get(mid, ahora) > timedelta(minutes=2)]


# ---------------- ejecución con MT5 ----------------
class Copiador:
    def __init__(self, ruta_cfg):
        self.cfg = cargar(ruta_cfg, None)
        if not self.cfg:
            raise SystemExit(f"No encuentro {ruta_cfg}. Copia copiador_ejemplo.json, renómbralo y rellénalo.")
        if not self.cfg.get("activo"):
            raise SystemExit(f'{ruta_cfg}: "activo" está en false.')
        self.nombre = self.cfg.get("nombre", "copiador")
        self.ruta_estado = ruta(f"copiador_{self.nombre}_estado.json")
        self.est = cargar(self.ruta_estado, {"byte": None, "copias": {}, "abiertas_desde": {}})
        self.ruta_alto = ruta(self.cfg.get("archivo_bloqueo", f"ALTO_{self.nombre}.flag"))
        self.ruta_metas = ruta(self.cfg.get("archivo_metas", f"metas_{self.nombre}.json"))

    def conectar(self):
        import MetaTrader5 as mt5
        self.mt5 = mt5
        ok = mt5.initialize(path=self.cfg["terminal"]) if self.cfg.get("terminal") else mt5.initialize()
        if not ok:
            raise SystemExit(f"No conecta con el MetaTrader 5 de {self.nombre}: {mt5.last_error()}")
        c = mt5.account_info()
        if c.login != self.cfg["cuenta"]:
            mt5.shutdown()
            raise SystemExit(f"El terminal tiene abierta la cuenta {c.login}, no la {self.cfg['cuenta']}. No copio nada.")
        if c.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
            aut = ruta(f"AUTORIZO_{c.login}.txt")
            texto = open(aut, encoding="utf-8").read() if os.path.exists(aut) else ""
            if not self.cfg.get("permitir_cuenta_real") or "AUTORIZO" not in texto.upper():
                mt5.shutdown()
                raise SystemExit(f"La cuenta {c.login} es REAL. Para copiar a ella necesitas \"permitir_cuenta_real\": true "
                                 f"Y crear tú el archivo AUTORIZO_{c.login}.txt con la palabra AUTORIZO.")
        if self.est["byte"] is None:  # primera vez: empieza desde ahora, no copia el pasado
            self.est["byte"] = os.path.getsize(RUTA_SENALES) if os.path.exists(RUTA_SENALES) else 0
        enviar(f"📡 Copiador «{self.nombre}» activo en la cuenta {c.login} ({'demo' if c.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else 'REAL'}). "
               f"Balance ${c.balance:,.2f}, riesgo {self.cfg['riesgo_por_operacion']:.2%} por operación.", "Copiador")

    def simbolo(self, s):
        return self.cfg.get("mapa_simbolos", {}).get(s, s + self.cfg.get("sufijo", ""))

    def valor_por_precio(self, s):
        i = self.mt5.symbol_info(s)
        return i.trade_tick_value / i.trade_tick_size

    def riesgo_abierto(self):
        total = 0.0
        for p in self.mt5.positions_get() or []:
            if p.sl:
                total += max(0.0, (p.price_open - p.sl) if p.type == 0 else (p.sl - p.price_open)) * self.valor_por_precio(p.symbol) * p.volume
        return total

    def filling(self, s):
        fm = self.mt5.symbol_info(s).filling_mode
        return self.mt5.ORDER_FILLING_FOK if fm & 1 else self.mt5.ORDER_FILLING_IOC if fm & 2 else self.mt5.ORDER_FILLING_RETURN

    def abrir(self, ev, ahora):
        mt5, s = self.mt5, self.simbolo(ev["simbolo"])
        if not mt5.symbol_select(s, True) or not mt5.symbol_info(s):
            return f"el símbolo {s} no existe en esta cuenta (revisa mapa_simbolos)"
        if os.path.exists(self.ruta_alto):
            return "bloqueado por el Supervisor de fondeo"
        tick, info = mt5.symbol_info_tick(s), mt5.symbol_info(s)
        d = ev["direccion"]
        precio = tick.ask if d == 1 else tick.bid
        motivo = decidir_copia(ev, self.cfg, ahora, precio)
        if motivo:
            return motivo
        bal = mt5.account_info().balance
        riesgo = bal * self.cfg["riesgo_por_operacion"] * factor_riesgo(self.cfg, cargar(self.ruta_metas, {}), cargar(RUTA_VIGIA, {}))
        if self.riesgo_abierto() + riesgo > bal * self.cfg["riesgo_abierto_max"]:
            return "sin espacio de riesgo"
        lote = int(riesgo / (ev["sl_dist"] * self.valor_por_precio(s) * info.volume_step)) * info.volume_step
        lote = round(min(lote, info.volume_max), 2)
        if lote < info.volume_min:
            return f"el lote mínimo ({info.volume_min}) arriesga más de ${riesgo:,.0f}"
        sl = round(precio - d * ev["sl_dist"], info.digits)
        tp = round(precio + d * ev["tp_dist"], info.digits) if ev.get("tp_dist") else 0.0
        r = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": s, "volume": lote, "price": precio, "sl": sl, "tp": tp,
                            "type": mt5.ORDER_TYPE_BUY if d == 1 else mt5.ORDER_TYPE_SELL, "deviation": 30,
                            "magic": ev.get("magic", 0), "comment": f"copia_{ev['id']}"[:31],
                            "type_time": mt5.ORDER_TIME_GTC, "type_filling": self.filling(s)})
        if r is None or r.retcode != mt5.TRADE_RETCODE_DONE:
            return f"el broker rechazó la orden (código {getattr(r, 'retcode', None)})"
        mid = str(ev["id"])
        self.est["copias"][mid] = r.order
        self.est["abiertas_desde"][mid] = ahora.isoformat()
        enviar(f"📡🟢 [{self.nombre}] Copiada {ev['estrategia']}: {'COMPRA' if d == 1 else 'VENTA'} {s} {lote} lotes @ {r.price} · "
               f"SL {sl} · TP {tp or '—'}", "Copiador")
        return None

    def cerrar(self, mid, motivo):
        mt5 = self.mt5
        ticket = self.est["copias"].pop(mid, None)
        self.est["abiertas_desde"].pop(mid, None)
        for p in mt5.positions_get(ticket=ticket) or [] if ticket else []:
            tick = mt5.symbol_info_tick(p.symbol)
            compra = p.type == mt5.POSITION_TYPE_BUY
            r = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
                                "type": mt5.ORDER_TYPE_SELL if compra else mt5.ORDER_TYPE_BUY, "price": tick.bid if compra else tick.ask,
                                "deviation": 30, "magic": p.magic, "comment": "copia_cierre", "type_filling": self.filling(p.symbol)})
            if r is not None and r.retcode == mt5.TRADE_RETCODE_DONE:
                enviar(f"📡{'✅' if p.profit + p.swap > 0 else '🔻'} [{self.nombre}] Cerrada copia {p.symbol}: {p.profit + p.swap:+,.2f}$ · {motivo}", "Copiador")

    def ciclo(self):
        ahora = datetime.now(timezone.utc)
        eventos, self.est["byte"] = leer_senales(RUTA_SENALES, self.est["byte"])
        for ev in eventos:
            if ev["accion"] == "ABRIR":
                motivo = self.abrir(ev, ahora)
                if motivo:
                    print(f"{ahora:%H:%M:%S} [{self.nombre}] No copio {ev['estrategia']} {ev['simbolo']}: {motivo}")
                    if "rechazó" in motivo or "no existe" in motivo:
                        enviar(f"❗ [{self.nombre}] No pude copiar {ev['estrategia']} {ev['simbolo']}: {motivo}", "Copiador")
            elif ev["accion"] == "CERRAR" and str(ev["id"]) in self.est["copias"]:
                self.cerrar(str(ev["id"]), "el maestro cerró (" + ev.get("motivo", "") + ")")
        # copias cuyo maestro ya cerró por SL/TP; y limpieza de copias que el broker ya cerró
        desde = {k: datetime.fromisoformat(v) for k, v in self.est["abiertas_desde"].items()}
        for mid in copias_huerfanas(self.est["copias"], cargar(RUTA_VIVAS, None), ahora, desde):
            self.cerrar(mid, "el maestro ya no tiene esa posición")
        for mid, t in list(self.est["copias"].items()):
            if not self.mt5.positions_get(ticket=t):
                self.est["copias"].pop(mid)
                self.est["abiertas_desde"].pop(mid, None)
        with open(self.ruta_estado, "w", encoding="utf-8") as f:
            json.dump(self.est, f, indent=2)

    def correr(self):
        self.conectar()
        while True:
            try:
                self.ciclo()
            except Exception as e:
                print(f"Copiador {self.nombre}: error (sigo): {e!r}"[:200])
            time.sleep(2)


if __name__ == "__main__":
    Copiador(sys.argv[1] if len(sys.argv) > 1 else os.path.join(CARPETA, "copiador_fondeo1.json")).correr()
