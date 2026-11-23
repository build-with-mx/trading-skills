"""
Obtiene tu chat_id de Telegram y crea telegram.json.
Pasos: 1) crea tu bot con @BotFather y copia el token; 2) escríbele cualquier mensaje a tu bot en Telegram;
3) ejecuta:  python obtener_chat_id.py   y pega el token cuando lo pida.
"""
import json
import os
import urllib.request

token = input("Pega el token que te dio @BotFather: ").strip()
datos = json.loads(urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20).read().decode())
chats = {str(u["message"]["chat"]["id"]): u["message"]["chat"].get("first_name", "") for u in datos.get("result", []) if "message" in u}
if not chats:
    raise SystemExit("No encontré mensajes. Escríbele algo a tu bot en Telegram y vuelve a ejecutar este archivo.")
chat_id = list(chats)[-1]
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "telegram.json"), "w", encoding="utf-8") as f:
    json.dump({"token": token, "chat_id": chat_id}, f, indent=2)
print(f"Listo: telegram.json creado (chat_id {chat_id}). Ahora ejecuta:  python mensajero.py   para probar.")
