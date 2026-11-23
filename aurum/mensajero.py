"""
MENSAJERO — envía avisos de Aurum a tu Telegram.
Configuración: archivo telegram.json junto a este archivo:
  {"token": "123456:ABC...", "chat_id": "123456789"}
(Ver LEEME.md para crearlo con @BotFather y obtener tu chat_id con obtener_chat_id.py)
Si no hay telegram.json, los mensajes solo se imprimen en pantalla.
"""
import json
import os
import urllib.parse
import urllib.request

CARPETA = os.path.dirname(os.path.abspath(__file__))
RUTA = os.path.join(CARPETA, "telegram.json")
_cfg = None


def _config():
    global _cfg
    if _cfg is None:
        try:
            with open(RUTA, encoding="utf-8") as f:
                _cfg = json.load(f)
        except Exception:
            _cfg = {}
    return _cfg


def enviar(texto, origen="Aurum"):
    """Envía un mensaje. Nunca lanza errores: si Telegram falla, sigue el trading."""
    msg = f"[{origen}] {texto}"
    cfg = _config()
    if not cfg.get("token") or not cfg.get("chat_id"):
        print("(Telegram no configurado) " + msg)
        return False
    try:
        datos = urllib.parse.urlencode({"chat_id": cfg["chat_id"], "text": msg[:4000]}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{cfg['token']}/sendMessage", data=datos, timeout=15)
        return True
    except Exception as e:
        print(f"(No pude enviar a Telegram: {str(e)[:80]}) " + msg)
        return False


if __name__ == "__main__":
    ok = enviar("✅ Prueba del Mensajero: si lees esto, Telegram funciona.")
    print("Enviado" if ok else "No enviado: revisa telegram.json")
