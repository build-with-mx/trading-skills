"""
RESPALDO — copia de seguridad diaria de la memoria del equipo (bases de datos, estados, configuración, reportes).
  • Cada día a las 23:00 UTC crea respaldos/aurum_AAAA-MM-DD.zip y conserva los últimos 14.
  • Las bases SQLite se copian con la API de respaldo (copia consistente aunque el bot esté escribiendo).
  • NUNCA incluye telegram.json ni archivos AUTORIZO_*.txt (son llaves/firmas tuyas).
  • Opcional: "respaldo": {"carpeta_extra": "D:\\\\RespaldoAurum"} en aurum_config.json → guarda otra copia ahí
    (por ejemplo una carpeta de Google Drive o OneDrive en tu PC, para tenerla fuera de la computadora).
Restaurar: descomprime el zip encima de la carpeta aurum (con los bots cerrados).
Ejecutar:  python respaldo.py      (o  python respaldo.py --ahora)
"""
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone

from mensajero import enviar

CARPETA = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(CARPETA, "respaldos")
CONSERVAR = 14
EXCLUIR = ("telegram.json",)
EXTENSIONES = (".json", ".jsonl", ".md", ".csv", ".log", ".db", ".flag", ".txt")


def archivos_a_respaldar(lista):
    return sorted(f for f in lista if f.endswith(EXTENSIONES) and f not in EXCLUIR and not f.startswith("AUTORIZO_"))


def respaldar(destino=DESTINO, extra=None):
    os.makedirs(destino, exist_ok=True)
    nombre = f"aurum_{datetime.now(timezone.utc):%Y-%m-%d}.zip"
    ruta = os.path.join(destino, nombre)
    with tempfile.TemporaryDirectory() as tmp, zipfile.ZipFile(ruta, "w", zipfile.ZIP_DEFLATED) as z:
        for f in archivos_a_respaldar(os.listdir(CARPETA)):
            origen = os.path.join(CARPETA, f)
            if f.endswith(".db"):
                copia = os.path.join(tmp, f)
                with sqlite3.connect(origen) as a, sqlite3.connect(copia) as b:
                    a.backup(b)
                z.write(copia, f)
            else:
                z.write(origen, f)
    viejos = sorted(x for x in os.listdir(destino) if x.startswith("aurum_") and x.endswith(".zip"))
    for x in viejos[:-CONSERVAR]:
        os.remove(os.path.join(destino, x))
    if extra:
        try:
            os.makedirs(extra, exist_ok=True)
            shutil.copy2(ruta, os.path.join(extra, nombre))
        except Exception as e:
            enviar(f"💾⚠️ No pude copiar el respaldo a {extra}: {e!r}"[:200], "Respaldo")
    return ruta, os.path.getsize(ruta)


def main():
    hecho = None
    while True:
        ahora = datetime.now(timezone.utc)
        if "--ahora" in sys.argv or (ahora.hour == 23 and hecho != ahora.date()):
            try:
                cfg = json.load(open(os.path.join(CARPETA, "aurum_config.json"), encoding="utf-8"))
                ruta, tam = respaldar(extra=cfg.get("respaldo", {}).get("carpeta_extra"))
                hecho = ahora.date()
                print(f"Respaldo creado: {ruta} ({tam / 1e6:.1f} MB)")
                if ahora.weekday() == 6:
                    enviar(f"💾 Respaldo semanal OK: {os.path.basename(ruta)} ({tam / 1e6:.1f} MB). Guardo los últimos {CONSERVAR} días.", "Respaldo")
            except Exception as e:
                enviar(f"💾❗ Falló el respaldo: {e!r}"[:200], "Respaldo")
            if "--ahora" in sys.argv:
                return
        time.sleep(600)


if __name__ == "__main__":
    main()
