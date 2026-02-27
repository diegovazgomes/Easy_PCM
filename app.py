from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request

from easypcm.config import MASTER_USER_ID, INVITE_EXPIRES_DAYS
from easypcm.db import engine, SessionLocal
from easypcm.models import Base
from easypcm.telegram import (
    send_message,
    main_menu_keyboard,
    close_os_inline_keyboard,
    update_os_inline_keyboard,
    status_inline_keyboard,
)
from easypcm.repository import (
    register_event_if_new,
    upsert_user,
    create_organization,
    get_org_by_id,
    get_user_org_id,
    get_user_role_in_org,
    create_invite,
    consume_invite,

    get_or_create_chat_state,
    set_state,
    clear_state,
    create_open_work_order,
    list_open_work_orders,
    close_work_order,
    add_materials,
    list_materials,
    add_technicians_to_os,
    list_technicians_for_os,
    update_work_order_status,
)
from easypcm.ui_labels import (
    BTN_OPEN, BTN_UPDATE, BTN_CLOSE, BTN_CONSULT,
    CMD_OPEN, CMD_UPDATE, CMD_CLOSE,
    CMD_MENU_1, CMD_MENU_2, CMD_MENU_3,
    CB_CLOSE_PREFIX, CB_UPDATE_PREFIX, CB_STATUS_PREFIX,
)
from easypcm.ui_texts import TXT

app = FastAPI()
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def home():
    return {"status": "Servidor rodando"}


def _normalize_text(t: str) -> str:
    return (t or "").strip()


def _parse_hhmm(text: str) -> int | None:
    t = text.strip()
    if ":" not in t:
        return None
    parts = t.split(":")
    if len(parts) != 2:
        return None
    try:
        hh = int(parts[0])
        mm = int(parts[1])
    except ValueError:
        return None
    if hh < 0 or hh > 23 or mm < 0 or mm > 59:
        return None
    return hh * 60 + mm


def _parse_total_duration_minutes(text: str) -> int | None:
    t = text.strip().lower()
    if t.startswith("total"):
        t = t.replace("total", "", 1).strip()

    if t.isdigit():
        return int(t)

    t = t.replace("horas", "h").replace("hora", "h")
    t = t.replace(" ", "")
    if t.endswith("h"):
        num = t[:-1]
        if num.isdigit():
            return int(num) * 60
    return None


