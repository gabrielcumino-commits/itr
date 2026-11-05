import { useEffect, useState } from "react";
import { getIndicadores } from "./api";
import CardIndicador from "./components/CardIndicador";
import Grafico from "./components/Grafico";
import Busca from "./components/Busca";

function agrupar(indicadores) {
  const grupos = new Map();
  for (const ind of indicadores) {
    if (!grupos.has(ind.grupo)) grupos.set(ind.grupo, []);
    grupos.get(ind.grupo).push(ind);
  }
  return [...grupos];
}

export default function App() {
  const [dados, setDados] = useState(null);
  const [erro, setErro] = useState(false);

  useEffect(() => {
    getIndicadores().then(setDados).catch(() => setErro(true));
  }, []);

  if (erro) {
    return (
      <main className="mx-auto max-w-xl p-10 text-center">
        <h1 className="text-xl font-semibold text-slate-900">Não consegui falar com a API</h1>
        <p className="mt-2 text-sm text-slate-600">
          Na raiz do projeto, rode:
        </p>
        <code className="mt-3 inline-block rounded-lg bg-slate-900 px-4 py-2 text-sm text-slate-100">
          py -m uvicorn api.main:app --reload
        </code>
      </main>
    );
  }

  if (!dados) {
    return <p className="p-10 text-center text-slate-500">Carregando...</p>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600">
            Analisador de ITR
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900">{dados.empresa}</h1>
          <p className="text-sm text-slate-500">
            Data-base: {dados.data_base} · demonstrações consolidadas · valores em reais
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-10 px-6 py-8">
        <Grafico indicadores={dados.indicadores} />

        {agrupar(dados.indicadores).map(([grupo, lista]) => (
          <section key={grupo}>
            <h2 className="mb-4 text-lg font-semibold text-slate-900">{grupo}</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {lista.map((ind) => (
                <CardIndicador key={ind.id} ind={ind} />
              ))}
            </div>
          </section>
        ))}

        <Busca />
      </main>
    </div>
  );
}
