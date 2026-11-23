"""
ANALISTA DE POSICIONAMIENTO (COT) — lee cada semana el informe Commitments of Traders de la CFTC (gobierno de EE.UU.,
datos públicos y gratuitos) y mide cómo están posicionados los especuladores grandes en oro, plata, petróleo, índices,
bitcoin y divisas.
  • Posición neta de los especuladores (no comerciales) y su percentil frente a los últimos 3 años.
  • Percentil >= 90 → "posicionamiento extremo comprador" (muchos ya compraron: riesgo de giro a la baja);
    <= 10 → "extremo vendedor". Es contexto, no una señal de entrada: Aurum no lo usa para operar.
  • Cambio semanal fuerte (> 2 desviaciones) → aviso.
El informe sale los viernes con datos del martes. El bot revisa los sábados 12:00 UTC.
Escribe cot_reporte.md y cot_estado.json.
Ejecutar:  python analista_cot.py      (o  python analista_cot.py --ahora)
"""
import json
import os
import statistics as st
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA_REPORTE = os.path.join(CARPETA, "cot_reporte.md")
RUTA_ESTADO = os.path.join(CARPETA, "cot_estado.json")
URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"  # Legacy, solo futuros
# mercado Axi → texto con el que empieza el nombre del contrato en la CFTC
MERCADOS = {"XAUUSD": "GOLD - COMMODITY EXCHANGE", "XAGUSD": "SILVER - COMMODITY EXCHANGE",
            "USOIL": "CRUDE OIL, LIGHT SWEET - NEW YORK MERCANTILE", "US500": "E-MINI S&P 500 - CHICAGO MERCANTILE",
            "USTECH": "NASDAQ MINI - CHICAGO MERCANTILE", "BTCUSD": "BITCOIN - CHICAGO MERCANTILE",
            "EURUSD": "EURO FX - CHICAGO MERCANTILE", "USDJPY": "JAPANESE YEN - CHICAGO MERCANTILE",
            "GBPUSD": "BRITISH POUND - CHICAGO MERCANTILE"}
INVERTIDO = {"USDJPY"}  # el contrato es yen/dólar: comprar yen = vender USDJPY


def descargar(nombre, semanas=160):
    q = {"$where": f"market_and_exchange_names like '{nombre}%'", "$order": "report_date_as_yyyy_mm_dd DESC", "$limit": str(semanas)}
    req = urllib.request.Request(URL + "?" + urllib.parse.urlencode(q), headers={"User-Agent": "aurum-bot"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())


# ---------------- lógica pura ----------------
def analizar(filas, invertido=False):
    """filas: registros de la CFTC (más reciente primero). Devuelve dict o None."""
    serie = []
    for f in reversed(filas):
        try:
            neto = float(f["noncomm_positions_long_all"]) - float(f["noncomm_positions_short_all"])
            oi = float(f["open_interest_all"])
        except (KeyError, ValueError):
            continue
        serie.append((f["report_date_as_yyyy_mm_dd"][:10], -neto if invertido else neto, oi))
    if len(serie) < 30:
        return None
    netos = [x[1] for x in serie]
    actual = netos[-1]
    pct = sum(1 for x in netos if x <= actual) / len(netos)
    cambios = [b - a for a, b in zip(netos, netos[1:])]
    z = (cambios[-1] - st.mean(cambios)) / st.stdev(cambios) if len(cambios) > 2 and st.stdev(cambios) else 0.0
    lectura = ("extremo comprador (riesgo de giro a la baja)" if pct >= 0.9 else "extremo vendedor (riesgo de giro al alza)" if pct <= 0.1
               else "comprador" if actual > 0 else "vendedor")
    return {"fecha": serie[-1][0], "neto": actual, "pct_oi": actual / serie[-1][2] if serie[-1][2] else 0.0,
            "percentil": pct, "cambio": cambios[-1], "z_cambio": z, "lectura": lectura}


def ciclo(est):
    filas_md, avisos = [], []
    for s, nombre in MERCADOS.items():
        try:
            r = analizar(descargar(nombre), s in INVERTIDO)
        except Exception as e:
            print(f"COT: no pude leer {s}: {e!r}"[:150])
            continue
        if not r:
            continue
        previo = est.get(s, {})
        if r["lectura"].startswith("extremo") and not previo.get("lectura", "").startswith("extremo"):
            avisos.append(f"{s}: especuladores en {r['lectura']} (percentil {r['percentil']:.0%} de 3 años)")
        if abs(r["z_cambio"]) >= 2:
            avisos.append(f"{s}: cambio semanal fuerte de los especuladores ({r['cambio']:+,.0f} contratos, {r['z_cambio']:+.1f} desv.)")
        est[s] = r
        filas_md.append(f"| {s} | {r['fecha']} | {r['neto']:+,.0f} | {r['pct_oi']:+.0%} | {r['percentil']:.0%} | {r['cambio']:+,.0f} | {r['lectura']} |")
    with open(RUTA_REPORTE, "w", encoding="utf-8") as f:
        f.write(f"# Posicionamiento COT (CFTC) — {datetime.now(timezone.utc):%Y-%m-%d}\n\nContexto, no señal. Especuladores grandes (no comerciales).\n\n"
                "| Mercado | Fecha | Neto (contratos) | % del interés abierto | Percentil 3 años | Cambio semanal | Lectura |\n|---|---|---|---|---|---|---|\n"
                + "\n".join(filas_md))
    with open(RUTA_ESTADO, "w", encoding="utf-8") as f:
        json.dump(est, f, indent=2, ensure_ascii=False)
    if avisos:
        enviar("🐂🐻 Posicionamiento COT (contexto, no señal):\n• " + "\n• ".join(avisos), "Analista COT")
    return filas_md, avisos


def main():
    try:
        est = json.load(open(RUTA_ESTADO, encoding="utf-8"))
    except Exception:
        est = {}
    hecho = None
    while True:
        ahora = datetime.now(timezone.utc)
        if "--ahora" in sys.argv or (ahora.weekday() == 5 and ahora.hour == 12 and hecho != ahora.date()) or not est:
            try:
                ciclo(est)
                hecho = ahora.date()
            except Exception as e:
                print(f"COT: error (sigo): {e!r}"[:200])
            if "--ahora" in sys.argv:
                return
        time.sleep(1800)


if __name__ == "__main__":
    main()