def _safe_float_string(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return "SEM INFORMAÇÃO"
    t2 = t.replace(",", ".")
    try:
        float(t2)
        return t2
    except ValueError:
        return t


def _parse_materials_list(text: str) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    if t.upper() in ("NENHUMA", "NENHUM", "NAO", "NÃO"):
        return []
    parts = [p.strip() for p in t.split(",")]
    return [p for p in parts if p]


def _parse_technicians_list(text: str) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    parts = [p.strip() for p in t.split(",")]
    return [p for p in parts if p]


def _is_private_chat(message: dict) -> bool:
    chat = message.get("chat", {})
    return chat.get("type") == "private"


def _parse_command(text: str) -> tuple[str, str]:
    """
    Retorna (cmd, arg)
    Ex:
      "/entrar INV-ABC123" -> ("/entrar", "INV-ABC123")
      "/criar_empresa Minha Empresa" -> ("/criar_empresa", "Minha Empresa")
    """
    t = (text or "").strip()
    if not t.startswith("/"):
        return ("", "")
    parts = t.split(" ", 1)
    cmd = parts[0].strip().lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    return (cmd, arg)


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    db = SessionLocal()

    try:
        # =====================================================
        # DEDUP (ANTI-FLOOD) por update_id
        # =====================================================
        update_id = update.get("update_id")
        dedup_key = f"upd:{update_id}" if update_id is not None else None

        chat_id_for_event = ""
        if "callback_query" in update:
            cb0 = update["callback_query"]
            chat_id_for_event = str(cb0["message"]["chat"]["id"])
        else:
            msg0 = update.get("message") or update.get("edited_message")
            if msg0:
                chat_id_for_event = str(msg0["chat"]["id"])

        if dedup_key:
            is_new = register_event_if_new(db, dedup_key, chat_id_for_event, update)
            if not is_new:
                return {"ok": True}

        menu = main_menu_keyboard()

        # =====================================================
        # CALLBACKS (inline buttons)
        # =====================================================
        if "callback_query" in update:
            cb = update["callback_query"]
            message = cb.get("message", {})
            chat_id = str(message.get("chat", {}).get("id", ""))
            data = cb.get("data", "")

            # callbacks devem funcionar só no privado
            # (se quiser permitir grupo depois, a gente adapta)
            st = get_or_create_chat_state(db, chat_id)

            # Identidade do usuário
            from_user = cb.get("from", {})
            telegram_user_id = str(from_user.get("id", ""))
            username = from_user.get("username", "") or ""
            first_name = from_user.get("first_name", "") or ""
            is_master = (telegram_user_id == str(MASTER_USER_ID))
            upsert_user(db, telegram_user_id, username=username, first_name=first_name, is_master=is_master)

            org_id = get_user_org_id(db, telegram_user_id)
            if not org_id:
                send_message(chat_id, "Você ainda não está em uma empresa. Use: /entrar SEU-CÓDIGO", reply_markup=menu)
                return {"ok": True}

            # Fechar OS: escolha da OS
            if data.startswith(CB_CLOSE_PREFIX):
                os_id = int(data.split(":", 1)[1])
                set_state(db, st, mode="CLOSE_FLOW", step="ASK_SOLUCAO", os_id=os_id)
                send_message(chat_id, TXT.close_intro(os_id), reply_markup=menu)
                return {"ok": True}

            # Atualizar OS: escolha da OS
            if data.startswith(CB_UPDATE_PREFIX):
                os_id = int(data.split(":", 1)[1])
                set_state(db, st, mode="UPDATE_FLOW", step="ASK_STATUS", os_id=os_id)
                send_message(chat_id, TXT.update_intro(os_id), reply_markup=status_inline_keyboard())
                return {"ok": True}

            # Atualizar OS: escolha do status
            if data.startswith(CB_STATUS_PREFIX):
                status_val = data.split(":", 1)[1]
                if st.mode != "UPDATE_FLOW" or st.step != "ASK_STATUS" or not st.os_id:
                    send_message(chat_id, TXT.UNKNOWN_ACTION, reply_markup=menu)
                    return {"ok": True}

                st.temp_status = status_val
                db.commit()
                set_state(db, st, mode="UPDATE_FLOW", step="ASK_OBS", os_id=st.os_id)
                send_message(chat_id, TXT.UPDATE_ASK_OBS, reply_markup=menu)
                return {"ok": True}

            send_message(chat_id, TXT.UNKNOWN_ACTION, reply_markup=menu)
            return {"ok": True}

        # =====================================================
        # MESSAGES
        # =====================================================
        message = update.get("message") or update.get("edited_message")
        if not message:
            return {"ok": True}

        chat_id = str(message["chat"]["id"])
        chat_type = message.get("chat", {}).get("type", "")
        text = _normalize_text(message.get("text", ""))

        # Identidade do usuário
        from_user = message.get("from", {})
        telegram_user_id = str(from_user.get("id", ""))
        username = from_user.get("username", "") or ""
        first_name = from_user.get("first_name", "") or ""
        is_master = (telegram_user_id == str(MASTER_USER_ID))
        upsert_user(db, telegram_user_id, username=username, first_name=first_name, is_master=is_master)

        # A partir de agora, a UX alvo é PRIVADO
        if chat_type != "private":
            send_message(
                chat_id,
                "Para manter privacidade e organização, use o bot no PRIVADO.\n"
                "Abra uma conversa comigo e use /menu.\n\n"
                "Se precisar entrar em uma empresa: /entrar SEU-CÓDIGO",
                reply_markup=menu,
            )
            return {"ok": True}

        st = get_or_create_chat_state(db, chat_id)

        # =====================================================
        # COMANDOS DE ORG/INVITE
        # =====================================================
        cmd, arg = _parse_command(text)

        if cmd == "/entrar":
            token = (arg or "").strip()
            if not token:
                send_message(chat_id, "Uso: /entrar INV-XXXXXX", reply_markup=menu)
                return {"ok": True}

            ok, msg, org_id, role = consume_invite(db, token, telegram_user_id)
            if not ok:
                send_message(chat_id, msg, reply_markup=menu)
                return {"ok": True}

            org = get_org_by_id(db, org_id) if org_id else None
            org_name = org.name if org else "Empresa"
            send_message(chat_id, f"{msg}\n\nEmpresa: {org_name}\nPerfil: {role}", reply_markup=menu)
            return {"ok": True}

        if cmd == "/criar_empresa":
            if not is_master:
                send_message(chat_id, "Sem permissão. Apenas o MASTER pode criar empresas.", reply_markup=menu)
                return {"ok": True}

            name = (arg or "").strip().strip('"')
            if not name:
                send_message(chat_id, 'Uso: /criar_empresa "Nome da Empresa"', reply_markup=menu)
                return {"ok": True}

            org = create_organization(db, name)
            send_message(chat_id, f"Empresa criada!\nID: {org.id}\nNome: {org.name}", reply_markup=menu)
            send_message(chat_id, f"Agora gere o convite do admin:\n/invite_admin {org.id}", reply_markup=menu)
            return {"ok": True}

        if cmd == "/invite_admin":
            if not is_master:
                send_message(chat_id, "Sem permissão. Apenas o MASTER pode criar convite de admin.", reply_markup=menu)
                return {"ok": True}

            if not arg or not arg.strip().isdigit():
                send_message(chat_id, "Uso: /invite_admin <ORG_ID>", reply_markup=menu)
                return {"ok": True}

            org_id = int(arg.strip())
            org = get_org_by_id(db, org_id)
            if not org or not org.active:
                send_message(chat_id, "Empresa não encontrada.", reply_markup=menu)
                return {"ok": True}

            inv = create_invite(
                db,
                org_id=org_id,
                created_by_user_id=telegram_user_id,
                role_to_grant="ORG_ADMIN",
                expires_days=INVITE_EXPIRES_DAYS,
            )
            send_message(
                chat_id,
                f"Convite de ADMIN criado (expira em {INVITE_EXPIRES_DAYS} dias):\n\n{inv.token}\n\n"
                f"Envie este código para o admin da empresa.",
                reply_markup=menu,
            )
            return {"ok": True}

        if cmd == "/invite_user":
            # precisa ser admin da org
            org_id = get_user_org_id(db, telegram_user_id)
            if not org_id:
                send_message(chat_id, "Você ainda não está em uma empresa. Use: /entrar SEU-CÓDIGO", reply_markup=menu)
                return {"ok": True}

            role = get_user_role_in_org(db, telegram_user_id, org_id)
            if role != "ORG_ADMIN":
                send_message(chat_id, "Sem permissão. Apenas ADMIN da empresa pode convidar usuários.", reply_markup=menu)
                return {"ok": True}

            inv = create_invite(
                db,
                org_id=org_id,
                created_by_user_id=telegram_user_id,
                role_to_grant="ORG_USER",
                expires_days=INVITE_EXPIRES_DAYS,
            )
            send_message(
                chat_id,
                f"Convite de USUÁRIO criado (expira em {INVITE_EXPIRES_DAYS} dias):\n\n{inv.token}\n\n"
                f"Envie este código para a pessoa entrar com /entrar {inv.token}",
                reply_markup=menu,
            )
            return {"ok": True}

        # =====================================================
        # BLOQUEIO: precisa estar em uma empresa para usar /menu e fluxos
        # =====================================================
        org_id = get_user_org_id(db, telegram_user_id)
        if not org_id:
            send_message(
                chat_id,
                "Você ainda não está em uma empresa.\n\n"
                "Use: /entrar INV-XXXXXX\n\n"
                "Se você é o MASTER, crie uma empresa com:\n/criar_empresa \"Nome\"",
                reply_markup=menu,
            )
            return {"ok": True}

        # =====================================================
        # MENU / COMANDOS EXISTENTES
        # =====================================================
        if text in (CMD_MENU_1, CMD_MENU_2, CMD_MENU_3, BTN_CONSULT):
            send_message(chat_id, TXT.MENU_TITLE, reply_markup=menu)
            return {"ok": True}

        if text in (CMD_OPEN, BTN_OPEN):
            set_state(db, st, mode="OPEN_FLOW", step="ASK_EQUIP", os_id=None)
            send_message(chat_id, TXT.OPEN_START, reply_markup=menu)
            return {"ok": True}

        if text in (CMD_CLOSE, BTN_CLOSE):
            abertas = list_open_work_orders(db, org_id, limit=10)
            if not abertas:
                send_message(chat_id, TXT.NO_OPEN_OS_TO_CLOSE, reply_markup=menu)
                return {"ok": True}

            items = []
            for wo in abertas:
                resumo = f"{wo.equipamento} - {wo.descricao_do_problema[:40].strip()}"
                items.append((wo.id, resumo))

            send_message(chat_id, "Selecione a OS para fechar:", reply_markup=close_os_inline_keyboard(items))
            return {"ok": True}

        if text in (CMD_UPDATE, BTN_UPDATE):
            abertas = list_open_work_orders(db, org_id, limit=10)
            if not abertas:
                send_message(chat_id, TXT.NO_OPEN_OS_TO_UPDATE, reply_markup=menu)
                return {"ok": True}

            items = []
            for wo in abertas:
                resumo = f"{wo.equipamento} - {wo.descricao_do_problema[:40].strip()}"
                items.append((wo.id, resumo))

            send_message(chat_id, TXT.UPDATE_PICK_OS, reply_markup=update_os_inline_keyboard(items))
            return {"ok": True}

        # =====================================================
        # OPEN_FLOW
        # =====================================================
        if st.mode == "OPEN_FLOW":
            if st.step == "ASK_EQUIP":
                st.temp_equipamento = text
                db.commit()
                set_state(db, st, mode="OPEN_FLOW", step="ASK_SETOR")
                send_message(chat_id, TXT.ASK_SETOR, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_SETOR":
                if not text:
                    send_message(chat_id, TXT.SETOR_REQUIRED, reply_markup=menu)
                    return {"ok": True}

                st.temp_setor = text
                db.commit()
                set_state(db, st, mode="OPEN_FLOW", step="ASK_PROBLEMA")
                send_message(chat_id, TXT.ASK_PROBLEMA, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_PROBLEMA":
                st.temp_problema = text
                db.commit()
                set_state(db, st, mode="OPEN_FLOW", step="ASK_PARADA")
                send_message(chat_id, TXT.ASK_PARADA, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_PARADA":
                val = text.upper()
                if val not in ("SIM", "NAO", "NÃO"):
                    send_message(chat_id, TXT.PARADA_INVALID, reply_markup=menu)
                    return {"ok": True}
                if val == "NÃO":
                    val = "NÃO"

                st.temp_maquina_parada = val
                db.commit()

                wo = create_open_work_order(
                    db,
                    org_id=org_id,
                    chat_id=chat_id,
                    equipamento=st.temp_equipamento,
                    setor=st.temp_setor,
                    problema=st.temp_problema,
                    maquina_parada=st.temp_maquina_parada,
                )

                clear_state(db, st)
                send_message(
                    chat_id,
                    TXT.open_done(wo.id, wo.equipamento, wo.setor, wo.maquina_parada, wo.descricao_do_problema),
                    reply_markup=menu,
                )
                return {"ok": True}

        # =====================================================
        # UPDATE_FLOW
        # =====================================================
        if st.mode == "UPDATE_FLOW":
            if st.step == "ASK_OBS":
                obs = "" if text.upper() == "PULAR" else text
                wo = update_work_order_status(db, org_id, st.os_id, st.temp_status, obs)
                clear_state(db, st)
                send_message(chat_id, TXT.update_done(wo.id, wo.status, wo.status_observacao), reply_markup=menu)
                return {"ok": True}

        # =====================================================
        # CLOSE_FLOW
        # =====================================================
        if st.mode == "CLOSE_FLOW":
            os_id = st.os_id

            if st.step == "ASK_SOLUCAO":
                st.temp_solucao = text
                db.commit()
                set_state(db, st, mode="CLOSE_FLOW", step="ASK_INICIO", os_id=os_id)
                send_message(chat_id, TXT.CLOSE_ASK_INICIO, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_INICIO":
                total_min = _parse_total_duration_minutes(text)
                if total_min is not None:
                    st.temp_inicio_hhmm = f"TOTAL:{total_min}"
                    st.temp_fim_hhmm = ""
                    db.commit()
                    set_state(db, st, mode="CLOSE_FLOW", step="ASK_TECNICOS", os_id=os_id)
                    send_message(chat_id, TXT.CLOSE_ASK_TECNICOS, reply_markup=menu)
                    return {"ok": True}

                inicio_min = _parse_hhmm(text)
                if inicio_min is None:
                    send_message(chat_id, TXT.CLOSE_INICIO_INVALID, reply_markup=menu)
                    return {"ok": True}

                st.temp_inicio_hhmm = text
                db.commit()
                set_state(db, st, mode="CLOSE_FLOW", step="ASK_FIM", os_id=os_id)
                send_message(chat_id, TXT.CLOSE_ASK_FIM, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_FIM":
                fim_min = _parse_hhmm(text)
                if fim_min is None:
                    send_message(chat_id, TXT.CLOSE_FIM_INVALID, reply_markup=menu)
                    return {"ok": True}

                st.temp_fim_hhmm = text
                db.commit()
                set_state(db, st, mode="CLOSE_FLOW", step="ASK_TECNICOS", os_id=os_id)
                send_message(chat_id, TXT.CLOSE_ASK_TECNICOS, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_TECNICOS":
                st.temp_tecnicos = text
                db.commit()
                set_state(db, st, mode="CLOSE_FLOW", step="ASK_MATERIAIS", os_id=os_id)
                send_message(chat_id, TXT.CLOSE_ASK_MATERIAIS, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_MATERIAIS":
                st.temp_materiais = text
                db.commit()
                set_state(db, st, mode="CLOSE_FLOW", step="ASK_CUSTO", os_id=os_id)
                send_message(chat_id, TXT.CLOSE_ASK_CUSTO, reply_markup=menu)
                return {"ok": True}

            if st.step == "ASK_CUSTO":
                st.temp_custo_pecas = _safe_float_string(text)
                db.commit()

                tempo_min = 0
                if st.temp_inicio_hhmm.startswith("TOTAL:"):
                    try:
                        tempo_min = int(st.temp_inicio_hhmm.split(":", 1)[1])
                    except Exception:
                        tempo_min = 0
                else:
                    inicio_min = _parse_hhmm(st.temp_inicio_hhmm)
                    fim_min = _parse_hhmm(st.temp_fim_hhmm)
                    if inicio_min is not None and fim_min is not None:
                        if fim_min < inicio_min:
                            fim_min += 24 * 60
                        tempo_min = max(0, fim_min - inicio_min)

                tech_names = _parse_technicians_list(st.temp_tecnicos)
                if tech_names:
                    add_technicians_to_os(db, os_id, tech_names)

                materiais = _parse_materials_list(st.temp_materiais)
                if materiais:
                    add_materials(db, os_id, materiais)

                wo = close_work_order(
                    db,
                    org_id=org_id,
                    os_id=os_id,
                    solucao=st.temp_solucao,
                    tempo_min=tempo_min,
                    custo_pecas=st.temp_custo_pecas,
                )

                techs_db = list_technicians_for_os(db, os_id)
                tecnicos_txt = ", ".join(techs_db) if techs_db else "SEM INFORMAÇÃO"

                mats = list_materials(db, os_id)
                if mats:
                    mats_txt = ", ".join([m.descricao for m in mats[:6]])
                    if len(mats) > 6:
                        mats_txt += "..."
                else:
                    mats_txt = "NENHUMA"

                clear_state(db, st)
                send_message(
                    chat_id,
                    TXT.close_done(
                        wo.id, wo.equipamento, wo.setor,
                        wo.tempo_gasto_minutos,
                        tecnicos_txt,
                        mats_txt,
                        wo.custo_pecas,
                        wo.solucao_aplicada
                    ),
                    reply_markup=menu,
                )
                return {"ok": True}

        send_message(chat_id, TXT.UNKNOWN_COMMAND, reply_markup=menu)
        return {"ok": True}

    finally:
        db.close()