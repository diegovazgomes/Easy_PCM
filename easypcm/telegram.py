import requests
from .config import TELEGRAM_BOT_TOKEN

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(chat_id: str, text: str, reply_markup: dict | None = None) -> None:
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload, timeout=30)


def main_menu_keyboard() -> dict:
    """
    Botões sempre visíveis (Reply Keyboard).
    """
    return {
        "keyboard": [
            [{"text": "Abrir OS"}],
            [{"text": "Fechar OS"}],
            [{"text": "Consultar OS"}],
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False,
        "is_persistent": True,
    }


def close_os_inline_keyboard(items: list[tuple[int, str]]) -> dict:
    """
    Inline keyboard para lista de OS abertas.
    items: [(os_id, resumo), ...]
    callback_data: "close:<id>"
    """
    buttons = []
    for os_id, resumo in items:
        buttons.append([{"text": f"Fechar #{os_id} - {resumo}", "callback_data": f"close:{os_id}"}])

    return {"inline_keyboard": buttons}
