from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import categorias, cartoes, lancamentos, planejamento, emprestimos, dashboard

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
