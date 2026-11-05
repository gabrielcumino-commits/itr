import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const paraBilhoes = (mil) => mil / 1e6;
const formatar = (v) => `R$ ${v.toFixed(2).replace(".", ",")} bi`;

export default function Grafico({ indicadores }) {
  const receita = indicadores.find((i) => i.id === "receita_trimestre");
  const lucro = indicadores.find((i) => i.id === "lucro_trimestre");
  if (!receita || !lucro) return null;

  const atual = receita.grupo.match(/\((.+)\)/)?.[1] ?? "Atual";
  const anterior = receita.referencia.replace(/^ao\s+/, "");

  const dados = [receita, lucro].map((i) => ({
    nome: i.nome,
    [anterior]: paraBilhoes(i.anterior),
    [atual]: paraBilhoes(i.atual),
  }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-sm font-medium text-slate-500">
        Receita e lucro: {atual} contra {anterior}
      </h2>
      <div className="mt-4 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={dados}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="nome" />
            <YAxis tickFormatter={(v) => `${v} bi`} />
            <Tooltip formatter={formatar} />
            <Legend />
            <Bar dataKey={anterior} fill="#cbd5e1" radius={[6, 6, 0, 0]} />
            <Bar dataKey={atual} fill="#4f46e5" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
