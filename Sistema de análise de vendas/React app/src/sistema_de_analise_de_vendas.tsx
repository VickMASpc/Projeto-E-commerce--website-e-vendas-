import { useEffect, useState } from 'react'
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
} from 'recharts'

type InventoryItem = {
  name: string
  value: number
}

type SalesPoint = {
  date: string
  sales: number
}

type TopProduct = {
  name: string
  sales: number
}

type RecentActivity = {
  id: string
  label: string
  customer: string
  created_at: string
}

type DashboardData = {
  totalRevenue: number
  totalOrders: number
  averageTicket: number
  inventoryStatus: InventoryItem[]
  salesOverTime: SalesPoint[]
  topProducts: TopProduct[]
  recentActivity: RecentActivity[]
}

const fallbackData: DashboardData = {
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
}

const chartColors = ['#d4af37', '#818cf8', '#34d399', '#fb7185', '#c084fc']
const statsUrl = import.meta.env.VITE_STATS_API_URL ?? 'http://localhost:5000/stats'

const formatCurrency = (value: number) =>
  `R$ ${Number(value || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`

const emptyActivity: RecentActivity = {
  id: 'empty',
  label: 'Nenhuma atividade recente',
  customer: 'Grand Parfum',
  created_at: 'Aguardando pedidos',
}

function KPIItem({
  title,
  value,
  trend,
}: {
  title: string
  value: string | number
  trend: string
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-[0_18px_60px_rgba(0,0,0,0.35)] backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:bg-white/8">
      <p className="mb-1 text-sm text-zinc-400">{title}</p>
      <div className="flex items-end justify-between gap-3">
        <h4 className="text-2xl font-bold text-white">{value}</h4>
        <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-200">
          {trend}
        </span>
      </div>
    </div>
  )
}

function EmptyChartMessage({ message }: { message: string }) {
  return (
    <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-white/10 bg-black/10 text-sm text-zinc-400">
      {message}
    </div>
  )
}

