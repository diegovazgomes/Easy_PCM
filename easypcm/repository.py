from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timezone

from .models import ChatState, WorkOrderRow, MaterialRow
from .schemas import SEM_INFO


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

    # abertura
    st.temp_equipamento = ""
    st.temp_setor = ""
    st.temp_problema = ""
    st.temp_maquina_parada = ""

    # fechamento
    st.temp_solucao = ""
    st.temp_inicio_hhmm = ""
    st.temp_fim_hhmm = ""
    st.temp_tecnicos = ""
    st.temp_materiais = ""
    st.temp_custo_pecas = ""

    db.commit()
    db.refresh(st)
    return st


def create_open_work_order(
    db: Session,
    chat_id: str,
    equipamento: str,
    setor: str,
    problema: str,
    maquina_parada: str,
) -> WorkOrderRow:
    wo = WorkOrderRow(
        chat_id=chat_id,
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


def list_open_work_orders(db: Session, chat_id: str, limit: int = 10) -> list[WorkOrderRow]:
    return (
        db.query(WorkOrderRow)
        .filter(WorkOrderRow.chat_id == chat_id, WorkOrderRow.status == "ABERTA")
        .order_by(desc(WorkOrderRow.id))
        .limit(limit)
        .all()
    )


def get_work_order(db: Session, chat_id: str, os_id: int) -> WorkOrderRow | None:
    return (
        db.query(WorkOrderRow)
        .filter(WorkOrderRow.chat_id == chat_id, WorkOrderRow.id == os_id)
        .first()
    )


def add_materials(db: Session, os_id: int, materiais: list[str]) -> None:
    """
    Cria 1 linha por material em materials.
    """
    for m in materiais:
        desc_txt = (m or "").strip()
        if not desc_txt:
            continue
        row = MaterialRow(work_order_id=os_id, descricao=desc_txt)
        db.add(row)
    db.commit()


def list_materials(db: Session, os_id: int) -> list[MaterialRow]:
    return (
        db.query(MaterialRow)
        .filter(MaterialRow.work_order_id == os_id)
        .order_by(desc(MaterialRow.id))
        .all()
    )


def close_work_order(
    db: Session,
    chat_id: str,
    os_id: int,
    solucao: str,
    tempo_min: int,
    custo_pecas: str,
) -> WorkOrderRow:
    wo = get_work_order(db, chat_id, os_id)
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
