"""
SOMBRA (Validador) — practica en papel, en vivo, las estrategias candidatas del Explorador. Sin dinero.
Cada hora recalcula cada candidata con las velas más recientes (datos.db) y cuenta solo las operaciones que empezaron
DESPUÉS de su alta: es una prueba hacia adelante real, con datos que no existían cuando se eligió.
Reglas de paso:
  • >= 20 operaciones (o >= 10 y 90 días, para estrategias diarias lentas), expectativa > 0 y >= 50% de la del backtest
    → "aprobada_papel" (te avisa: lista para la demo)
  • >= 20 operaciones y expectativa <= 0                                     → "descartada_papel"
Ninguna candidata se opera con dinero sin que tú (con Claude) la agregues a la configuración de Aurum.
Ejecutar:  python sombra.py      (o  python sombra.py --una-vez)
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import lab_motor as L
from minero import leer_velas
from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CAND = os.path.join(CARPETA, "candidatos.json")
RUTA_REPORTE = os.path.join(CARPETA, "sombra_reporte.md")
MIN_OPS = 20          # aprobación normal
MIN_OPS_TEMPRANA = 10 # aprobación temprana para estrategias lentas (diarias): >= 10 ops y >= 90 días en papel
DIAS_TEMPRANA = 90


def evaluar_candidata(c):
    """Devuelve las operaciones en papel (entrada posterior al alta) de una candidata. Función pura salvo la lectura de datos."""
    v = leer_velas(c["simbolo"], c["tf"])
    if not v:
        return None
    t, o, h, l, cl, costo = v
    m = L.M(t, o, h, l, cl, costo)
    if c["tf"] == "H1":
        m.a = L.atr(h, l, cl, 14)
    ops = L.evaluar(m, "h1" if c["tf"] == "H1" else "d1", c["familia"], tuple(c["params"]))
    alta = datetime.fromisoformat(c["fecha_alta"]).replace(tzinfo=None)
    papel = [(f, r) for f, r in ops if f >= alta]
    return papel[:-1] if papel else papel  # la última puede seguir abierta: no se cuenta


def ciclo():
    if not os.path.exists(RUTA_CAND):
        return
    cand = json.load(open(RUTA_CAND, encoding="utf-8"))
    lineas = [f"# Sombra — práctica en papel ({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC)", "",
              "| Candidata | Estado | Ops papel | Expectativa papel | Expectativa backtest (OOS) |", "|---|---|---|---|---|"]
    cambios = False
    for c in cand:
        if c.get("estado") not in ("sombra", "aprobada_papel", "descartada_papel"):
            continue
        papel = evaluar_candidata(c)
        if papel is None:
            continue
        n = len(papel)
        exp = sum(r for _, r in papel) / n if n else 0.0
        c.update({"papel_ops": n, "papel_exp": round(exp, 3), "papel_actualizado": datetime.now(timezone.utc).isoformat()})
        dias = (datetime.now(timezone.utc) - datetime.fromisoformat(c["fecha_alta"])).days
        listo = n >= MIN_OPS or (n >= MIN_OPS_TEMPRANA and dias >= DIAS_TEMPRANA)
        if c["estado"] == "sombra" and listo:
            if exp > 0 and exp >= 0.5 * c["exp_oos"]:
                c["estado"] = "aprobada_papel"
                enviar(f"🎓 {c['familia']} en {c['simbolo']} ({c['tf']}) APROBÓ la práctica en papel: {n} ops, {exp:+.2f}R por operación "
                       f"(backtest {c['exp_oos']:+.2f}R). Lista para la demo: pídele a Claude que la agregue a Aurum."
                       + ("" if c.get("diversifica", True) else "\n⚠️ Ojo: es la misma ventaja que una estrategia ya activa en ese mercado; sumarla concentra riesgo."), "Sombra")
            elif exp <= 0:
                c["estado"] = "descartada_papel"
                enviar(f"🗑️ {c['familia']} en {c['simbolo']} ({c['tf']}) falló en papel: {n} ops, {exp:+.2f}R. Descartada.", "Sombra")
            cambios = True
        lineas.append(f"| {c['familia']} {c['simbolo']} {c['tf']} | {c['estado']} | {n} | {exp:+.2f}R | {c['exp_oos']:+.2f}R |")
    json.dump(cand, open(RUTA_CAND, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    return cambios


def main():
    if "--una-vez" not in sys.argv:
        enviar("👻 Sombra activa: practico en papel las candidatas del Explorador.", "Sombra")
    while True:
        try:
            ciclo()
        except Exception as e:
            print(f"Sombra: error (sigo): {e!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(3600)


if __name__ == "__main__":
    main()
