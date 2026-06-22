import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
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
  isoDate?: string
  sales: number
  orders?: number
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
  total?: number
  status?: string
}

type CategoryPerformance = {
  name: string
  value: number
  orders: number
  units: number
}

type StatusPoint = {
  name: string
  value: number
}

type LowStockItem = {
  id: string
  name: string
  category: string
  stock: number
}

type TopCustomer = {
  name: string
  revenue: number
  orders: number
}

type DashboardData = {
  totalRevenue: number
  totalOrders: number
  averageTicket: number
  inventoryUnits: number
  activeCategories: number
  ordersToday: number
  paidOrders: number
  pendingOrders: number
  shippedOrders: number
  lowStockCount: number
  revenueDeltaPct: number
  ordersDeltaPct: number
  realtimeRevenue: number
  lastUpdated: string
  periodSummary: {
    current: {
      revenue: number
      orders: number
    }
    previous: {
      revenue: number
      orders: number
    }
  }
  inventoryStatus: InventoryItem[]
  salesOverTime: SalesPoint[]
  topProducts: TopProduct[]
  recentActivity: RecentActivity[]
  categoryPerformance: CategoryPerformance[]
  orderStatus: StatusPoint[]
  lowStockItems: LowStockItem[]
  topCustomers: TopCustomer[]
}

type OrderItem = {
  product_id?: string
  product_name?: string
  quantity?: number
  unit_price?: number
  produtoId?: string
  produtoNome?: string
  quantidade?: number
  preco?: number
}

type RawOrder = {
  id?: string
  customer_name?: string
  clienteNome?: string
  total?: number
  status?: string
  created_at?: string
  dataCriacao?: string
  items?: OrderItem[]
  itens?: OrderItem[]
}

type RawProduct = {
  id?: string
  stock?: number
}

type TabKey = 'overview' | 'orders' | 'drivers'

const fallbackData: DashboardData = {
  totalRevenue: 0,
  totalOrders: 0,
  averageTicket: 0,
  inventoryUnits: 0,
  activeCategories: 0,
  ordersToday: 0,
  paidOrders: 0,
  pendingOrders: 0,
  shippedOrders: 0,
  lowStockCount: 0,
  revenueDeltaPct: 0,
  ordersDeltaPct: 0,
  realtimeRevenue: 0,
  lastUpdated: '',
  periodSummary: {
    current: { revenue: 0, orders: 0 },
    previous: { revenue: 0, orders: 0 },
  },
  inventoryStatus: [],
  salesOverTime: [],
  topProducts: [],
  recentActivity: [],
  categoryPerformance: [],
  orderStatus: [],
  lowStockItems: [],
  topCustomers: [],
}

const statsUrl = import.meta.env.VITE_STATS_API_URL ?? 'http://localhost:5000/stats'
const apiToken = import.meta.env.VITE_API_TOKEN?.trim() ?? ''
const apiFetchOptions: RequestInit = apiToken
  ? { cache: 'no-store', headers: { Authorization: `Bearer ${apiToken}` } }
  : { cache: 'no-store' }
const pollMs = 15000
const chartColors = ['#f6c453', '#ff8f6b', '#44c4a1', '#54a6ff', '#a78bfa', '#f472b6']
const tabs: { id: TabKey; label: string; caption: string }[] = [
  { id: 'overview', label: 'Visão geral', caption: 'Receita, tendências e mix de categorias' },
  { id: 'orders', label: 'Pedidos', caption: 'Fluxo, expedição e recência' },
  { id: 'drivers', label: 'Drivers', caption: 'Pressão de estoque e demanda recorrente' },
]

const formatCurrency = (value: number) =>
  `R$ ${Number(value || 0).toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`

const formatDelta = (value: number, suffix = 'vs 7d anteriores') => {
  const signal = value > 0 ? '+' : ''
  return `${signal}${value.toFixed(1)}% ${suffix}`
}

