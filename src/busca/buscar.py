import json
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
JSON_PADRAO = RAIZ / "data" / "processed" / "ITR.json"
LIMITE = 25


def normalizar(texto):
    sem_acento = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sem_acento if unicodedata.category(c) != "Mn").casefold()


def buscar(dados, termo, escopo=None):
    palavras = normalizar(termo).split()
    achados = []
    for nome, df in dados["demonstracoes"].items():
        if escopo and not nome.startswith(escopo):
            continue
        for conta in df["contas"]:
            alvo = normalizar(conta["descricao"])
            if conta["codigo"].startswith(termo.strip()) or all(p in alvo for p in palavras):
                achados.append({**conta, "demonstracao": nome, "colunas": df["colunas"]})
    return achados


def fmt(valor):
    if isinstance(valor, float):
        return f"{valor:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{valor:,}".replace(",", ".")


def main():
    args = sys.argv[1:]
    escopo = None
    if "--escopo" in args:
        i = args.index("--escopo")
        escopo = args[i + 1]
        args = args[:i] + args[i + 2:]
    if not args:
        sys.exit("Uso: py src/busca/buscar.py caixa [--escopo consolidadas|individuais]")

    if not JSON_PADRAO.exists():
        sys.exit("Rode antes: py src/extrator/extrair.py")

    with open(JSON_PADRAO, encoding="utf-8") as f:
        dados = json.load(f)

    termo = " ".join(args)
    achados = buscar(dados, termo, escopo)
    print(f"{len(achados)} resultado(s) para '{termo}' (valores em R$ mil)\n")
    for conta in achados[:LIMITE]:
        print(f"[{conta['demonstracao']}] {conta['codigo']}  {conta['descricao']}")
        for coluna, valor in zip(conta["colunas"], conta["valores"]):
            print(f"      {coluna.replace('_', ' ')}: {fmt(valor)}")
    if len(achados) > LIMITE:
        print(f"\n... e mais {len(achados) - LIMITE}. Refine a busca ou use --escopo.")


if __name__ == "__main__":
    main()