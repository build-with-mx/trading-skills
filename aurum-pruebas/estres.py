exec(open("prueba_general.py").read().split("import sqlite3\nfrom datetime")[0])  # corre la simulación completa primero
import os
from collections import Counter
MENSAJES.clear()
time.time = lambda: maestra.T
print("=== ESTRÉS 1: alguien abre 5 lotes de oro SIN stop loss ===")
r = maestra.order_send({"action": 1, "symbol": "XAUUSD", "volume": 5.0, "type": 0, "magic": 0, "comment": "manual"})
guardian.paso(maestra.account_info(), cfg, {"caida_maxima": 0.10}, g_est)
p = maestra.pos[r.order]; print("SL puesto por el Guardián:", p.sl, "| riesgo ≈ $%.0f" % ((p.price_open - p.sl) * 100 * 5))
auditor.ciclo(maestra, {})
print("=== ESTRÉS 2: la cuenta cae 11% desde su máximo ===")
maestra.balance -= 0.11 * g_est["pico_equity"]
guardian.paso(maestra.account_info(), cfg, {"caida_maxima": 0.10}, g_est)
print("Bloqueo:", open("aurum_ALTO.flag").read()[:80], "| posiciones abiertas:", len(maestra.pos))
antes = len(maestra.deals)
for T in pasos[-1:]:
    bot.ciclo()
print("Aurum abrió algo estando bloqueado?:", len([d for d in maestra.deals[antes:] if d.entry == 0]) > 0)
print("=== ESTRÉS 3: alguien sube el riesgo al 5% en la configuración ===")
c2 = json.load(open("aurum_config.json")); c2["riesgo_por_operacion"] = 0.05; json.dump(c2, open("aurum_config.json", "w"))
auditor.ciclo(maestra, {})
print("=== ESTRÉS 4: Algo Trading apagado y un bot congelado ===")
maestra.trade_allowed = False
time.time = real_time
os.utime("vigia_estado.json", (real_time() - 7200,) * 2) if os.path.exists("vigia_estado.json") else open("vigia_estado.json", "w").write("{}") or os.utime("vigia_estado.json", (real_time() - 7200,) * 2)
mecanico.ciclo(maestra, {}, cfg)
print("=== Mensajes que te llegarían ===")
for o, t in MENSAJES:
    print(f"[{o}] {t[:230]}".replace("\n", " | "))
