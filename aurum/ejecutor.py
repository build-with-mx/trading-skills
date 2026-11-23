"""
EJECUTOR INTELIGENTE — módulo que usa Aurum para ENTRAR MEJOR (no es una ventana aparte).
  • Spread: guarda una muestra por minuto del spread de cada mercado (último día) y NO entra si el spread actual es
    más de 2× su mediana. Caso típico: las velas diarias abren a las 17:00 de Nueva York, justo en el "rollover", cuando
    el spread se dispara; el Ejecutor pospone la entrada unos minutos hasta que el spread vuelve a lo normal
    (como máximo 3 horas; si sigue alto, entra igual para no perder la señal).
  • Recotizaciones: si el broker contesta "el precio cambió", reintenta hasta 3 veces con el precio nuevo.
  • Mide el deslizamiento de cada entrada (lo usa el Auditor y el Contador).
"""
import json
import os
import statistics as st
import time
from datetime import datetime, timedelta, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_SPREADS = os.path.join(CARPETA, "ejecutor_spreads.json")
MUESTRAS = 1440          # un día de muestras por minuto
FACTOR_MAX = 2.0
ESPERA_MAX = timedelta(hours=3)
RECOTIZA = (10004, 10020, 10021)  # requote, price changed, price off


def spread_ok(actual, muestras, factor=FACTOR_MAX):
    """Función pura. Con menos de 30 muestras no bloquea (aún no sabe qué es normal)."""
    if len(muestras) < 30:
        return True, None
    med = st.median(muestras)
    return actual <= factor * med if med > 0 else True, med


def decidir(actual, muestras, primera_vez, ahora):
    """Devuelve ("entrar"|"esperar", texto). primera_vez: cuándo apareció la señal por primera vez."""
    ok, med = spread_ok(actual, muestras)
    if ok:
        return "entrar", None
    if ahora - primera_vez >= ESPERA_MAX:
        return "entrar", f"spread {actual:g} sigue alto ({actual / med:.1f}× lo normal) tras {ESPERA_MAX}; entro igual"
    return "esperar", f"spread {actual:g} = {actual / med:.1f}× lo normal ({med:g}); espero a que baje"


class Ejecutor:
    def __init__(self):
        try:
            with open(RUTA_SPREADS, encoding="utf-8") as f:
                self.spreads = json.load(f)
        except Exception:
            self.spreads = {}
        self.ultima_muestra = 0.0
        self.esperando = {}  # clave de señal -> primera vez vista

    def muestrear(self, mt5, simbolos):
        if time.time() - self.ultima_muestra < 60:
            return
        self.ultima_muestra = time.time()
        for s in simbolos:
            t = mt5.symbol_info_tick(s)
            if t and t.ask > t.bid:
                self.spreads.setdefault(s, []).append(round(t.ask - t.bid, 6))
                del self.spreads[s][:-MUESTRAS]
        try:
            with open(RUTA_SPREADS, "w", encoding="utf-8") as f:
                json.dump(self.spreads, f)
        except Exception:
            pass

    def puede_entrar(self, mt5, clave, simbolo):
        t = mt5.symbol_info_tick(simbolo)
        ahora = datetime.now(timezone.utc)
        primera = self.esperando.get(clave)
        if primera is None or ahora - primera > 2 * ESPERA_MAX:  # una espera vieja no cuenta para una señal nueva
            primera = self.esperando[clave] = ahora
        accion, texto = decidir(t.ask - t.bid, self.spreads.get(simbolo, []), primera, ahora)
        if accion == "entrar":
            self.esperando.pop(clave, None)
        return accion == "entrar", texto

    @staticmethod
    def enviar(mt5, req, direccion, intentos=3):
        """Envía la orden; si recotiza, actualiza el precio (y mueve SL/TP la misma distancia) y reintenta."""
        r = None
        for _ in range(intentos):
            r = mt5.order_send(req)
            if r is None or r.retcode not in RECOTIZA:
                return r
            tick = mt5.symbol_info_tick(req["symbol"])
            nuevo = tick.ask if direccion == 1 else tick.bid
            delta = nuevo - req["price"]
            req = dict(req, price=nuevo, sl=req["sl"] + delta if req.get("sl") else 0.0, tp=req["tp"] + delta if req.get("tp") else 0.0)
            time.sleep(0.5)
        return r
