import { useEffect, useState } from "react";
import { buscarContas } from "../api";

const NOMES = {
  balanco_ativo: "Balanço - Ativo",
  balanco_passivo: "Balanço - Passivo",
  dre: "Resultado (DRE)",
  fluxo_caixa: "Fluxo de caixa",
  dva: "Valor adicionado",
};

const COLUNAS = {
  atual: "Atual",
  exercicio_anterior: "Ano anterior",
  trimestre_atual: "Trimestre atual",
  acumulado_atual: "Acumulado atual",
  trimestre_anterior: "Trimestre anterior",
  acumulado_anterior: "Acumulado anterior",
};

const numero = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 4 });

export default function Busca() {
  const [termo, setTermo] = useState("");
  const [escopo, setEscopo] = useState("consolidadas");
  const [resposta, setResposta] = useState(null);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    if (termo.trim().length < 2) {
      setResposta(null);
      return;
    }
    const espera = setTimeout(() => {
      buscarContas(termo.trim(), escopo)
        .then((r) => {
          setResposta(r);
          setErro(false);
        })
        .catch(() => setErro(true));
    }, 300);
    return () => clearTimeout(espera);
  }, [termo, escopo]);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-slate-900">Buscar uma conta</h2>
      <p className="mt-1 text-sm text-slate-500">
        Digite o nome (caixa, estoques, lucro) ou o código da conta (3.03).
      </p>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row">
        <input
          value={termo}
          onChange={(e) => setTermo(e.target.value)}
          placeholder="Ex.: empréstimos e financiamentos"
          className="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 text-sm outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
        />
        <select
          value={escopo}
          onChange={(e) => setEscopo(e.target.value)}
          className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
        >
          <option value="consolidadas">Consolidado</option>
          <option value="individuais">Individual</option>
        </select>
      </div>

      {erro && <p className="mt-4 text-sm text-rose-600">Não consegui buscar. A API está rodando?</p>}

      {resposta && (
        <div className="mt-4">
          <p className="text-xs text-slate-400">
            {resposta.total} resultado(s). Valores em R$ mil.
          </p>
          <ul className="mt-2 divide-y divide-slate-100">
            {resposta.resultados.slice(0, 30).map((c) => (
              <li key={`${c.demonstracao}-${c.codigo}`} className="py-3">
                <p className="text-sm font-medium text-slate-800">
                  <span className="mr-2 font-mono text-xs text-slate-400">{c.codigo}</span>
                  {c.descricao}
                </p>
                <p className="text-xs text-indigo-600">
                  {NOMES[c.demonstracao.split("/")[1]] ?? c.demonstracao}
                </p>
                <div className="mt-1 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-600">
                  {c.colunas.map((col, i) => (
                    <span key={col}>
                      <span className="text-xs text-slate-400">{COLUNAS[col] ?? col}: </span>
                      {numero.format(c.valores[i])}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
          {resposta.total > 30 && (
            <p className="mt-2 text-xs text-slate-400">
              Mostrando 30. Refine a busca para ver o resto.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
