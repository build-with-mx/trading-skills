"""
CENTRALITA — controla el equipo desde Telegram (tu celular). Solo obedece a TU chat (el chat_id de telegram.json):
cualquier otra persona que escriba a tu bot es ignorada.
Comandos:
  /estado          balance, equity, posiciones, bloqueos, modo precaución, metas
  /posiciones      lista de posiciones abiertas con su resultado
  /hoy             operaciones cerradas hoy
  /bots            salud del equipo (Mecánico)
  /pausa           Aurum y los Copiadores dejan de ABRIR operaciones (las abiertas siguen con su SL/TP y reglas de salida)
  /reanudar        quita TU pausa (no quita los bloqueos del Guardián ni del Supervisor: esos son por seguridad)
  /cerrar_todo     pide confirmación;  /cerrar_todo CONFIRMO  cierra todas las posiciones de la demo de Aurum
  /ayuda
Ejecutar:  python centralita.py
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_TG = os.path.join(CARPETA, "telegram.json")
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_PAUSA = os.path.join(CARPETA, "aurum_PAUSA.flag")
RUTA_ALTO = os.path.join(CARPETA, "aurum_ALTO.flag")
AYUDA = ("Comandos: /estado · /posiciones · /hoy · /bots · /pausa · /reanudar · /cerrar_todo · /ayuda\n"
         "/pausa solo frena entradas nuevas; las abiertas siguen protegidas por su SL.")


def cargar(nombre, defecto):
    try:
        with open(os.path.join(CARPETA, nombre), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def leer(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


# ---------------- lógica pura ----------------
def responder(texto, ctx):
    """ctx: {"cuenta", "posiciones", "hoy", "bots", "pausa", "alto", "vigia", "metas"}. Devuelve (respuesta, accion)."""
    partes = (texto or "").strip().split()
    cmd = partes[0].lower().split("@")[0] if partes else ""
    if cmd == "/estado":
        c = ctx.get("cuenta")
        linea = f"Balance ${c['balance']:,.2f} · Equity ${c['equity']:,.2f} ({c['equity'] - c['balance']:+,.2f})\n" if c else "MetaTrader no disponible\n"
        m = ctx.get("metas") or {}
        return (f"📟 Estado\n{linea}Posiciones abiertas: {len(ctx.get('posiciones') or [])}\n"
                f"Pausa manual: {'SÍ' if ctx.get('pausa') else 'no'} · Bloqueo de seguridad: {ctx.get('alto') or 'ninguno'}\n"
                f"Modo precaución: {'SÍ' if (ctx.get('vigia') or {}).get('modo_precaucion') else 'no'}"
                + (f"\nMeta: {max(0, m.get('progreso', 0)):.0%} del camino · prob. {m.get('prob_objetivo', 0):.0%} · riesgo ×{m.get('factor_riesgo', 1):g}" if m else ""), None)
    if cmd == "/posiciones":
        ps = ctx.get("posiciones") or []
        return ("📂 Sin posiciones abiertas" if not ps else "📂 Posiciones:\n" + "\n".join(
            f"• {p['simbolo']} {p['dir']} {p['lote']} @ {p['entrada']} · SL {p['sl'] or '⚠️ ninguno'} · {p['res']:+,.2f}$" for p in ps)), None
    if cmd == "/hoy":
        h = ctx.get("hoy") or []
        return ("📊 Hoy no se cerró ninguna operación" if not h else f"📊 Hoy: {len(h)} cerradas, {sum(x for _, x in h):+,.2f}$\n"
                + "\n".join(f"• {s}: {x:+,.2f}$" for s, x in h[:15])), None
    if cmd == "/bots":
        b = ctx.get("bots") or {}
        return ("🔧 El Mecánico aún no reporta" if not b else "🔧 Bots:\n" + "\n".join(
            f"{'🟢' if e == 'ok' else '🔴' if e == 'atrasado' else '⚪'} {n}" for n, (e, _) in b.items())), None
    if cmd == "/pausa":
        return ("⏸️ Pausa activada: no se abren operaciones nuevas. Las abiertas siguen con su SL/TP. Usa /reanudar para volver.", "pausar")
    if cmd == "/reanudar":
        extra = f"\n⚠️ Sigue activo un bloqueo de seguridad: {ctx['alto']}. Ese no se quita desde aquí." if ctx.get("alto") else ""
        return ("▶️ Pausa quitada: Aurum vuelve a operar." + extra, "reanudar")
    if cmd == "/cerrar_todo":
        if len(partes) > 1 and partes[1].upper() == "CONFIRMO":
            return ("🛑 Cerrando todas las posiciones y pausando entradas nuevas...", "cerrar_todo")
        return (f"¿Seguro? Se cerrarán {len(ctx.get('posiciones') or [])} posiciones al precio actual. Responde:  /cerrar_todo CONFIRMO", None)
    return (AYUDA, None)


# ---------------- ejecución ----------------
def contexto(mt5):
    ctx = {"pausa": os.path.exists(RUTA_PAUSA), "alto": leer(RUTA_ALTO).split(":")[0][:60], "vigia": cargar("vigia_estado.json", {}),
           "metas": cargar("metas_estado.json", {}), "bots": cargar("mecanico_estado.json", {}).get("bots", {})}
    if mt5 is not None:
        try:
            a = mt5.account_info()
            ctx["cuenta"] = {"balance": a.balance, "equity": a.equity}
            ctx["posiciones"] = [{"simbolo": p.symbol, "dir": "COMPRA" if p.type == 0 else "VENTA", "lote": p.volume, "entrada": p.price_open,
                                  "sl": p.sl, "res": p.profit + p.swap} for p in mt5.positions_get() or []]
            desde = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time())
            ctx["hoy"] = [(d.symbol, d.profit + d.swap + d.commission) for d in mt5.history_deals_get(desde, datetime.now() + timedelta(days=1)) or []
                          if d.entry == mt5.DEAL_ENTRY_OUT]
        except Exception:
            pass
    return ctx


def cerrar_todo(mt5):
    cfg = cargar("aurum_config.json", {})
    a = mt5.account_info()
    if a.login != cfg.get("cuenta_permitida") or a.trade_mode != mt5.ACCOUNT_TRADE_MODE_DEMO:
        return "No cierro nada: este MetaTrader no tiene abierta la demo de Aurum."
    ok = 0
    for p in mt5.positions_get() or []:
        t = mt5.symbol_info_tick(p.symbol)
        compra = p.type == mt5.POSITION_TYPE_BUY
        fm = mt5.symbol_info(p.symbol).filling_mode
        r = mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": p.symbol, "volume": p.volume, "position": p.ticket,
                            "type": mt5.ORDER_TYPE_SELL if compra else mt5.ORDER_TYPE_BUY, "price": t.bid if compra else t.ask,
                            "deviation": 50, "magic": p.magic, "comment": "centralita_cierre",
                            "type_filling": mt5.ORDER_FILLING_FOK if fm & 1 else mt5.ORDER_FILLING_IOC if fm & 2 else mt5.ORDER_FILLING_RETURN})
        ok += bool(r and r.retcode == mt5.TRADE_RETCODE_DONE)
    return f"Cerradas {ok} posiciones."


def main():
    tg = cargar("telegram.json", {})
    if not tg.get("token") or not tg.get("chat_id"):
        print("Centralita: falta telegram.json (ver LEEME.md). Reviso otra vez en 1 hora.")
        time.sleep(3600)
        return
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            mt5 = None
    except ImportError:
        mt5 = None
    base = f"https://api.telegram.org/bot{tg['token']}/"
    est = cargar("centralita_estado.json", {"offset": 0})
    enviar("📟 Centralita activa. Escribe /ayuda para ver los comandos.", "Centralita")
    while True:
        try:
            url = base + "getUpdates?" + urllib.parse.urlencode({"offset": est["offset"], "timeout": 50})
            datos = json.loads(urllib.request.urlopen(url, timeout=70).read().decode())
            for u in datos.get("result", []):
                est["offset"] = u["update_id"] + 1
                msg = u.get("message") or {}
                if str(msg.get("chat", {}).get("id")) != str(tg["chat_id"]):
                    print(f"Ignoro un mensaje de otro chat ({msg.get('chat', {}).get('id')})")
                    continue
                texto, accion = responder(msg.get("text", ""), contexto(mt5))
                if accion == "pausar" or accion == "cerrar_todo":
                    with open(RUTA_PAUSA, "w", encoding="utf-8") as f:
                        f.write(f"MANUAL desde Telegram {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC")
                elif accion == "reanudar" and os.path.exists(RUTA_PAUSA):
                    os.remove(RUTA_PAUSA)
                if accion == "cerrar_todo":
                    texto += "\n" + (cerrar_todo(mt5) if mt5 is not None else "MetaTrader no disponible.")
                enviar(texto, "Centralita")
            with open(os.path.join(CARPETA, "centralita_estado.json"), "w", encoding="utf-8") as f:
                json.dump(est, f)
        except Exception as e:
            print(f"Centralita: error (sigo): {e!r}"[:200])
            time.sleep(10)


if __name__ == "__main__":
    main()
