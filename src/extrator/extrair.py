
import json
import re
import sys
from pathlib import Path

import pdfplumber

RAIZ = Path(__file__).resolve().parents[2]
PDF_PADRAO = RAIZ / "data" / "raw" / "ITR.pdf"
PASTA_SAIDA = RAIZ / "data" / "processed"

COLUNAS = {
    "balanco": ["atual", "exercicio_anterior"],
    "dre": [
        "trimestre_atual",
        "acumulado_atual",
        "trimestre_anterior",
        "acumulado_anterior",
    ],
    "fluxo_caixa": ["acumulado_atual", "acumulado_anterior"],
    "dva": ["acumulado_atual", "acumulado_anterior"],
}

TIPOS = [
    ("Balanço Patrimonial Ativo", "balanco", "balanco_ativo"),
    ("Balanço Patrimonial Passivo", "balanco", "balanco_passivo"),
    ("Demonstração do Resultado Abrangente", None, None),  # ignorada
    ("Demonstração do Resultado", "dre", "dre"),
    ("Demonstração do Fluxo de Caixa", "fluxo_caixa", "fluxo_caixa"),
    ("Demonstração de Valor Adicionado", "dva", "dva"),
]

PREFIXOS_IGNORADOS = ("(Reais", "Código", "Conta", "ITR -", "PÁGINA", "Exercício", "Atual", "Anterior", "Trimestre")

RE_CABECALHO_DF = re.compile(r"^DFs (Individuais|Consolidadas) / (.+)$")
RE_CODIGO = re.compile(r"^(\d(?:\.\d{2})*)\s+(.+)$")
RE_NUMERO = re.compile(r"^-?\d{1,3}(?:\.\d{3})*(?:,\d+)?$|^-?\d+(?:,\d+)?$")
RE_EMPRESA = re.compile(
    r"^ITR - Informações Trimestrais - (\d{2}/\d{2}/\d{4}) - (.+?)\s+Versão"
)


def converter_numero(texto: str):
    """'-1.627.952' -> -1627952   |   '1,0363' -> 1.0363"""
    limpo = texto.replace(".", "")
    if "," in limpo:
        return float(limpo.replace(",", "."))
    return int(limpo)


def separar_linha(linha: str):
   
    m = RE_CODIGO.match(linha.strip())
    if not m:
        return None
    codigo, resto = m.groups()
    partes = resto.split()

    valores = []
    while partes and RE_NUMERO.match(partes[-1]):
        valores.insert(0, converter_numero(partes.pop()))
    if not valores or not partes:
        return None
    return codigo, " ".join(partes), valores


def identificar_tipo(titulo: str):
    for trecho, tipo, nome in TIPOS:
        if trecho in titulo:
            return tipo, nome
    return None, None


def extrair(caminho_pdf: Path) -> dict:
    resultado = {
        "arquivo": caminho_pdf.name,
        "empresa": None,
        "data_base": None,
        "unidade": "Reais mil",
        "demonstracoes": {},
    }

    viu_dfs = False
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            linhas = [l for l in texto.splitlines() if l.strip()]

            if linhas and resultado["empresa"] is None:
                m = RE_EMPRESA.match(linhas[0])
                if m:
                    resultado["data_base"], resultado["empresa"] = m.groups()

            titulo = next((l for l in linhas[:4] if RE_CABECALHO_DF.match(l)), None)
            if titulo is None:
                if viu_dfs:
                    break  # acabaram as demonstrações (começa o Comentário)
                continue
            viu_dfs = True

            escopo, nome_df = RE_CABECALHO_DF.match(titulo).groups()
            tipo, nome = identificar_tipo(nome_df)
            if tipo is None:
                continue

            chave = f"{escopo.lower()}/{nome}"  # ex.: consolidadas/dre
            contas = resultado["demonstracoes"].setdefault(
                chave, {"colunas": COLUNAS[tipo], "contas": []}
            )["contas"]

            for linha in linhas:
                if linha == titulo or linha.startswith(PREFIXOS_IGNORADOS):
                    continue
                conta = separar_linha(linha)
                if conta:
                    codigo, descricao, valores = conta
                    contas.append(
                        {"codigo": codigo, "descricao": descricao, "valores": valores}
                    )
                elif RE_CODIGO.match(linha.strip()):
                    continue 
                elif contas and not re.search(r"\d{2}/\d{2}/\d{4}", linha):
             
                    contas[-1]["descricao"] += " " + linha.strip()

    return resultado


def valor_conta(dados: dict, demonstracao: str, codigo: str):
    for conta in dados["demonstracoes"].get(demonstracao, {}).get("contas", []):
        if conta["codigo"] == codigo:
            return conta["valores"]
    return None


def verificar(dados: dict):
    print("Conferência (Ativo Total = Passivo Total):")
    for escopo in ("individuais", "consolidadas"):
        ativo = valor_conta(dados, f"{escopo}/balanco_ativo", "1")
        passivo = valor_conta(dados, f"{escopo}/balanco_passivo", "2")
        ok = ativo is not None and ativo == passivo
        print(f"  {escopo}: {'OK' if ok else 'DIVERGENTE'}  {ativo} x {passivo}")


def main():
    pdf = Path(sys.argv[1]) if len(sys.argv) > 1 else PDF_PADRAO
    if not pdf.exists():
        sys.exit(f"Arquivo não encontrado: {pdf}")

    print(f"Lendo {pdf.name} ...")
    dados = extrair(pdf)

    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    saida = PASTA_SAIDA / (pdf.stem + ".json")
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

    print(f"Empresa: {dados['empresa']}  |  Data-base: {dados['data_base']}")
    for nome, df in dados["demonstracoes"].items():
        print(f"  {nome}: {len(df['contas'])} contas")
    print(f"Salvo em {saida}")
    verificar(dados)


if __name__ == "__main__":  
    main()