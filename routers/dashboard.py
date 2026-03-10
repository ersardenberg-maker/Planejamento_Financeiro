from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from schemas import ResumoMensal, SaldoMensal

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/resumo-mensal", response_model=list[ResumoMensal])
def resumo_mensal(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
):
    """Retorna planejado vs realizado por categoria para o mês/ano."""
    rows = db.execute(
        text("SELECT * FROM vw_resumo_mensal WHERE mes = :mes AND ano = :ano ORDER BY tipo, categoria"),
        {"mes": mes, "ano": ano},
    ).mappings().all()
    return [ResumoMensal(**row) for row in rows]


@router.get("/saldo-mensal", response_model=SaldoMensal)
def saldo_mensal(
    mes: int = Query(..., ge=1, le=12),
    ano: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
):
    """Retorna o saldo consolidado do mês: receitas, despesas e saldo."""
    row = db.execute(
        text("SELECT * FROM vw_saldo_mensal WHERE mes = :mes AND ano = :ano"),
        {"mes": mes, "ano": ano},
    ).mappings().first()
    if not row:
        return SaldoMensal(
            mes=mes, ano=ano,
            total_receitas=0, total_despesas=0, saldo_realizado=0,
            total_receitas_plan=0, total_despesas_plan=0, saldo_planejado=0,
        )
    return SaldoMensal(**row)
