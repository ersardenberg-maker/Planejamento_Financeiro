from uuid import UUID
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Emprestimo, ParcelaEmprestimo
from schemas import (
    EmprestimoCreate,
    EmprestimoUpdate,
    EmprestimoOut,
    ParcelaUpdate,
    ParcelaOut,
    ParcelaComEmprestimo,
)

router = APIRouter(prefix="/emprestimos", tags=["Emprestimos"])


def _gerar_parcelas(emprestimo: Emprestimo) -> list[ParcelaEmprestimo]:
    parcelas = []
    for i in range(emprestimo.total_parcelas):
        ano = emprestimo.data_inicio.year
        mes = emprestimo.data_inicio.month + i
        while mes > 12:
            mes -= 12
            ano += 1
        dia = emprestimo.dia_vencimento or emprestimo.data_inicio.day
        try:
            vencimento = date(ano, mes, dia)
        except ValueError:
            vencimento = date(ano, mes, 1) + timedelta(days=32)
            vencimento = vencimento.replace(day=1) - timedelta(days=1)

        parcelas.append(ParcelaEmprestimo(
            emprestimo_id=emprestimo.id,
            numero_parcela=i + 1,
            data_vencimento=vencimento,
            valor_previsto=emprestimo.valor_parcela,
        ))
    return parcelas


def _intervalo_mes(mes: int, ano: int) -> tuple[date, date]:
    inicio = date(ano, mes, 1)
    if mes == 12:
        return inicio, date(ano + 1, 1, 1)
    return inicio, date(ano, mes + 1, 1)


def _recalcular_status_emprestimo(emprestimo_id: UUID, db: Session) -> None:
    emprestimo = db.get(Emprestimo, emprestimo_id)
    pagas = db.query(ParcelaEmprestimo).filter(
        ParcelaEmprestimo.emprestimo_id == emprestimo_id,
        ParcelaEmprestimo.status == "paga",
    ).count()
    emprestimo.parcelas_pagas = pagas
    if pagas >= emprestimo.total_parcelas:
        emprestimo.status = "quitado"
    elif emprestimo.status == "quitado":
        emprestimo.status = "ativo"


@router.get("/", response_model=list[EmprestimoOut])
def listar_emprestimos(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Emprestimo)
    if status:
        query = query.filter(Emprestimo.status == status)
    return query.order_by(Emprestimo.data_inicio).all()


@router.get("/parcelas", response_model=list[ParcelaComEmprestimo])
def listar_parcelas_por_mes(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000),
    status: str | None = None,
    db: Session = Depends(get_db),
):
    inicio, fim = _intervalo_mes(mes, ano)
    query = db.query(ParcelaEmprestimo).options(joinedload(ParcelaEmprestimo.emprestimo)).filter(
        ParcelaEmprestimo.data_vencimento >= inicio,
        ParcelaEmprestimo.data_vencimento < fim,
    )
    if status:
        query = query.filter(ParcelaEmprestimo.status == status)
    return query.order_by(ParcelaEmprestimo.data_vencimento).all()


@router.post("/", response_model=EmprestimoOut, status_code=status.HTTP_201_CREATED)
def criar_emprestimo(payload: EmprestimoCreate, db: Session = Depends(get_db)):
    emprestimo = Emprestimo(**payload.model_dump())
    db.add(emprestimo)
    db.flush()
    db.add_all(_gerar_parcelas(emprestimo))
    db.commit()
    db.refresh(emprestimo)
    return emprestimo


@router.get("/{emprestimo_id}/parcelas", response_model=list[ParcelaOut])
def listar_parcelas(emprestimo_id: UUID, db: Session = Depends(get_db)):
    emprestimo = db.get(Emprestimo, emprestimo_id)
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Emprestimo nao encontrado")
    return db.query(ParcelaEmprestimo).filter(
        ParcelaEmprestimo.emprestimo_id == emprestimo_id
    ).order_by(ParcelaEmprestimo.numero_parcela).all()


@router.patch("/{emprestimo_id}", response_model=EmprestimoOut)
def atualizar_emprestimo(emprestimo_id: UUID, payload: EmprestimoUpdate, db: Session = Depends(get_db)):
    emprestimo = db.get(Emprestimo, emprestimo_id)
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Emprestimo nao encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(emprestimo, campo, valor)
    db.commit()
    db.refresh(emprestimo)
    return emprestimo


@router.patch("/{emprestimo_id}/parcelas/{parcela_id}", response_model=ParcelaOut)
def registrar_pagamento_parcela(
    emprestimo_id: UUID, parcela_id: UUID, payload: ParcelaUpdate, db: Session = Depends(get_db)
):
    parcela = db.query(ParcelaEmprestimo).filter(
        ParcelaEmprestimo.id == parcela_id,
        ParcelaEmprestimo.emprestimo_id == emprestimo_id,
    ).first()
    if not parcela:
        raise HTTPException(status_code=404, detail="Parcela nao encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(parcela, campo, valor)
    db.flush()
    _recalcular_status_emprestimo(emprestimo_id, db)
    db.commit()
    db.refresh(parcela)
    return parcela
