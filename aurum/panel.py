"""
PANEL — tablero para ver todo el equipo de un vistazo. Cada minuto genera panel.html (ábrelo con doble clic en tu
navegador; se actualiza solo). No necesita internet ni instalar nada.
Muestra: cuenta y posiciones abiertas, resultado por estrategia (Contador), metas y probabilidad (Estratega),
mercados y modo precaución (Vigía), salud de los bots (Mecánico), bloqueos (Guardián/Supervisor), candidatas
(Explorador/Sombra), auditoría y últimas operaciones.
Ejecutar:  python panel.py      (o  python panel.py --una-vez)
"""
import html
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_PANEL = os.path.join(CARPETA, "panel.html")


def cargar(nombre, defecto):
    try:
        with open(os.path.join(CARPETA, nombre), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


def e(x):
    return html.escape(str(x))


def tabla(cabecera, filas, vacio="Sin datos todavía"):
    if not filas:
        return f'<p class="vacio">{e(vacio)}</p>'
    th = "".join(f"<th>{e(c)}</th>" for c in cabecera)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas)
    return f'<div class="scroll"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'


def color(v, fmt="{:+,.2f}"):
    try:
        cls = "pos" if float(v) > 0 else "neg" if float(v) < 0 else ""
        return f'<span class="{cls}">{e(fmt.format(float(v)))}</span>'
    except Exception:
        return e(v)


def estadisticas_db():
    ruta = os.path.join(CARPETA, "aurum.db")
    if not os.path.exists(ruta):
        return [], []
    try:
        con = sqlite3.connect(ruta)
        por = con.execute("""SELECT estrategia, COUNT(*), SUM(neto), AVG(R), SUM(CASE WHEN neto > 0 THEN 1 ELSE 0 END)
                             FROM operaciones GROUP BY estrategia ORDER BY SUM(neto) DESC""").fetchall()
        ult = con.execute("SELECT cerrada, estrategia, simbolo, direccion, lote, neto, R FROM operaciones ORDER BY cerrada DESC LIMIT 12").fetchall()
        con.close()
        return por, ult
    except Exception:
        return [], []


def generar(cuenta=None, posiciones=None):
    ahora = datetime.now(timezone.utc)
    mec, vig, met = cargar("mecanico_estado.json", {}), cargar("vigia_estado.json", {}), cargar("metas_estado.json", {})
    cand, aud = cargar("candidatos.json", []), cargar("auditor_estado.json", {})
    bloqueo = open(os.path.join(CARPETA, "aurum_ALTO.flag"), encoding="utf-8").read() if os.path.exists(os.path.join(CARPETA, "aurum_ALTO.flag")) else ""
    por, ult = estadisticas_db()

    tarjetas = []
    if cuenta:
        tarjetas += [("Balance", f"${cuenta['balance']:,.2f}"), ("Equity", f"${cuenta['equity']:,.2f}"),
                     ("Flotante", color(cuenta["equity"] - cuenta["balance"]))]
    if met:
        tarjetas += [("Progreso a la meta", f"{max(0, met.get('progreso', 0)):.0%}"),
                     ("Prob. de lograrla", f"{met.get('prob_objetivo', 0):.0%}"),
                     ("Factor de riesgo", f"×{met.get('factor_riesgo', 1):g}")]
    tarjetas.append(("Modo precaución", "SÍ" if vig.get("modo_precaucion") else "no"))
    tarjetas.append(("Bloqueo", e(bloqueo.split(":")[0]) if bloqueo else "ninguno"))
    tarjetas.append(("Pausa manual", "SÍ" if os.path.exists(os.path.join(CARPETA, "aurum_PAUSA.flag")) else "no"))
    html_tarjetas = "".join(f'<div class="tarjeta"><div class="et">{e(k)}</div><div class="v">{v}</div></div>' for k, v in tarjetas)

    pos = tabla(["Símbolo", "Dirección", "Lote", "Entrada", "SL", "TP", "Resultado"],
                [[e(p["simbolo"]), e(p["dir"]), e(p["lote"]), e(p["entrada"]), e(p["sl"] or "⚠️ sin SL"), e(p["tp"] or "—"), color(p["res"])]
                 for p in (posiciones or [])], "Sin posiciones abiertas")
    estr = tabla(["Estrategia", "Ops", "Acierto", "R medio", "Neto $"],
                 [[e(n), e(c), f"{(g or 0) / c:.0%}", color(r or 0, "{:+.2f}R"), color(s or 0)] for n, c, s, r, g in por])
    ults = tabla(["Cerrada", "Estrategia", "Símbolo", "Dir.", "Lote", "Neto $", "R"],
                 [[e(str(c)[:16]), e(n), e(s), e(d), e(l), color(x or 0), color(r or 0, "{:+.2f}")] for c, n, s, d, l, x, r in ult])
    bots = tabla(["Bot", "Estado", "Último latido (min)"],
                 [[e(b), {"ok": "🟢 ok", "atrasado": "🔴 atrasado", "sin_datos": "⚪ sin datos"}.get(st, st), e(m if m is not None else "—")]
                  for b, (st, m) in mec.get("bots", {}).items()], "El Mecánico aún no reporta")
    merc = tabla(["Mercado", "Régimen", "Volatilidad", "ATR/media", "Tendencia 20d"],
                 [[e(s), e(a["regimen"]), e(a["volatilidad"]), e(a["atr_ratio"]), e(a["tendencia_20d"])] for s, a in vig.get("mercados", {}).items()])
    cands = tabla(["Candidata", "Estado", "Ops papel", "Exp. papel", "Exp. backtest"],
                  [[e(f"{c['familia']} {c['simbolo']} {c['tf']}"), e(c.get("estado")), e(c.get("papel_ops", 0)),
                    color(c.get("papel_exp", 0), "{:+.2f}R"), color(c.get("exp_oos", 0), "{:+.2f}R")] for c in cand[:20]])
    alertas = (mec.get("alertas") or []) + (aud.get("hallazgos") or [])
    html_alertas = "".join(f'<div class="alerta">⚠️ {e(a)}</div>' for a in alertas)

    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="60"><title>Panel Aurum</title><style>
