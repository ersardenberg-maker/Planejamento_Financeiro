from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from routers import categorias, cartoes, planejamento, lancamentos, emprestimos, dashboard

app = FastAPI(
    title="Financa Familiar API",
    description="Backend para controle financeiro familiar",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://planejamento-financeiro-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(categorias.router)
app.include_router(cartoes.router)
app.include_router(planejamento.router)
app.include_router(lancamentos.router)
app.include_router(emprestimos.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "app": "Financa Familiar API"}


@app.get("/ping-db", tags=["Health"])
def ping_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)}
