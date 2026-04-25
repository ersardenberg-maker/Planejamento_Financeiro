from uuid import UUID
from datetime import date, timedelta
from calendar import monthrange
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from database import get_db
from models import Cartao, Lancamento, Recorrencia
from schemas import RecorrenciaCreate, RecorrenciaUpdate, RecorrenciaOut, LancamentoOut

router = APIRouter(prefix="/recorrencias", tags=["Recorrencias"])


def _data_no_mes(ano: int, mes: int, dia: int) -> date:
    ultimo_dia = monthrange(ano, mes)[1]
    return date(ano, mes, min(dia, ultimo_dia))


def _calcular_fatura(data_compra: date, cartao: Cartao | None) -> tuple[int | None, int | None]:
    if not cartao:
        return None, None
    mes = data_compra.month
    ano = data_compra.year
    if cartao.dia_fechamento and data_compra.day > cartao.dia_fechamento:
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return mes, ano


@router.get("/", response_model=list[RecorrenciaOut])
def listar_recorrencias(ativo: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Recorrencia)
    if ativo is not None:
        query = query.filter(Recorrencia.ativo == ativo)
    return query.order_by(Recorrencia.descricao).all()


@router.post("/", response_model=RecorrenciaOut, status_code=status.HTTP_201_CREATED)
def criar_recorrencia(payload: RecorrenciaCreate, db: Session = Depends(get_db)):
    recorrencia = Recorrencia(**payload.model_dump())
    db.add(recorrencia)
    db.commit()
    db.refresh(recorrencia)
    return recorrencia


@router.patch("/{recorrencia_id}", response_model=RecorrenciaOut)
def atualizar_recorrencia(recorrencia_id: UUID, payload: RecorrenciaUpdate, db: Session = Depends(get_db)):
    recorrencia = db.get(Recorrencia, recorrencia_id)
    if not recorrencia:
        raise HTTPException(status_code=404, detail="Recorrencia nao encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(recorrencia, campo, valor)
    db.commit()
    db.refresh(recorrencia)
    return recorrencia


@router.delete("/{recorrencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_recorrencia(recorrencia_id: UUID, db: Session = Depends(get_db)):
    recorrencia = db.get(Recorrencia, recorrencia_id)
    if not recorrencia:
        raise HTTPException(status_code=404, detail="Recorrencia nao encontrada")
    recorrencia.ativo = False
    db.commit()


@router.post("/gerar", response_model=list[LancamentoOut])
def gerar_lancamentos_recorrentes(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
):
    inicio = date(ano, mes, 1)
    fim = date(ano + (mes // 12), (mes % 12) + 1, 1)
    recorrencias = db.query(Recorrencia).filter(Recorrencia.ativo == True).all()
    criados = []

    for recorrencia in recorrencias:
        data_lancamento = _data_no_mes(ano, mes, recorrencia.dia)
        if recorrencia.data_inicio and data_lancamento < recorrencia.data_inicio:
            continue
        if recorrencia.data_fim and data_lancamento > recorrencia.data_fim:
            continue
        existente = db.query(Lancamento).filter(
            Lancamento.recorrencia_id == recorrencia.id,
            Lancamento.data >= inicio,
            Lancamento.data < fim,
        ).first()
        if existente:
            continue

        cartao = db.get(Cartao, recorrencia.cartao_id) if recorrencia.cartao_id else None
        mes_fatura, ano_fatura = _calcular_fatura(data_lancamento, cartao)
        lancamento = Lancamento(
            categoria_id=recorrencia.categoria_id,
            descricao=recorrencia.descricao,
            valor=recorrencia.valor,
            data=data_lancamento,
            meio_pagamento=recorrencia.meio_pagamento,
            cartao_id=recorrencia.cartao_id if recorrencia.meio_pagamento == "cartao" else None,
            mes_fatura=mes_fatura if recorrencia.meio_pagamento == "cartao" else None,
            ano_fatura=ano_fatura if recorrencia.meio_pagamento == "cartao" else None,
            recorrencia_id=recorrencia.id,
        )
        db.add(lancamento)
        criados.append(lancamento)

    db.commit()
    for lancamento in criados:
        db.refresh(lancamento)
    return criados