export default function SalesDashboard() {
  const [data, setData] = useState<DashboardData>(fallbackData)
  const [loading, setLoading] = useState(true)
  const [isOffline, setIsOffline] = useState(false)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(statsUrl)
        if (!response.ok) {
          throw new Error('Stats indisponiveis')
        }

        const stats = (await response.json()) as Partial<DashboardData>
        setData({
          ...fallbackData,
          ...stats,
          inventoryStatus: stats.inventoryStatus ?? fallbackData.inventoryStatus,
          salesOverTime: stats.salesOverTime ?? fallbackData.salesOverTime,
          topProducts: stats.topProducts ?? fallbackData.topProducts,
          recentActivity: stats.recentActivity ?? fallbackData.recentActivity,
        })
        setIsOffline(false)
      } catch (error) {
        console.error('Erro ao carregar dashboard', error)
        setData(fallbackData)
        setIsOffline(true)
      } finally {
        setLoading(false)
      }
    }

    void fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0a0a0c] text-white">
        Carregando metricas...
      </div>
    )
  }

  const inventoryTotal = data.inventoryStatus.reduce(
    (sum, item) => sum + Number(item.value || 0),
    0,
  )
  const recentActivity = data.recentActivity.length ? data.recentActivity : [emptyActivity]

  return (
    <div className="min-h-screen bg-transparent px-4 py-6 text-white md:px-8 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="mb-3 inline-flex rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-amber-200">
              Grand Parfum
            </p>
            <h1 className="text-3xl font-bold tracking-tight text-white md:text-5xl">
              Business Intelligence
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-zinc-400 md:text-base">
              Painel operacional para acompanhar faturamento, pedidos, estoque e
              movimentacao recente do e-commerce.
            </p>
          </div>

          <div className="rounded-2xl border border-white/10 bg-zinc-950/70 px-4 py-3 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
            <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">
              Status do Sistema
            </span>
            <div className="mt-2 flex items-center gap-2">
              <div
                className={`h-2.5 w-2.5 rounded-full ${
                  isOffline ? 'bg-amber-400' : 'animate-pulse bg-green-500'
                }`}
              />
              <span className="text-sm font-medium text-white">
                {isOffline ? 'Modo offline com dados vazios' : 'Integrado'}
              </span>
            </div>
            <p className="mt-2 text-xs text-zinc-500">{statsUrl}</p>
          </div>
        </header>

        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <KPIItem
            title="Faturamento Total"
            value={formatCurrency(data.totalRevenue)}
            trend="receita"
          />
          <KPIItem title="Pedidos Realizados" value={data.totalOrders} trend="pedidos" />
          <KPIItem
            title="Ticket Medio"
            value={formatCurrency(data.averageTicket)}
            trend="media"
          />
          <KPIItem title="Itens em Estoque" value={inventoryTotal} trend="catalogo" />
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          <section className="rounded-3xl border border-white/10 bg-zinc-950/55 p-6 backdrop-blur-xl">
            <h3 className="mb-6 text-lg font-semibold text-white">Volume de Vendas</h3>
            <div className="h-[300px] w-full">
              {data.salesOverTime.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.salesOverTime}>
                    <defs>
                      <linearGradient id="colorSales" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#d4af37" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#d4af37" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#a1a1aa"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      stroke="#a1a1aa"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(value) => `R$ ${value}`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#18181b',
                        border: '1px solid #3f3f46',
                        borderRadius: '12px',
                      }}
                      itemStyle={{ color: '#fff' }}
                      formatter={(value) => [
                        formatCurrency(Number(value ?? 0)),
                        'Vendas',
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="sales"
                      stroke="#d4af37"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorSales)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChartMessage message="As vendas aparecerao aqui quando houver pedidos processados." />
              )}
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-zinc-950/55 p-6 backdrop-blur-xl">
            <h3 className="mb-6 text-lg font-semibold text-white">Distribuicao de Estoque</h3>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.inventoryStatus}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {data.inventoryStatus.map((entry, index) => (
                      <Cell
                        key={`${entry.name}-${index}`}
                        fill={chartColors[index % chartColors.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#18181b',
                      border: '1px solid #3f3f46',
                      borderRadius: '12px',
                    }}
                    formatter={(value) => [Number(value ?? 0), 'Itens']}
                  />
                  <Legend iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-zinc-950/55 p-6 backdrop-blur-xl">
            <h3 className="mb-6 text-lg font-semibold text-white">Produtos Mais Vendidos</h3>
            <div className="h-[300px] w-full">
              {data.topProducts.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.topProducts} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis
                      dataKey="name"
                      type="category"
                      stroke="#a1a1aa"
                      fontSize={12}
                      width={120}
                      tickLine={false}
                      axisLine={false}
                    />
                    <Tooltip
                      cursor={{ fill: 'transparent' }}
                      contentStyle={{
                        backgroundColor: '#18181b',
                        border: '1px solid #3f3f46',
                        borderRadius: '12px',
                      }}
                      formatter={(value) => [Number(value ?? 0), 'Unidades']}
                    />
                    <Bar dataKey="sales" fill="#d4af37" radius={[0, 4, 4, 0]} barSize={20} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyChartMessage message="Os produtos lideres serao listados quando o sistema registrar vendas." />
              )}
            </div>
          </section>

          <section className="rounded-3xl border border-white/10 bg-zinc-950/55 p-6 backdrop-blur-xl">
            <h3 className="mb-6 text-lg font-semibold text-white">
              Ultimas Atividades de Logistica
            </h3>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div
                  key={activity.id}
                  className="flex items-center justify-between gap-4 border-b border-white/8 pb-3 last:border-0 last:pb-0"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-2.5 w-2.5 rounded-full bg-sky-400" />
                    <div>
                      <p className="text-sm font-medium text-white">{activity.label}</p>
                      <p className="text-xs text-zinc-500">
                        {activity.customer} - {activity.created_at}
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">
                    Operacao
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
