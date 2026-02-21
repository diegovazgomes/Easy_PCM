# easypcm/telegram.py
import os
import requests

from .ui_labels import (
    BTN_OPEN, BTN_UPDATE, BTN_CLOSE, BTN_CONSULT,
    CB_CLOSE_PREFIX, CB_UPDATE_PREFIX, CB_STATUS_PREFIX,
    STATUS_OPTIONS,
)


def send_message(chat_id: str, text: str, reply_markup: dict | None = None) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        print("ERRO: TELEGRAM_BOT_TOKEN não carregado (None). Verifique .env e load_dotenv().")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    r = requests.post(url, json=payload, timeout=20)
    print("sendMessage:", r.status_code, r.text[:200])


def main_menu_keyboard() -> dict:
    return {
        "keyboard": [
            [BTN_OPEN, BTN_UPDATE],
            [BTN_CLOSE, BTN_CONSULT],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
        "one_time_keyboard": False,
        "input_field_placeholder": "Escolha uma opção abaixo",
    }


def close_os_inline_keyboard(items: list[tuple[int, str]]) -> dict:
    buttons = []
    for os_id, resumo in items:
        buttons.append([{
            "text": f"#{os_id} - {resumo}",
            "callback_data": f"{CB_CLOSE_PREFIX}{os_id}",
        }])
    return {"inline_keyboard": buttons}


def update_os_inline_keyboard(items: list[tuple[int, str]]) -> dict:
    buttons = []
    for os_id, resumo in items:
        buttons.append([{
            "text": f"#{os_id} - {resumo}",
            "callback_data": f"{CB_UPDATE_PREFIX}{os_id}",
        }])
    return {"inline_keyboard": buttons}


def status_inline_keyboard() -> dict:
    buttons = []
    for label, value in STATUS_OPTIONS:
        buttons.append([{
            "text": label,
            "callback_data": f"{CB_STATUS_PREFIX}{value}",
        }])
    return {"inline_keyboard": buttons}
