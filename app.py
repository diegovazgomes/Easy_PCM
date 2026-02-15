from fastapi import FastAPI, Request
from openai import OpenAI
import json

from easypcm.config import OPENAI_API_KEY
from easypcm.telegram import send_message
from easypcm.ai import extrair_os
from easypcm.formatters import format_os_message

openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/")
def home():
    return {"status": "Servidor rodando"}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = str(message["chat"]["id"])

    # Por enquanto: só texto
    if "text" not in message:
        send_message(chat_id, "Por enquanto eu processo apenas texto. Áudio entra no próximo passo.")
        return {"ok": True}

    texto = message["text"]

    try:
        json_str = extrair_os(openai_client, texto)
        data = json.loads(json_str)
        reply = format_os_message(data)
        send_message(chat_id, reply)
    except Exception as e:
        send_message(chat_id, f"Erro ao interpretar OS: {e}")

    return {"ok": True}
