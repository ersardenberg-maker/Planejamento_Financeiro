from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Planejamento
from schemas import PlanejamentoCreate, PlanejamentoUpdate, PlanejamentoOut, PlanejamentoComCategoria

router = APIRouter(prefix="/planejamento", tags=["Planejamento"])


@router.get("/", response_model=list[PlanejamentoComCategoria])
def listar_planejamento(mes: int | None = None, ano: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Planejamento).options(joinedload(Planejamento.categoria))
    if mes:
        query = query.filter(Planejamento.mes == mes)
    if ano:
        query = query.filter(Planejamento.ano == ano)
    return query.order_by(Planejamento.ano, Planejamento.mes).all()


@router.post("/", response_model=PlanejamentoOut, status_code=status.HTTP_201_CREATED)
def criar_planejamento(payload: PlanejamentoCreate, db: Session = Depends(get_db)):
    # Upsert: atualiza se já existe para esse categoria/mes/ano
    existente = db.query(Planejamento).filter(
        Planejamento.categoria_id == payload.categoria_id,
        Planejamento.mes == payload.mes,
        Planejamento.ano == payload.ano,
    ).first()
    if existente:
        existente.valor = payload.valor
        db.commit()
        db.refresh(existente)
        return existente
    planejamento = Planejamento(**payload.model_dump())
    db.add(planejamento)
    db.commit()
    db.refresh(planejamento)
    return planejamento


@router.patch("/{planejamento_id}", response_model=PlanejamentoOut)
def atualizar_planejamento(planejamento_id: UUID, payload: PlanejamentoUpdate, db: Session = Depends(get_db)):
    planejamento = db.get(Planejamento, planejamento_id)
    if not planejamento:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado")
    planejamento.valor = payload.valor
    db.commit()
    db.refresh(planejamento)
    return planejamento


@router.delete("/{planejamento_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_planejamento(planejamento_id: UUID, db: Session = Depends(get_db)):
    planejamento = db.get(Planejamento, planejamento_id)
    if not planejamento:
        raise HTTPException(status_code=404, detail="Planejamento não encontrado")
    db.delete(planejamento)
    db.commit()
