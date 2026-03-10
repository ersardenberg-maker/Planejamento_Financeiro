from uuid import UUID
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Emprestimo, ParcelaEmprestimo
from schemas import EmprestimoCreate, EmprestimoUpdate, EmprestimoOut, ParcelaUpdate, ParcelaOut

router = APIRouter(prefix="/emprestimos", tags=["Empréstimos"])


def _gerar_parcelas(emprestimo: Emprestimo) -> list[ParcelaEmprestimo]:
    """Gera automaticamente as parcelas ao criar um empréstimo."""
    parcelas = []
    for i in range(emprestimo.total_parcelas):
        # Calcula o mês de vencimento de cada parcela
        mes_offset = i
        ano = emprestimo.data_inicio.year
        mes = emprestimo.data_inicio.month + mes_offset
        while mes > 12:
            mes -= 12
            ano += 1
        dia = emprestimo.dia_vencimento or emprestimo.data_inicio.day
        try:
            vencimento = date(ano, mes, dia)
        except ValueError:
            # Dia inválido para o mês (ex: 31 em fevereiro) — usa último dia
            vencimento = date(ano, mes, 1) + timedelta(days=32)
            vencimento = vencimento.replace(day=1) - timedelta(days=1)

        parcelas.append(ParcelaEmprestimo(
            emprestimo_id=emprestimo.id,
            numero_parcela=i + 1,
            data_vencimento=vencimento,
            valor_previsto=emprestimo.valor_parcela,
        ))
    return parcelas


@router.get("/", response_model=list[EmprestimoOut])
def listar_emprestimos(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Emprestimo)
    if status:
        query = query.filter(Emprestimo.status == status)
    return query.order_by(Emprestimo.data_inicio).all()


@router.post("/", response_model=EmprestimoOut, status_code=status.HTTP_201_CREATED)
def criar_emprestimo(payload: EmprestimoCreate, db: Session = Depends(get_db)):
    emprestimo = Emprestimo(**payload.model_dump())
    db.add(emprestimo)
    db.flush()  # obtém o id antes do commit
    parcelas = _gerar_parcelas(emprestimo)
    db.add_all(parcelas)
    db.commit()
    db.refresh(emprestimo)
    return emprestimo


@router.get("/{emprestimo_id}/parcelas", response_model=list[ParcelaOut])
def listar_parcelas(emprestimo_id: UUID, db: Session = Depends(get_db)):
    emprestimo = db.get(Emprestimo, emprestimo_id)
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
    return db.query(ParcelaEmprestimo).filter(
        ParcelaEmprestimo.emprestimo_id == emprestimo_id
    ).order_by(ParcelaEmprestimo.numero_parcela).all()


@router.patch("/{emprestimo_id}", response_model=EmprestimoOut)
def atualizar_emprestimo(emprestimo_id: UUID, payload: EmprestimoUpdate, db: Session = Depends(get_db)):
    emprestimo = db.get(Emprestimo, emprestimo_id)
    if not emprestimo:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado")
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
        raise HTTPException(status_code=404, detail="Parcela não encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(parcela, campo, valor)
    # Atualiza parcelas_pagas no empréstimo automaticamente
    if payload.status == "paga":
        emprestimo = db.get(Emprestimo, emprestimo_id)
        pagas = db.query(ParcelaEmprestimo).filter(
            ParcelaEmprestimo.emprestimo_id == emprestimo_id,
            ParcelaEmprestimo.status == "paga",
        ).count()
        emprestimo.parcelas_pagas = pagas + 1
        if emprestimo.parcelas_pagas >= emprestimo.total_parcelas:
            emprestimo.status = "quitado"
    db.commit()
    db.refresh(parcela)
    return parcela
