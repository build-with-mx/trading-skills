"""
VIGÍA — inteligencia de mercado. Corre en su propia ventana y revisa cada 15 minutos:
  • RÉGIMEN de cada mercado operado (tendencia / rango / mixto) con el Efficiency Ratio de 20 días.
  • VOLATILIDAD: ATR(20) frente a su media de 60 días; avisa si se dispara (> 1.5×) y marca extrema (> 2×).
  • VIX (índice del miedo) si el broker lo cotiza.
  • NOTICIAS: calendario de alto impacto USD de las próximas 24 h (resumen diario a las 12:00 UTC ≈ 6 am Monterrey).
  • CAZANOTICIAS: comunicados nuevos de la Reserva Federal (RSS oficial) con palabras clave importantes.
  • REVISIÓN PROFUNDA (del prompt maestro): si un mercado operado tiene volatilidad > 2× su media, si 3+ estrategias cierran
    en pérdida el mismo día o si la cuenta cae −2% en el día → activa MODO PRECAUCIÓN (Aurum arriesga la mitad) y te avisa.
    Se desactiva solo al día siguiente si ya no se cumple ninguna condición.
Escribe vigia_estado.json (Aurum lo lee) y vigia_reporte.md.
Ejecutar:  python vigia.py      (o  python vigia.py --una-vez)
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from mensajero import enviar
from minero import leer_velas

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_ESTADO = os.path.join(CARPETA, "vigia_estado.json")
RUTA_REPORTE = os.path.join(CARPETA, "vigia_reporte.md")
FED_RSS = "https://www.federalreserve.gov/feeds/press_all.xml"
PALABRAS_FED = ("FOMC", "federal funds", "rate", "statement", "emergency", "liquidity", "minutes", "balance sheet")


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


# ---------------- análisis puro (se puede probar sin MT5) ----------------
def efficiency_ratio(cierres, n=20):
    if len(cierres) < n + 1:
        return None
    cambio = abs(cierres[-1] - cierres[-1 - n])
    ruido = sum(abs(cierres[i] - cierres[i - 1]) for i in range(len(cierres) - n, len(cierres)))
    return cambio / ruido if ruido else 0.0


def atr_serie(h, l, c, n=20):
    tr = [h[0] - l[0]] + [max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, len(c))]
    return [sum(tr[i - n + 1:i + 1]) / n if i >= n - 1 else None for i in range(len(tr))]


def analizar_mercado(t, o, h, l, c):
    er = efficiency_ratio(c)
    a = atr_serie(h, l, c)
    validos = [x for x in a[-61:-1] if x]
    ratio = a[-1] / (sum(validos) / len(validos)) if validos and a[-1] else None
    regimen = "tendencia" if er is not None and er > 0.35 else "rango" if er is not None and er < 0.2 else "mixto"
    vol = "extrema" if ratio and ratio > 2 else "alta" if ratio and ratio > 1.5 else "normal"
    return {"regimen": regimen, "er": round(er, 2) if er is not None else None, "atr_ratio": round(ratio, 2) if ratio else None,
            "volatilidad": vol, "tendencia_20d": "alcista" if c[-1] > c[-21] else "bajista"}


# ---------------- fuentes externas ----------------
def noticias_24h(cfg):
    fn = cfg.get("filtro_noticias", {})
    try:
        datos = json.loads(urllib.request.urlopen(fn["url"], timeout=20).read().decode())
    except Exception as e:
        return None, str(e)[:80]
    ahora = datetime.now(timezone.utc)
    ev = []
    for x in datos:
        if x.get("country") in fn.get("monedas", ["USD"]) and x.get("impact") in fn.get("impacto", ["High"]):
            cuando = datetime.fromisoformat(x["date"]).astimezone(timezone.utc)
            if ahora <= cuando <= ahora + timedelta(hours=24):
                ev.append((cuando, x.get("title", ""), x.get("forecast", ""), x.get("previous", "")))
    return sorted(ev), None


def comunicados_fed(vistos):
    try:
        xml = urllib.request.urlopen(FED_RSS, timeout=20).read().decode("utf-8", "ignore")
    except Exception:
        return []
    nuevos = []
    for item in re.findall(r"<item>(.*?)</item>", xml, re.S)[:20]:
        titulo = re.sub(r"<!\[CDATA\[|\]\]>", "", (re.findall(r"<title>(.*?)</title>", item, re.S) or [""])[0]).strip()
        enlace = (re.findall(r"<link>(.*?)</link>", item, re.S) or [""])[0].strip()
        if enlace and enlace not in vistos:
            vistos.append(enlace)
            if any(p.lower() in titulo.lower() for p in PALABRAS_FED):
                nuevos.append((titulo, enlace))
    del vistos[:-200]
    return nuevos


# ---------------- ciclo ----------------
def ciclo(mt5, est, cfg):
    ahora = datetime.now(timezone.utc)
    hoy = ahora.date().isoformat()
    simbolos = sorted({s for e in cfg["estrategias"].values() if e.get("activa") for s in e["simbolos"]})
    mercados, motivos = {}, []
    for s in simbolos:
        v = leer_velas(s, "D1")
        if not v or len(v[4]) < 80:
            continue
        a = analizar_mercado(*v[:5])
        mercados[s] = a
        if a["volatilidad"] == "extrema":
            motivos.append(f"volatilidad extrema en {s} ({a['atr_ratio']}× su media)")
        clave = f"vol_{s}_{hoy}"
        if a["volatilidad"] in ("alta", "extrema") and clave not in est["avisos"]:
            est["avisos"][clave] = 1
            enviar(f"🌪️ Volatilidad {a['volatilidad']} en {s}: ATR {a['atr_ratio']}× su media de 60 días. Régimen: {a['regimen']}.", "Vigía")

    vix = None
    if mt5 is not None:
        try:
            q = mt5.symbol_info_tick("VIX.fs")
            vix = round((q.bid + q.ask) / 2, 2) if q else None
        except Exception:
            vix = None
        # condiciones de cuenta: pérdidas del día por estrategia y caída diaria
        try:
            desde = datetime.combine(ahora.date(), datetime.min.time())
            deals = mt5.history_deals_get(desde, datetime.now() + timedelta(days=1)) or []
            perdedoras = {d.magic for d in deals if d.entry == mt5.DEAL_ENTRY_OUT and d.profit + d.swap < 0}
            if len(perdedoras) >= 3:
                motivos.append(f"{len(perdedoras)} estrategias cerraron en pérdida hoy")
            info = mt5.account_info()
            if est.get("dia") != hoy:
                est["dia"], est["equity_inicio"] = hoy, info.equity
            if info.equity <= est["equity_inicio"] * 0.98:
                motivos.append(f"la cuenta cae {info.equity / est['equity_inicio'] - 1:.1%} hoy")
        except Exception:
            pass

    # modo precaución (revisión profunda)
    antes = est.get("modo_precaucion", False)
    if motivos and not antes:
        est.update({"modo_precaucion": True, "desde": ahora.isoformat(), "motivos": motivos})
        enviar("🧯 REVISIÓN PROFUNDA activada → Aurum arriesga la MITAD por operación.\nMotivos:\n• " + "\n• ".join(motivos)
               + "\nRevísalo con Claude. Se desactiva solo mañana si ya no se cumple ninguna condición.", "Vigía")
    elif antes and not motivos and est.get("desde", "")[:10] != hoy:
        est.update({"modo_precaucion": False, "motivos": []})
        enviar("✅ Modo precaución desactivado: las condiciones volvieron a la normalidad.", "Vigía")

    # noticias y Fed
    ev, err = noticias_24h(cfg)
    if ev is not None and est.get("resumen_noticias") != hoy and ahora.hour >= 12:
        est["resumen_noticias"] = hoy
        lista = "\n".join(f"• {(c - timedelta(hours=6)):%a %H:%M} MTY — {t} (pronóstico {f or '—'}, anterior {p or '—'})" for c, t, f, p in ev)
        enviar(f"📰 Noticias de alto impacto (USD) en las próximas 24 h:\n{lista or '• Ninguna'}", "Vigía")
    for titulo, enlace in comunicados_fed(est.setdefault("fed_vistos", [])):
        enviar(f"🏛️ Nuevo comunicado de la Fed: {titulo}\n{enlace}", "Cazanoticias")

    est.update({"actualizado": ahora.isoformat(), "mercados": mercados, "vix": vix})
    with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, indent=2, ensure_ascii=False)
    lineas = [f"# Vigía — {ahora:%Y-%m-%d %H:%M} UTC", f"Modo precaución: **{'SÍ' if est.get('modo_precaucion') else 'no'}**"
              + (f" ({'; '.join(est.get('motivos', []))})" if est.get("modo_precaucion") else ""), f"VIX: {vix or '—'}", "",
              "| Mercado | Régimen | ER 20d | Volatilidad | ATR vs media | Tendencia 20d |", "|---|---|---|---|---|---|"]
    lineas += [f"| {s} | {a['regimen']} | {a['er']} | {a['volatilidad']} | {a['atr_ratio']}× | {a['tendencia_20d']} |" for s, a in mercados.items()]
    if ev:
        lineas += ["", "## Noticias próximas 24 h"] + [f"- {(c - timedelta(hours=6)):%a %H:%M} MTY — {t}" for c, t, _, _ in ev]
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))


def main():
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            mt5 = None
    except ImportError:
        mt5 = None
    est = cargar(RUTA_ESTADO, {"avisos": {}})
    est.setdefault("avisos", {})
    if "--una-vez" not in sys.argv:
        enviar("🔭 Vigía activo: régimen, volatilidad, noticias y comunicados de la Fed.", "Vigía")
    while True:
        try:
            ciclo(mt5, est, cargar(RUTA_CONFIG, {}))
        except Exception as e:
            print(f"Vigía: error (sigo): {e!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(900)


if __name__ == "__main__":
    main()
