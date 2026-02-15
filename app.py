from fastapi import FastAPI, Request
from openai import OpenAI
import json

from easypcm.config import OPENAI_API_KEY
from easypcm.telegram import send_message
from easypcm.ai import extrair_os
from easypcm.formatters import format_os_message
from easypcm.schemas import WorkOrder

from easypcm.db import engine, SessionLocal
from easypcm.models import Base
from easypcm.repository import event_exists, save_event, save_work_order

openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# Cria as tabelas no primeiro start (para MVP é suficiente)
Base.metadata.create_all(bind=engine)


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
    message_id = str(message.get("message_id", ""))

    # Por enquanto: só texto
    if "text" not in message:
        send_message(chat_id, "Por enquanto eu processo apenas texto. Áudio entra no próximo passo.")
        return {"ok": True}

    texto = message["text"]
    raw_update = json.dumps(update, ensure_ascii=False)

    db = SessionLocal()
    try:
        # Idempotência: se o Telegram reenviar o mesmo message_id, ignorar
        if message_id and event_exists(db, message_id):
            return {"ok": True}

        # Salva evento bruto + texto
        if message_id:
            save_event(db, message_id, chat_id, raw_update, texto)

        # IA -> JSON
        json_str = extrair_os(openai_client, texto)
        data = json.loads(json_str)

        # Normaliza/valida
        wo = WorkOrder.from_ai_dict(data)

        # Salva OS e pega ID
        row = save_work_order(db, chat_id, wo, texto)

        # Responde com OS #id
        reply = format_os_message(wo, row.id)
        send_message(chat_id, reply)

    except Exception as e:
        send_message(chat_id, f"Erro ao interpretar/salvar OS: {e}")
    finally:
        db.close()

    return {"ok": True}
