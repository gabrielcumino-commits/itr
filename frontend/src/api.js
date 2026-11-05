const BASE = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function get(caminho) {
  const resposta = await fetch(`${BASE}${caminho}`);
  if (!resposta.ok) throw new Error(`Erro ${resposta.status}`);
  return resposta.json();
}

export const getIndicadores = () => get("/indicadores");

export const buscarContas = (termo, escopo) => {
  const filtro = escopo ? `&escopo=${escopo}` : "";
  return get(`/buscar?q=${encodeURIComponent(termo)}${filtro}`);
};
