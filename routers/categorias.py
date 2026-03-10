from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Categoria
from schemas import CategoriaCreate, CategoriaUpdate, CategoriaOut

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.get("/", response_model=list[CategoriaOut])
def listar_categorias(ativo: bool | None = None, db: Session = Depends(get_db)):
    query = db.query(Categoria)
    if ativo is not None:
        query = query.filter(Categoria.ativo == ativo)
    return query.order_by(Categoria.tipo, Categoria.nome).all()


@router.post("/", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def criar_categoria(payload: CategoriaCreate, db: Session = Depends(get_db)):
    categoria = Categoria(**payload.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.patch("/{categoria_id}", response_model=CategoriaOut)
def atualizar_categoria(categoria_id: UUID, payload: CategoriaUpdate, db: Session = Depends(get_db)):
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(categoria, campo, valor)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def desativar_categoria(categoria_id: UUID, db: Session = Depends(get_db)):
    """Desativa a categoria ao invés de deletar (preserva histórico)."""
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    categoria.ativo = False
    db.commit()
