import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
JSON_PADRAO = RAIZ / "data" / "processed" / "ITR.json"

DRE_TRI_ATUAL, DRE_ACUM_ATUAL, DRE_TRI_ANT, DRE_ACUM_ANT = 0, 1, 2, 3
BP_ATUAL, BP_ANTERIOR = 0, 1


class Demonstracoes:
    def __init__(self, dados: dict):
        self.dados = dados
        self._indice = {}
        for nome, df in dados["demonstracoes"].items():
            self._indice[nome] = {c["codigo"]: c["valores"] for c in df["contas"]}

    def valor(self, demonstracao: str, codigo: str, coluna: int):
        valores = self._indice.get(demonstracao, {}).get(codigo)
        if valores is None or coluna >= len(valores):
            return None
        return valores[coluna]


def dividir(a, b):
    if a is None or b in (None, 0):
        return None
    return a / b


def somar(*valores):
    if any(v is None for v in valores):
        return None
    return sum(valores)


def subtrair(a, b):
    if a is None or b is None:
        return None
    return a - b


def variacao_percentual(atual, anterior):
    if atual is None or anterior in (None, 0):
        return None
    return (atual - anterior) / abs(anterior) * 100


def fmt_numero(x: float, casas: int = 2) -> str:
    texto = f"{x:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_moeda_mil(mil) -> str:
    if mil is None:
        return "n/d"
    reais = mil * 1000
    if abs(reais) >= 1e9:
        return f"R$ {fmt_numero(reais / 1e9)} bi"
    return f"R$ {fmt_numero(reais / 1e6, 0)} mi"


def fmt_valor(valor, formato: str) -> str:
    if valor is None:
        return "n/d"
    if formato == "moeda_mil":
        return fmt_moeda_mil(valor)
    if formato == "percentual":
        return f"{fmt_numero(valor, 1)}%"
    return f"{fmt_numero(valor, 2)}x"


def rotulo_trimestre(data_base: str) -> tuple[str, str]:
    _, mes, ano = (int(p) for p in data_base.split("/"))
    tri = (mes - 1) // 3 + 1
    return f"{tri}T{ano % 100}", f"{tri}T{(ano - 1) % 100}"


def indicador(id_, nome, grupo, formato, atual, anterior, referencia, explicacao):
    if formato == "percentual" or formato == "razao":
        var = None if atual is None or anterior is None else atual - anterior
        unidade = "p.p." if formato == "percentual" else "x"
    else:
        var = variacao_percentual(atual, anterior)
        unidade = "%"

    limiar = 0.005 if unidade == "x" else 0.05
    if atual is not None and anterior is None:
        leitura = "Sem comparação disponível para este indicador."
    elif var is None:
        leitura = "Sem dados suficientes para comparar."
    elif abs(var) < limiar:
        leitura = f"Ficou estável em relação {referencia}."
    else:
        verbo = "subiu" if var > 0 else "caiu"
        casas = 2 if unidade == "x" else 1
        sep = "" if unidade in ("%", "x") else " "
        leitura = (
            f"{nome} {verbo} {fmt_numero(abs(var), casas)}{sep}{unidade} "
            f"em relação {referencia}."
        )

    return {
        "id": id_,
        "nome": nome,
        "grupo": grupo,
        "formato": formato,
        "atual": atual,
        "anterior": anterior,
        "referencia": referencia,
        "variacao": var,
        "unidade_variacao": unidade,
        "atual_formatado": fmt_valor(atual, formato),
        "anterior_formatado": fmt_valor(anterior, formato),
        "leitura": leitura,
        "explicacao": explicacao,
    }


