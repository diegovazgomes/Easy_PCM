from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
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

    # Identificação
    equipamento: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    setor: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")

    # Dados iniciais
    descricao_do_problema: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")
    maquina_parada: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")  # SIM / NAO

    # Execução (preenchidos no fechamento)
    solucao_aplicada: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")
    tempo_gasto_minutos: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    custo_pecas: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")

    # Ciclo de vida
    status: Mapped[str] = mapped_column(String, default="ABERTA")  # ABERTA / FECHADA
    abertura_em: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fechamento_em: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Controle
    source_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaterialRow(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_orders.id"), index=True)
    descricao: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ChatState(Base):
    __tablename__ = "chat_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_id: Mapped[str] = mapped_column(String, unique=True, index=True)

    mode: Mapped[str] = mapped_column(String, default="IDLE")  # IDLE, OPEN_FLOW, CLOSE_FLOW, CONSULT_FLOW
    step: Mapped[str] = mapped_column(String, default="")      # qual pergunta estamos esperando
    os_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Dados temporários (abertura)
    temp_equipamento: Mapped[str] = mapped_column(String, default="")
    temp_setor: Mapped[str] = mapped_column(String, default="")
    temp_problema: Mapped[str] = mapped_column(Text, default="")
    temp_maquina_parada: Mapped[str] = mapped_column(String, default="")  # SIM/NAO

    # Dados temporários (fechamento)
    temp_solucao: Mapped[str] = mapped_column(Text, default="")
    temp_inicio_hhmm: Mapped[str] = mapped_column(String, default="")
    temp_fim_hhmm: Mapped[str] = mapped_column(String, default="")
    temp_tecnicos: Mapped[str] = mapped_column(Text, default="")
    temp_materiais: Mapped[str] = mapped_column(Text, default="")
    temp_custo_pecas: Mapped[str] = mapped_column(String, default="")

    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
