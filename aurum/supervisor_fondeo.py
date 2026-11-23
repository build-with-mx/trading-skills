"""
SUPERVISOR DE FONDEO — hace cumplir las reglas de la empresa de fondeo (prop firm) CON MARGEN DE SEGURIDAD.
Corre junto a Aurum (o junto al Copiador) en la cuenta del reto. Revisa cada 5 segundos:
  • Pérdida diaria: al llegar al 50% del límite bloquea nuevas entradas; al 80% CIERRA TODO (antes de que la empresa lo haga).
  • Pérdida total (estática o "trailing" desde el máximo): mismo esquema 50% / 80%.
  • Objetivo alcanzado: bloquea nuevas entradas para no arriesgar lo ganado (te avisa: ¡reto superado!).
  • Consistencia: si el beneficio de hoy se acerca al % máximo permitido del beneficio total, bloquea el resto del día.
  • Noticias: si la empresa las prohíbe, cierra posiciones N minutos antes de noticias de alto impacto.
  • Fin de semana: si la empresa lo exige, cierra todo el viernes antes del cierre.
Usa el mismo archivo de bloqueo que el Guardián (aurum_ALTO.flag). Reglas en aurum_config.json → "fondeo".
Ejecutar:  python supervisor_fondeo.py copiador_fondeo1.json   (cuenta de fondeo: usa su "terminal", "cuenta", "fondeo" y "archivo_bloqueo")
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_ESTADO = os.path.join(CARPETA, "supervisor_estado.json")
RUTA_ALTO = os.path.join(CARPETA, "aurum_ALTO.flag")


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


# ---------------- lógica pura (probada sin MT5) ----------------
def evaluar(reglas, est, equity, balance, ahora):
    """Devuelve (acciones, mensajes). acciones ⊂ {"bloquear_dia", "bloquear_total", "cerrar_todo", "objetivo"}."""
    acciones, msgs = set(), []
    ini = reglas["balance_inicial"]
    # pérdida diaria (la mayoría de empresas la miden desde el balance o la equity al inicio del día, hora del servidor)
    base_dia = est["equity_inicio_dia"] if reglas.get("base_perdida_diaria") == "equity" else est["balance_inicio_dia"]
    limite_dia = ini * reglas["perdida_diaria_max"]
    perdida_dia = base_dia - equity
    if perdida_dia >= limite_dia * reglas["cerrar_en"]:
        acciones |= {"cerrar_todo", "bloquear_dia"}
        msgs.append(f"pérdida del día ${perdida_dia:,.0f} = {perdida_dia / limite_dia:.0%} del límite (${limite_dia:,.0f})")
    elif perdida_dia >= limite_dia * reglas["bloquear_en"]:
        acciones.add("bloquear_dia")
        msgs.append(f"pérdida del día al {perdida_dia / limite_dia:.0%} del límite: no abro más hoy")
    # pérdida total
    nivel = (est["pico"] if reglas.get("tipo_perdida_total") == "trailing" else ini) - ini * reglas["perdida_total_max"]
    colchon = equity - nivel
    tramo = ini * reglas["perdida_total_max"]
    if colchon <= tramo * (1 - reglas["cerrar_en"]):
        acciones |= {"cerrar_todo", "bloquear_total"}
        msgs.append(f"equity ${equity:,.0f} a solo ${colchon:,.0f} del límite total (${nivel:,.0f})")
    elif colchon <= tramo * (1 - reglas["bloquear_en"]):
        acciones.add("bloquear_dia")
        msgs.append(f"equity a ${colchon:,.0f} del límite total: no abro más hoy")
    # objetivo
    if reglas.get("objetivo") and balance >= ini * (1 + reglas["objetivo"]) and equity >= ini * (1 + reglas["objetivo"]):
        acciones |= {"objetivo", "bloquear_total"}
        msgs.append(f"¡OBJETIVO ALCANZADO! balance ${balance:,.0f} (+{balance / ini - 1:.1%})")
    # consistencia: beneficio de hoy no debe superar X% del beneficio total
    cons = reglas.get("consistencia_max_dia")
    beneficio_total = balance - ini
    hoy = equity - est["balance_inicio_dia"]
    if cons and beneficio_total > 0 and hoy > 0 and hoy >= cons * 0.8 * max(beneficio_total, hoy):
        acciones.add("bloquear_dia")
        msgs.append(f"consistencia: hoy +${hoy:,.0f} se acerca al {cons:.0%} del beneficio total")
    # fin de semana (viernes, desde 1 h antes del cierre de las 22:00 UTC)
    if reglas.get("cerrar_fin_semana") and ahora.weekday() == 4 and ahora.hour >= 20:
        acciones |= {"cerrar_todo", "bloquear_dia"}
        msgs.append("viernes: cierro todo antes del fin de semana (regla de la empresa)")
    return acciones, msgs


def noticia_cercana(eventos, ahora, minutos):
    return next((t for c, t in eventos if c - timedelta(minutes=minutos) <= ahora <= c + timedelta(minutes=minutos)), None)


# ---------------- ejecución con MT5 ----------------
def cerrar_todo(mt5, motivo):
    for p in mt5.positions_get() or []:
        tick = mt5.symbol_info_tick(p.symbol)
        compra = p.type == mt5.POSITION_TYPE_BUY
        fm = mt5.symbol_info(p.symbol).filling_mode
        mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
                        "type": mt5.ORDER_TYPE_SELL if compra else mt5.ORDER_TYPE_BUY, "price": tick.bid if compra else tick.ask,
                        "deviation": 50, "magic": p.magic, "comment": "supervisor_fondeo",
                        "type_filling": mt5.ORDER_FILLING_FOK if fm & 1 else mt5.ORDER_FILLING_IOC if fm & 2 else mt5.ORDER_FILLING_RETURN})
    enviar(f"🛑 Cerré todas las posiciones. {motivo}", "Supervisor de fondeo")


def main():
    import MetaTrader5 as mt5
    ruta_cfg = sys.argv[1] if len(sys.argv) > 1 else RUTA_CONFIG
    if not os.path.isabs(ruta_cfg):
        ruta_cfg = os.path.join(CARPETA, ruta_cfg)
    cfg = cargar(ruta_cfg, {})
    reglas = cfg.get("fondeo", {})
    if not reglas.get("activo"):
        raise SystemExit(f'El Supervisor de fondeo está desactivado. Configura "fondeo" en {os.path.basename(ruta_cfg)} ("activo": true).')
    global RUTA_ALTO, RUTA_ESTADO
    if cfg.get("archivo_bloqueo"):
        RUTA_ALTO = os.path.join(CARPETA, cfg["archivo_bloqueo"])
        RUTA_ESTADO = os.path.join(CARPETA, f"supervisor_{cfg.get('nombre', 'fondeo')}_estado.json")
    ok = mt5.initialize(path=cfg["terminal"]) if cfg.get("terminal") else mt5.initialize()
    if not ok:
        raise SystemExit(f"No conecta con MetaTrader 5: {mt5.last_error()}")
    info = mt5.account_info()
    if cfg.get("cuenta") and info.login != cfg["cuenta"]:
        raise SystemExit(f"El terminal tiene la cuenta {info.login}, no la {cfg['cuenta']}.")
    url_noticias = cfg.get("filtro_noticias", cargar(RUTA_CONFIG, {}).get("filtro_noticias", {})).get("url", "")
    est = cargar(RUTA_ESTADO, {"dia": "", "pico": info.equity, "balance_inicio_dia": info.balance, "equity_inicio_dia": info.equity})
    enviar(f"🏢 Supervisor de fondeo activo ({reglas.get('empresa', '?')}): pérdida diaria {reglas['perdida_diaria_max']:.0%}, "
           f"total {reglas['perdida_total_max']:.0%} ({reglas.get('tipo_perdida_total', 'estatica')}), objetivo {reglas.get('objetivo', 0):.0%}. "
           f"Actúo al {reglas['bloquear_en']:.0%} (bloqueo) y {reglas['cerrar_en']:.0%} (cierre) de cada límite.", "Supervisor de fondeo")
    eventos, ultima_carga = [], None
    while True:
        try:
            ahora = datetime.now(timezone.utc)
            info = mt5.account_info()
            dia_srv = (ahora + timedelta(hours=reglas.get("offset_dia_servidor_h", 2))).date().isoformat()
            if est["dia"] != dia_srv:
                est.update({"dia": dia_srv, "balance_inicio_dia": info.balance, "equity_inicio_dia": info.equity})
                if os.path.exists(RUTA_ALTO) and open(RUTA_ALTO).read().startswith("DIARIO"):
                    os.remove(RUTA_ALTO)
            est["pico"] = max(est["pico"], info.equity)
            acciones, msgs = evaluar(reglas, est, info.equity, info.balance, ahora)
            if "cerrar_todo" in acciones and (mt5.positions_get() or []):
                cerrar_todo(mt5, "Motivo: " + "; ".join(msgs))
            if acciones & {"bloquear_dia", "bloquear_total"}:
                tipo = "TOTAL" if "bloquear_total" in acciones else "DIARIO"
                actual = open(RUTA_ALTO).read() if os.path.exists(RUTA_ALTO) else ""
                if not actual.startswith(tipo) and not actual.startswith("TOTAL"):
                    with open(RUTA_ALTO, "w") as f:
                        f.write(f"{tipo} fondeo: {'; '.join(msgs)}")
                    enviar(("🏆 " if "objetivo" in acciones else "🧱 ") + "; ".join(msgs), "Supervisor de fondeo")
            # noticias prohibidas por la empresa
            mins = reglas.get("cerrar_antes_de_noticias_min", 0)
            if mins:
                if not ultima_carga or ahora - ultima_carga > timedelta(hours=1):
                    try:
                        datos = json.loads(urllib.request.urlopen(url_noticias, timeout=20).read().decode())
                        eventos = [(datetime.fromisoformat(x["date"]).astimezone(timezone.utc), x.get("title", "")) for x in datos
                                   if x.get("country") == "USD" and x.get("impact") == "High"]
                        ultima_carga = ahora
                    except Exception:
                        pass
                n = noticia_cercana(eventos, ahora, mins)
                if n and (mt5.positions_get() or []):
                    cerrar_todo(mt5, f"Noticia de alto impacto ({n}): la empresa no permite posiciones abiertas.")
            with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
                json.dump(est, f, indent=2)
        except Exception as e:
            print(f"Supervisor: error (sigo): {e!r}"[:200])
        time.sleep(5)


if __name__ == "__main__":
    main()
