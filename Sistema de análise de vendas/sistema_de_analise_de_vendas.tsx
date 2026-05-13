import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';

/**
 * Dashboard de Análise de Vendas Premium
 * Integrado ao Sistema Logístico e E-commerce
 */

const SalesDashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Simulação de carregamento de dados do banco centralizado
  useEffect(() => {
    const fetchData = async () => {
      try {
        // No mundo real: fetch('http://localhost:5000/stats')
        // Aqui: usando dados mockados que refletem o db_mock.json
        const mockData = {
          totalRevenue: 15420.50,
          totalOrders: 42,
          inventoryStatus: [
            { name: 'Eletrônicos', value: 15 },
            { name: 'Moda', value: 25 },
            { name: 'Beleza', value: 12 },
            { name: 'Esportes', value: 18 },
          ],
          salesOverTime: [
            { date: '24/03', sales: 1200 },
            { date: '25/03', sales: 1900 },
            { date: '26/03', sales: 1500 },
            { date: '27/03', sales: 2100 },
            { date: '28/03', sales: 2800 },
            { date: '29/03', sales: 3200 },
            { date: '30/03', sales: 2700 },
          ],
          topProducts: [
            { name: 'Fone Pro Max', sales: 12 },
            { name: 'Smartwatch Fit', sales: 8 },
            { name: 'Tênis Running', sales: 7 },
            { name: 'Kit Skincare', sales: 5 },
          ]
        };
        
        setData(mockData);
        setLoading(false);
      } catch (err) {
        console.error("Erro ao carregar dashboard", err);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="flex h-screen items-center justify-center bg-[#0a0a0c] text-white">Carregando métricas...</div>;

  return (
    <div className="min-h-screen bg-[#0a0a0c] p-8 font-sans text-white">
      {/* Header */}
      <header className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Business Intelligence</h1>
          <p className="text-zinc-400">Análise em tempo real do ecossistema MinhaLoja</p>
        </div>
        <div className="flex gap-4">
          <div className="rounded-lg bg-zinc-900 px-4 py-2 border border-zinc-800">
            <span className="text-xs text-zinc-500 uppercase">Status do Sistema</span>
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
              <span className="text-sm font-medium">Integrado</span>
            </div>
          </div>
        </div>
      </header>

      {/* KPI Cards */}
      <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-4">
        <KPIItem title="Faturamento Total" value={`R$ ${data.totalRevenue.toLocaleString('pt-BR')}`} trend="+12.5%" />
        <KPIItem title="Pedidos Realizados" value={data.totalOrders} trend="+5.2%" />
        <KPIItem title="Ticket Médio" value="R$ 367,15" trend="-1.2%" />
        <KPIItem title="Taxa de Conversão" value="3.8%" trend="+0.4%" />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        
        {/* Sales Chart */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Volume de Vendas (7 dias)</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.salesOverTime}>
                <defs>
                  <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8533ff" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#8533ff" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="date" stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `R$ ${val}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                  itemStyle={{ color: '#fff' }}
                />
                <Area type="monotone" dataKey="sales" stroke="#8533ff" strokeWidth={3} fillOpacity={1} fill="url(#colorSales)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Inventory Pie Chart */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Distribuição de Estoque</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.inventoryStatus}
                  cx="50%" cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  <Cell fill="#818cf8" />
                  <Cell fill="#c084fc" />
                  <Cell fill="#fb7185" />
                  <Cell fill="#34d399" />
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                />
                <Legend iconType="circle" />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Products */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Produtos Mais Vendidos</h3>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.topProducts} layout="vertical">
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" stroke="#71717a" fontSize={12} width={100} tickLine={false} axisLine={false} />
                <Tooltip 
                  cursor={{fill: 'transparent'}}
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #3f3f46', borderRadius: '8px' }}
                />
                <Bar dataKey="sales" fill="#8533ff" radius={[0, 4, 4, 0]} barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Recent Transactions Stub */}
        <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 backdrop-blur-xl">
          <h3 className="mb-6 text-lg font-semibold">Últimas Atividades de Logística</h3>
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex items-center justify-between border-b border-zinc-800 pb-3 last:border-0 last:pb-0">
                <div className="flex items-center gap-3">
                  <div className="h-2 w-2 rounded-full bg-blue-500"></div>
                  <div>
                    <p className="text-sm font-medium">Pedido #ord-00{i} despachado</p>
                    <p className="text-xs text-zinc-500">Há {i * 15} minutos</p>
                  </div>
                </div>
                <span className="text-xs font-semibold text-zinc-400">Ver detalhes</span>
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
      <span className={`text-xs font-bold ${trend.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
        {trend}
      </span>
    </div>
  </div>
);

export default SalesDashboard;
