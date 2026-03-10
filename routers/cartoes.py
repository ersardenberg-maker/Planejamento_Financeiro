from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Cartao
from schemas import CartaoCreate, CartaoUpdate, CartaoOut

router = APIRouter(prefix="/cartoes", tags=["Cartões"])


@router.get("/", response_model=list[CartaoOut])
def listar_cartoes(ativo: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Cartao)
    if ativo is not None:
        query = query.filter(Cartao.ativo == ativo)
    return query.order_by(Cartao.nome).all()


@router.post("/", response_model=CartaoOut, status_code=status.HTTP_201_CREATED)
def criar_cartao(payload: CartaoCreate, db: Session = Depends(get_db)):
    cartao = Cartao(**payload.model_dump())
    db.add(cartao)
    db.commit()
    db.refresh(cartao)
    return cartao


@router.patch("/{cartao_id}", response_model=CartaoOut)
def atualizar_cartao(cartao_id: UUID, payload: CartaoUpdate, db: Session = Depends(get_db)):
    cartao = db.get(Cartao, cartao_id)
    if not cartao:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(cartao, campo, valor)
    db.commit()
    db.refresh(cartao)
    return cartao


@router.delete("/{cartao_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_cartao(cartao_id: UUID, db: Session = Depends(get_db)):
    cartao = db.get(Cartao, cartao_id)
    if not cartao:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    cartao.ativo = False
    db.commit()
