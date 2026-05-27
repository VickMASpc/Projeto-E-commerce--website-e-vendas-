import React, { useEffect, useState } from 'react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const fallbackData = {
  totalRevenue: 0,
  totalOrders: 0,
  averageTicket: 0,
  inventoryStatus: [
    { name: 'Masculino', value: 0 },
    { name: 'Feminino', value: 0 },
    { name: 'Unissex', value: 0 },
    { name: 'Nicho', value: 0 },
  ],
  salesOverTime: [],
  topProducts: [],
  recentActivity: [],
};

const formatCurrency = (value: number) => `R$ ${Number(value || 0).toLocaleString('pt-BR')}`;

const SalesDashboard: React.FC = () => {
  const [data, setData] = useState<any>(fallbackData);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5000/stats');
        if (!response.ok) throw new Error('Stats indisponiveis');
        const stats = await response.json();
        setData({ ...fallbackData, ...stats });
      } catch (err) {
        console.error('Erro ao carregar dashboard', err);
        setData(fallbackData);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="flex h-screen items-center justify-center bg-[#0a0a0c] text-white">Carregando metricas...</div>;
  }

  const inventoryTotal = data.inventoryStatus.reduce((sum: number, item: any) => sum + Number(item.value || 0), 0);
  const recentActivity = data.recentActivity.length
    ? data.recentActivity
    : [{ id: 'empty', label: 'Nenhuma atividade recente', customer: 'Grand Parfum', created_at: 'Aguardando pedidos' }];

  return (
    <div className="min-h-screen bg-[#0a0a0c] p-8 font-sans text-white">
      <header className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Business Intelligence</h1>
          <p className="text-zinc-400">Analise operacional da Grand Parfum</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900 px-4 py-2">
          <span className="text-xs uppercase text-zinc-500">Status do Sistema</span>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 animate-pulse rounded-full bg-green-500"></div>
            <span className="text-sm font-medium">Integrado</span>
          </div>
        </div>
      </header>

      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-4">
        <KPIItem title="Faturamento Total" value={formatCurrency(data.totalRevenue)} trend="beta" />
        <KPIItem title="Pedidos Realizados" value={data.totalOrders} trend="pedidos" />
        <KPIItem title="Ticket Medio" value={formatCurrency(data.averageTicket)} trend="media" />
        <KPIItem title="Itens em Estoque" value={inventoryTotal} trend="catalogo" />
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Volume de Vendas</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.salesOverTime}>
                <defs>
                  <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#d4af37" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#d4af37" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="date" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `R$ ${val}`} />
                <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }} itemStyle={{ color: '#fff' }} />
                <Area type="monotone" dataKey="sales" stroke="#d4af37" strokeWidth={3} fillOpacity={1} fill="url(#colorSales)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Distribuicao de Estoque</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={data.inventoryStatus} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                  <Cell fill="#d4af37" />
                  <Cell fill="#818cf8" />
                  <Cell fill="#34d399" />
                  <Cell fill="#fb7185" />
                  <Cell fill="#c084fc" />
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }} />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Produtos Mais Vendidos</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.topProducts} layout="vertical">
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#71717a" fontSize={12} width={120} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }} />
                <Bar dataKey="sales" fill="#d4af37" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Ultimas Atividades de Logistica</h3>
          <div className="space-y-4">
            {recentActivity.map((activity: any) => (
              <div key={activity.id} className="flex items-center justify-between border-b border-zinc-800 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                  <div>
                    <p className="text-sm font-medium">{activity.label}</p>
                    <p className="text-xs text-zinc-500">{activity.customer} - {activity.created_at}</p>
                  </div>
                </div>
                <span className="text-xs font-semibold text-zinc-400">Operacao</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const KPIItem = ({ title, value, trend }: any) => (
  <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl transition-all hover:bg-zinc-800/50">
    <p className="mb-1 text-sm text-zinc-400">{title}</p>
    <div className="flex items-end justify-between">
      <h4 className="text-2xl font-bold">{value}</h4>
      <span className="text-xs font-bold text-zinc-400">{trend}</span>
    </div>
  </div>
);

export default SalesDashboard;
