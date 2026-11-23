"""
MECÁNICO — revisa cada 2 minutos que todo el equipo esté vivo y que MetaTrader pueda operar.
  • Latidos: cada bot deja un archivo que se actualiza solo; si alguno deja de actualizarse más de lo normal → aviso
    (un bot "colgado" no se reinicia solo: el .bat solo reinicia los que se cierran).
  • MetaTrader: conectado, botón "Algo Trading" encendido, cuenta correcta, sin errores de trading en el registro.
  • Disco: avisa si quedan menos de 2 GB.
  • Te manda un "todo en orden" cada día a las 13:00 UTC (7 am Monterrey) para que sepas que sigue vivo.
Escribe mecanico_estado.json (lo usa el Panel).
Ejecutar:  python mecanico.py      (o  python mecanico.py --una-vez)
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_CONFIG = os.path.join(CARPETA, "aurum_config.json")
RUTA_ESTADO = os.path.join(CARPETA, "mecanico_estado.json")

# archivo que cada bot actualiza y cuántos minutos puede tardar como máximo
LATIDOS = {
    "Aurum": ("aurum_estado.json", 5),
    "Guardián": ("guardian_latido.txt", 3),
    "Vigía": ("vigia_estado.json", 40),
    "Contador": ("contador_reporte.md", 130),
    "Minero": ("datos.db", 7 * 60),
    "Sombra": ("sombra_reporte.md", 130),
    "Estratega de metas": ("metas_estado.json", 130),
    "Auditor": ("auditor_reporte.md", 130),
    "Panel": ("panel.html", 5),
}


def cargar(ruta, defecto):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return defecto


# ---------------- lógica pura ----------------
def revisar_latidos(ahora_ts, mtimes, latidos=LATIDOS):
    """mtimes: {archivo: timestamp o None}. Devuelve {bot: (estado, minutos)}; estado ∈ ok / atrasado / sin_datos."""
    res = {}
    for bot, (archivo, maximo) in latidos.items():
        t = mtimes.get(archivo)
        if t is None:
            res[bot] = ("sin_datos", None)
        else:
            mins = (ahora_ts - t) / 60
            res[bot] = ("ok" if mins <= maximo else "atrasado", round(mins, 1))
    return res


def problemas_nuevos(antes, ahora):
    """Solo avisa de cambios (para no llenarte el Telegram): devuelve (caidos, recuperados)."""
    caidos = [b for b, (e, _) in ahora.items() if e == "atrasado" and antes.get(b, ["ok"])[0] != "atrasado"]
    recuperados = [b for b, (e, _) in ahora.items() if e == "ok" and antes.get(b, ["ok"])[0] == "atrasado"]
    return caidos, recuperados


# ---------------- ciclo ----------------
def ciclo(mt5, est, cfg):
    ahora = datetime.now(timezone.utc)
    mtimes = {}
    for archivo, _ in LATIDOS.values():
        r = os.path.join(CARPETA, archivo)
        mtimes[archivo] = os.path.getmtime(r) if os.path.exists(r) else None
    # bots copiadores: copiador_<nombre>_estado.json (se actualiza cada 2 s)
    latidos = dict(LATIDOS)
    for f in os.listdir(CARPETA):
        if f.startswith("copiador_") and f.endswith("_estado.json"):
            latidos[f"Copiador {f[9:-12]}"] = (f, 3)
            mtimes[f] = os.path.getmtime(os.path.join(CARPETA, f))
    res = revisar_latidos(time.time(), mtimes, latidos)
    caidos, recuperados = problemas_nuevos(est.get("bots", {}), res)
    for b in caidos:
        enviar(f"🔧 {b} no da señales de vida desde hace {res[b][1]:.0f} min. Revisa su ventana: si está congelada, ciérrala (se reinicia sola).", "Mecánico")
    for b in recuperados:
        enviar(f"🔧✅ {b} volvió a funcionar.", "Mecánico")

    alertas = []
    if mt5 is not None:
        try:
            term, cuenta = mt5.terminal_info(), mt5.account_info()
            if term is None or not term.connected:
                alertas.append("MetaTrader sin conexión al servidor")
            elif not term.trade_allowed:
                alertas.append("el botón «Algo Trading» está APAGADO: Aurum no puede operar")
            if cuenta and cuenta.login != cfg.get("cuenta_permitida"):
                alertas.append(f"MetaTrader tiene abierta la cuenta {cuenta.login}, no la {cfg.get('cuenta_permitida')}")
        except Exception as e:
            alertas.append(f"no pude consultar MetaTrader ({e!r}"[:80] + ")")
    libre_gb = shutil.disk_usage(CARPETA).free / 1e9
    if libre_gb < 2:
        alertas.append(f"queda poco disco: {libre_gb:.1f} GB")
    nuevas = [a for a in alertas if a not in est.get("alertas", [])]
    if nuevas:
        enviar("🔧⚠️ " + "\n⚠️ ".join(nuevas), "Mecánico")

    hoy = ahora.date().isoformat()
    if ahora.hour >= 13 and est.get("parte_diario") != hoy:
        est["parte_diario"] = hoy
        ok = sum(1 for e, _ in res.values() if e == "ok")
        enviar(f"🔧 Parte diario: {ok}/{len(res)} bots con latido normal. "
               + ("Sin alertas." if not alertas else "Alertas: " + "; ".join(alertas)), "Mecánico")
    est.update({"actualizado": ahora.isoformat(), "bots": res, "alertas": alertas, "disco_gb": round(libre_gb, 1)})
    with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, indent=2, ensure_ascii=False)


def main():
    try:
        import MetaTrader5 as mt5
        if not mt5.initialize():
            mt5 = None
    except ImportError:
        mt5 = None
    est = cargar(RUTA_ESTADO, {})
    if "--una-vez" not in sys.argv:
        enviar("🔧 Mecánico activo: reviso cada 2 minutos que todos los bots y MetaTrader funcionen.", "Mecánico")
    while True:
        try:
            ciclo(mt5, est, cargar(RUTA_CONFIG, {}))
        except Exception as e:
            print(f"Mecánico: error (sigo): {e!r}"[:200])
        if "--una-vez" in sys.argv:
            return
        time.sleep(120)


if __name__ == "__main__":
    main()
