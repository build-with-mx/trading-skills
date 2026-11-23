"""
ESTRATEGA DE METAS — mide el avance hacia la meta, estima cuánto falta y PROTEGE lo ganado.
Cada hora:
  • Progreso: cuánto llevas hacia el objetivo y cuánto margen te queda antes del límite de pérdida.
  • Pronóstico (Monte Carlo, 3,000 simulaciones): con los resultados reales en R del Contador (o los del backtest si aún
    hay pocas operaciones) estima la probabilidad de llegar al objetivo antes de tocar el límite y las semanas que faltan.
  • Factor de riesgo (metas_estado.json → lo leen Aurum y el Copiador):
       1.0  normal
       0.5  si ya recorriste el 80% del camino al objetivo (no regalar lo ganado)
       0.5  si ya consumiste el 50% del margen de pérdida (sobrevivir primero)
    NUNCA sube el riesgo por encima de lo configurado: solo lo baja.
  • Te manda el resumen los domingos y cada vez que cambia el factor.
Ejecutar:  python estratega_metas.py                     (cuenta maestra, bloque "metas" de aurum_config.json)
           python estratega_metas.py copiador_fondeo1.json  (cuenta de fondeo, bloque "metas" de ese archivo)
"""
import json
import os
import random
import sqlite3
import statistics as st
import sys
import time
from datetime import datetime, timedelta, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.join(CARPETA, "aurum.db")
# distribución previa CONSERVADORA: el backtest del portafolio da ~+0.2R por operación; en vivo se espera ~la mitad →
# 37% ganadoras de +2R y 63% perdedoras de −1R = +0.11R por operación
PREVIA = [2.0] * 37 + [-1.0] * 63
OPS_SEMANA_PREVIA = 4.0


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


# ---------------- lógica pura (probada sin MT5) ----------------
def factor_riesgo(equity, metas):
    ini, obj, lim = metas["balance_inicial"], metas["objetivo"], metas["limite_perdida"]
    progreso = (equity - ini) / (ini * obj) if obj else 0.0
    consumido = (ini - equity) / (ini * lim) if lim else 0.0
    f, motivo = 1.0, "normal"
    if progreso >= metas.get("proteger_cerca_objetivo", 0.8):
        f, motivo = metas.get("factor_proteccion", 0.5), f"ya llevas {progreso:.0%} del camino: protejo lo ganado"
    elif consumido >= metas.get("proteger_cerca_limite", 0.5):
        f, motivo = metas.get("factor_proteccion", 0.5), f"consumiste {consumido:.0%} del margen de pérdida: primero sobrevivir"
    return min(1.0, f), motivo, progreso, consumido


def pronostico(R, ops_semana, riesgo, equity, ini, objetivo, limite, metas, sims=3000, semanas_max=104, semilla=7):
    """Probabilidad de llegar al objetivo antes del límite y semanas (mediana) hasta lograrlo. Aplica el factor de protección."""
    rnd = random.Random(semilla)
    meta, piso = ini * (1 + objetivo), ini * (1 - limite)
    exitos, semanas = 0, []
    ops_max = int(semanas_max * ops_semana)
    for _ in range(sims):
        eq = equity
        for k in range(ops_max):
            if eq >= meta:
                exitos += 1
                semanas.append(k / ops_semana)
                break
            if eq <= piso:
                break
            f = factor_riesgo(eq, metas)[0]
            eq += eq * riesgo * f * rnd.choice(R)
    return exitos / sims, (st.median(semanas) if semanas else None)


def resultados_reales():
    """(lista de R, operaciones por semana) del Contador. Vacío si aún no hay datos."""
    if not os.path.exists(RUTA_DB):
        return [], None
    try:
        con = sqlite3.connect(RUTA_DB)
        filas = con.execute("SELECT R, cerrada FROM operaciones WHERE R IS NOT NULL ORDER BY cerrada").fetchall()
        con.close()
    except Exception:
        return [], None
    R = [f[0] for f in filas]
    if len(filas) < 2:
        return R, None
    dias = (datetime.fromisoformat(filas[-1][1][:19]) - datetime.fromisoformat(filas[0][1][:19])).days
    return R, (len(filas) / max(1.0, dias / 7)) if dias >= 14 else None


def muestra_R(reales):
    """Mezcla: con menos de 30 operaciones reales, la previa del backtest pesa; luego mandan los datos reales."""
    if len(reales) >= 30:
        return reales
    return reales + PREVIA * max(1, (30 - len(reales)) // len(PREVIA))


# ---------------- ejecución ----------------
def main():
    import MetaTrader5 as mt5
    ruta_cfg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(CARPETA, "aurum_config.json")
    cfg = cargar(ruta_cfg, {})
    metas = cfg.get("metas")
    if not metas or not metas.get("activo"):
        raise SystemExit(f'Sin bloque "metas" activo en {ruta_cfg}.')
    nombre = cfg.get("nombre", "maestra")
    ruta_estado = os.path.join(CARPETA, cfg.get("archivo_metas", "metas_estado.json"))
    ok = mt5.initialize(path=cfg["terminal"]) if cfg.get("terminal") else mt5.initialize()
    if not ok:
        raise SystemExit(f"No conecta con MetaTrader 5: {mt5.last_error()}")
    est = cargar(ruta_estado, {})
    while True:
        try:
            ahora = datetime.now(timezone.utc)
            eq = mt5.account_info().equity
            f, motivo, progreso, consumido = factor_riesgo(eq, metas)
            reales, ops_sem = resultados_reales()
            prob, semanas = pronostico(muestra_R(reales), ops_sem or OPS_SEMANA_PREVIA, cfg["riesgo_por_operacion"], eq,
                                       metas["balance_inicial"], metas["objetivo"], metas["limite_perdida"], metas)
            nuevo = {"actualizado": ahora.isoformat(), "cuenta": nombre, "equity": round(eq, 2), "factor_riesgo": f, "motivo": motivo,
                     "progreso": round(progreso, 3), "margen_consumido": round(max(0.0, consumido), 3),
                     "prob_objetivo": round(prob, 3), "semanas_estimadas": round(semanas, 1) if semanas is not None else None,
                     "ops_reales": len(reales), "resumen_enviado": est.get("resumen_enviado")}
            texto = (f"🎯 Metas [{nombre}]: equity ${eq:,.0f} · progreso {max(0, progreso):.0%} hacia +{metas['objetivo']:.0%} · "
                     f"margen de pérdida usado {max(0.0, consumido):.0%}\nProbabilidad de lograrlo: {prob:.0%} · "
                     f"tiempo estimado: {f'{semanas:.0f} semanas' if semanas is not None else 'no se alcanza en 2 años con este ritmo'}"
                     f"\nFactor de riesgo: {f:g} ({motivo})" + ("" if len(reales) >= 30 else f"\n(con {len(reales)} operaciones reales: el pronóstico aún usa el backtest)"))
            if est.get("factor_riesgo") is not None and est["factor_riesgo"] != f:
                enviar(("🛡️ Bajo el riesgo a la mitad. " if f < 1 else "✅ Riesgo normal otra vez. ") + texto, "Estratega de metas")
            if ahora.weekday() == 6 and est.get("resumen_enviado") != ahora.date().isoformat():
                nuevo["resumen_enviado"] = ahora.date().isoformat()
                enviar(texto, "Estratega de metas")
            est = nuevo
            with open(ruta_estado, "w", encoding="utf-8") as fh:
                json.dump(est, fh, indent=2, ensure_ascii=False)
            print(texto)
        except Exception as e:
            print(f"Estratega: error (sigo): {e!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(3600)


if __name__ == "__main__":
    main()
