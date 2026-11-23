#!/bin/bash
# uso: RIESGO=0.02 ABIERTO=0.06 ./variante.sh NOMBRE PAR(0/1) RESERVA(0/1) LAB(0/1)
S=/tmp/claude-0/-home-user/67e7c150-c6ee-5649-9149-3f01503f0718/scratchpad
D=$S/sim/v_$1; rm -rf $D && mkdir -p $D && cp $S/sim/*.py $D/ && cp -r /home/user/aurum $D/equipo && rm -rf $D/equipo/__pycache__ && cp $S/aurumtest2/datos.db $D/equipo/datos.db
python3 - "$S/div/datos.db" "$D/equipo/datos.db" <<'P'
import sqlite3, sys
a = sqlite3.connect(sys.argv[2]); a.execute("attach ? as d", (sys.argv[1],))
a.execute("insert or replace into velas select * from d.velas where not (simbolo='XAUUSD')"); a.commit()
P
python3 - "$D/equipo/aurum_config.json" "$2" "$3" "$4" <<'P'
import json, os, sys
f, par, res, lab = sys.argv[1], sys.argv[2] == "1", sys.argv[3] == "1", sys.argv[4] == "1"
c = json.load(open(f, encoding="utf-8"))
c.pop("grupos_riesgo", None)
c["estrategias"]["par_ratio"]["activa"] = par
if res:
    c["reservas_riesgo"] = {"ruptura_asiatica": 0.01}
else:
    c.pop("reservas_riesgo", None)
for k, e in c["estrategias"].items():
    if "familia_lab" in e:
        e["activa"] = lab
if os.environ.get("RIESGO"):
    c["riesgo_por_operacion"] = float(os.environ["RIESGO"])
    if res:
        c["reservas_riesgo"] = {"ruptura_asiatica": float(os.environ["RIESGO"])}
if os.environ.get("ABIERTO"):
    c["riesgo_abierto_max"] = float(os.environ["ABIERTO"])
c["perdida_diaria_max"] = float(os.environ.get("DIARIA", c["perdida_diaria_max"]))
json.dump(c, open(f, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
P
cd $D && PYTHONHASHSEED=0 python3 correr_base.py 2>&1 | grep RESULTADO | sed "s/^/[$1 riesgo=${RIESGO:-0.01} abierto=${ABIERTO:-0.03} par=$2 res=$3 lab=$4] /"
