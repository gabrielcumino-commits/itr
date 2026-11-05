import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src.busca.buscar import buscar
from src.indicadores.calcular import calcular

RAIZ = Path(__file__).resolve().parents[1]
JSON_ITR = RAIZ / "data" / "processed" / "ITR.json"

app = FastAPI(title="Analisador de ITR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@lru_cache
def carregar():
    if not JSON_ITR.exists():
        raise HTTPException(
            status_code=503,
            detail="Dados não encontrados. Rode: py src/extrator/extrair.py",
        )
    with open(JSON_ITR, encoding="utf-8") as f:
        return json.load(f)


@app.get("/")
def raiz():
    dados = carregar()
    return {
        "empresa": dados["empresa"],
        "data_base": dados["data_base"],
        "demonstracoes": list(dados["demonstracoes"]),
    }


@app.get("/indicadores")
def indicadores():
    return calcular(carregar())


@app.get("/buscar")
def buscar_contas(
    q: str = Query(..., min_length=2),
    escopo: str | None = Query(None, pattern="^(consolidadas|individuais)$"),
):
    achados = buscar(carregar(), q, escopo)
    return {"termo": q, "total": len(achados), "resultados": achados}


@app.get("/demonstracoes/{escopo}/{nome}")
def demonstracao(escopo: str, nome: str):
    chave = f"{escopo}/{nome}"
    df = carregar()["demonstracoes"].get(chave)
    if df is None:
        raise HTTPException(status_code=404, detail=f"Demonstração '{chave}' não existe.")
    return {"demonstracao": chave, **df}