const formatUpdatedAt = (value: string) => {
  if (!value) return 'Aguardando sincronizacao'

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value

  return parsed.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const formatOrderMoment = (value?: string) => {
  if (!value) return 'Aguardando sincronizacao'

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return value

  return parsed.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const normalizeStatus = (value?: string) => {
  const normalized = String(value || 'pendente').trim().toLowerCase()

  if (normalized === 'paid') return 'pago'
  if (normalized === 'shipped') return 'enviado'
  if (normalized === 'pending') return 'pendente'

  return normalized || 'pendente'
}

const normalizeOrder = (order: RawOrder) => {
  const items = (order.items ?? order.itens ?? []).map((item) => ({
    product_id: item.product_id ?? item.produtoId ?? '',
    product_name: item.product_name ?? item.produtoNome ?? 'Item',
    quantity: Number(item.quantity ?? item.quantidade ?? 1) || 1,
    unit_price: Number(item.unit_price ?? item.preco ?? 0) || 0,
  }))

  return {
    id: order.id ?? '',
    customer_name: order.customer_name ?? order.clienteNome ?? 'Cliente',
    total:
      Number(order.total ?? 0) ||
      items.reduce((sum, item) => sum + item.quantity * item.unit_price, 0),
    status: normalizeStatus(order.status),
    created_at: order.created_at ?? order.dataCriacao ?? '',
  }
}

const buildRecentActivityFromOrders = (orders: RawOrder[]): RecentActivity[] =>
  orders
    .map(normalizeOrder)
    .sort((left, right) => {
      const leftTime = new Date(left.created_at).getTime()
      const rightTime = new Date(right.created_at).getTime()
      return rightTime - leftTime
    })
    .slice(0, 5)
    .map((order) => ({
      id: order.id,
      label: `Pedido ${order.id} - ${order.status}`,
      customer: order.customer_name,
      created_at: order.created_at,
      total: order.total,
      status: order.status,
    }))

const countInventoryUnits = (products: RawProduct[]) =>
  products.reduce((sum, product) => sum + (Number(product.stock ?? 0) || 0), 0)

function KPIItem({
  title,
  value,
  trend,
  accent = 'amber',
}: {
  title: string
  value: string | number
  trend: string
  accent?: 'amber' | 'emerald' | 'sky' | 'rose'
}) {
  const accentClass = {
    amber: 'border-amber-300/20 bg-amber-300/10 text-amber-100',
    emerald: 'border-emerald-300/20 bg-emerald-300/10 text-emerald-100',
    sky: 'border-sky-300/20 bg-sky-300/10 text-sky-100',
    rose: 'border-rose-300/20 bg-rose-300/10 text-rose-100',
  }[accent]

  return (
    <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-5 shadow-[0_18px_60px_rgba(0,0,0,0.28)] backdrop-blur-xl">
      <p className="mb-2 text-sm text-slate-400">{title}</p>
      <div className="flex items-end justify-between gap-3">
        <h3 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">{value}</h3>
        <span
          className={`rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] ${accentClass}`}
        >
          {trend}
        </span>
      </div>
    </div>
  )
}

function Panel({
  title,
  subtitle,
  children,
  className = '',
}: {
  title: string
  subtitle?: string
  children: ReactNode
  className?: string
}) {
  return (
    <section
      className={`rounded-[30px] border border-white/10 bg-slate-950/65 p-6 shadow-[0_28px_80px_rgba(0,0,0,0.24)] backdrop-blur-xl ${className}`}
    >
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
        </div>
      </div>
      {children}
    </section>
  )
}

function EmptyChartMessage({ message }: { message: string }) {
  return (
    <div className="flex h-full items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-black/10 px-6 text-center text-sm text-slate-400">
      {message}
    </div>
  )
}

function InsightCard({
  title,
  body,
  tone = 'neutral',
}: {
  title: string
  body: string
  tone?: 'neutral' | 'warm' | 'danger'
}) {
  const toneClass = {
    neutral: 'border-white/10 bg-white/[0.035]',
    warm: 'border-amber-300/20 bg-amber-300/10',
    danger: 'border-rose-300/20 bg-rose-300/10',
  }[tone]

  return (
    <div className={`rounded-[24px] border p-5 ${toneClass}`}>
      <p className="text-sm font-semibold uppercase tracking-[0.22em] text-white/70">{title}</p>
      <p className="mt-3 text-sm leading-6 text-slate-200">{body}</p>
    </div>
  )
}

export default function SalesDashboard() {
  const [data, setData] = useState<DashboardData>(fallbackData)
  const [loading, setLoading] = useState(true)
  const [isOffline, setIsOffline] = useState(false)
  const [activeTab, setActiveTab] = useState<TabKey>('overview')

  useEffect(() => {
    let cancelled = false

    const fetchData = async (keepLoading = false) => {
      try {
        if (!keepLoading) setLoading(true)

        const [statsResponse, ordersResponse, productsResponse] = await Promise.all([
          fetch(statsUrl, apiFetchOptions),
          fetch(statsUrl.replace(/\/stats$/, '/orders'), apiFetchOptions),
          fetch(statsUrl.replace(/\/stats$/, '/products'), apiFetchOptions),
        ])

        if (!statsResponse.ok) {
          throw new Error('Stats indisponiveis')
        }

        const stats = (await statsResponse.json()) as Partial<DashboardData>
        const ordersPayload = ordersResponse.ok
          ? ((await ordersResponse.json()) as { orders?: RawOrder[] })
          : {}
        const productsPayload = productsResponse.ok
          ? ((await productsResponse.json()) as { products?: RawProduct[] })
          : {}

        const recentOrdersFallback = buildRecentActivityFromOrders(
          ordersPayload.orders ?? [],
        )
        const recentActivity = (stats.recentActivity ?? []).map((activity) => {
          const matchingOrder = recentOrdersFallback.find((entry) => entry.id === activity.id)

          return {
            ...activity,
            total: Number(activity.total ?? 0) || matchingOrder?.total || 0,
            status: activity.status ?? matchingOrder?.status ?? 'pendente',
            created_at: activity.created_at || matchingOrder?.created_at || '',
            customer: activity.customer || matchingOrder?.customer || 'Cliente',
          }
        })

        if (cancelled) return

        setData({
          ...fallbackData,
          ...stats,
          inventoryUnits:
            Number(stats.inventoryUnits ?? 0) ||
            countInventoryUnits(productsPayload.products ?? []),
          periodSummary: stats.periodSummary ?? fallbackData.periodSummary,
          inventoryStatus: stats.inventoryStatus ?? fallbackData.inventoryStatus,
          salesOverTime: stats.salesOverTime ?? fallbackData.salesOverTime,
          topProducts: stats.topProducts ?? fallbackData.topProducts,
          recentActivity: recentActivity.length ? recentActivity : recentOrdersFallback,
          categoryPerformance:
            stats.categoryPerformance ?? fallbackData.categoryPerformance,
          orderStatus: stats.orderStatus ?? fallbackData.orderStatus,
          lowStockItems: stats.lowStockItems ?? fallbackData.lowStockItems,
          topCustomers: stats.topCustomers ?? fallbackData.topCustomers,
        })
        setIsOffline(false)
      } catch (error) {
        console.error('Erro ao carregar dashboard', error)
        if (cancelled) return
        setData(fallbackData)
        setIsOffline(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void fetchData()
    const interval = window.setInterval(() => {
      void fetchData(true)
    }, pollMs)

    return () => {
      cancelled = true
      window.clearInterval(interval)
    }
  }, [])

  const orderMix = useMemo(() => {
    const total = data.orderStatus.reduce((sum, item) => sum + Number(item.value || 0), 0)
    return data.orderStatus.map((item) => ({
      ...item,
      share: total ? Math.round((item.value / total) * 100) : 0,
    }))
  }, [data.orderStatus])

  const latestPoint = data.salesOverTime[data.salesOverTime.length - 1]
  const strongestCategory = data.categoryPerformance[0]
  const highestCustomer = data.topCustomers[0]
  const categoryMixTotal = data.categoryPerformance.reduce(
    (sum, item) => sum + Number(item.value || 0),
    0,
  )

  const insights = [
    {
      title: 'Pulso de receita',
      body:
        data.totalOrders > 0
          ? `${formatCurrency(data.realtimeRevenue)} registrados hoje, com ${formatDelta(data.revenueDeltaPct)}.`
          : 'Nenhum pedido confirmado ainda. Assim que os pedidos entrarem, o painel passa a ler o ritmo real automaticamente.',
      tone: data.revenueDeltaPct >= 0 ? 'warm' : 'neutral',
    },
    {
      title: 'Driver de categoria',
      body: strongestCategory
        ? `${strongestCategory.name} lidera com ${formatCurrency(strongestCategory.value)} e ${strongestCategory.units} unidades vendidas no periodo visivel.`
        : 'Sem vendas por categoria suficientes para detectar um driver principal.',
      tone: 'neutral',
    },
    {
      title: 'Pressão de estoque',
      body:
        data.lowStockCount > 0
          ? `${data.lowStockCount} SKUs estao com estoque baixo e ${data.pendingOrders} pedidos ainda exigem acompanhamento operacional.`
          : 'Nenhum SKU em nivel de atencao no momento. O catalogo esta respirando bem.',
      tone: data.lowStockCount > 0 ? 'danger' : 'neutral',
    },
  ] as const

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#08111f] text-white">
        Carregando central de inteligência...
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-transparent px-4 py-5 text-white md:px-8 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="relative overflow-hidden rounded-[34px] border border-white/10 bg-[linear-gradient(135deg,rgba(8,17,31,0.95),rgba(19,35,58,0.92)_45%,rgba(82,48,20,0.82))] p-6 shadow-[0_30px_100px_rgba(0,0,0,0.35)] md:p-8">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(246,196,83,0.22),transparent_28%),radial-gradient(circle_at_left,rgba(84,166,255,0.16),transparent_35%)]" />
          <div className="relative flex flex-col gap-7 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="mb-3 inline-flex rounded-full border border-white/15 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-amber-100">
                Grand Parfum
              </p>
              <h1 className="max-w-2xl text-3xl font-semibold tracking-tight text-white md:text-5xl">
                Inteligência de vendas que acompanha a operação em tempo real
              </h1>
              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-300 md:text-base">
                Pedidos, receita, concentração por categoria e pressão de estoque ficam
                sincronizados com o sistema local para que você acompanhe o que está
                acontecendo agora, e não um painel estático.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 xl:min-w-[420px]">
              <div className="rounded-[24px] border border-white/10 bg-black/15 p-4">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Hoje</p>
                <p className="mt-3 text-2xl font-semibold text-white">
                  {formatCurrency(data.realtimeRevenue)}
                </p>
                <p className="mt-1 text-sm text-slate-400">{data.ordersToday} pedidos hoje</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-black/15 p-4">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Status</p>
                <div className="mt-3 flex items-center gap-2">
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${
                      isOffline ? 'bg-amber-400' : 'animate-pulse bg-emerald-400'
                    }`}
                  />
                  <p className="text-base font-semibold text-white">
                    {isOffline ? 'Fallback offline' : 'Conectado em tempo real'}
                  </p>
                </div>
                <p className="mt-1 text-sm text-slate-400">{formatUpdatedAt(data.lastUpdated)}</p>
              </div>
              <div className="rounded-[24px] border border-white/10 bg-black/15 p-4">
                <p className="text-xs uppercase tracking-[0.22em] text-slate-400">Janela</p>
                <p className="mt-3 text-2xl font-semibold text-white">
                  {data.salesOverTime.length || 14} dias
                </p>
                <p className="mt-1 text-sm text-slate-400">{formatDelta(data.ordersDeltaPct, 'em pedidos')}</p>
              </div>
            </div>
          </div>
        </header>

        <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <KPIItem
            title="Faturamento acumulado"
            value={formatCurrency(data.totalRevenue)}
            trend={formatDelta(data.revenueDeltaPct, '7d')}
            accent="amber"
          />
          <KPIItem
            title="Pedidos capturados"
            value={data.totalOrders}
            trend={`${data.paidOrders} pagos`}
            accent="sky"
          />
          <KPIItem
            title="Ticket medio"
            value={formatCurrency(data.averageTicket)}
            trend={`${data.activeCategories} categorias`}
            accent="emerald"
          />
          <KPIItem
            title="Inventario disponivel"
            value={data.inventoryUnits}
            trend={`${data.lowStockCount} em alerta`}
            accent="rose"
          />
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-full border px-4 py-3 text-left transition ${
                activeTab === tab.id
                  ? 'border-amber-300/30 bg-amber-300/15 text-white'
                  : 'border-white/10 bg-white/[0.035] text-slate-300 hover:bg-white/[0.06]'
              }`}
            >
              <span className="block text-sm font-semibold">{tab.label}</span>
              <span className="mt-1 block text-xs uppercase tracking-[0.18em] text-slate-400">
                {tab.caption}
              </span>
            </button>
          ))}
        </div>

        {activeTab === 'overview' ? (
          <div className="mt-8 space-y-8">
            <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
              {insights.map((item) => (
                <InsightCard
                  key={item.title}
                  title={item.title}
                  body={item.body}
                  tone={item.tone}
                />
              ))}
            </div>

            <div className="grid grid-cols-1 gap-8 xl:grid-cols-[1.6fr_1fr]">
              <Panel
                title="Ritmo de receita e pedidos"
                subtitle="Série diária cronológica construída a partir dos horários reais dos pedidos"
              >
                <div className="h-[340px] w-full">
                  {data.salesOverTime.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={data.salesOverTime}>
                        <defs>
                          <linearGradient id="salesGlow" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#f6c453" stopOpacity={0.45} />
                            <stop offset="95%" stopColor="#f6c453" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#203047" vertical={false} />
                        <XAxis
                          dataKey="date"
                          stroke="#8fa4bd"
                          tickLine={false}
                          axisLine={false}
                          fontSize={12}
                        />
                        <YAxis
                          yAxisId="sales"
                          stroke="#8fa4bd"
                          tickLine={false}
                          axisLine={false}
                          fontSize={12}
                          tickFormatter={(value) => `R$ ${value}`}
                        />
                        <YAxis
                          yAxisId="orders"
                          orientation="right"
                          stroke="#5f7391"
                          tickLine={false}
                          axisLine={false}
                          fontSize={12}
                          allowDecimals={false}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#09101b',
                            border: '1px solid #223149',
                            borderRadius: '16px',
                          }}
                          formatter={(value, name) =>
                            name === 'sales'
                              ? [formatCurrency(Number(value ?? 0)), 'Receita']
                              : [Number(value ?? 0), 'Pedidos']
                          }
                          labelFormatter={(label) => `Dia ${label}`}
                        />
                        <Area
                          yAxisId="sales"
                          type="monotone"
                          dataKey="sales"
                          stroke="#f6c453"
                          strokeWidth={3}
                          fill="url(#salesGlow)"
                          fillOpacity={1}
                        />
                        <Area
                          yAxisId="orders"
                          type="monotone"
                          dataKey="orders"
                          stroke="#5ab0ff"
                          strokeWidth={2}
                          fillOpacity={0}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChartMessage message="Assim que os pedidos forem registrados, a serie diaria aparece aqui com receita e volume." />
                  )}
                </div>
              </Panel>

              <Panel
                title="Mix de receita por categoria"
                subtitle="Participação das categorias com base nas vendas reais"
              >
                <div className="h-[340px] w-full">
                  {data.categoryPerformance.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={data.categoryPerformance}
                          cx="50%"
                          cy="50%"
                          innerRadius={72}
                          outerRadius={112}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {data.categoryPerformance.map((entry, index) => (
                            <Cell
                              key={`${entry.name}-${index}`}
                              fill={chartColors[index % chartColors.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#09101b',
                            border: '1px solid #223149',
                            borderRadius: '16px',
                          }}
                          formatter={(value) => [formatCurrency(Number(value ?? 0)), 'Receita']}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChartMessage message="A distribuicao por categoria sera exibida quando houver itens vendidos." />
                  )}
                </div>
                <div className="mt-4 space-y-3">
                  {data.categoryPerformance.slice(0, 4).map((item, index) => {
                    const share = categoryMixTotal
                      ? Math.round((item.value / categoryMixTotal) * 100)
                      : 0

                    return (
                      <div
                        key={item.name}
                        className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3"
                      >
                        <div className="flex items-center gap-3">
                          <span
                            className="h-3 w-3 rounded-full"
                            style={{ backgroundColor: chartColors[index % chartColors.length] }}
                          />
                          <div>
                            <p className="text-sm font-medium text-white">{item.name}</p>
                            <p className="text-xs text-slate-400">
                              {item.units} unidades · {item.orders} pedidos
                            </p>
                          </div>
                        </div>
                        <span className="text-sm font-semibold text-slate-200">{share}%</span>
                      </div>
                    )
                  })}
                </div>
              </Panel>
            </div>

            <div className="grid grid-cols-1 gap-8 xl:grid-cols-[1.2fr_0.8fr]">
              <Panel
                title="Produtos mais vendidos"
                subtitle="SKUs com maior giro por unidades registradas"
              >
                <div className="h-[320px] w-full">
                  {data.topProducts.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.topProducts} layout="vertical" margin={{ left: 10 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#203047" horizontal={false} />
                        <XAxis type="number" hide />
                        <YAxis
                          type="category"
                          dataKey="name"
                          width={130}
                          stroke="#8fa4bd"
                          tickLine={false}
                          axisLine={false}
                          fontSize={12}
                        />
                        <Tooltip
                          cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                          contentStyle={{
                            backgroundColor: '#09101b',
                            border: '1px solid #223149',
                            borderRadius: '16px',
                          }}
                          formatter={(value) => [Number(value ?? 0), 'Unidades']}
                        />
                        <Bar dataKey="sales" fill="#f6c453" radius={[0, 10, 10, 0]} barSize={18} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyChartMessage message="Os produtos de maior giro aparecem aqui assim que o sistema detectar vendas." />
                  )}
                </div>
              </Panel>

              <Panel title="Concentração comercial" subtitle="Clientes com maior receita acumulada">
                <div className="space-y-3">
                  {data.topCustomers.length ? (
                    data.topCustomers.map((customer, index) => (
                      <div
                        key={`${customer.name}-${index}`}
                        className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"
                      >
                        <div className="flex items-center justify-between gap-4">
                          <div>
                            <p className="text-sm font-semibold text-white">{customer.name}</p>
                            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">
                              {customer.orders} pedidos
                            </p>
                          </div>
                          <p className="text-base font-semibold text-amber-100">
                            {formatCurrency(customer.revenue)}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <EmptyChartMessage message="Os compradores de maior impacto aparecem aqui quando houver historico suficiente." />
                  )}
                </div>
                {highestCustomer ? (
                  <div className="mt-5 rounded-[24px] border border-amber-300/20 bg-amber-300/10 p-4 text-sm leading-6 text-amber-50">
                    {highestCustomer.name} e o cliente com maior faturamento acumulado, somando{' '}
                    {formatCurrency(highestCustomer.revenue)} em {highestCustomer.orders} pedidos.
                  </div>
                ) : null}
              </Panel>
            </div>
          </div>
        ) : null}

        {activeTab === 'orders' ? (
          <div className="mt-8 grid grid-cols-1 gap-8 xl:grid-cols-[1.05fr_1.35fr]">
            <Panel
              title="Visão de expedição"
              subtitle="Equilíbrio operacional entre pedidos pendentes, pagos e enviados"
            >
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Pendentes</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{data.pendingOrders}</p>
                </div>
                <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Pagos</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{data.paidOrders}</p>
                </div>
                <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Enviados</p>
                  <p className="mt-3 text-3xl font-semibold text-white">{data.shippedOrders}</p>
                </div>
              </div>

              <div className="mt-6 space-y-3">
                {orderMix.length ? (
                  orderMix.map((item, index) => (
                    <div key={item.name} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-300">{item.name}</span>
                        <span className="font-semibold text-white">
                          {item.value} pedidos · {item.share}%
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-white/6">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${item.share}%`,
                            backgroundColor: chartColors[index % chartColors.length],
                          }}
                        />
                      </div>
                    </div>
                  ))
                ) : (
                  <EmptyChartMessage message="O mix de status aparece assim que houver pedidos sendo processados." />
                )}
              </div>

              <div className="mt-6 rounded-[24px] border border-white/8 bg-white/[0.03] p-4">
                <p className="text-sm text-slate-300">
                  Ultima leitura do ritmo:
                  <span className="ml-2 font-semibold text-white">
                    {latestPoint
                      ? `${latestPoint.orders ?? 0} pedidos e ${formatCurrency(latestPoint.sales)} no dia ${latestPoint.date}`
                      : 'sem serie disponivel ainda'}
                  </span>
                </p>
              </div>
            </Panel>

            <Panel title="Últimos pedidos" subtitle="Eventos operacionais mais recentes do log ao vivo">
              <div className="overflow-hidden rounded-[24px] border border-white/8">
                <div className="hidden grid-cols-[1.1fr_0.7fr_0.7fr_0.8fr] gap-4 bg-white/[0.04] px-5 py-4 text-xs font-semibold uppercase tracking-[0.22em] text-slate-400 md:grid">
                  <span>Pedido</span>
                  <span>Status</span>
                  <span>Total</span>
                  <span>Momento</span>
                </div>
                <div className="divide-y divide-white/8">
                  {data.recentActivity.length ? (
                    data.recentActivity.map((activity) => (
                      <div
                        key={activity.id}
                        className="grid gap-4 px-5 py-4 md:grid-cols-[1.1fr_0.7fr_0.7fr_0.8fr] md:items-center"
                      >
                        <div>
                          <p className="text-sm font-semibold text-white">{activity.label}</p>
                          <p className="mt-1 text-sm text-slate-400">{activity.customer}</p>
                        </div>
                        <div>
                          <span className="inline-flex rounded-full border border-sky-300/20 bg-sky-300/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-100">
                            {activity.status ?? 'operacao'}
                          </span>
                        </div>
                        <div className="text-sm font-semibold text-white">
                          {formatCurrency(Number(activity.total ?? 0))}
                        </div>
                        <div className="text-sm text-slate-400">
                          {formatOrderMoment(activity.created_at)}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="px-5 py-10">
                      <EmptyChartMessage message="Nenhum pedido recente disponivel no feed ainda." />
                    </div>
                  )}
                </div>
              </div>
            </Panel>
          </div>
        ) : null}

        {activeTab === 'drivers' ? (
          <div className="mt-8 grid grid-cols-1 gap-8 xl:grid-cols-[1fr_1fr]">
            <Panel title="Drivers por categoria" subtitle="Onde a receita se concentra e quanto estoque ainda resta">
              <div className="space-y-4">
                {(data.categoryPerformance.length
                  ? data.categoryPerformance
                  : data.inventoryStatus.map((item) => ({
                      name: item.name,
                      value: 0,
                      units: 0,
                      orders: 0,
                    }))
                ).map((category, index) => {
                  const stockLevel =
                    data.inventoryStatus.find((item) => item.name === category.name)?.value ?? 0
                  const maxReference = Math.max(data.inventoryUnits, 1)
                  const stockShare = Math.max(8, Math.round((stockLevel / maxReference) * 100))

                  return (
                    <div
                      key={category.name}
                      className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"
                    >
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <p className="text-sm font-semibold text-white">{category.name}</p>
                          <p className="mt-1 text-xs text-slate-400">
                            {formatCurrency(category.value)} em vendas · {category.units} unidades
                          </p>
                        </div>
                        <p className="text-sm font-semibold text-slate-200">{stockLevel} em estoque</p>
                      </div>
                      <div className="mt-3 h-2 rounded-full bg-white/6">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${stockShare}%`,
                            backgroundColor: chartColors[index % chartColors.length],
                          }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </Panel>

            <Panel title="Radar de risco de estoque" subtitle="SKUs que merecem atenção antes de frear a operação">
              <div className="space-y-3">
                {data.lowStockItems.length ? (
                  data.lowStockItems.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between rounded-[24px] border border-white/8 bg-white/[0.03] px-4 py-4"
                    >
                      <div>
                        <p className="text-sm font-semibold text-white">{item.name}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-400">
                          {item.category} · {item.id}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-semibold text-rose-100">{item.stock}</p>
                        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">unidades</p>
                      </div>
                    </div>
                  ))
                ) : (
                  <EmptyChartMessage message="Nenhum SKU com pressao de estoque neste momento." />
                )}
              </div>
            </Panel>

            <Panel title="Distribuição de estoque" subtitle="Estoque atual por categoria para orientar o balanceamento">
              <div className="h-[320px] w-full">
                {data.inventoryStatus.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={data.inventoryStatus}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#203047" vertical={false} />
                      <XAxis
                        dataKey="name"
                        stroke="#8fa4bd"
                        tickLine={false}
                        axisLine={false}
                        fontSize={12}
                      />
                      <YAxis
                        stroke="#8fa4bd"
                        tickLine={false}
                        axisLine={false}
                        fontSize={12}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#09101b',
                          border: '1px solid #223149',
                          borderRadius: '16px',
                        }}
                        formatter={(value) => [Number(value ?? 0), 'Itens em estoque']}
                      />
                      <Bar dataKey="value" radius={[10, 10, 0, 0]}>
                        {data.inventoryStatus.map((entry, index) => (
                          <Cell
                            key={`${entry.name}-${index}`}
                            fill={chartColors[index % chartColors.length]}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChartMessage message="A distribuicao do estoque aparece quando o catalogo estiver carregado." />
                )}
              </div>
            </Panel>

            <Panel title="Comparação de período" subtitle="Janela curta contra o bloco anterior para diagnóstico rápido">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">7 dias atuais</p>
                  <p className="mt-3 text-2xl font-semibold text-white">
                    {formatCurrency(data.periodSummary.current.revenue)}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">
                    {data.periodSummary.current.orders} pedidos capturados
                  </p>
                </div>
                <div className="rounded-[24px] border border-white/8 bg-white/[0.03] p-5">
                  <p className="text-xs uppercase tracking-[0.2em] text-slate-400">7 dias anteriores</p>
                  <p className="mt-3 text-2xl font-semibold text-white">
                    {formatCurrency(data.periodSummary.previous.revenue)}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">
                    {data.periodSummary.previous.orders} pedidos capturados
                  </p>
                </div>
              </div>

              <div className="mt-5 rounded-[24px] border border-amber-300/20 bg-amber-300/10 p-5 text-sm leading-6 text-amber-50">
                {data.revenueDeltaPct >= 0
                  ? `A receita esta acelerando ${formatDelta(data.revenueDeltaPct)}. Se esse ritmo continuar, vale priorizar reposicao nas categorias com menor folga.`
                  : `A receita caiu ${Math.abs(data.revenueDeltaPct).toFixed(1)}% vs 7d anteriores. Vale investigar se a queda vem de menos pedidos, ticket menor ou ruptura de estoque.`}
              </div>
            </Panel>
          </div>
        ) : null}
      </div>
    </div>
  )
}
