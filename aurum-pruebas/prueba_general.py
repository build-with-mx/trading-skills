"""Prueba general: todo el equipo Aurum operando ~4 meses de velas reales contra un broker simulado (maestra + copia)."""
import contextlib
import io
import json
import os
import sys
import time
from collections import Counter

AQUI = os.path.dirname(os.path.abspath(__file__))
EQ = os.path.join(AQUI, "equipo")
sys.path.insert(0, AQUI)
import broker_simulado as bs

for k, v in vars(bs).items():
    if k.isupper():
        setattr(bs.Broker, k, v)
DB = os.path.join(EQ, "datos.db")
maestra = bs.Broker(DB, 10076749, 100000.0)
copia = bs.Broker(DB, 555, 5000.0)
sys.modules["MetaTrader5"] = maestra
os.chdir(EQ)
sys.path.insert(0, EQ)

MENSAJES = []
import mensajero
mensajero.enviar = lambda texto, origen="Aurum": MENSAJES.append((origen, texto))

cfg = json.load(open("aurum_config.json", encoding="utf-8"))
cfg["filtro_noticias"]["activo"] = False  # sin internet en la prueba
json.dump(cfg, open("aurum_config.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
cp_cfg = json.load(open("copiador_ejemplo.json", encoding="utf-8"))
cp_cfg.update(activo=True, cuenta=555, terminal="", mapa_simbolos={})
json.dump(cp_cfg, open("copiador_fondeo1.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

import aurum, guardian, contador, archivista, auditor, panel, mecanico, estratega_metas, profesor, copiador

real_time = time.time
time.time = lambda: maestra.T  # el reloj de los bots es el de la simulación

bot = aurum.Aurum()
bot.conectar()
bot.adoptar_posiciones()
cp = copiador.Copiador("copiador_fondeo1.json")
cp.mt5 = copia
cp.est["byte"] = 0
g_est = {"pico_equity": 100000.0, "dia": "", "balance_inicio_dia": 100000.0, "avisos": {}}

h1 = [b[0] for b in maestra.data[("XAUUSD", "H1")]]
inicio, fin = h1[-1] - 120 * 86400, h1[-1] + 3600
pasos = [t + 3600 for t in h1 if inicio <= t]  # cada vez que cierra una vela H1
errores = Counter()
dia_ant = None
salida = io.StringIO()
t0 = real_time()
with contextlib.redirect_stdout(salida):
    for i, T in enumerate(pasos):
        maestra.avanzar(T)
        copia.avanzar(T)
        dia = T // 86400
        if dia != dia_ant:
            dia_ant = dia
            g_est["dia"], g_est["balance_inicio_dia"] = "", maestra.balance
        for nombre, f in (("aurum", bot.ciclo), ("guardian", lambda: guardian.paso(maestra.account_info(), cfg, {"caida_maxima": 0.10}, g_est)),
                          ("copiador", cp.ciclo)):
            try:
                f()
            except Exception as e:
                errores[f"{nombre}: {e!r}"[:160]] += 1
        if i % 24 == 0:
            for nombre, f in (("autocontrol", bot.revisar_autocontrol), ("contador", lambda: contador.ciclo(maestra, False)),
                              ("archivista", lambda: archivista.ciclo(json.load(open("archivista_estado.json")) if os.path.exists("archivista_estado.json") else {"byte": 0})),
                              ("auditor", lambda: auditor.ciclo(maestra, {})), ("panel", lambda: panel.generar(*panel.datos_mt5(maestra)))):
                try:
                    f()
                except Exception as e:
                    errores[f"{nombre}: {e!r}"[:160]] += 1
    time.time = real_time
    for nombre, f in (("contador", lambda: contador.ciclo(maestra, False)), ("archivista", lambda: archivista.ciclo({"byte": 0})),
                      ("profesor", profesor.estudiar), ("mecanico", lambda: mecanico.ciclo(maestra, {}, cfg)),
                      ("panel", lambda: panel.generar(*panel.datos_mt5(maestra)))):
        try:
            f()
        except Exception as e:
            errores[f"{nombre} (final): {e!r}"[:160]] += 1

import sqlite3
from datetime import datetime, timezone
print(f"Simulé {len(pasos)} horas ({datetime.fromtimestamp(pasos[0], timezone.utc):%Y-%m-%d} a {datetime.fromtimestamp(pasos[-1], timezone.utc):%Y-%m-%d}) en {real_time() - t0:.0f} s")
print(f"MAESTRA: balance ${maestra.balance:,.2f} | abiertas {len(maestra.pos)} | deals {len(maestra.deals)}")
print(f"COPIA:   balance ${copia.balance:,.2f} | abiertas {len(copia.pos)} | deals {len(copia.deals)}")
con = sqlite3.connect("aurum.db")
for fila in con.execute("SELECT estrategia, simbolo, COUNT(*), ROUND(SUM(neto),2), ROUND(AVG(R),2) FROM operaciones GROUP BY 1,2"):
    print("  Contador:", fila)
print("  Contexto (Archivista):", con.execute("SELECT COUNT(*) FROM contexto").fetchone()[0], "registros")
con.close()
print("ERRORES:", dict(errores) or "ninguno")
print("Mensajes por bot:", dict(Counter(o for o, _ in MENSAJES)))
for o, t in MENSAJES[:6] + MENSAJES[-6:]:
    print(f"  [{o}] {t[:150]}".replace("\n", " | "))
print("Riesgo de cada apertura (CSV):")
import csv
for r in list(csv.DictReader(open("aurum_operaciones.csv", encoding="utf-8")))[:8]:
    print("  ", r["accion"], r["estrategia"], r["simbolo"], r["lote"], r["riesgo_usd"], r["resultado_usd"], r["motivo"][:60])
open(os.path.join(AQUI, "salida_bots.txt"), "w").write(salida.getvalue())

# --- fidelidad del Copiador: cada copia frente a su original ---
ins_m = {d.time: d for d in maestra.deals if d.entry == 0}
ins_c = [d for d in copia.deals if d.entry == 0]
dif = [(abs(d.price - ins_m[d.time].price), d.type == ins_m[d.time].type) for d in ins_c if d.time in ins_m]
print(f"Copias con original a la misma hora: {len(dif)}/{len(ins_c)} | misma dirección: {sum(1 for _, ok in dif if ok)} | máx. diferencia de precio: {max(x for x, _ in dif):.2f}")
sin = [d for d in ins_c if d.time not in ins_m]
print("Copias SIN original a la misma hora:", [(d.symbol, d.price, d.time) for d in sin][:5])
huerf = [(d.symbol, d.comment) for d in copia.deals if d.entry == 1 and d.comment not in ("sl", "tp")]
print("Cierres de copias por el Copiador (no por SL/TP):", Counter(c for _, c in huerf))
no_copiadas = len([d for d in maestra.deals if d.entry == 0]) - len(dif)
print("Entradas de la maestra no copiadas:", no_copiadas)
print("Motivos de no copia:", Counter(l.split(": ", 1)[1][:60] for l in salida.getvalue().splitlines() if "No copio" in l))
