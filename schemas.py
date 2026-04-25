import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


# ── Tipos permitidos ────────────────────────────────────────────
TipoCategoria = Literal["receita", "despesa_fixa", "despesa_variavel"]
MeioPagamento = Literal["cartao", "pix", "debito", "dinheiro", "transferencia", "outros"]
StatusEmprestimo = Literal["ativo", "quitado", "pausado"]
StatusParcela = Literal["pendente", "paga", "atrasada"]


# ── Categoria ───────────────────────────────────────────────────
class CategoriaCreate(BaseModel):
    nome: str
    tipo: TipoCategoria

class CategoriaUpdate(BaseModel):
    nome: str | None = None
    tipo: TipoCategoria | None = None
    ativo: bool | None = None

class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    tipo: TipoCategoria
    ativo: bool
    criado_em: datetime


# ── Cartão ──────────────────────────────────────────────────────
class CartaoCreate(BaseModel):
    nome: str
    bandeira: str | None = None
    dia_fechamento: int | None = Field(default=None, ge=1, le=31)
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)

class CartaoUpdate(BaseModel):
    nome: str | None = None
    bandeira: str | None = None
    dia_fechamento: int | None = Field(default=None, ge=1, le=31)
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)
    ativo: bool | None = None

class CartaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    bandeira: str | None
    dia_fechamento: int | None
    dia_vencimento: int | None
    ativo: bool


# ── Planejamento ────────────────────────────────────────────────
class PlanejamentoCreate(BaseModel):
    categoria_id: uuid.UUID
    mes: int = Field(ge=1, le=12)
    ano: int = Field(ge=2000)
    valor: Decimal = Field(ge=0)

class PlanejamentoUpdate(BaseModel):
    valor: Decimal = Field(ge=0)

class PlanejamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    categoria_id: uuid.UUID
    mes: int
    ano: int
    valor: Decimal
    atualizado_em: datetime

class PlanejamentoComCategoria(PlanejamentoOut):
    categoria: CategoriaOut


# ── Lançamento ──────────────────────────────────────────────────
class LancamentoCreate(BaseModel):
    categoria_id: uuid.UUID
    descricao: str | None = None
    valor: Decimal = Field(gt=0)
    data: date
    meio_pagamento: MeioPagamento = "outros"
    cartao_id: uuid.UUID | None = None
    mes_fatura: int | None = Field(default=None, ge=1, le=12)
    ano_fatura: int | None = Field(default=None, ge=2000)
    observacao: str | None = None

class LancamentoUpdate(BaseModel):
    categoria_id: uuid.UUID | None = None
    descricao: str | None = None
    valor: Decimal | None = Field(default=None, gt=0)
    data: date | None = None
    meio_pagamento: MeioPagamento | None = None
    cartao_id: uuid.UUID | None = None
    mes_fatura: int | None = Field(default=None, ge=1, le=12)
    ano_fatura: int | None = Field(default=None, ge=2000)
    observacao: str | None = None

class LancamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    categoria_id: uuid.UUID
    descricao: str | None
    valor: Decimal
    data: date
    meio_pagamento: str
    cartao_id: uuid.UUID | None
    mes_fatura: int | None
    ano_fatura: int | None
    observacao: str | None
    criado_em: datetime
    recorrencia_id: uuid.UUID | None = None

class LancamentoDetalhe(LancamentoOut):
    categoria: CategoriaOut
    cartao: CartaoOut | None


# ── Empréstimo ──────────────────────────────────────────────────
class EmprestimoCreate(BaseModel):
    nome: str
    valor_total: Decimal = Field(gt=0)
    valor_parcela: Decimal = Field(gt=0)
    total_parcelas: int = Field(ge=1)
    data_inicio: date
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)
    taxa_juros_mensal: Decimal | None = None
    credor: str | None = None
    observacao: str | None = None

class EmprestimoUpdate(BaseModel):
    nome: str | None = None
    valor_parcela: Decimal | None = Field(default=None, gt=0)
    parcelas_pagas: int | None = Field(default=None, ge=0)
    dia_vencimento: int | None = Field(default=None, ge=1, le=31)
    status: StatusEmprestimo | None = None
    observacao: str | None = None

class EmprestimoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nome: str
    valor_total: Decimal
    valor_parcela: Decimal
    total_parcelas: int
    parcelas_pagas: int
    data_inicio: date
    dia_vencimento: int | None
    taxa_juros_mensal: Decimal | None
    credor: str | None
    status: StatusEmprestimo
    observacao: str | None


# ── Parcela ─────────────────────────────────────────────────────
class ParcelaUpdate(BaseModel):
    data_pagamento: date | None = None
    valor_pago: Decimal | None = Field(default=None, ge=0)
    status: StatusParcela | None = None
    lancamento_id: uuid.UUID | None = None

class ParcelaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    emprestimo_id: uuid.UUID
    numero_parcela: int
    data_vencimento: date
    data_pagamento: date | None
    valor_previsto: Decimal
    valor_pago: Decimal | None
    status: StatusParcela

class ParcelaComEmprestimo(ParcelaOut):
    emprestimo: EmprestimoOut


# ── Dashboard ───────────────────────────────────────────────────
class ResumoMensal(BaseModel):
    categoria: str
    tipo: TipoCategoria
    mes: int
    ano: int
    planejado: Decimal
    realizado: Decimal
    diferenca: Decimal

class SaldoMensal(BaseModel):
    mes: int
    ano: int
    total_receitas: Decimal
    total_despesas: Decimal
    saldo_realizado: Decimal
    total_receitas_plan: Decimal
    total_despesas_plan: Decimal
    saldo_planejado: Decimal


class RecorrenciaCreate(BaseModel):
    categoria_id: uuid.UUID
    descricao: str
    valor: Decimal = Field(gt=0)
    dia: int = Field(ge=1, le=31)
    meio_pagamento: MeioPagamento = "outros"
    cartao_id: uuid.UUID | None = None
    data_inicio: date | None = None
    data_fim: date | None = None


class RecorrenciaUpdate(BaseModel):
    categoria_id: uuid.UUID | None = None
    descricao: str | None = None
    valor: Decimal | None = Field(default=None, gt=0)
    dia: int | None = Field(default=None, ge=1, le=31)
    meio_pagamento: MeioPagamento | None = None
    cartao_id: uuid.UUID | None = None
    ativo: bool | None = None
    data_inicio: date | None = None
    data_fim: date | None = None


class RecorrenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    categoria_id: uuid.UUID
    descricao: str
    valor: Decimal
    dia: int
    meio_pagamento: str
    cartao_id: uuid.UUID | None
    ativo: bool
    data_inicio: date | None
    data_fim: date | None
