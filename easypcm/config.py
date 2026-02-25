import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # opcional no MVP (IA futura)

MASTER_USER_ID = os.getenv("MASTER_USER_ID")  # ex: "1350252394"

INVITE_EXPIRES_DAYS = int(os.getenv("INVITE_EXPIRES_DAYS", "7"))

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN não encontrado no .env")

# OPENAI_API_KEY não deve travar o bot no MVP
# if not OPENAI_API_KEY:
#     raise RuntimeError("OPENAI_API_KEY não encontrado no .env")

if not MASTER_USER_ID:
    raise RuntimeError("MASTER_USER_ID não encontrado no .env (ex: 1350252394)")