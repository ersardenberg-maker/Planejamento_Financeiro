from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Lancamento
from schemas import LancamentoCreate, LancamentoUpdate, LancamentoOut, LancamentoDetalhe

router = APIRouter(prefix="/lancamentos", tags=["Lançamentos"])


@router.get("/", response_model=list[LancamentoDetalhe])
def listar_lancamentos(
    mes: int | None = Query(None, ge=1, le=12),
    ano: int | None = Query(None, ge=2000),
    categoria_id: UUID | None = None,
    meio_pagamento: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Lancamento).options(
        joinedload(Lancamento.categoria),
        joinedload(Lancamento.cartao),
    )
    if mes and ano:
        if meio_pagamento == "cartao":
            # Para cartao filtra pelo mes/ano da FATURA, nao da compra
            query = query.filter(
                Lancamento.mes_fatura == mes,
                Lancamento.ano_fatura == ano,
            )
        else:
            # Para outros meios filtra pela data da compra
            query = query.filter(
                Lancamento.data >= date(ano, mes, 1),
                Lancamento.data < date(ano + (mes // 12), (mes % 12) + 1, 1),
            )
    if categoria_id:
        query = query.filter(Lancamento.categoria_id == categoria_id)
    if meio_pagamento:
        query = query.filter(Lancamento.meio_pagamento == meio_pagamento)
    return query.order_by(Lancamento.data.desc()).all()


@router.get("/{lancamento_id}", response_model=LancamentoDetalhe)
def buscar_lancamento(lancamento_id: UUID, db: Session = Depends(get_db)):
    lancamento = db.query(Lancamento).options(
        joinedload(Lancamento.categoria),
        joinedload(Lancamento.cartao),
    ).filter(Lancamento.id == lancamento_id).first()
    if not lancamento:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    return lancamento


@router.post("/", response_model=LancamentoOut, status_code=status.HTTP_201_CREATED)
def criar_lancamento(payload: LancamentoCreate, db: Session = Depends(get_db)):
    lancamento = Lancamento(**payload.model_dump())
    db.add(lancamento)
    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.patch("/{lancamento_id}", response_model=LancamentoOut)
def atualizar_lancamento(lancamento_id: UUID, payload: LancamentoUpdate, db: Session = Depends(get_db)):
    lancamento = db.get(Lancamento, lancamento_id)
    if not lancamento:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(lancamento, campo, valor)
    db.commit()
    db.refresh(lancamento)
    return lancamento


@router.delete("/{lancamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_lancamento(lancamento_id: UUID, db: Session = Depends(get_db)):
    lancamento = db.get(Lancamento, lancamento_id)
    if not lancamento:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    db.delete(lancamento)
    db.commit()
