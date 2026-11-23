"""Construye el código de simulación completo (prueba_general + medición de caída) en un solo texto, para poder parchearlo."""
def codigo(caida_guardian=9.9, parches=()):
    src = open("prueba_general.py").read().split("import sqlite3\nfrom datetime")[0]
    src = src.replace("h1[-1] - 120 * 86400", "h1[0] + 30 * 86400")
    src = src.replace('{"caida_maxima": 0.10}', '{"caida_maxima": %s}' % caida_guardian)
    src = src.replace("        maestra.avanzar(T)\n", "        maestra.avanzar(T)\n        CM.append((T, maestra.account_info().equity))\n", 1)
    for a, b in parches:
        assert a in src, a
        src = src.replace(a, b)
    return "CM = []\n" + src + '''
import sqlite3
from datetime import datetime, timezone
pico = CM[0][1]; dd = 0.0
for t, e in CM:
    pico = max(pico, e); dd = max(dd, 1 - e / pico)
con = sqlite3.connect("aurum.db")
OPS = dict(con.execute("select estrategia, count(*) from operaciones group by 1").fetchall())
NETO = dict(con.execute("select estrategia, round(sum(neto)) from operaciones group by 1").fetchall())
print(f"RESULTADO balance ${maestra.balance:,.0f} | caída máx {dd:.1%} | errores {dict(errores) or 0} | ops {OPS} | neto {NETO}")
'''