def calcular(dados: dict) -> dict:
    dem = Demonstracoes(dados)
    dre, ativo, passivo = (
        "consolidadas/dre",
        "consolidadas/balanco_ativo",
        "consolidadas/balanco_passivo",
    )

    tri, tri_ant = rotulo_trimestre(dados["data_base"])
    ano = int(dados["data_base"].split("/")[2])
    fim_ano_ant = f"31/12/{ano - 1}"

    def d(codigo, coluna):
        return dem.valor(dre, codigo, coluna)

    def a(codigo, coluna):
        return dem.valor(ativo, codigo, coluna)

    def p(codigo, coluna):
        return dem.valor(passivo, codigo, coluna)

    indicadores = []
    add = indicadores.append

    G = f"Resultado do trimestre ({tri})"
    receita = (d("3.01", DRE_TRI_ATUAL), d("3.01", DRE_TRI_ANT))
    bruto = (d("3.03", DRE_TRI_ATUAL), d("3.03", DRE_TRI_ANT))
    ebit = (d("3.05", DRE_TRI_ATUAL), d("3.05", DRE_TRI_ANT))
    lucro = (d("3.11", DRE_TRI_ATUAL), d("3.11", DRE_TRI_ANT))

    add(indicador(
        "receita_trimestre", "Receita líquida", G, "moeda_mil", *receita, f"ao {tri_ant}",
        "Quanto a empresa vendeu no trimestre, já descontados os impostos sobre a venda.",
    ))
    add(indicador(
        "lucro_trimestre", "Lucro líquido", G, "moeda_mil", *lucro, f"ao {tri_ant}",
        "O que sobrou de dinheiro no final, depois de pagar todos os custos, despesas e impostos.",
    ))
    add(indicador(
        "margem_bruta", "Margem bruta", G, "percentual",
        *(None if x is None else x * 100 for x in (
            dividir(bruto[0], receita[0]), dividir(bruto[1], receita[1]))),
        f"ao {tri_ant}",
        "De cada R$ 100 vendidos, quanto sobra depois de pagar o custo de construir e entregar os imóveis.",
    ))
    add(indicador(
        "margem_operacional", "Margem operacional", G, "percentual",
        *(None if x is None else x * 100 for x in (
            dividir(ebit[0], receita[0]), dividir(ebit[1], receita[1]))),
        f"ao {tri_ant}",
        "De cada R$ 100 vendidos, quanto sobra do negócio em si, antes de juros e impostos.",
    ))
    add(indicador(
        "margem_liquida", "Margem líquida", G, "percentual",
        *(None if x is None else x * 100 for x in (
            dividir(lucro[0], receita[0]), dividir(lucro[1], receita[1]))),
        f"ao {tri_ant}",
        "De cada R$ 100 vendidos, quanto vira lucro no bolso no final de tudo.",
    ))

    G = f"Acumulado do ano (até {dados['data_base']})"
    add(indicador(
        "receita_acumulada", "Receita líquida acumulada", G, "moeda_mil",
        d("3.01", DRE_ACUM_ATUAL), d("3.01", DRE_ACUM_ANT), "ao mesmo período do ano anterior",
        "Tudo o que a empresa vendeu desde 1º de janeiro.",
    ))
    add(indicador(
        "lucro_acumulado", "Lucro líquido acumulado", G, "moeda_mil",
        d("3.11", DRE_ACUM_ATUAL), d("3.11", DRE_ACUM_ANT), "ao mesmo período do ano anterior",
        "Todo o lucro obtido desde 1º de janeiro.",
    ))

    G = "Situação financeira (balanço)"
    ref = f"a {fim_ano_ant}"

    caixa = tuple(somar(a("1.01.01", c), a("1.01.02", c)) for c in (BP_ATUAL, BP_ANTERIOR))
    divida = tuple(somar(p("2.01.04", c), p("2.02.01", c)) for c in (BP_ATUAL, BP_ANTERIOR))
    liquida = tuple(subtrair(divida[i], caixa[i]) for i in (0, 1))
    pl = (p("2.03", BP_ATUAL), p("2.03", BP_ANTERIOR))
    ac = (a("1.01", BP_ATUAL), a("1.01", BP_ANTERIOR))
    pc = (p("2.01", BP_ATUAL), p("2.01", BP_ANTERIOR))
    pnc = (p("2.02", BP_ATUAL), p("2.02", BP_ANTERIOR))

    add(indicador(
        "caixa_aplicacoes", "Caixa e aplicações financeiras", G, "moeda_mil", *caixa, ref,
        "Dinheiro disponível e investimentos de curto prazo que podem virar dinheiro rápido.",
    ))
    add(indicador(
        "divida_bruta", "Dívida bruta", G, "moeda_mil", *divida, ref,
        "Total de empréstimos e financiamentos, de curto e de longo prazo.",
    ))
    add(indicador(
        "divida_liquida", "Dívida líquida", G, "moeda_mil", *liquida, ref,
        "Dívida bruta menos o dinheiro em caixa e aplicações. Mostra o que ainda "
        "ficaria devendo se a empresa usasse o caixa para pagar dívidas.",
    ))
    add(indicador(
        "divida_liquida_pl", "Dívida líquida / patrimônio líquido", G, "percentual",
        *(None if x is None else x * 100 for x in (
            dividir(liquida[0], pl[0]), dividir(liquida[1], pl[1]))),
        ref,
        "Compara a dívida líquida com o que é dos sócios. Quanto menor, mais folgada a situação.",
    ))
    add(indicador(
        "liquidez_corrente", "Liquidez corrente", G, "razao",
        dividir(ac[0], pc[0]), dividir(ac[1], pc[1]), ref,
        "Quanto a empresa tem para receber ou usar em até 12 meses para cada R$ 1 que "
        "precisa pagar no mesmo prazo. Acima de 1 é sinal de folga.",
    ))
    add(indicador(
        "endividamento_geral", "Endividamento geral", G, "razao",
        dividir(somar(pc[0], pnc[0]), pl[0]), dividir(somar(pc[1], pnc[1]), pl[1]), ref,
        "Quanto a empresa deve no total (a prazo curto e longo) para cada R$ 1 de patrimônio dos sócios.",
    ))
    add(indicador(
        "patrimonio_liquido", "Patrimônio líquido", G, "moeda_mil", *pl, ref,
        "O que realmente é dos sócios: tudo o que a empresa tem menos tudo o que deve.",
    ))
    lucro_acum = d("3.11", DRE_ACUM_ATUAL)
    add(indicador(
        "roe_semestre", "Retorno sobre o patrimônio (ROE) do período", G, "percentual",
        None if dividir(lucro_acum, pl[0]) is None else dividir(lucro_acum, pl[0]) * 100,
        None, ref,
        "Quanto a empresa lucrou no período em relação ao patrimônio dos sócios. "
        "Não está convertido para ano inteiro, então não compare direto com taxas anuais.",
    ))

    return {
        "empresa": dados["empresa"],
        "data_base": dados["data_base"],
        "escopo": "consolidadas",
        "indicadores": indicadores,
    }


def imprimir(resultado: dict):
    print(f"{resultado['empresa']}  |  data-base {resultado['data_base']}  |  consolidado\n")
    grupo_atual = None
    for ind in resultado["indicadores"]:
        if ind["grupo"] != grupo_atual:
            grupo_atual = ind["grupo"]
            print(f"\n== {grupo_atual}")
        comparativo = (
            f"  (antes: {ind['anterior_formatado']})" if ind["anterior"] is not None else ""
        )
        print(f"  {ind['nome']}: {ind['atual_formatado']}{comparativo}")
        print(f"      {ind['leitura']}")


def main():
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else JSON_PADRAO
    if not caminho.exists():
        sys.exit(f"Arquivo não encontrado: {caminho}\nRode antes: py src/extrator/extrair.py")

    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)

    resultado = calcular(dados)

    saida = caminho.with_name(caminho.stem + "_indicadores.json")
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    imprimir(resultado)
    print(f"\nSalvo em {saida}")


if __name__ == "__main__":
    main()