from fastapi import FastAPI, Request
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
import json

from ai import extrair_os  # usa seu ai.py

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN não encontrado no .env")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY não encontrado no .env")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()


def send_message(chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=30)


def safe_get(d: dict, key: str, default: str = "SEM INFORMAÇÃO") -> str:
    """
    Pega campo do JSON e garante string utilizável.
    Se vier None/vazio, retorna default.
    """
    val = d.get(key, default)
    if val is None:
        return default
    if isinstance(val, str) and val.strip() == "":
        return default
    return str(val)


def format_os_message(data: dict) -> str:
    def safe_get(key: str):
        val = data.get(key)
        if val is None or val == "" or val == "SEM INFORMAÇÃO":
            return "SEM INFORMAÇÃO"
        return str(val)

    equipamento = safe_get("equipamento")
    setor = safe_get("setor")
    solicitante = safe_get("solicitante")
    executor = safe_get("executor")
    descricao = safe_get("descrição_do_problema")
    tipo = safe_get("tipo_manutenção")
    status = safe_get("status")
    tempo = safe_get("tempo_gasto_minutos")
    custo = safe_get("custo_peças")
    solucao = safe_get("solução_aplicada")

    msg = (
        "🟢 OS REGISTRADA (PRÉ-ANÁLISE)\n\n"
        f"🔧 Equipamento: {equipamento}\n"
        f"📍 Setor: {setor}\n"
        f"📝 Solicitante: {solicitante}\n"
        f"👨‍🔧 Executor: {executor}\n"
        f"⚙️ Tipo de manutenção: {tipo}\n"
        f"📌 Status: {status}\n"
        f"⏱ Tempo gasto (min): {tempo}\n"
        f"💰 Custo de peças: {custo}\n"
        f"🚨 Problema detectado:\n{descricao}\n"
        f"🛠 Solução aplicada:\n{solucao}"
    )

    return msg

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = str(message["chat"]["id"])

    # Por enquanto: só texto (áudio entra depois)
    if "text" not in message:
        send_message(chat_id, "Por enquanto eu processo apenas texto. Áudio entra no próximo passo.")
        return {"ok": True}

    texto = message["text"]

    try:
        json_str = extrair_os(openai_client, texto)

        # extrair_os retorna uma STRING JSON; aqui convertemos para dict
        data = json.loads(json_str)

        # Garante que veio um objeto
        if not isinstance(data, dict):
            raise ValueError("A IA não retornou um objeto JSON válido.")

        # Resposta formatada (estilo Make)
        reply = format_os_message(data)
        send_message(chat_id, reply)

    except Exception as e:
        send_message(chat_id, f"Erro ao interpretar OS: {e}")

    return {"ok": True}


@app.get("/")
def home():
    return {"status": "Servidor rodando"}

@app.get("/health")
def health():
    return {"ok": True}

