from sqlalchemy.orm import Session

from .models import Event, WorkOrderRow
from .schemas import WorkOrder


def event_exists(db: Session, message_id: str) -> bool:
    return db.query(Event).filter(Event.message_id == message_id).first() is not None


def save_event(db: Session, message_id: str, chat_id: str, raw_update: str, extracted_text: str) -> Event:
    ev = Event(
        message_id=message_id,
        chat_id=chat_id,
        raw_update=raw_update,
        extracted_text=extracted_text or "",
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev


def save_work_order(db: Session, chat_id: str, wo: WorkOrder, source_text: str) -> WorkOrderRow:
    row = WorkOrderRow(
        chat_id=chat_id,
        equipamento=wo.equipamento,
        setor=wo.setor,
        solicitante=wo.solicitante,
        executor=wo.executor,
        descricao_do_problema=wo.descrição_do_problema,
        tipo_manutencao=wo.tipo_manutenção,
        status=wo.status,
        tempo_gasto_minutos=str(wo.tempo_gasto_minutos),
        custo_pecas=str(wo.custo_peças),
        solucao_aplicada=wo.solução_aplicada,
        source_text=source_text or "",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
