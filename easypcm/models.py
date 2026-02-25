from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Boolean
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


# ============================================================
# MULTI-EMPRESA (ORG) + USUÁRIOS + INVITES
# ============================================================

class OrganizationRow(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserRow(Base):
    __tablename__ = "users"

    telegram_user_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)  # ex: "1350252394"
    username: Mapped[str] = mapped_column(String, default="")
    first_name: Mapped[str] = mapped_column(String, default="")
    is_master: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OrgUserRow(Base):
    __tablename__ = "org_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)
    telegram_user_id: Mapped[str] = mapped_column(String, ForeignKey("users.telegram_user_id"), index=True)

    role: Mapped[str] = mapped_column(String, default="ORG_USER")  # ORG_ADMIN / ORG_USER
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InviteRow(Base):
    __tablename__ = "invites"

    token: Mapped[str] = mapped_column(String, primary_key=True, index=True)  # ex: INV-AB12CD
    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("organizations.id"), index=True)

    role_to_grant: Mapped[str] = mapped_column(String, default="ORG_USER")  # ORG_ADMIN / ORG_USER
    created_by_user_id: Mapped[str] = mapped_column(String, index=True)  # telegram_user_id
    expires_at: Mapped[str] = mapped_column(DateTime(timezone=True), index=True)

    used_by_user_id: Mapped[str] = mapped_column(String, default="", index=True)  # vazio = não usado
    used_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ============================================================
# WORK ORDERS
# ============================================================

class WorkOrderRow(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # NOVO: empresa / organização dona da OS
    org_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)

    # chat_id (mantemos para histórico / compatibilidade, mas deixa de ser "dono")
    chat_id: Mapped[str] = mapped_column(String, index=True)

    equipamento: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    setor: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")

    descricao_do_problema: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")
    maquina_parada: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")  # SIM / NAO

    solucao_aplicada: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")
    tempo_gasto_minutos: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")
    custo_pecas: Mapped[str] = mapped_column(String, default="SEM INFORMAÇÃO")

    status: Mapped[str] = mapped_column(String, default="ABERTA")  # ABERTA / FECHADA / etc
    status_observacao: Mapped[str] = mapped_column(Text, default="")
    status_updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    abertura_em: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    fechamento_em: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaterialRow(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_orders.id"), index=True)
    descricao: Mapped[str] = mapped_column(Text, default="SEM INFORMAÇÃO")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TechnicianRow(Base):
    __tablename__ = "technicians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, unique=True, index=True)


class WorkOrderTechnicianRow(Base):
    __tablename__ = "work_order_technicians"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_orders.id"), index=True)
    technician_id: Mapped[int] = mapped_column(Integer, ForeignKey("technicians.id"), index=True)


class ChatState(Base):
    __tablename__ = "chat_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    chat_id: Mapped[str] = mapped_column(String, unique=True, index=True)

    mode: Mapped[str] = mapped_column(String, default="IDLE")  # IDLE, OPEN_FLOW, CLOSE_FLOW, UPDATE_FLOW
    step: Mapped[str] = mapped_column(String, default="")
    os_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # abertura
    temp_equipamento: Mapped[str] = mapped_column(String, default="")
    temp_setor: Mapped[str] = mapped_column(String, default="")
    temp_problema: Mapped[str] = mapped_column(Text, default="")
    temp_maquina_parada: Mapped[str] = mapped_column(String, default="")

    # fechamento
    temp_solucao: Mapped[str] = mapped_column(Text, default="")
    temp_inicio_hhmm: Mapped[str] = mapped_column(String, default="")
    temp_fim_hhmm: Mapped[str] = mapped_column(String, default="")
    temp_tecnicos: Mapped[str] = mapped_column(Text, default="")
    temp_materiais: Mapped[str] = mapped_column(Text, default="")
    temp_custo_pecas: Mapped[str] = mapped_column(String, default="")

    # atualização
    temp_status: Mapped[str] = mapped_column(String, default="")
    temp_status_obs: Mapped[str] = mapped_column(Text, default="")

    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )