import { useState } from "react";

const MENOR_E_MELHOR = new Set([
  "divida_bruta",
  "divida_liquida",
  "divida_liquida_pl",
  "endividamento_geral",
]);

function textoVariacao(ind) {
  if (ind.variacao == null) return null;
  const casas = ind.unidade_variacao === "x" ? 2 : 1;
  const numero = new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  }).format(Math.abs(ind.variacao));
  const espaco = ind.unidade_variacao === "p.p." ? " " : "";
  return `${numero}${espaco}${ind.unidade_variacao}`;
}

function corVariacao(ind) {
  if (!ind.variacao) return "bg-slate-100 text-slate-600";
  const subiu = ind.variacao > 0;
  const bom = MENOR_E_MELHOR.has(ind.id) ? !subiu : subiu;
  return bom ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700";
}

export default function CardIndicador({ ind }) {
  const [aberto, setAberto] = useState(false);
  const variacao = textoVariacao(ind);

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-slate-500">{ind.nome}</p>
        {variacao && (
          <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${corVariacao(ind)}`}>
            {ind.variacao > 0 ? "▲" : ind.variacao < 0 ? "▼" : "●"} {variacao}
          </span>
        )}
      </div>

      <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
        {ind.atual_formatado}
      </p>

      {ind.anterior != null && (
        <p className="mt-1 text-xs text-slate-400">antes: {ind.anterior_formatado}</p>
      )}

      <p className="mt-3 text-sm text-slate-600">{ind.leitura}</p>

      <button
        onClick={() => setAberto(!aberto)}
        className="mt-3 self-start text-xs font-medium text-indigo-600 hover:text-indigo-800"
      >
        {aberto ? "Fechar" : "O que é isso?"}
      </button>

      {aberto && (
        <p className="mt-2 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
          {ind.explicacao}
        </p>
      )}
    </div>
  );
}