:root{{--bg:#f6f7f9;--card:#fff;--txt:#1b1f24;--sub:#5f6b7a;--borde:#e3e6ea;--pos:#0a7d43;--neg:#c0392b;--acento:#b8860b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111418;--card:#1a1f25;--txt:#e8ebef;--sub:#97a3b0;--borde:#2a3139;--pos:#3ccf7e;--neg:#ff6b5e;--acento:#e0b84a}}}}
body{{margin:0;background:var(--bg);color:var(--txt);font:14px/1.45 system-ui,Segoe UI,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:16px}} h1{{font-size:22px;margin:4px 0}} h1 b{{color:var(--acento)}}
h2{{font-size:15px;margin:22px 0 8px;color:var(--sub);text-transform:uppercase;letter-spacing:.04em}}
.sub{{color:var(--sub);font-size:12px}} .tarjetas{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;margin-top:12px}}
.tarjeta{{background:var(--card);border:1px solid var(--borde);border-radius:10px;padding:10px 12px}} .et{{color:var(--sub);font-size:12px}} .v{{font-size:19px;font-weight:600;margin-top:2px}}
.scroll{{overflow-x:auto;background:var(--card);border:1px solid var(--borde);border-radius:10px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}} th,td{{padding:7px 10px;text-align:left;border-bottom:1px solid var(--borde);white-space:nowrap}}
th{{color:var(--sub);font-weight:600;font-size:12px}} tr:last-child td{{border-bottom:0}} .pos{{color:var(--pos)}} .neg{{color:var(--neg)}}
.vacio{{color:var(--sub)}} .alerta{{background:var(--card);border:1px solid var(--neg);border-radius:8px;padding:8px 10px;margin:6px 0}}
.dos{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} @media (max-width:760px){{.dos{{grid-template-columns:1fr}}}}
</style></head><body><main>
<h1><b>Aurum</b> · panel del equipo</h1><div class="sub">Actualizado {ahora:%Y-%m-%d %H:%M} UTC · se refresca cada minuto</div>
{html_alertas}<div class="tarjetas">{html_tarjetas}</div>
<h2>Posiciones abiertas</h2>{pos}
<div class="dos"><div><h2>Resultado por estrategia</h2>{estr}</div><div><h2>Salud de los bots</h2>{bots}</div></div>
<h2>Últimas operaciones</h2>{ults}
<div class="dos"><div><h2>Mercados (Vigía)</h2>{merc}</div><div><h2>Candidatas (Explorador → Sombra)</h2>{cands}</div></div>
</main></body></html>"""
    tmp = RUTA_PANEL + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(pagina)
    os.replace(tmp, RUTA_PANEL)


def datos_mt5(mt5):
    if mt5 is None:
        return None, None
    try:
        a = mt5.account_info()
        cuenta = {"balance": a.balance, "equity": a.equity}
        pos = [{"simbolo": p.symbol, "dir": "COMPRA" if p.type == 0 else "VENTA", "lote": p.volume, "entrada": p.price_open,
                "sl": p.sl, "tp": p.tp, "res": p.profit + p.swap} for p in mt5.positions_get() or []]
        return cuenta, pos
    except Exception:
        return None, None


def main():
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            mt5 = None
    except ImportError:
        mt5 = None
    while True:
        try:
            generar(*datos_mt5(mt5))
        except Exception as ex:
            print(f"Panel: error (sigo): {ex!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(60)


if __name__ == "__main__":
    main()
