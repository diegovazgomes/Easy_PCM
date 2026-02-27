import json
import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from .models import (
    Event,
    ChatState,
    WorkOrderRow,
    MaterialRow,
    TechnicianRow,
    WorkOrderTechnicianRow,
    OrganizationRow,
    UserRow,
    OrgUserRow,
    InviteRow,
)
from .schemas import SEM_INFO


# ============================================================
# DEDUPLICAÇÃO (ANTI-FLOOD TELEGRAM)
# ============================================================

def register_event_if_new(db: Session, dedup_key: str, chat_id: str, raw_update: dict) -> bool:
    """
    Registra o update no banco para evitar duplicação.
    Retorna True se for novo.
    Retorna False se já existir (duplicado).
    """
    evt = Event(
        message_id=dedup_key,
        chat_id=str(chat_id),
        raw_update=json.dumps(raw_update, ensure_ascii=False),
    )
    db.add(evt)
    try:
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


# ============================================================
# ORG / USERS / INVITES
# ============================================================

def upsert_user(db: Session, telegram_user_id: str, username: str = "", first_name: str = "", is_master: bool = False) -> UserRow:
    u = db.query(UserRow).filter(UserRow.telegram_user_id == str(telegram_user_id)).first()
    if not u:
        u = UserRow(
            telegram_user_id=str(telegram_user_id),
            username=username or "",
            first_name=first_name or "",
            is_master=bool(is_master),
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    # atualiza dados básicos sem sobrescrever com vazio
    if username and u.username != username:
        u.username = username
    if first_name and u.first_name != first_name:
        u.first_name = first_name
    if is_master and not u.is_master:
        u.is_master = True

    db.commit()
    db.refresh(u)
    return u


def create_organization(db: Session, name: str) -> OrganizationRow:
    org = OrganizationRow(name=name.strip())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def get_org_by_id(db: Session, org_id: int) -> OrganizationRow | None:
    return db.query(OrganizationRow).filter(OrganizationRow.id == org_id).first()


def get_user_org_membership(db: Session, telegram_user_id: str) -> OrgUserRow | None:
    return (
        db.query(OrgUserRow)
        .filter(OrgUserRow.telegram_user_id == str(telegram_user_id), OrgUserRow.active == True)
        .order_by(desc(OrgUserRow.id))
        .first()
    )


def get_user_org_id(db: Session, telegram_user_id: str) -> int | None:
    mem = get_user_org_membership(db, telegram_user_id)
    return mem.org_id if mem else None


def get_user_role_in_org(db: Session, telegram_user_id: str, org_id: int) -> str | None:
    mem = (
        db.query(OrgUserRow)
        .filter(
            OrgUserRow.telegram_user_id == str(telegram_user_id),
            OrgUserRow.org_id == org_id,
            OrgUserRow.active == True,
        )
        .first()
    )
    return mem.role if mem else None


def _generate_invite_token() -> str:
    # Formato amigável: INV-XXXXXX
    alphabet = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"INV-{code}"


def create_invite(
    db: Session,
    org_id: int,
    created_by_user_id: str,
    role_to_grant: str,
    expires_days: int = 7,
) -> InviteRow:
    # garante token único (tenta algumas vezes)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)

    for _ in range(10):
        token = _generate_invite_token()
        existing = db.query(InviteRow).filter(InviteRow.token == token).first()
        if existing:
            continue

        inv = InviteRow(
            token=token,
            org_id=org_id,
            role_to_grant=role_to_grant,
            created_by_user_id=str(created_by_user_id),
            expires_at=expires_at,
            used_by_user_id="",
            used_at=None,
            active=True,
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)
        return inv

    raise RuntimeError("Falha ao gerar token de convite (tente novamente).")


def consume_invite(db: Session, token: str, telegram_user_id: str) -> tuple[bool, str, int | None, str | None]:
    """
    Retorna (ok, msg, org_id, granted_role)
    """
    token = (token or "").strip().upper()
    inv = db.query(InviteRow).filter(InviteRow.token == token).first()
    if not inv or not inv.active:
        return (False, "Convite inválido.", None, None)

    now = datetime.now(timezone.utc)

    exp = inv.expires_at
    # SQLite às vezes devolve datetime "naive" ou até string
    if isinstance(exp, str):
        try:
            # tenta ISO
            exp = datetime.fromisoformat(exp)
        except Exception:
            exp = None

    if isinstance(exp, datetime):
        # se for naive, assume UTC
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)

    if exp and now > exp:
        return (False, "Convite expirado.", None, None)

    if inv.used_by_user_id:
        return (False, "Convite já foi utilizado.", None, None)

    # marca como usado
    inv.used_by_user_id = str(telegram_user_id)
    inv.used_at = now
    inv.active = False
    db.commit()

    # cria vínculo org_users
    existing = (
        db.query(OrgUserRow)
        .filter(
            OrgUserRow.org_id == inv.org_id,
            OrgUserRow.telegram_user_id == str(telegram_user_id),
        )
        .first()
    )
    if existing:
        existing.active = True
        existing.role = inv.role_to_grant
        db.commit()
        return (True, "Você já fazia parte da empresa. Seu acesso foi atualizado.", inv.org_id, inv.role_to_grant)

    mem = OrgUserRow(
        org_id=inv.org_id,
        telegram_user_id=str(telegram_user_id),
        role=inv.role_to_grant,
        active=True,
    )
    db.add(mem)
    db.commit()
    return (True, "Entrada na empresa confirmada.", inv.org_id, inv.role_to_grant)


# ============================================================
# CHAT STATE
# ============================================================

