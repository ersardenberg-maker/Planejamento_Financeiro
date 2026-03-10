import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Numeric, Boolean, SmallInteger, Text,
    ForeignKey, Date, DateTime, CheckConstraint, UniqueConstraint, Computed
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lancamentos: Mapped[list["Lancamento"]] = relationship(back_populates="categoria")
    planejamentos: Mapped[list["Planejamento"]] = relationship(back_populates="categoria")


class Cartao(Base):
    __tablename__ = "cartoes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    bandeira: Mapped[str | None] = mapped_column(String(50))
    dia_fechamento: Mapped[int | None] = mapped_column(SmallInteger)
    dia_vencimento: Mapped[int | None] = mapped_column(SmallInteger)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lancamentos: Mapped[list["Lancamento"]] = relationship(back_populates="cartao")


class Planejamento(Base):
    __tablename__ = "planejamento"
    __table_args__ = (UniqueConstraint("categoria_id", "mes", "ano"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoria_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categorias.id", ondelete="CASCADE"))
    mes: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    ano: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categoria: Mapped["Categoria"] = relationship(back_populates="planejamentos")


class Lancamento(Base):
    __tablename__ = "lancamentos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    categoria_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categorias.id"))
    descricao: Mapped[str | None] = mapped_column(String(255))
    valor: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data: Mapped[date] = mapped_column(Date, nullable=False)
    meio_pagamento: Mapped[str] = mapped_column(String(30), nullable=False, default="outros")
    cartao_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("cartoes.id"))
    mes_fatura: Mapped[int | None] = mapped_column(SmallInteger)
    ano_fatura: Mapped[int | None] = mapped_column(SmallInteger)
    observacao: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    categoria: Mapped["Categoria"] = relationship(back_populates="lancamentos")
    cartao: Mapped["Cartao | None"] = relationship(back_populates="lancamentos")


class Emprestimo(Base):
    __tablename__ = "emprestimos"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valor_parcela: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_parcelas: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    parcelas_pagas: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    data_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    dia_vencimento: Mapped[int | None] = mapped_column(SmallInteger)
    taxa_juros_mensal: Mapped[Decimal | None] = mapped_column(Numeric(6, 4))
    credor: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ativo")
    observacao: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcelas: Mapped[list["ParcelaEmprestimo"]] = relationship(back_populates="emprestimo")


class ParcelaEmprestimo(Base):
    __tablename__ = "parcelas_emprestimo"
    __table_args__ = (UniqueConstraint("emprestimo_id", "numero_parcela"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    emprestimo_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("emprestimos.id", ondelete="CASCADE"))
    numero_parcela: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False)
    data_pagamento: Mapped[date | None] = mapped_column(Date)
    valor_previsto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    valor_pago: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pendente")
    lancamento_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lancamentos.id"))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    emprestimo: Mapped["Emprestimo"] = relationship(back_populates="parcelas")
