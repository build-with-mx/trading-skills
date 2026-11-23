import os, sys
RIESGO = float(sys.argv[1])
src = open("prueba_general.py").read().split("import sqlite3\nfrom datetime")[0]
src = src.replace('cp_cfg.update(activo=True,', f'cp_cfg.update(riesgo_por_operacion={RIESGO}, riesgo_abierto_max={RIESGO * 3}, activo=True,')
src = src.replace("        copia.avanzar(T)\n", "        copia.avanzar(T)\n        CURVA.append(copia.account_info().equity)\n")
CURVA = []
exec(src)
pico, caida = 0, 0
for e in CURVA:
    pico = max(pico, e); caida = max(caida, 1 - e / pico)
ins = len([d for d in copia.deals if d.entry == 0]); tot = len([d for d in maestra.deals if d.entry == 0])
print(f"RIESGO {RIESGO:.1%}: copió {ins}/{tot} | resultado {copia.balance / 5000 - 1:+.1%} en 4 meses | caída máx {caida:.1%}")