def get_or_create_chat_state(db: Session, chat_id: str) -> ChatState:
    st = db.query(ChatState).filter(ChatState.chat_id == chat_id).first()
    if not st:
        st = ChatState(chat_id=chat_id)
        db.add(st)
        db.commit()
        db.refresh(st)
    return st


def set_state(db: Session, st: ChatState, mode: str, step: str = "", os_id: int | None = None) -> ChatState:
    st.mode = mode
    st.step = step
    st.os_id = os_id
    db.commit()
    db.refresh(st)
    return st


def clear_state(db: Session, st: ChatState) -> ChatState:
    st.mode = "IDLE"
    st.step = ""
    st.os_id = None

    st.temp_equipamento = ""
    st.temp_setor = ""
    st.temp_problema = ""
    st.temp_maquina_parada = ""

    st.temp_solucao = ""
    st.temp_inicio_hhmm = ""
    st.temp_fim_hhmm = ""
    st.temp_tecnicos = ""
    st.temp_materiais = ""
    st.temp_custo_pecas = ""

    st.temp_status = ""
    st.temp_status_obs = ""

    db.commit()
    db.refresh(st)
    return st


# ============================================================
# WORK ORDERS (AGORA POR ORG_ID)
# ============================================================

def create_open_work_order(
    db: Session,
    org_id: int,
    chat_id: str,
    equipamento: str,
    setor: str,
    problema: str,
    maquina_parada: str,
) -> WorkOrderRow:
    wo = WorkOrderRow(
        org_id=org_id,
        chat_id=chat_id,  # chat privado de quem abriu (registro)
        equipamento=(equipamento or SEM_INFO),
        setor=(setor or SEM_INFO),
        descricao_do_problema=(problema or SEM_INFO),
        maquina_parada=(maquina_parada or SEM_INFO),
        status="ABERTA",
        source_text="",
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    return wo


def list_open_work_orders(db: Session, org_id: int, limit: int = 10) -> list[WorkOrderRow]:
    return (
        db.query(WorkOrderRow)
        .filter(WorkOrderRow.org_id == org_id, WorkOrderRow.status.notin_(["FECHADA", "CANCELADA"]))
        .order_by(desc(WorkOrderRow.id))
        .limit(limit)
        .all()
    )


def get_work_order(db: Session, org_id: int, os_id: int) -> WorkOrderRow | None:
    return (
        db.query(WorkOrderRow)
        .filter(WorkOrderRow.org_id == org_id, WorkOrderRow.id == os_id)
        .first()
    )


def add_materials(db: Session, os_id: int, materiais: list[str]) -> None:
    for m in materiais:
        desc_txt = (m or "").strip()
        if not desc_txt:
            continue
        db.add(MaterialRow(work_order_id=os_id, descricao=desc_txt))
    db.commit()


def list_materials(db: Session, os_id: int) -> list[MaterialRow]:
    return (
        db.query(MaterialRow)
        .filter(MaterialRow.work_order_id == os_id)
        .order_by(desc(MaterialRow.id))
        .all()
    )


def _get_or_create_technician(db: Session, nome: str) -> TechnicianRow:
    nome_norm = (nome or "").strip()
    if not nome_norm:
        raise ValueError("Nome de técnico vazio.")

    nome_norm = " ".join([p[:1].upper() + p[1:].lower() for p in nome_norm.split()])

    tech = db.query(TechnicianRow).filter(TechnicianRow.nome == nome_norm).first()
    if tech:
        return tech

    tech = TechnicianRow(nome=nome_norm)
    db.add(tech)
    db.commit()
    db.refresh(tech)
    return tech


def add_technicians_to_os(db: Session, os_id: int, nomes: list[str]) -> list[str]:
    saved_names: list[str] = []
    for nome in nomes:
        nome_clean = (nome or "").strip()
        if not nome_clean:
            continue

        tech = _get_or_create_technician(db, nome_clean)

        exists = (
            db.query(WorkOrderTechnicianRow)
            .filter(
                WorkOrderTechnicianRow.work_order_id == os_id,
                WorkOrderTechnicianRow.technician_id == tech.id,
            )
            .first()
        )
        if not exists:
            db.add(WorkOrderTechnicianRow(work_order_id=os_id, technician_id=tech.id))

        saved_names.append(tech.nome)

    db.commit()
    return saved_names


def list_technicians_for_os(db: Session, os_id: int) -> list[str]:
    rows = (
        db.query(TechnicianRow.nome)
        .join(WorkOrderTechnicianRow, WorkOrderTechnicianRow.technician_id == TechnicianRow.id)
        .filter(WorkOrderTechnicianRow.work_order_id == os_id)
        .order_by(TechnicianRow.nome.asc())
        .all()
    )
    return [r[0] for r in rows]


def close_work_order(
    db: Session,
    org_id: int,
    os_id: int,
    solucao: str,
    tempo_min: int,
    custo_pecas: str,
) -> WorkOrderRow:
    wo = get_work_order(db, org_id, os_id)
    if not wo:
        raise ValueError("OS não encontrada.")

    wo.solucao_aplicada = solucao or SEM_INFO
    wo.tempo_gasto_minutos = str(tempo_min)
    wo.custo_pecas = custo_pecas or SEM_INFO
    wo.status = "FECHADA"
    wo.fechamento_em = datetime.now(timezone.utc)

    db.commit()
    db.refresh(wo)
    return wo


def update_work_order_status(
    db: Session,
    org_id: int,
    os_id: int,
    status: str,
    observacao: str,
) -> WorkOrderRow:
    wo = get_work_order(db, org_id, os_id)
    if not wo:
        raise ValueError("OS não encontrada.")

    wo.status = status
    wo.status_observacao = (observacao or "").strip()
    wo.status_updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(wo)
    return wo