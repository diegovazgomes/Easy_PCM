from sqlalchemy import String, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .db import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    chat_id: Mapped[str] = mapped_column(String, index=True)
    raw_update: Mapped[str] = mapped_column(Text)
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WorkOrderRow(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_id: Mapped[str] = mapped_column(String, index=True)

    equipamento: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    setor: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    solicitante: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    executor: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    descricao_do_problema: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")
    tipo_manutencao: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    status: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")

    tempo_gasto_minutos: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    custo_pecas: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")

    solucao_aplicada: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")

    source_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
