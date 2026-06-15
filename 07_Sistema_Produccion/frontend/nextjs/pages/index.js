import { getServerSession } from 'next-auth/next'
import { authOptions } from './api/auth/[...nextauth]'
import { signOut, useSession } from 'next-auth/react'
import { useState, useEffect, useMemo } from 'react'
import {
  ComposedChart, BarChart, Bar, Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, ReferenceLine,
} from 'recharts'

// ─── Constants ───────────────────────────────────────────────────────────────

const BLUE = '#1a237e'
const BLUE_LIGHT = '#3b82f6'
const GREEN = '#43a047'
const ORANGE = '#f59e0b'
const RED = '#ef4444'
const PURPLE = '#8b5cf6'
const TEAL = '#06b6d4'
const SKU_COLORS = ['#1a237e','#3b82f6','#43a047','#f59e0b','#ef4444','#8b5cf6','#06b6d4']

const fmt = v => (typeof v === 'number' ? Math.round(v).toLocaleString('es-PE') : v)
const fmtDec = (v, d = 1) => (typeof v === 'number' ? v.toFixed(d) : v)

const MODULES = [
  {
    id: 'historico',
    label: 'Histórico de Ventas y Stock',
    description: 'Resumen ejecutivo, análisis por producto y exploración de datos históricos de ventas y stock.',
    color: '#1a237e',
    bg: '#eff6ff',
    accent: '#3b82f6',
    icon: '📊',
    roles: ['admin', 'gerente_financiero'],
    tabs: [
      { id: 'resumen',            label: 'Resumen Ejecutivo'     },
      { id: 'producto',           label: 'Por Producto'          },
      { id: 'analisis_productos',  label: 'Análisis de Productos'   },
      { id: 'canal_mercado',       label: 'Canal y Mercado'         },
      { id: 'modelo_comparativa',  label: 'Comparativa de Modelos'  },
    ],
  },
  {
    id: 'finanzas',
    label: 'Módulo Finanzas',
    description: 'Proyección de costos de planchas metálicas, inversión semanal por producto y análisis financiero de producción.',
    color: '#0e7490',
    bg: '#f0fdfe',
    accent: '#06b6d4',
    icon: '💰',
    roles: ['admin', 'gerente_financiero'],
    tabs: [
      { id: 'costo_planchas',      label: 'Inversión de Planchas' },
      { id: 'analisis_financiero', label: 'Análisis Financiero Histórico' },
      { id: 'backtest_predicast',  label: 'Simulación con Predicast' },
    ],
  },
  {
    id: 'produccion',
    label: 'Módulo Producción',
    description: 'Planificación operativa, análisis de GAP y calendario de producción con safety stock dinámico.',
    color: '#166534',
    bg: '#f0fdf4',
    accent: '#43a047',
    icon: '🏭',
    roles: ['admin', 'gerente_produccion'],
    tabs: [
      { id: 'produccion',  label: 'Plan de Producción' },
      { id: 'asignacion',  label: 'Asignación de Operarios' },
      { id: 'ingesta',     label: 'Actualización de Datos' },
    ],
  },
  {
    id: 'admin',
    label: 'Administración',
    description: 'Gestión de usuarios, asignación de roles y control de accesos al sistema.',
    color: '#7c3aed',
    bg: '#f5f3ff',
    accent: '#8b5cf6',
    icon: '⚙️',
    roles: ['admin'],
    tabs: [
      { id: 'admin', label: 'Usuarios' },
    ],
  },
]

// ─── Plancha config ───────────────────────────────────────────────────────────

// Fallback mientras carga la config del servidor
const PLANCHA_CONFIG_DEFAULT = {
  precios: { '0.75': 129.95, '1.20': 201.63 },
  skus: {
    CER001:  { tipo: '0.75', prod_por_plancha: 141 },
    CER005:  { tipo: '0.75', prod_por_plancha: 141 },
    CEO001:  { tipo: '0.75', prod_por_plancha: 113 },
    CEO006:  { tipo: '0.75', prod_por_plancha: 113 },
    CER008:  { tipo: '1.20', prod_por_plancha: 115 },
    CER004:  { tipo: '1.20', prod_por_plancha: 141 },
    CERE002: { tipo: '1.20', prod_por_plancha: 141 },
  },
}

function visibleModules(roles) {
  return MODULES.filter(m => m.roles.some(r => roles.includes(r)))
}

// ─── Small helpers ────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, color = BLUE, bg = '#f0f4ff' }) {
  return (
    <div style={{ background: bg, padding: '14px 18px', borderRadius: 8, borderLeft: `4px solid ${color}`, minWidth: 150, flex: 1 }}>
      <div style={{ fontSize: 11, color: '#666', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: '#888', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function SectionTitle({ children, sub, right }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12, marginTop: 24 }}>
      <div>
        <h2 style={{ color: BLUE, margin: 0, fontSize: 17, fontWeight: 700 }}>{children}</h2>
        {sub && <p style={{ color: '#666', margin: '4px 0 0', fontSize: 13 }}>{sub}</p>}
      </div>
      {right && <div style={{ flexShrink: 0, marginLeft: 12, marginTop: 4 }}>{right}</div>}
    </div>
  )
}

function RangeSelector({ value, onChange, options }) {
  return (
    <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
      {options.map(opt => (
        <button key={opt.label} onClick={() => onChange(opt.value)}
          style={{
            padding: '3px 10px', borderRadius: 14,
            border: `1px solid ${value === opt.value ? BLUE : '#cbd5e1'}`,
            background: value === opt.value ? BLUE : '#f8fafc',
            color: value === opt.value ? '#fff' : '#64748b',
            cursor: 'pointer', fontSize: 12, fontWeight: 600,
          }}>
          {opt.label}
        </button>
      ))}
    </div>
  )
}

function Alert({ type = 'info', children }) {
  const colors = {
    info:    { bg: '#eff6ff', border: BLUE_LIGHT, text: '#1e40af' },
    success: { bg: '#f0fdf4', border: GREEN,      text: '#166534' },
    warning: { bg: '#fffbeb', border: ORANGE,     text: '#92400e' },
    danger:  { bg: '#fef2f2', border: RED,        text: '#991b1b' },
  }
  const c = colors[type] || colors.info
  return (
    <div style={{ background: c.bg, border: `1px solid ${c.border}`, borderLeft: `4px solid ${c.border}`, borderRadius: 6, padding: '10px 14px', color: c.text, fontSize: 13, marginBottom: 10 }}>
      {children}
    </div>
  )
}

function SkuSelect({ skus, value, onChange, pareto }) {
  const descMap = useMemo(() => {
    const m = {}
    pareto.forEach(r => { m[r.codigo] = r.descripcion })
    return m
  }, [pareto])
  return (
    <select
      value={value || ''}
      onChange={e => onChange(e.target.value)}
      style={{ padding: '7px 12px', fontSize: 14, borderRadius: 6, border: '1px solid #ccc', minWidth: 220 }}
    >
      {skus.map(s => (
        <option key={s} value={s}>{s}{descMap[s] ? ` — ${descMap[s].slice(0, 30)}` : ''}</option>
      ))}
    </select>
  )
}

// ─── Tab: Resumen Ejecutivo ───────────────────────────────────────────────────

const RANGE_SEMANAL = [
  { label: '1 año',  value: 52  },
  { label: '2 años', value: 104 },
  { label: '3 años', value: 156 },
  { label: 'Todo',   value: 0   },
]

function TabResumen({ pareto, semanal, canal }) {
  const totalVentas = semanal.reduce((s, r) => s + (r.ventas || 0), 0)
  const totalProd   = semanal.reduce((s, r) => s + (r.produccion || 0), 0)
  const periodoDesde = semanal[0]?.semana || ''
  const periodoHasta = semanal[semanal.length - 1]?.semana || ''

  const skuTotals = pareto.slice(0, 7).map((p, i) => ({
    sku: p.codigo,
    total: Math.round(p.ventas),
    fill: SKU_COLORS[i % SKU_COLORS.length],
  }))

  const [semWeeks, setSemWeeks] = useState(104)
  const semanalSlice = semWeeks ? semanal.slice(-semWeeks) : semanal
  const semTick = semanalSlice.length <= 52 ? 6 : semanalSlice.length <= 104 ? 12 : semanalSlice.length <= 156 ? 18 : 26
  const semFrom = semanalSlice[0]?.semana || ''
  const semTo   = semanalSlice[semanalSlice.length - 1]?.semana || ''

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="SKUs monitoreados" value={pareto.length} sub="Productos activos" color={BLUE} />
        <StatCard label="Total ventas históricas" value={fmt(totalVentas)} sub={periodoDesde ? `${periodoDesde} → ${periodoHasta}` : 'acumulado'} color={GREEN} />
        <StatCard label="Total producción histórica" value={fmt(totalProd)} sub="unidades ingresadas" color={ORANGE} />
      </div>

      <SectionTitle
        sub={semFrom ? `${semFrom} → ${semTo} — ventas y producción global consolidadas` : 'Ventas y producción global consolidadas'}
        right={<RangeSelector value={semWeeks} onChange={setSemWeeks} options={RANGE_SEMANAL} />}
      >
        Serie histórica global
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={semanalSlice} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="semana" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % semTick === 0 ? v : ''} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), n === 'ventas' ? 'Ventas' : n === 'produccion' ? 'Producción' : 'Stock']} />
            <Legend formatter={v => ({ ventas: 'Ventas', produccion: 'Producción', stock: 'Stock' }[v] ?? v)} />
            <Area dataKey="stock" name="stock" stroke={TEAL} fill={TEAL} fillOpacity={0.1} dot={false} />
            <Line dataKey="produccion" name="produccion" stroke={ORANGE} strokeWidth={1.5} dot={false} />
            <Line dataKey="ventas" name="ventas" stroke={GREEN} strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'flex', gap: 20, marginTop: 8, flexWrap: 'wrap' }}>
        <div style={{ flex: 2, minWidth: 300 }}>
          <SectionTitle sub="Volumen total de ventas históricas por referencia (Pareto)">
            Ventas por producto
          </SectionTitle>
          <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart layout="vertical" data={skuTotals} margin={{ left: 10, right: 50 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={fmt} />
                <YAxis type="category" dataKey="sku" width={70} tick={{ fontSize: 12, fontWeight: 600 }} />
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <Tooltip formatter={(v, n) => [fmt(v), 'Ventas históricas (u)']} labelFormatter={label => {
                  const p = pareto.find(r => r.codigo === label)
                  return p ? `${label} — ${p.descripcion.slice(0, 40)}` : label
                }} />
                <Bar dataKey="total" name="Ventas históricas" radius={[0, 4, 4, 0]}
                  label={{ position: 'right', formatter: fmt, fontSize: 10, fill: '#555' }}>
                  {skuTotals.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 220 }}>
          <SectionTitle sub="Distribución de ventas históricas por canal">Canal de ventas</SectionTitle>
          <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={canal} dataKey="ventas" nameKey="canal"
                  cx="50%" cy="50%" outerRadius={80}
                  label={({ canal: c, percent }) => `${c}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {canal.map((_, i) => <Cell key={i} fill={[BLUE, GREEN][i % 2]} />)}
                </Pie>
                <Tooltip formatter={v => fmt(v)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Tab: Por Producto ────────────────────────────────────────────────────────

const RANGE_MENSUAL = [
  { label: '1 año',  value: 12 },
  { label: '2 años', value: 24 },
  { label: '3 años', value: 36 },
  { label: 'Todo',   value: 0  },
]

function TabProducto({ sku, setSku, historical, pareto, gap, eficiencia, predictions }) {
  const skuList = pareto.map(r => r.codigo)
  const [lagMonths, setLagMonths] = useState(36)
  const [gapWeeks, setGapWeeks] = useState(104)

  const skuEfic = eficiencia.find(r => r.codigo === sku) || null
  const gapSlice = gapWeeks ? gap.slice(-gapWeeks) : gap
  const gapTick = gapSlice.length <= 52 ? 6 : gapSlice.length <= 104 ? 8 : gapSlice.length <= 156 ? 12 : 20
  const forecastData = predictions?.[sku] || []
  const avgDemanda = forecastData.length ? forecastData.reduce((s, r) => s + r.forecast, 0) / forecastData.length : 0
  const avgProd = gapSlice.length ? gapSlice.reduce((s, r) => s + r.produccion, 0) / gapSlice.length : 0
  const gapRatio = avgProd > 0 ? (avgDemanda / avgProd) * 100 : 0

  const descMap = useMemo(() => {
    const m = {}
    pareto.forEach(r => { m[r.codigo] = r.descripcion })
    return m
  }, [pareto])

  // Annual ventas vs produccion + overproduction gap
  const annualData = useMemo(() => {
    const byYear = {}
    historical.forEach(h => {
      const year = h.semana ? h.semana.slice(0, 4) : null
      if (!year || isNaN(+year)) return
      if (!byYear[year]) byYear[year] = { year, ventas: 0, produccion: 0 }
      byYear[year].ventas += h.ventas || 0
      byYear[year].produccion += h.produccion || 0
    })
    return Object.values(byYear)
      .sort((a, b) => a.year.localeCompare(b.year))
      .map(r => ({ ...r, ventas: Math.round(r.ventas), produccion: Math.round(r.produccion), gap: Math.round(r.produccion - r.ventas) }))
  }, [historical])

  // Monthly produccion vs ventas del mes anterior (company production logic)
  const monthlyLagData = useMemo(() => {
    const byMonth = {}
    historical.forEach(h => {
      const key = h.semana ? h.semana.slice(0, 7) : null
      if (!key || key.length < 7) return
      if (!byMonth[key]) byMonth[key] = { label: key, ventas: 0, produccion: 0 }
      byMonth[key].ventas += h.ventas || 0
      byMonth[key].produccion += h.produccion || 0
    })
    const months = Object.values(byMonth).sort((a, b) => a.label.localeCompare(b.label))
    return months.map((m, i) => ({
      label: m.label,
      produccion: Math.round(m.produccion),
      ventas_anterior: i > 0 ? Math.round(months[i - 1].ventas) : null,
    }))
  }, [historical])

  // Summary stats for annual view
  const totalOverprod = annualData.reduce((s, r) => s + (r.gap > 0 ? r.gap : 0), 0)
  const avgGapPct = annualData.length
    ? annualData.reduce((s, r) => s + (r.ventas > 0 ? (r.gap / r.ventas) * 100 : 0), 0) / annualData.length
    : 0

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 20 }}>
        <div>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 4 }}>PRODUCTO (SKU)</label>
          <SkuSelect skus={skuList} value={sku} onChange={setSku} pareto={pareto} />
        </div>
      </div>

      {descMap[sku] && (
        <p style={{ color: '#555', fontSize: 13, marginBottom: 16, fontStyle: 'italic' }}>{descMap[sku]}</p>
      )}

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="Sobreproducción acumulada" value={fmt(totalOverprod)} color={totalOverprod > 0 ? ORANGE : GREEN} sub="unidades totales sobre ventas" />
        <StatCard label="Gap promedio anual" value={`${fmtDec(avgGapPct, 1)}%`} color={avgGapPct > 10 ? ORANGE : GREEN} sub="(producción − ventas) / ventas" />
      </div>

      <SectionTitle sub="Comparativa anual de ventas totales vs producción ingresada — el gap muestra la sobreproducción de cada año">
        Ventas vs Producción por año — {sku}
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={annualData} margin={{ top: 10, right: 40, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), { ventas: 'Ventas', produccion: 'Producción', gap: 'Gap (Prod − Ventas)' }[n] ?? n]} />
            <Legend formatter={v => ({ ventas: 'Ventas', produccion: 'Producción', gap: 'Gap sobreproducción' }[v] ?? v)} />
            <Bar yAxisId="left" dataKey="ventas" name="ventas" fill={GREEN} opacity={0.85} />
            <Bar yAxisId="left" dataKey="produccion" name="produccion" fill={BLUE_LIGHT} opacity={0.85} />
            <Line yAxisId="right" dataKey="gap" name="gap" stroke={ORANGE} strokeWidth={2.5} dot={{ r: 5, fill: ORANGE }} />
            <ReferenceLine yAxisId="right" y={0} stroke="#999" strokeDasharray="4 4" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <SectionTitle
        sub="Producción mensual (línea) vs ventas del mes anterior (barras) — si la empresa produce en base a ventas previas + % crecimiento, ambas curvas deben seguir el mismo patrón"
        right={<RangeSelector value={lagMonths} onChange={setLagMonths} options={RANGE_MENSUAL} />}
      >
        Lógica de producción mensual — {sku}
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 8 }}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={lagMonths ? monthlyLagData.slice(-lagMonths) : monthlyLagData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % 3 === 0 ? v : ''} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), { produccion: 'Producción (mes t)', ventas_anterior: 'Ventas mes anterior (t−1)' }[n] ?? n]} />
            <Legend formatter={v => ({ produccion: 'Producción (mes t)', ventas_anterior: 'Ventas mes anterior (t−1)' }[v] ?? v)} />
            <Bar dataKey="ventas_anterior" name="ventas_anterior" fill={GREEN} opacity={0.6} />
            <Line dataKey="produccion" name="produccion" stroke={BLUE} strokeWidth={2} dot={false} connectNulls />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p style={{ fontSize: 12, color: '#888', marginTop: 6, marginBottom: 24 }}>
        Si la empresa sigue la lógica de producir según ventas del mes anterior, la línea azul debería tener el mismo patrón que las barras verdes desplazadas un mes.
      </p>

      {/* ── GAP / Planificación ───────────────────────────────────────────── */}
      {skuEfic && (
        <>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
            <StatCard label="Producción total histórica" value={fmt(skuEfic.produccion_total)} sub="unidades" color={BLUE} />
            <StatCard label="Ventas totales históricas" value={fmt(skuEfic.ventas_total)} sub="unidades" color={GREEN} />
            <StatCard label="GAP acumulado (planchas)" value={fmtDec(skuEfic.planchas_gap)} sub="planchas excedente" color={ORANGE} />
            <StatCard label="Eficiencia productiva" value={`${fmtDec(skuEfic.eficiencia)}%`} sub="Ventas / Producción" color={skuEfic.eficiencia >= 98 ? GREEN : ORANGE} />
            <StatCard label="Ahorro potencial" value={`S/ ${fmt(skuEfic.ahorro)}`} sub="optimizando producción" color={PURPLE} />
          </div>
          {skuEfic.eficiencia < 95 && (
            <Alert type="warning">Eficiencia {fmtDec(skuEfic.eficiencia)}% — existe margen de mejora ajustando lotes de producción a la demanda real.</Alert>
          )}
          {skuEfic.eficiencia >= 98 && (
            <Alert type="success">Alta eficiencia operativa ({fmtDec(skuEfic.eficiencia)}%). Producción alineada con demanda real.</Alert>
          )}
        </>
      )}

      <SectionTitle
        sub={gapSlice[0]?.semana ? `${gapSlice[0].semana} → ${gapSlice[gapSlice.length - 1]?.semana} — comparación semanal ventas vs producción real` : 'Comparación semanal ventas vs producción real'}
        right={<RangeSelector value={gapWeeks} onChange={setGapWeeks} options={RANGE_SEMANAL} />}
      >
        Ventas vs Producción semanal — {sku}
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 20 }}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={gapSlice} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="semana" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % gapTick === 0 ? v : ''} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), { ventas: 'Ventas', produccion: 'Producción' }[n] ?? n]} />
            <Legend formatter={v => ({ ventas: 'Ventas reales', produccion: 'Producción ingresada' }[v] ?? v)} />
            <Area dataKey="produccion" name="produccion" stroke={ORANGE} fill={ORANGE} fillOpacity={0.15} dot={false} />
            <Line dataKey="ventas" name="ventas" stroke={GREEN} strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="Producción media histórica/semana" value={fmt(avgProd)} color={ORANGE} />
        {gapRatio > 0 && (
          <StatCard label="Cobertura de demanda" value={`${fmtDec(gapRatio)}%`} color={gapRatio >= 100 ? GREEN : RED} sub={gapRatio >= 100 ? 'Producción suficiente' : 'Producción insuficiente'} />
        )}
      </div>
    </div>
  )
}

// ─── Tab: Comparativa de Modelos ─────────────────────────────────────────────

const ALGO_COLORS = { XGBoost: '#1d4ed8', RandomForest: '#16a34a', Ridge: '#d97706' }
const ALGO_LABELS = { XGBoost: 'XGBoost', RandomForest: 'Random Forest', Ridge: 'Ridge' }
const ALGOS = ['XGBoost', 'RandomForest', 'Ridge']

function TabModeloComparativa({ modeloComparativa }) {
  const [selectedSku, setSelectedSku] = useState(null)

  if (!modeloComparativa.length) return (
    <div style={{ padding: 60, textAlign: 'center', color: '#64748b' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>🤖</div>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>No hay reporte de optimización disponible.</div>
      <div style={{ fontSize: 13 }}>Ejecuta el pipeline desde Actualización de Datos para generar los resultados.</div>
    </div>
  )

  const r2Min = Math.min(...modeloComparativa.flatMap(d => ALGOS.map(a => d.comparativa[a]?.r2 ?? 1)))
  const yDomain = [Math.max(0, Math.floor(r2Min * 100 - 2) / 100), 1]

  const chartData = modeloComparativa.map(d => ({
    sku: d.sku,
    XGBoost:      d.comparativa.XGBoost?.r2      ?? null,
    RandomForest: d.comparativa.RandomForest?.r2  ?? null,
    Ridge:        d.comparativa.Ridge?.r2          ?? null,
  }))

  const ganadorCount = {}
  modeloComparativa.forEach(d => { ganadorCount[d.ganador] = (ganadorCount[d.ganador] || 0) + 1 })
  const topGanador = Object.entries(ganadorCount).sort((a, b) => b[1] - a[1])[0]

  const avgR2 = v => {
    const vals = modeloComparativa.map(d => d.comparativa[v]?.r2).filter(x => x != null)
    return vals.length ? vals.reduce((s, x) => s + x, 0) / vals.length : null
  }

  const detail = selectedSku ? modeloComparativa.find(d => d.sku === selectedSku) : null

  return (
    <div>
      {/* ── Summary cards ── */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="Algoritmo ganador" value={topGanador?.[0] ?? '—'} color={ALGO_COLORS[topGanador?.[0]] ?? BLUE}
          sub={`${topGanador?.[1] ?? 0} de ${modeloComparativa.length} SKUs`} />
        {ALGOS.map(a => {
          const avg = avgR2(a)
          return (
            <StatCard key={a} label={`R² promedio — ${ALGO_LABELS[a]}`}
              value={avg != null ? avg.toFixed(4) : '—'}
              color={ALGO_COLORS[a]}
              sub="validación cruzada (k=5)" />
          )
        })}
      </div>

      {/* ── Grouped bar chart ── */}
      <SectionTitle sub="R² de validación cruzada (TimeSeriesSplit k=5) — eje Y recortado para ampliar diferencias entre algoritmos">
        Comparación de R² por SKU y algoritmo
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 16, justifyContent: 'flex-end', marginBottom: 8, paddingRight: 16 }}>
          {ALGOS.map(a => (
            <span key={a} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#374151' }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, background: ALGO_COLORS[a], display: 'inline-block' }} />
              {ALGO_LABELS[a]}
            </span>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="sku" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" interval={0} />
            <YAxis domain={yDomain} tick={{ fontSize: 11 }} tickFormatter={v => v.toFixed(3)} />
            <Tooltip formatter={(v, n) => [v?.toFixed(4) ?? '—', ALGO_LABELS[n] ?? n]} />
            {ALGOS.map(a => (
              <Bar key={a} dataKey={a} name={a} fill={ALGO_COLORS[a]} radius={[3, 3, 0, 0]} opacity={0.88} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Comparison table ── */}
      <SectionTitle sub="Haz clic en una fila para ver los hiperparámetros del modelo ganador">
        Métricas por producto — modelo ganador vs. alternativas
      </SectionTitle>
      <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 8, marginBottom: 24 }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
          <thead>
            <tr style={{ background: BLUE }}>
              {['SKU', 'Ganador', 'R² XGBoost', 'R² Random Forest', 'R² Ridge', 'MAE (ganador)', 'RMSE (ganador)'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'center', color: '#fff', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {modeloComparativa.map((d, i) => {
              const isSelected = selectedSku === d.sku
              return (
                <tr key={d.sku} onClick={() => setSelectedSku(isSelected ? null : d.sku)}
                  style={{ background: isSelected ? '#eff6ff' : i % 2 === 0 ? '#fafafa' : '#fff', cursor: 'pointer' }}>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee', fontWeight: 700, color: isSelected ? BLUE : '#374151', whiteSpace: 'nowrap' }}>{d.sku}</td>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                    <span style={{ background: ALGO_COLORS[d.ganador] ?? '#e2e8f0', color: '#fff', borderRadius: 10, padding: '2px 10px', fontWeight: 700, fontSize: 11 }}>
                      {d.ganador}
                    </span>
                  </td>
                  {ALGOS.map(a => {
                    const r2 = d.comparativa[a]?.r2
                    const isWinner = d.ganador === a
                    return (
                      <td key={a} style={{ padding: '7px 12px', borderBottom: '1px solid #eee', textAlign: 'center',
                        fontWeight: isWinner ? 800 : 400,
                        color: isWinner ? ALGO_COLORS[a] : '#374151',
                        background: isWinner ? (a === 'XGBoost' ? '#eff6ff' : a === 'RandomForest' ? '#f0fdf4' : '#fffbeb') : 'transparent',
                      }}>
                        {r2 != null ? r2.toFixed(4) : '—'}
                        {isWinner && <span style={{ marginLeft: 4, fontSize: 10 }}>✓</span>}
                      </td>
                    )
                  })}
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                    {d.metricas.mae != null ? d.metricas.mae.toFixed(1) : '—'}
                  </td>
                  <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                    {d.metricas.rmse != null ? d.metricas.rmse.toFixed(1) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* ── Hyperparameters detail ── */}
      {detail && (
        <div style={{ background: '#fff', border: `2px solid ${ALGO_COLORS[detail.ganador] ?? BLUE}`, borderRadius: 10, padding: 20, marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <h3 style={{ margin: 0, color: ALGO_COLORS[detail.ganador] ?? BLUE, fontSize: 15, fontWeight: 700 }}>
              {detail.sku} — Hiperparámetros ganadores ({detail.ganador})
            </h3>
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {Object.entries(detail.hiperparametros).map(([k, v]) => (
              <div key={k} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '8px 14px', minWidth: 120 }}>
                <div style={{ fontSize: 10, color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: 2 }}>{k}</div>
                <div style={{ fontSize: 16, fontWeight: 800, color: ALGO_COLORS[detail.ganador] ?? BLUE }}>{String(v)}</div>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 16 }}>
            <StatCard label="R² validación" value={detail.metricas.r2?.toFixed(4) ?? '—'} color={ALGO_COLORS[detail.ganador] ?? BLUE} />
            <StatCard label="MAE" value={detail.metricas.mae?.toFixed(1) ?? '—'} sub="unidades" color={ALGO_COLORS[detail.ganador] ?? BLUE} />
            <StatCard label="RMSE" value={detail.metricas.rmse?.toFixed(1) ?? '—'} sub="unidades" color={ALGO_COLORS[detail.ganador] ?? BLUE} />
            {detail.metricas.mape != null && (
              <StatCard label="MAPE" value={detail.metricas.mape.toFixed(1) + '%'} sub="error porcentual" color={ALGO_COLORS[detail.ganador] ?? BLUE} />
            )}
          </div>
        </div>
      )}

      {/* ── Métricas finales del ganador por producto ── */}
      <SectionTitle sub="Métricas de test del modelo seleccionado para cada SKU">
        Métricas del modelo ganador por producto
      </SectionTitle>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16, marginBottom: 24 }}>
        {modeloComparativa.map(d => {
          const color = ALGO_COLORS[d.ganador] ?? BLUE
          return (
            <div key={d.sku} style={{ background: '#fff', border: `1px solid ${color}30`, borderLeft: `4px solid ${color}`, borderRadius: 10, padding: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <span style={{ fontWeight: 800, fontSize: 15, color: '#1e293b' }}>{d.sku}</span>
                <span style={{ background: color, color: '#fff', borderRadius: 10, padding: '2px 10px', fontWeight: 700, fontSize: 11 }}>{d.ganador}</span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                {[
                  { label: 'R²',   value: d.metricas.r2   != null ? d.metricas.r2.toFixed(4)              : '—', sub: 'coef. determinación' },
                  { label: 'MAE',  value: d.metricas.mae  != null ? d.metricas.mae.toFixed(1)             : '—', sub: 'unidades'            },
                  { label: 'RMSE', value: d.metricas.rmse != null ? d.metricas.rmse.toFixed(1)            : '—', sub: 'unidades'            },
                  { label: 'MAPE', value: d.metricas.mape != null ? d.metricas.mape.toFixed(1) + '%' : '—', sub: 'error porcentual' },
                ].map(m => (
                  <div key={m.label} style={{ background: '#f8fafc', borderRadius: 8, padding: '8px 12px' }}>
                    <div style={{ fontSize: 10, color: '#64748b', fontWeight: 600, textTransform: 'uppercase', marginBottom: 2 }}>{m.label}</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color }}>{m.value}</div>
                    <div style={{ fontSize: 10, color: '#94a3b8' }}>{m.sub}</div>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── Tab: Análisis de Productos ──────────────────────────────────────────────

const MESES_LABEL = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
const SKU_LINE_COLORS = [BLUE, GREEN, ORANGE, RED, PURPLE, TEAL, '#f97316']

function TabAnalisisProductos({ resumenProductos, pareto }) {
  const descMap = useMemo(() => {
    const m = {}
    pareto.forEach(r => { m[r.codigo.trim()] = r.descripcion })
    return m
  }, [pareto])

  const enriched = resumenProductos.map(p => ({
    ...p,
    descripcion: descMap[p.codigo.trim()] || descMap[p.codigo.replace(/\s+/g, '')] || p.codigo,
  }))

  // Estacionalidad: normalized demand index per month (100 = annual avg)
  const estacionalData = MESES_LABEL.slice(1).map((label, i) => {
    const m = i + 1
    const row = { mes: label }
    enriched.forEach(p => {
      const total12 = p.por_mes.reduce((s, d) => s + d.ventas, 0)
      const avg = total12 / 12
      const mesVal = (p.por_mes.find(d => d.mes === m) || {}).ventas || 0
      row[p.codigo] = avg > 0 ? Math.round((mesVal / avg) * 100) : 0
    })
    return row
  })

  // Annual comparison: all skus by year
  const allAnios = [...new Set(enriched.flatMap(p => p.por_anio.map(a => a.anio)))].sort()
  const anualData = allAnios.map(anio => {
    const row = { anio }
    enriched.forEach(p => {
      const d = p.por_anio.find(a => a.anio === anio)
      row[p.codigo] = d ? d.ventas : null
    })
    return row
  })

  if (!enriched.length) return (
    <div style={{ padding: 60, textAlign: 'center', color: '#64748b' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>📦</div>
      <div style={{ fontWeight: 600 }}>Ejecuta el pipeline para generar el análisis de productos.</div>
    </div>
  )

  return (
    <div>
      {/* ── 1. Impacto e Inversión ───────────────────────────────────────────── */}
      <SectionTitle sub="Total de unidades vendidas vs producidas por producto acumulado en todo el histórico — la brecha muestra cuánto se produjo sin lograr vender">
        Impacto por producto — ventas vs producción acumulada
      </SectionTitle>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        {enriched.map(p => (
          <StatCard key={p.codigo} label={p.codigo}
            value={`${p.eficiencia}%`}
            color={p.eficiencia >= 95 ? GREEN : p.eficiencia >= 85 ? ORANGE : RED}
            sub="eficiencia ventas/producción" />
        ))}
      </div>

      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 16 }}>
        <ResponsiveContainer width="100%" height={Math.max(260, enriched.length * 58)}>
          <BarChart layout="vertical" data={enriched} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <YAxis type="category" dataKey="codigo" width={80} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v, n) => [fmt(v), { total_produccion: 'Total producido (u)', total_ventas: 'Total vendido (u)' }[n] ?? n]} />
            <Legend formatter={v => ({ total_produccion: 'Total producido', total_ventas: 'Total vendido' }[v] ?? v)} />
            <Bar dataKey="total_produccion" name="total_produccion" fill={BLUE_LIGHT} opacity={0.75} radius={[0, 3, 3, 0]} />
            <Bar dataKey="total_ventas"     name="total_ventas"     fill={GREEN}      opacity={0.9}  radius={[0, 3, 3, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── 2. Estacionalidad ───────────────────────────────────────────────── */}
      <SectionTitle sub="Índice 100 = demanda promedio mensual del producto — valores superiores indican meses de alta demanda relativa">
        Estacionalidad mensual por producto
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 8 }}>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={estacionalData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}`} domain={[0, 'auto']} />
            <Tooltip formatter={(v, n) => [`${v} (índice)`, n]} />
            <Legend />
            <ReferenceLine y={100} stroke="#bbb" strokeDasharray="5 4" />
            {enriched.map((p, i) => (
              <Line key={p.codigo} dataKey={p.codigo} name={p.codigo}
                stroke={SKU_LINE_COLORS[i % SKU_LINE_COLORS.length]}
                strokeWidth={2} dot={{ r: 3 }} connectNulls />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p style={{ fontSize: 12, color: '#888', marginTop: 6, marginBottom: 32 }}>
        La línea punteada marca el índice 100 (promedio). Un producto en 150 en julio significa que ese mes vende 50% más que su promedio.
      </p>

      {/* ── 3. Tendencia anual por SKU ──────────────────────────────────────── */}
      <SectionTitle sub="Evolución del volumen de ventas anuales por producto — permite identificar cuáles SKUs crecen, decrecen o se mantienen estables">
        Tendencia anual de ventas por producto
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 32 }}>
        <ResponsiveContainer width="100%" height={260}>
          <ComposedChart data={anualData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="anio" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), n]} />
            <Legend />
            {enriched.map((p, i) => (
              <Line key={p.codigo} dataKey={p.codigo} name={p.codigo}
                stroke={SKU_LINE_COLORS[i % SKU_LINE_COLORS.length]}
                strokeWidth={2} dot={{ r: 5, fill: SKU_LINE_COLORS[i % SKU_LINE_COLORS.length] }} connectNulls />
            ))}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* ── 4. Rotación de inventario ────────────────────────────────────────── */}
      <SectionTitle sub="Número de veces que el inventario promedio se renueva anualmente — mayor rotación indica mayor eficiencia operativa">
        Rotación de inventario por producto
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={Math.max(180, enriched.length * 44)}>
          <BarChart layout="vertical" data={[...enriched].sort((a, b) => b.rotacion - a.rotacion)} margin={{ top: 5, right: 40, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11 }} unit="×" />
            <YAxis type="category" dataKey="codigo" width={80} tick={{ fontSize: 11 }} />
            <Tooltip formatter={v => [`${v}×`, 'Rotación anual']} />
            <Bar dataKey="rotacion" name="Rotación" radius={[0, 4, 4, 0]}
              label={{ position: 'right', formatter: v => `${v}×`, fontSize: 11, fill: '#555' }}>
              {[...enriched].sort((a, b) => b.rotacion - a.rotacion).map((_, i) => (
                <Cell key={i} fill={SKU_LINE_COLORS[i % SKU_LINE_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ─── Tab: Canal y Mercado ─────────────────────────────────────────────────────

function TabCanalMercado({ canalClientes, bodega, pareto }) {
  const { canal_por_producto = [], top_clientes = [] } = canalClientes

  // Pareto SKU set (normalized, no spaces)
  const paretoSet = useMemo(() => new Set((pareto || []).map(p => p.codigo.replace(/\s+/g, ''))), [pareto])

  // Build per-product stacked data — filtered to Pareto SKUs only
  const skuCanalMap = useMemo(() => {
    const m = {}
    canal_por_producto.forEach(r => {
      const cod = r.codigo.replace(/\s+/g, '')
      if (paretoSet.size > 0 && !paretoSet.has(cod)) return
      if (!m[cod]) m[cod] = {}
      m[cod][r.canal] = (m[cod][r.canal] || 0) + r.ventas
    })
    return m
  }, [canal_por_producto, paretoSet])

  const canales = [...new Set(canal_por_producto.map(r => r.canal))].filter(Boolean).sort()
  const CANAL_COLORS = { Online: BLUE, Presencial: GREEN }

  const stackedData = Object.entries(skuCanalMap).map(([sku, vals]) => {
    const total = Object.values(vals).reduce((s, v) => s + v, 0)
    const row = { sku, total }
    canales.forEach(c => {
      row[c] = vals[c] || 0
      row[`${c}_pct`] = total > 0 ? Math.round((row[c] / total) * 100) : 0
    })
    return row
  }).sort((a, b) => b.total - a.total)


  if (!canal_por_producto.length) return (
    <div style={{ padding: 60, textAlign: 'center', color: '#64748b' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>📡</div>
      <div style={{ fontWeight: 600 }}>Ejecuta el pipeline para generar el análisis de canal y clientes.</div>
    </div>
  )

  return (
    <div>
      {/* ── 1. Canal por producto ─────────────────────────────────────────── */}
      <SectionTitle sub="Volumen de ventas por canal (Online vs Presencial) desglosado por producto — identifica qué canales potenciar por SKU">
        Canal de ventas por producto
      </SectionTitle>

      <div style={{ marginBottom: 24 }}>
        <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
          <ResponsiveContainer width="100%" height={Math.max(240, stackedData.length * 56)}>
            <BarChart layout="vertical" data={stackedData} margin={{ top: 5, right: 50, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={fmt} />
              <YAxis type="category" dataKey="sku" width={80} tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v, n) => [fmt(v), n]} />
              <Legend />
              {canales.map(c => (
                <Bar key={c} dataKey={c} name={c} stackId="a"
                  fill={CANAL_COLORS[c] || ORANGE}
                  label={canales.indexOf(c) === canales.length - 1
                    ? { position: 'right', formatter: (_, __, idx) => `${stackedData[idx]?.[`${c}_pct`] ?? ''}%`, fontSize: 10, fill: '#666' }
                    : false} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── 2. Concentración de clientes ─────────────────────────────────── */}
      <SectionTitle sub="Top 15 clientes por volumen total comprado — la curva naranja muestra el % acumulado (Pareto de clientes)">
        Concentración de clientes
      </SectionTitle>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        {top_clientes[0] && (
          <StatCard label="Cliente #1" value={top_clientes[0].cliente}
            color={BLUE} sub={`${fmt(top_clientes[0].ventas)} u — ${top_clientes[0].acumulado_pct}% del total`} />
        )}
        {top_clientes[2] && (
          <StatCard label="Top 3 clientes" value={`${top_clientes[2].acumulado_pct}% del total`}
            color={ORANGE} sub="concentración en 3 clientes" />
        )}
        {top_clientes[4] && (
          <StatCard label="Top 5 clientes" value={`${top_clientes[4].acumulado_pct}% del total`}
            color={top_clientes[4].acumulado_pct >= 80 ? RED : GREEN}
            sub={top_clientes[4].acumulado_pct >= 80 ? 'alta concentración — riesgo' : 'concentración moderada'} />
        )}
      </div>

      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 32 }}>
        <ResponsiveContainer width="100%" height={Math.max(300, top_clientes.length * 26)}>
          <BarChart layout="vertical" data={top_clientes} margin={{ top: 5, right: 60, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <YAxis type="category" dataKey="cliente" width={160} tick={{ fontSize: 10 }}
              tickFormatter={v => v.length > 22 ? v.slice(0, 22) + '…' : v} />
            <Tooltip formatter={(v, n) => [n === 'ventas' ? fmt(v) : `${v}%`, n === 'ventas' ? 'Ventas (u)' : '% acumulado']} />
            <Legend formatter={v => ({ ventas: 'Ventas (u)' }[v] ?? v)} />
            <Bar dataKey="ventas" name="ventas" radius={[0, 4, 4, 0]}
              label={{ position: 'right', formatter: (_, __, idx) => `${top_clientes[idx]?.acumulado_pct ?? ''}%`, fontSize: 10, fill: '#777' }}>
              {top_clientes.map((r, i) => (
                <Cell key={i} fill={r.acumulado_pct <= 50 ? RED : r.acumulado_pct <= 80 ? ORANGE : GREEN} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <p style={{ fontSize: 11, color: '#aaa', marginTop: 4, textAlign: 'center' }}>
          Rojo = clientes que concentran el 50% del volumen · Naranja = hasta 80% · Verde = resto
        </p>
      </div>

      {/* ── 3. Ventas por bodega ──────────────────────────────────────────── */}
      <SectionTitle sub="Volumen total de ventas por almacén / punto de venta — útil para entender dónde se despacha más">
        Ventas por bodega / punto de venta
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={Math.max(160, bodega.length * 44)}>
          <BarChart layout="vertical" data={bodega} margin={{ left: 10, right: 40 }}>
            <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
            <YAxis type="category" dataKey="bodega" width={170} tick={{ fontSize: 10 }}
              tickFormatter={v => v.length > 24 ? v.slice(0, 24) + '…' : v} />
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <Tooltip formatter={v => [fmt(v), 'Ventas (u)']} />
            <Bar dataKey="ventas" name="Ventas" radius={[0, 4, 4, 0]}
              label={{ position: 'right', formatter: fmt, fontSize: 11, fill: '#555' }}>
              {bodega.map((_, i) => <Cell key={i} fill={SKU_COLORS[i % SKU_COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ─── Tab: Plan de Producción ──────────────────────────────────────────────────

function fmtWeekDate(dateStr) {
  const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
  const d = new Date(dateStr + 'T00:00:00')
  return `${String(d.getDate()).padStart(2,'0')} ${months[d.getMonth()]} ${d.getFullYear()}`
}

function TabProduccion({ produccion, safetyWeeks, setSafetyWeeks }) {
  const [horizon, setHorizon] = useState(12)
  const [detailSku, setDetailSku] = useState(null)
  const [viewMode, setViewMode] = useState('completa')

  if (!produccion) return (
    <div style={{ padding: 60, textAlign: 'center', color: '#64748b' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>📅</div>
      <div style={{ fontWeight: 600 }}>Cargando plan de producción...</div>
    </div>
  )

  const skus = Object.keys(produccion)
  if (!skus.length) return (
    <div style={{ padding: 40, color: RED }}>No se encontraron datos de stock para generar el plan.</div>
  )

  // First week index (across all SKUs) where any production is recommended
  let firstProdIdx = 0
  {
    let minIdx = horizon
    for (const sku of skus) {
      const cal = produccion[sku]?.calendar || []
      const idx = cal.findIndex(w => w.produccion > 0)
      if (idx !== -1 && idx < minIdx) minIdx = idx
    }
    firstProdIdx = minIdx < horizon ? minIdx : 0
  }
  const startIdx = viewMode === 'produccion' ? firstProdIdx : 0

  const activeSku = detailSku && produccion[detailSku] ? detailSku : skus[0]
  const allWeeks = produccion[skus[0]]?.calendar.slice(startIdx, horizon) || []

  const totalProduccion = skus.reduce((s, k) => {
    return s + produccion[k].calendar.slice(startIdx, horizon).reduce((a, w) => a + w.produccion, 0)
  }, 0)
  const urgentSkus = skus.filter(k =>
    produccion[k].calendar.slice(startIdx, horizon).some(w => w.urgente)
  ).length
  const skusConPlan = skus.filter(k =>
    produccion[k].calendar.slice(startIdx, horizon).some(w => w.produccion > 0)
  ).length

  const cellColor = (w) => {
    if (w.urgente) return '#fecaca'
    if (w.produccion > 0) return '#bbf7d0'
    return '#f1f5f9'
  }

  const detailData = produccion[activeSku]?.calendar.slice(startIdx, horizon).map(w => ({
    name: fmtWeekDate(w.fecha),
    stock: w.stock_inicio,
    produccion: w.produccion,
    demanda: w.demanda,
  })) || []
  const safetyVal = produccion[activeSku]?.stock_seguridad || 0

  return (
    <div>
      {/* ── Controls ── */}
      <div style={{ display: 'flex', gap: 32, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 4 }}>
            Stock de seguridad: <span style={{ color: BLUE }}>{safetyWeeks} sem</span>
          </label>
          <input type="range" min={0.5} max={6} step={0.5} value={safetyWeeks}
            onChange={e => setSafetyWeeks(parseFloat(e.target.value))}
            style={{ width: 180 }} />
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>0.5 – 6 semanas</div>
        </div>
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 4 }}>
            Horizonte: <span style={{ color: BLUE }}>{horizon} sem</span>
          </label>
          <input type="range" min={4} max={52} step={4} value={horizon}
            onChange={e => setHorizon(parseInt(e.target.value))}
            style={{ width: 180 }} />
          <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>4 – 52 semanas</div>
        </div>
      </div>

      {/* ── Summary cards ── */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { label: 'SKUs con plan activo', value: skusConPlan, color: BLUE },
          { label: 'SKUs con stock crítico', value: urgentSkus, color: RED },
          { label: 'Unidades totales a producir', value: fmt(totalProduccion), color: GREEN },
          { label: 'Horizonte analizado', value: `${horizon} sem`, color: ORANGE },
        ].map(c => (
          <div key={c.label} style={{
            flex: '1 1 160px', background: 'white', borderRadius: 10, padding: '14px 18px',
            boxShadow: '0 1px 4px rgba(0,0,0,0.08)', borderLeft: `4px solid ${c.color}`,
          }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* ── Gantt heatmap ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24, overflowX: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <h3 style={{ margin: 0, color: BLUE, fontSize: 15, fontWeight: 700 }}>
            Calendario de Producción — próximas {horizon} semanas
          </h3>
          <div style={{ display: 'flex', gap: 4 }}>
            {[
              { value: 'completa', label: 'Vista completa' },
              { value: 'produccion', label: 'Desde producción' },
            ].map(opt => (
              <button key={opt.value} onClick={() => setViewMode(opt.value)} style={{
                padding: '4px 12px', borderRadius: 14,
                border: `1px solid ${viewMode === opt.value ? BLUE : '#cbd5e1'}`,
                background: viewMode === opt.value ? BLUE : '#f8fafc',
                color: viewMode === opt.value ? '#fff' : '#64748b',
                cursor: 'pointer', fontSize: 12, fontWeight: 600,
              }}>{opt.label}</button>
            ))}
          </div>
        </div>
        <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 10, display: 'flex', gap: 16 }}>
          <span><span style={{ background: '#bbf7d0', padding: '1px 6px', borderRadius: 3 }}>■</span> Producir</span>
          <span><span style={{ background: '#fecaca', padding: '1px 6px', borderRadius: 3 }}>■</span> Urgente (stock bajo 0)</span>
          <span><span style={{ background: '#f1f5f9', padding: '1px 6px', borderRadius: 3 }}>■</span> Sin producción</span>
        </div>
        <table style={{ borderCollapse: 'collapse', fontSize: 11, minWidth: '100%' }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 10px', textAlign: 'left', background: '#f8fafc', borderBottom: '2px solid #e2e8f0', fontWeight: 700, color: '#374151', minWidth: 90 }}>SKU</th>
              {allWeeks.map((w, i) => (
                <th key={i} style={{ padding: '4px 6px', textAlign: 'center', background: '#f8fafc', borderBottom: '2px solid #e2e8f0', fontWeight: 600, color: '#64748b', minWidth: 68, fontSize: 10 }}>
                  {fmtWeekDate(w.fecha)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {skus.map(sku => {
              const weeks = produccion[sku].calendar.slice(startIdx, horizon)
              return (
                <tr key={sku} onClick={() => setDetailSku(sku)} style={{ cursor: 'pointer' }}>
                  <td style={{
                    padding: '5px 10px', fontWeight: activeSku === sku ? 800 : 600,
                    color: activeSku === sku ? BLUE : '#374151',
                    borderBottom: '1px solid #f1f5f9', background: activeSku === sku ? '#eff6ff' : 'white',
                    whiteSpace: 'nowrap',
                  }}>
                    {sku}
                  </td>
                  {weeks.map((w, i) => (
                    <td key={i} title={w.produccion > 0 ? `Producir: ${fmt(w.produccion)} u` : 'Sin producción'} style={{
                      padding: '4px 2px', textAlign: 'center',
                      background: cellColor(w),
                      borderBottom: '1px solid #f1f5f9',
                      color: w.produccion > 0 ? '#166534' : '#94a3b8',
                      fontWeight: w.produccion > 0 ? 700 : 400,
                    }}>
                      {w.produccion > 0 ? fmt(w.produccion) : '·'}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* ── Detail chart ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 4px', color: BLUE, fontSize: 15, fontWeight: 700 }}>
          Detalle: {activeSku}
        </h3>
        <div style={{ fontSize: 12, color: '#64748b', marginBottom: 16 }}>
          Stock actual: <strong>{fmt(produccion[activeSku]?.stock_actual)}</strong> &nbsp;·&nbsp;
          Stock seguridad: <strong>{fmt(safetyVal)}</strong> &nbsp;·&nbsp;
          Demanda promedio: <strong>{fmt(produccion[activeSku]?.avg_demand)}/sem</strong> &nbsp;·&nbsp;
          Semanas a producir: <strong>{produccion[activeSku]?.calendar.slice(startIdx, horizon).filter(w => w.produccion > 0).length}</strong>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={detailData} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => fmt(v)} />
            <Tooltip formatter={(v, n) => [fmt(v), n]} labelFormatter={v => v} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <ReferenceLine y={safetyVal} stroke={ORANGE} strokeDasharray="5 3" label={{ value: 'Stock seg.', fill: ORANGE, fontSize: 10 }} />
            <Area type="monotone" dataKey="stock" name="Stock inicio" fill="#dbeafe" stroke={BLUE_LIGHT} strokeWidth={2} />
            <Bar dataKey="produccion" name="Producción" fill={GREEN} radius={[3, 3, 0, 0]} />
            <Line type="monotone" dataKey="demanda" name="Demanda" stroke={RED} strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* ── Detail table ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflowX: 'auto' }}>
        <h3 style={{ margin: '0 0 12px', color: BLUE, fontSize: 15, fontWeight: 700 }}>
          Tabla detallada — {activeSku}
        </h3>
        <table style={{ borderCollapse: 'collapse', fontSize: 12, width: '100%' }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {['Fecha', 'Demanda', 'Producción', 'Stock inicio', 'Stock fin', 'Estado'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700, color: '#374151', borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {produccion[activeSku]?.calendar.slice(startIdx, horizon).map((w, i) => (
              <tr key={i} style={{ background: w.urgente ? '#fff5f5' : w.produccion > 0 ? '#f0fdf4' : 'white' }}>
                <td style={{ padding: '6px 12px', textAlign: 'right', color: '#64748b', borderBottom: '1px solid #f1f5f9' }}>{fmtWeekDate(w.fecha)}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right', borderBottom: '1px solid #f1f5f9' }}>{fmt(w.demanda)}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right', fontWeight: w.produccion > 0 ? 700 : 400, color: w.produccion > 0 ? GREEN : '#94a3b8', borderBottom: '1px solid #f1f5f9' }}>{fmt(w.produccion)}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right', borderBottom: '1px solid #f1f5f9' }}>{fmt(w.stock_inicio)}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right', borderBottom: '1px solid #f1f5f9' }}>{fmt(w.stock_fin)}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right', borderBottom: '1px solid #f1f5f9' }}>
                  {w.urgente
                    ? <span style={{ color: RED, fontWeight: 700 }}>⚠ Urgente</span>
                    : w.produccion > 0
                      ? <span style={{ color: GREEN, fontWeight: 600 }}>✓ Producir</span>
                      : <span style={{ color: '#94a3b8' }}>—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Tab: Costo de Planchas ───────────────────────────────────────────────────

const TEAL_DARK = '#0e7490'
const TEAL_LIGHT = '#06b6d4'

function TabCostoPlanchas({ produccion, safetyWeeks, setSafetyWeeks, precios, setPrecios, skuPlancha }) {
  const [horizon, setHorizon] = useState(12)
  const [editando, setEditando] = useState(false)
  const [preciosTemp, setPreciosTemp] = useState(precios)

  if (!produccion) return (
    <div style={{ padding: 60, textAlign: 'center', color: '#64748b' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>💰</div>
      <div style={{ fontWeight: 600 }}>Cargando datos de producción...</div>
    </div>
  )

  const skus = Object.keys(produccion).filter(k => skuPlancha[k])

  // Compute per-SKU cost data
  const costData = skus.map((sku, idx) => {
    const cfg = skuPlancha[sku]
    const precioPlancha = precios[cfg.tipo]
    const planchasPorUnidad = 1 / cfg.prod_por_plancha
    const costoPorUnidad = precioPlancha * planchasPorUnidad
    const cal = produccion[sku]?.calendar.slice(0, horizon) || []

    const weeks = cal.map(w => ({
      semana: w.semana,
      fecha: w.fecha,
      unidades: w.produccion,
      planchas: w.produccion * planchasPorUnidad,
      costo: w.produccion * costoPorUnidad,
      urgente: w.urgente,
    }))

    const totUnidades = weeks.reduce((s, w) => s + w.unidades, 0)
    const totPlanchas = weeks.reduce((s, w) => s + w.planchas, 0)
    const totCosto = weeks.reduce((s, w) => s + w.costo, 0)

    return { sku, cfg, precioPlancha, costoPorUnidad, weeks, totUnidades, totPlanchas, totCosto, color: SKU_COLORS[idx % SKU_COLORS.length] }
  })

  const totalInversion = costData.reduce((s, d) => s + d.totCosto, 0)
  const totalPlanchas = costData.reduce((s, d) => s + d.totPlanchas, 0)
  const avgSemanal = horizon > 0 ? totalInversion / horizon : 0

  // Chart: weekly total cost stacked by SKU
  const allWeeks = produccion[skus[0]]?.calendar.slice(0, horizon) || []
  const chartData = allWeeks.map((w, i) => {
    const pt = { semana: fmtWeekDate(w.fecha) }
    costData.forEach(d => { pt[d.sku] = Math.round(d.weeks[i]?.costo || 0) })
    return pt
  })

  const guardarPrecios = () => {
    setPrecios({ ...preciosTemp })
    setEditando(false)
  }

  return (
    <div>

      {/* ── Precio editor ── */}
      <div style={{ background: '#f0fdfe', border: '1px solid #a5f3fc', borderRadius: 10, padding: '16px 20px', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, color: TEAL_DARK, marginBottom: 4 }}>
              Precios de planchas metálicas
            </div>
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              {Object.entries(precios).map(([tipo, precio]) => (
                <span key={tipo} style={{ fontSize: 13, color: '#0e7490' }}>
                  <strong>F.G. {tipo}:</strong> S/ {precio.toFixed(2)} por plancha
                </span>
              ))}
            </div>
          </div>
          <button
            onClick={() => { setPreciosTemp({ ...precios }); setEditando(!editando) }}
            style={{
              padding: '7px 14px', borderRadius: 7, border: `1px solid ${TEAL_LIGHT}`,
              background: editando ? '#e0f2fe' : 'white', color: TEAL_DARK,
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
            }}
          >
            {editando ? 'Cancelar' : '✏️ Editar precios'}
          </button>
        </div>

        {editando && (
          <div style={{ marginTop: 16, display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
            {['0.75', '1.20'].map(tipo => (
              <div key={tipo}>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#475569', marginBottom: 4 }}>
                  Plancha F.G. {tipo} (S/ por plancha)
                </label>
                <input
                  type="number" step="0.01" min="0"
                  value={preciosTemp[tipo]}
                  onChange={e => setPreciosTemp(p => ({ ...p, [tipo]: parseFloat(e.target.value) || 0 }))}
                  style={{ padding: '7px 10px', borderRadius: 6, border: `1px solid ${TEAL_LIGHT}`, fontSize: 14, width: 130 }}
                />
              </div>
            ))}
            <button
              onClick={guardarPrecios}
              style={{
                padding: '7px 18px', borderRadius: 7, background: TEAL_DARK,
                color: 'white', border: 'none', cursor: 'pointer', fontWeight: 700, fontSize: 13,
              }}
            >
              Aplicar
            </button>
          </div>
        )}
      </div>

      {/* ── Controls ── */}
      <div style={{ display: 'flex', gap: 32, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center' }}>
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 4 }}>
            Stock de seguridad: <span style={{ color: TEAL_DARK }}>{safetyWeeks} sem</span>
          </label>
          <input type="range" min={0.5} max={6} step={0.5} value={safetyWeeks}
            onChange={e => setSafetyWeeks(parseFloat(e.target.value))} style={{ width: 160 }} />
        </div>
        <div>
          <label style={{ fontSize: 13, fontWeight: 600, color: '#374151', display: 'block', marginBottom: 4 }}>
            Horizonte: <span style={{ color: TEAL_DARK }}>{horizon} sem</span>
          </label>
          <input type="range" min={4} max={52} step={4} value={horizon}
            onChange={e => setHorizon(parseInt(e.target.value))} style={{ width: 160 }} />
        </div>
      </div>

      {/* ── KPI cards ── */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { label: 'Inversión total proyectada', value: `S/ ${fmt(totalInversion)}`, color: TEAL_DARK },
          { label: 'Promedio semanal', value: `S/ ${fmt(avgSemanal)}`, color: TEAL_LIGHT },
          { label: 'Planchas totales a comprar', value: fmtDec(totalPlanchas, 1), color: ORANGE },
          { label: 'Horizonte analizado', value: `${horizon} semanas`, color: PURPLE },
        ].map(c => (
          <div key={c.label} style={{
            flex: '1 1 160px', background: 'white', borderRadius: 10,
            padding: '14px 18px', boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
            borderLeft: `4px solid ${c.color}`,
          }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{c.label}</div>
          </div>
        ))}
      </div>

      {/* ── Chart ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 4px', color: TEAL_DARK, fontSize: 15, fontWeight: 700 }}>
          Inversión semanal en planchas por SKU — próximas {horizon} semanas
        </h3>
        <p style={{ margin: '0 0 16px', fontSize: 12, color: '#64748b' }}>Costo total de planchas requeridas por semana de producción (S/)</p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 4, right: 20, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="semana" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `S/${fmt(v)}`} />
            <Tooltip formatter={(v, n) => [`S/ ${fmt(v)}`, n]} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            {costData.map(d => (
              <Bar key={d.sku} dataKey={d.sku} stackId="a" fill={d.color} radius={costData[costData.length - 1].sku === d.sku ? [3, 3, 0, 0] : [0, 0, 0, 0]} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Resumen por SKU ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24, overflowX: 'auto' }}>
        <h3 style={{ margin: '0 0 14px', color: TEAL_DARK, fontSize: 15, fontWeight: 700 }}>Resumen por producto</h3>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f0fdfe' }}>
              {['SKU', 'Tipo plancha', 'Precio plancha', 'Costo/unidad', 'Unidades totales', 'Planchas totales', 'Inversión total'].map(h => (
                <th key={h} style={{ padding: '9px 12px', textAlign: 'right', fontWeight: 700, color: TEAL_DARK, borderBottom: `2px solid ${TEAL_LIGHT}`, whiteSpace: 'nowrap', fontSize: 12 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {costData.map((d, i) => (
              <tr key={d.sku} style={{ background: i % 2 === 0 ? '#fafafa' : 'white' }}>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', fontWeight: 700, color: d.color, textAlign: 'right' }}>{d.sku}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' }}>
                  <span style={{ background: d.cfg.tipo === '0.75' ? '#eff6ff' : '#fefce8', color: d.cfg.tipo === '0.75' ? BLUE : '#92400e', border: `1px solid ${d.cfg.tipo === '0.75' ? '#bfdbfe' : '#fde68a'}`, borderRadius: 12, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
                    F.G. {d.cfg.tipo}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' }}>S/ {d.precioPlancha.toFixed(2)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', color: '#64748b' }}>S/ {d.costoPorUnidad.toFixed(4)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' }}>{fmt(d.totUnidades)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' }}>{fmtDec(d.totPlanchas, 2)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', fontWeight: 700, color: TEAL_DARK }}>S/ {fmt(d.totCosto)}</td>
              </tr>
            ))}
            <tr style={{ background: '#f0fdfe', fontWeight: 700 }}>
              <td colSpan={4} style={{ padding: '9px 12px', textAlign: 'right', color: TEAL_DARK, borderTop: `2px solid ${TEAL_LIGHT}` }}>TOTAL</td>
              <td style={{ padding: '9px 12px', textAlign: 'right', borderTop: `2px solid ${TEAL_LIGHT}` }}>{fmt(costData.reduce((s, d) => s + d.totUnidades, 0))}</td>
              <td style={{ padding: '9px 12px', textAlign: 'right', borderTop: `2px solid ${TEAL_LIGHT}` }}>{fmtDec(totalPlanchas, 2)}</td>
              <td style={{ padding: '9px 12px', textAlign: 'right', borderTop: `2px solid ${TEAL_LIGHT}`, color: TEAL_DARK }}>S/ {fmt(totalInversion)}</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* ── Detalle semanal por SKU ── */}
      {costData.map(d => d.totUnidades > 0 && (
        <div key={d.sku} style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 16, overflowX: 'auto' }}>
          <h4 style={{ margin: '0 0 12px', fontSize: 14, fontWeight: 700, color: d.color }}>
            {d.sku} — F.G. {d.cfg.tipo} &nbsp;
            <span style={{ fontWeight: 400, fontSize: 12, color: '#64748b' }}>
              ({d.cfg.prod_por_plancha} unidades/plancha · S/ {d.precioPlancha.toFixed(2)}/plancha)
            </span>
          </h4>
          <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
            <thead>
              <tr style={{ background: '#f8fafc' }}>
                {['Semana', 'Fecha', 'Unidades a producir', 'Planchas necesarias', 'Costo planchas (S/)', 'Estado'].map(h => (
                  <th key={h} style={{ padding: '7px 10px', textAlign: 'right', fontWeight: 700, color: '#475569', borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {d.weeks.filter(w => w.unidades > 0).map((w, i) => (
                <tr key={i} style={{ background: w.urgente ? '#fff5f5' : i % 2 === 0 ? '#fafafa' : 'white' }}>
                  <td style={{ padding: '6px 10px', textAlign: 'right', color: '#64748b', borderBottom: '1px solid #f1f5f9' }}>{w.semana}</td>
                  <td style={{ padding: '6px 10px', textAlign: 'right', color: '#64748b', borderBottom: '1px solid #f1f5f9' }}>{w.fecha}</td>
                  <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 600, borderBottom: '1px solid #f1f5f9' }}>{fmt(w.unidades)}</td>
                  <td style={{ padding: '6px 10px', textAlign: 'right', borderBottom: '1px solid #f1f5f9' }}>{fmtDec(w.planchas, 3)}</td>
                  <td style={{ padding: '6px 10px', textAlign: 'right', fontWeight: 700, color: TEAL_DARK, borderBottom: '1px solid #f1f5f9' }}>S/ {fmt(w.costo)}</td>
                  <td style={{ padding: '6px 10px', textAlign: 'right', borderBottom: '1px solid #f1f5f9' }}>
                    {w.urgente
                      ? <span style={{ color: RED, fontWeight: 700 }}>⚠ Urgente</span>
                      : <span style={{ color: GREEN, fontWeight: 600 }}>✓ Normal</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}

// ─── Tab: Administración ─────────────────────────────────────────────────────

const ROLE_LABELS = {
  admin: 'Admin',
  gerente_produccion: 'Gte. Producción',
  gerente_financiero: 'Gte. Financiero',
}

function TabAdmin() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState({ open: false, email: '', password: '', name: '' })
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState(null)

  const load = () => {
    setLoading(true)
    fetch('/api/admin/users')
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }

  useEffect(() => { load() }, [])

  const flash = (text, ok = true) => {
    setMsg({ text, ok })
    setTimeout(() => setMsg(null), 3500)
  }

  const handleRoleChange = async (userId, roleId) => {
    const res = await fetch(`/api/admin/users/${encodeURIComponent(userId)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ roleId }),
    })
    if (res.ok) { flash('Rol actualizado'); load() }
    else { const e = await res.json(); flash(e.error, false) }
  }

  const handleDelete = async (userId, email) => {
    if (!confirm(`¿Eliminar usuario ${email}?`)) return
    const res = await fetch(`/api/admin/users/${encodeURIComponent(userId)}`, { method: 'DELETE' })
    if (res.ok || res.status === 204) { flash('Usuario eliminado'); load() }
    else { const e = await res.json(); flash(e.error, false) }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSaving(true)
    const res = await fetch('/api/admin/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: form.email, password: form.password, name: form.name }),
    })
    const body = await res.json()
    setSaving(false)
    if (res.ok) {
      flash(`Usuario ${form.email} creado`)
      setForm({ open: false, email: '', password: '', name: '' })
      load()
    } else {
      flash(body.error || 'Error al crear usuario', false)
    }
  }

  if (loading) return <p style={{ color: '#64748b', padding: 24 }}>Cargando usuarios...</p>
  if (error) return <p style={{ color: RED, padding: 24 }}>Error: {error}</p>

  const { users = [], allRoles = [] } = data || {}

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h2 style={{ color: BLUE, margin: 0, fontSize: 17, fontWeight: 700 }}>Gestión de usuarios</h2>
          <p style={{ color: '#666', margin: '4px 0 0', fontSize: 13 }}>{users.length} usuario{users.length !== 1 ? 's' : ''} registrado{users.length !== 1 ? 's' : ''}</p>
        </div>
        <button
          onClick={() => setForm(f => ({ ...f, open: !f.open }))}
          style={{ padding: '8px 16px', background: BLUE, color: 'white', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600, fontSize: 13 }}
        >
          + Nuevo usuario
        </button>
      </div>

      {msg && (
        <div style={{ padding: '10px 14px', borderRadius: 6, marginBottom: 16, fontSize: 13,
          background: msg.ok ? '#f0fdf4' : '#fef2f2',
          border: `1px solid ${msg.ok ? '#86efac' : '#fca5a5'}`,
          color: msg.ok ? '#166534' : '#dc2626' }}>
          {msg.text}
        </div>
      )}

      {form.open && (
        <form onSubmit={handleCreate} style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 20, marginBottom: 24 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 15, color: BLUE }}>Crear nuevo usuario</h3>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <input
              required placeholder="Nombre completo"
              value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              style={{ flex: 1, minWidth: 180, padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 13 }}
            />
            <input
              required type="email" placeholder="Correo electrónico"
              value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              style={{ flex: 1, minWidth: 220, padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 13 }}
            />
            <input
              required type="password" placeholder="Contraseña temporal"
              value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              style={{ flex: 1, minWidth: 180, padding: '8px 10px', borderRadius: 6, border: '1px solid #cbd5e1', fontSize: 13 }}
            />
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button type="submit" disabled={saving}
              style={{ padding: '8px 18px', background: GREEN, color: 'white', border: 'none', borderRadius: 6, cursor: saving ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: 13 }}>
              {saving ? 'Creando...' : 'Crear usuario'}
            </button>
            <button type="button" onClick={() => setForm(f => ({ ...f, open: false }))}
              style={{ padding: '8px 14px', background: 'white', border: '1px solid #cbd5e1', borderRadius: 6, cursor: 'pointer', fontSize: 13 }}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 8, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
              <th style={th}>Usuario</th>
              <th style={th}>Último acceso</th>
              <th style={th}>Rol</th>
              <th style={th}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u, i) => (
              <tr key={u.user_id} style={{ borderBottom: i < users.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <td style={td}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {u.picture
                      ? <img src={u.picture} alt="" style={{ width: 32, height: 32, borderRadius: '50%' }} />
                      : <div style={{ width: 32, height: 32, borderRadius: '50%', background: BLUE, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700, fontSize: 13 }}>
                          {(u.name || u.email || '?')[0].toUpperCase()}
                        </div>
                    }
                    <div>
                      <div style={{ fontWeight: 600, color: '#1e293b' }}>{u.name || '—'}</div>
                      <div style={{ color: '#64748b', fontSize: 12 }}>{u.email}</div>
                    </div>
                  </div>
                </td>
                <td style={td}>
                  <span style={{ color: '#64748b' }}>
                    {u.last_login ? new Date(u.last_login).toLocaleDateString('es-PE') : 'Nunca'}
                  </span>
                </td>
                <td style={td}>
                  <select
                    value={u.roles[0]?.name || ''}
                    onChange={e => {
                      const roleId = allRoles.find(r => r.name === e.target.value)?.id || null
                      handleRoleChange(u.user_id, roleId)
                    }}
                    style={{ padding: '5px 8px', borderRadius: 5, border: '1px solid #cbd5e1', fontSize: 12, background: 'white', cursor: 'pointer' }}
                  >
                    <option value="">Sin rol</option>
                    {allRoles.map(r => (
                      <option key={r.id} value={r.name}>{ROLE_LABELS[r.name] || r.name}</option>
                    ))}
                  </select>
                </td>
                <td style={td}>
                  <button
                    onClick={() => handleDelete(u.user_id, u.email)}
                    style={{ padding: '5px 10px', background: '#fef2f2', color: RED, border: `1px solid #fca5a5`, borderRadius: 5, cursor: 'pointer', fontSize: 12, fontWeight: 600 }}
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const th = { padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#475569', fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 }
const td = { padding: '12px 16px', verticalAlign: 'middle' }

// ─── Module selector ─────────────────────────────────────────────────────────

function ModuleSelector({ modules, onSelect }) {
  return (
    <div style={{ marginTop: 8 }}>
      <p style={{ color: '#64748b', fontSize: 14, marginBottom: 20 }}>
        Selecciona un módulo para comenzar:
      </p>
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        {modules.map(m => (
          <button
            key={m.id}
            onClick={() => onSelect(m)}
            style={{
              flex: '1 1 240px', maxWidth: 340,
              background: m.bg,
              border: `2px solid ${m.accent}`,
              borderRadius: 14,
              padding: '24px 28px',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'box-shadow 0.15s',
              boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
            }}
            onMouseEnter={e => e.currentTarget.style.boxShadow = `0 4px 16px ${m.accent}33`}
            onMouseLeave={e => e.currentTarget.style.boxShadow = '0 1px 4px rgba(0,0,0,0.06)'}
          >
            <div style={{ fontSize: 32, marginBottom: 10 }}>{m.icon}</div>
            <div style={{ fontSize: 17, fontWeight: 700, color: m.color, marginBottom: 6 }}>{m.label}</div>
            <div style={{ fontSize: 13, color: '#64748b', lineHeight: 1.6, marginBottom: 14 }}>{m.description}</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {m.tabs.map(t => (
                <span key={t.id} style={{
                  fontSize: 11, background: 'white',
                  border: `1px solid ${m.accent}`,
                  color: m.color, borderRadius: 20,
                  padding: '3px 10px', fontWeight: 500,
                }}>
                  {t.label}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Tab: Análisis Financiero Histórico ──────────────────────────────────────

const COSTOS_CONFIG = [
  { key: 'mano_obra',     label: 'Mano de obra extra',          pct: 18, icon: '👷', color: '#7c3aed', desc: 'Horas hombre adicionales en producción no vendida' },
  { key: 'transporte',    label: 'Transporte y logística',      pct:  6, icon: '🚚', color: '#0891b2', desc: 'Flete y distribución de pedidos sobreproducidos' },
  { key: 'energia',       label: 'Energía eléctrica',           pct:  5, icon: '⚡', color: '#d97706', desc: 'Consumo eléctrico adicional de producción excedente' },
  { key: 'almacenamiento',label: 'Almacenamiento',              pct:  8, icon: '🏪', color: '#059669', desc: 'Espacio de almacén ocupado por sobrestock' },
  { key: 'depreciacion',  label: 'Depreciación de maquinaria',  pct:  3, icon: '⚙️', color: '#64748b', desc: 'Desgaste por uso de equipos en producción excedente' },
  { key: 'oportunidad',   label: 'Costo de oportunidad',        pct: 10, icon: '📉', color: '#dc2626', desc: 'Capital inmovilizado sin retorno financiero' },
  { key: 'deterioro',     label: 'Riesgo de deterioro / merma', pct:  2, icon: '⚠️', color: '#b45309', desc: 'Productos potencialmente dañados en almacén' },
]

function TabAnalisisFinanciero({ eficiencia, precios, skuPlancha }) {
  const [tasas, setTasas] = useState(() => Object.fromEntries(COSTOS_CONFIG.map(c => [c.key, c.pct])))
  const [expandConfig, setExpandConfig] = useState(false)

  const skuData = eficiencia
    .filter(e => skuPlancha[e.codigo])
    .map((e, idx) => {
      const cfg = skuPlancha[e.codigo]
      const precioP = precios[cfg.tipo]
      const sobreprod = Math.max(0, e.produccion_total - e.ventas_total)
      const costoMP = (sobreprod / cfg.prod_por_plancha) * precioP
      return { sku: e.codigo, tipo: cfg.tipo, produccion_total: e.produccion_total, ventas_total: e.ventas_total, eficiencia: e.eficiencia, sobreprod, costoMP, color: SKU_COLORS[idx % SKU_COLORS.length] }
    })

  const totalSobreprod   = skuData.reduce((s, d) => s + d.sobreprod, 0)
  const totalProduccion  = skuData.reduce((s, d) => s + d.produccion_total, 0)
  const totalCostoMP     = skuData.reduce((s, d) => s + d.costoMP, 0)
  const adicionales      = COSTOS_CONFIG.map(c => ({ ...c, pct: tasas[c.key], valor: totalCostoMP * tasas[c.key] / 100 }))
  const totalAdicionales = adicionales.reduce((s, c) => s + c.valor, 0)
  const impactoTotal     = totalCostoMP + totalAdicionales
  const multiplicador    = totalCostoMP > 0 ? impactoTotal / totalCostoMP : 1
  const sobreprodPct     = totalProduccion > 0 ? (totalSobreprod / totalProduccion) * 100 : 0

  const waterfallData = [
    { name: 'Materia prima', valor: Math.round(totalCostoMP), color: TEAL_DARK },
    ...adicionales.map(c => ({ name: c.label, valor: Math.round(c.valor), color: c.color })),
  ]

  // Chart data — derived from eficiencia (same source as KPIs)
  const barDataUnidades = skuData.map(d => ({
    sku: d.sku,
    Vendido: d.ventas_total,
    Sobreproducido: d.sobreprod,
  }))

  const barDataCosto = skuData.map(d => ({
    sku: d.sku,
    costoMP: Math.round(d.costoMP),
    costoAdicional: Math.round(d.costoMP * (multiplicador - 1)),
  }))

  const avgEfic = skuData.length ? skuData.reduce((s, d) => s + d.eficiencia, 0) / skuData.length : 0

  return (
    <div>
      {/* ── Config panel ── */}
      <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 10, padding: '14px 20px', marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div>
            <span style={{ fontWeight: 700, fontSize: 14, color: '#9a3412' }}>Tasas de costos adicionales</span>
            <span style={{ fontSize: 12, color: '#c2410c', marginLeft: 10 }}>
              Multiplicador actual: <strong>{fmtDec(multiplicador, 2)}×</strong> el costo de materia prima
            </span>
          </div>
          <button onClick={() => setExpandConfig(!expandConfig)}
            style={{ padding: '6px 12px', borderRadius: 6, border: '1px solid #fed7aa', background: expandConfig ? '#ffedd5' : 'white', color: '#9a3412', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
            {expandConfig ? 'Cerrar' : '⚙️ Ajustar tasas'}
          </button>
        </div>
        {expandConfig && (
          <div style={{ marginTop: 16, display: 'flex', gap: 14, flexWrap: 'wrap' }}>
            {COSTOS_CONFIG.map(c => (
              <div key={c.key} style={{ minWidth: 130 }}>
                <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#7c2d12', marginBottom: 3 }}>{c.icon} {c.label}</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <input type="number" min={0} max={100} step={0.5} value={tasas[c.key]}
                    onChange={e => setTasas(t => ({ ...t, [c.key]: parseFloat(e.target.value) || 0 }))}
                    style={{ width: 58, padding: '4px 6px', borderRadius: 5, border: '1px solid #fed7aa', fontSize: 13 }} />
                  <span style={{ fontSize: 12, color: '#92400e' }}>%</span>
                </div>
                <div style={{ fontSize: 10, color: '#a16207', marginTop: 2, lineHeight: 1.4 }}>{c.desc}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── KPI cards ── */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { label: 'Unidades sobreproducidas', value: fmt(totalSobreprod), sub: `${fmtDec(sobreprodPct)}% del total producido`, color: ORANGE },
          { label: 'Costo MP sobreproducida',  value: `S/ ${fmt(totalCostoMP)}`,    sub: 'Solo planchas metálicas',                  color: TEAL_DARK },
          { label: 'Costos adicionales',        value: `S/ ${fmt(totalAdicionales)}`, sub: `${fmtDec(multiplicador - 1, 2)}× sobre costo MP`, color: PURPLE },
          { label: 'IMPACTO TOTAL ESTIMADO',    value: `S/ ${fmt(impactoTotal)}`,    sub: 'Pérdida potencial por sobrestock',          color: RED },
        ].map(c => (
          <div key={c.label} style={{ flex: '1 1 175px', background: 'white', borderRadius: 10, padding: '16px 18px', boxShadow: '0 1px 4px rgba(0,0,0,0.08)', borderLeft: `4px solid ${c.color}` }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: c.color }}>{c.value}</div>
            <div style={{ fontSize: 12, color: '#374151', marginTop: 3, fontWeight: 600 }}>{c.label}</div>
            <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{c.sub}</div>
          </div>
        ))}
      </div>

      {/* ── Waterfall ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 4px', color: '#991b1b', fontSize: 15, fontWeight: 700 }}>Desglose de impacto económico</h3>
        <p style={{ margin: '0 0 16px', fontSize: 12, color: '#64748b' }}>Cada categoría como % aplicado sobre el costo de materia prima sobreproducida</p>
        <ResponsiveContainer width="100%" height={310}>
          <BarChart data={waterfallData} layout="vertical" margin={{ left: 10, right: 90, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={v => `S/${fmt(v)}`} />
            <YAxis type="category" dataKey="name" width={175} tick={{ fontSize: 11 }} />
            <Tooltip formatter={v => [`S/ ${fmt(v)}`, 'Costo estimado']} />
            <Bar dataKey="valor" radius={[0, 4, 4, 0]} label={{ position: 'right', formatter: v => `S/ ${fmt(v)}`, fontSize: 11, fill: '#374151' }}>
              {waterfallData.map((d, i) => <Cell key={i} fill={d.color} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Producido vs Vendido por SKU ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 20 }}>
        <h3 style={{ margin: '0 0 4px', color: '#991b1b', fontSize: 15, fontWeight: 700 }}>Producido vs Vendido por SKU — histórico total</h3>
        <p style={{ margin: '0 0 4px', fontSize: 12, color: '#64748b' }}>Unidades producidas desagregadas en vendidas (verde) y sobreproducidas no vendidas (rojo). Misma fuente que los KPIs.</p>
        <div style={{ display: 'flex', gap: 16, marginBottom: 12, marginTop: 8 }}>
          <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 12, height: 12, background: GREEN, borderRadius: 2, display: 'inline-block' }} /> Vendido
          </span>
          <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 12, height: 12, background: RED, borderRadius: 2, display: 'inline-block' }} /> Sobreproducido (no vendido)
          </span>
        </div>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={barDataUnidades} margin={{ top: 4, right: 20, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="sku" tick={{ fontSize: 12, fontWeight: 600 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v) + ' u', n]} />
            <Bar dataKey="Vendido"        stackId="a" fill={GREEN} radius={[0, 0, 0, 0]} />
            <Bar dataKey="Sobreproducido" stackId="a" fill={RED}   radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Costo de sobreproducción por SKU ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', marginBottom: 24 }}>
        <h3 style={{ margin: '0 0 4px', color: '#991b1b', fontSize: 15, fontWeight: 700 }}>Impacto económico por SKU</h3>
        <p style={{ margin: '0 0 4px', fontSize: 12, color: '#64748b' }}>Costo de materia prima sobreproducida (teal) más costos adicionales estimados (rojo) por producto.</p>
        <div style={{ display: 'flex', gap: 16, marginBottom: 12, marginTop: 8 }}>
          <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 12, height: 12, background: TEAL_DARK, borderRadius: 2, display: 'inline-block' }} /> Costo MP sobreproducida
          </span>
          <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ width: 12, height: 12, background: RED, borderRadius: 2, display: 'inline-block' }} /> Costos adicionales est.
          </span>
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={barDataCosto} margin={{ top: 4, right: 20, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="sku" tick={{ fontSize: 12, fontWeight: 600 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `S/${fmt(v)}`} />
            <Tooltip formatter={(v, n) => [`S/ ${fmt(v)}`, n === 'costoMP' ? 'Costo MP' : 'Costos adicionales']} />
            <Bar dataKey="costoMP"       stackId="b" fill={TEAL_DARK} radius={[0, 0, 0, 0]} />
            <Bar dataKey="costoAdicional" stackId="b" fill={RED}      radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Tabla por SKU ── */}
      <div style={{ background: 'white', borderRadius: 10, padding: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.08)', overflowX: 'auto' }}>
        <h3 style={{ margin: '0 0 14px', color: '#991b1b', fontSize: 15, fontWeight: 700 }}>Detalle por producto</h3>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
          <thead>
            <tr style={{ background: '#fff1f2' }}>
              {['SKU', 'Plancha', 'Producido', 'Vendido', 'Sobreproducido', 'Eficiencia', 'Costo MP excedente', 'Impacto total est.'].map(h => (
                <th key={h} style={{ padding: '9px 12px', textAlign: 'right', fontWeight: 700, color: '#991b1b', borderBottom: '2px solid #fca5a5', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {skuData.map((d, i) => (
              <tr key={d.sku} style={{ background: i % 2 === 0 ? '#fafafa' : 'white' }}>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', fontWeight: 700, color: d.color, textAlign: 'right' }}>{d.sku}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' }}>
                  <span style={{ background: d.tipo === '0.75' ? '#eff6ff' : '#fefce8', color: d.tipo === '0.75' ? BLUE : '#92400e', border: `1px solid ${d.tipo === '0.75' ? '#bfdbfe' : '#fde68a'}`, borderRadius: 12, padding: '2px 8px', fontSize: 11, fontWeight: 600 }}>
                    F.G. {d.tipo}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' }}>{fmt(d.produccion_total)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right' }}>{fmt(d.ventas_total)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', fontWeight: 600, color: d.sobreprod > 0 ? RED : GREEN }}>{fmt(d.sobreprod)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', fontWeight: 600, color: d.eficiencia >= 98 ? GREEN : d.eficiencia >= 90 ? ORANGE : RED }}>{fmtDec(d.eficiencia)}%</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', color: TEAL_DARK, fontWeight: 600 }}>S/ {fmt(d.costoMP)}</td>
                <td style={{ padding: '8px 12px', borderBottom: '1px solid #f1f5f9', textAlign: 'right', color: RED, fontWeight: 700 }}>S/ {fmt(d.costoMP * multiplicador)}</td>
              </tr>
            ))}
            <tr style={{ background: '#fff1f2', fontWeight: 700 }}>
              <td colSpan={4} style={{ padding: '9px 12px', textAlign: 'right', color: '#991b1b', borderTop: '2px solid #fca5a5' }}>TOTAL</td>
              <td style={{ padding: '9px 12px', textAlign: 'right', borderTop: '2px solid #fca5a5', color: RED }}>{fmt(totalSobreprod)}</td>
              <td style={{ padding: '9px 12px', textAlign: 'right', borderTop: '2px solid #fca5a5', color: avgEfic >= 98 ? GREEN : ORANGE }}>{fmtDec(avgEfic)}%</td>
              <td style={{ padding: '9px 12px', textAlign: 'right', borderTop: '2px solid #fca5a5', color: TEAL_DARK }}>S/ {fmt(totalCostoMP)}</td>
              <td style={{ padding: '9px 12px', textAlign: 'right', borderTop: '2px solid #fca5a5', color: RED }}>S/ {fmt(impactoTotal)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Tab: Asignación y Seguimiento de Operarios ──────────────────────────────

const STATUS_COLOR = (p) => p >= 80 ? '#166534' : p >= 40 ? '#92400e' : p > 0 ? '#991b1b' : '#64748b'
const STATUS_BG    = (p) => p >= 80 ? '#f0fdf4' : p >= 40 ? '#fffbeb' : p > 0 ? '#fef2f2' : '#f8fafc'
const STATUS_LABEL = (p) => p >= 80 ? 'En meta' : p >= 40 ? 'En progreso' : p > 0 ? 'Rezagado' : 'Sin iniciar'

function TabAsignacionSeguimiento({ produccion }) {
  const [view, setView]         = useState('asignar')
  const [weekIdx, setWeekIdx]   = useState(0)
  const [operarios, setOperarios] = useState([])
  const [progreso, setProgreso] = useState({})
  const [saving, setSaving]     = useState(false)
  const [msg, setMsg]           = useState(null)
  const [baseUrl, setBaseUrl]   = useState('')

  useEffect(() => { setBaseUrl(window.location.origin) }, [])

  // Extract weeks that have ≥1 SKU with recommended production
  const productionWeeks = useMemo(() => {
    if (!produccion) return []
    const skus = Object.keys(produccion)
    if (!skus.length) return []
    const nWeeks = produccion[skus[0]]?.calendar?.length || 0
    const result = []
    for (let i = 0; i < nWeeks; i++) {
      const metas = {}
      for (const s of skus) metas[s] = produccion[s]?.calendar[i]?.produccion || 0
      if (Object.values(metas).some(v => v > 0)) {
        result.push({
          fecha: produccion[skus[0]].calendar[i].fecha,
          semana: produccion[skus[0]].calendar[i].semana || `Semana ${i + 1}`,
          metas,
        })
      }
    }
    return result
  }, [produccion])

  const week = productionWeeks[weekIdx]
  const activeSKUs = week ? Object.entries(week.metas).filter(([, v]) => v > 0).map(([k]) => k) : []

  // Load assignment from server when week changes
  useEffect(() => {
    if (!week?.fecha) return
    fetch(`/api/asignaciones?semana=${week.fecha}`)
      .then(r => r.json())
      .then(d => {
        if (d?.operarios) { setOperarios(d.operarios); setProgreso(d.progreso || {}) }
        else { setOperarios([]); setProgreso({}) }
      })
      .catch(() => {})
  }, [week?.fecha])

  const addOperario = () => {
    const id    = Math.random().toString(36).slice(2, 10)
    const token = Math.random().toString(36).slice(2, 18)
    setOperarios(prev => [...prev, {
      id, token, nombre: '', email: '',
      asignaciones: Object.fromEntries(activeSKUs.map(s => [s, 0])),
    }])
  }

  const updateOp = (id, field, val) =>
    setOperarios(prev => prev.map(o => o.id === id ? { ...o, [field]: val } : o))

  const updateOpSKU = (id, sku, val) =>
    setOperarios(prev => prev.map(o =>
      o.id === id ? { ...o, asignaciones: { ...o.asignaciones, [sku]: Number(val) || 0 } } : o
    ))

  const removeOp = (id) => setOperarios(prev => prev.filter(o => o.id !== id))

  const saveAsignacion = async () => {
    if (!week) return
    setSaving(true); setMsg(null)
    try {
      const r = await fetch('/api/asignaciones', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ semana: week.fecha, fecha_inicio: week.fecha, metas_sku: week.metas, operarios }),
      })
      if (!r.ok) {
        let errMsg = `Error ${r.status}`
        try { const e = await r.json(); errMsg = e.error || errMsg } catch (_) { errMsg = await r.text().then(t => t.slice(0, 120)).catch(() => errMsg) }
        setMsg({ ok: false, text: errMsg }); return
      }
      const d = await r.json()
      setOperarios(d.semana?.operarios || operarios)
      setMsg({ ok: true, text: 'Asignación guardada. Los links de operarios ya están disponibles.' })
    } catch (err) {
      setMsg({ ok: false, text: String(err) })
    } finally { setSaving(false) }
  }

  const saveProgreso = async (opId) => {
    const p = progreso[opId] || { avances: {}, notas: '' }
    await fetch('/api/asignaciones', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ semana: week.fecha, operario_id: opId, avances: p.avances, notas: p.notas }),
    }).catch(() => {})
    setMsg({ ok: true, text: 'Progreso guardado.' })
    setTimeout(() => setMsg(null), 2000)
  }

  const updateAvance = (opId, sku, val) =>
    setProgreso(prev => ({
      ...prev,
      [opId]: { ...prev[opId], avances: { ...prev[opId]?.avances, [sku]: Number(val) || 0 } },
    }))

  const updateNotas = (opId, val) =>
    setProgreso(prev => ({ ...prev, [opId]: { ...prev[opId], notas: val } }))

  const copyLink = (token) => {
    navigator.clipboard.writeText(`${baseUrl}/asignacion/${token}`).then(() => {
      setMsg({ ok: true, text: 'Link copiado al portapapeles.' })
      setTimeout(() => setMsg(null), 2000)
    })
  }

  const mailtoOp = (op) => {
    const link = `${baseUrl}/asignacion/${op.token}`
    const body = [
      `Hola ${op.nombre},`,
      ``,
      `Aquí está tu plan de producción para la semana del ${week?.fecha}:`,
      ...activeSKUs.map(s => `  - ${s}: ${(op.asignaciones[s] || 0).toLocaleString('es-PE')} unidades`),
      ``,
      `Consulta tu avance aquí: ${link}`,
      ``,
      `Saludos,`,
      `Gerencia de Producción — Predicast`,
    ].join('\n')
    window.location.href = `mailto:${op.email}?subject=Tu plan de producción — semana del ${week?.fecha}&body=${encodeURIComponent(body)}`
  }

  const mailtoAll = () => {
    const to = operarios.filter(o => o.email).map(o => o.email).join(';')
    const body = [
      `Equipo,`,
      ``,
      `Plan de producción para la semana del ${week?.fecha}:`,
      ...operarios.map(o =>
        [`${o.nombre}:`, ...activeSKUs.map(s => `  - ${s}: ${(o.asignaciones[s] || 0).toLocaleString('es-PE')} uds.`)].join('\n')
      ),
      ``,
      `Predicast · Módulo Producción`,
    ].join('\n')
    window.location.href = `mailto:${to}?subject=Plan de producción — semana del ${week?.fecha}&body=${encodeURIComponent(body)}`
  }

  // ── Header shared across views ──────────────────────────────────────────────
  const ViewBtn = ({ id, label }) => (
    <button onClick={() => setView(id)} style={{
      padding: '8px 20px', borderRadius: 8, border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 13,
      background: view === id ? '#166534' : '#f1f5f9',
      color: view === id ? '#fff' : '#64748b',
      transition: 'all 0.15s',
    }}>{label}</button>
  )

  const WeekSelect = () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
      <span style={{ fontSize: 13, fontWeight: 600, color: '#475569' }}>Semana:</span>
      <select value={weekIdx}
        onChange={e => { setWeekIdx(Number(e.target.value)); setMsg(null) }}
        style={{ padding: '6px 12px', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 13, color: '#1a237e', fontWeight: 600 }}>
        {productionWeeks.map((w, i) => (
          <option key={w.fecha} value={i}>{w.fecha} — {Object.values(w.metas).filter(v => v > 0).length} SKUs con producción</option>
        ))}
      </select>
    </div>
  )

  if (!produccion) return <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>Cargando datos de producción...</div>
  if (productionWeeks.length === 0) return <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>No hay semanas con producción programada.</div>

  return (
    <div>
      {/* View selector */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <ViewBtn id="asignar"     label="① Asignar" />
          <ViewBtn id="seguimiento" label="② Seguimiento" />
          <ViewBtn id="resumen"     label="③ Resumen" />
        </div>
        <WeekSelect />
      </div>

      {msg && (
        <div style={{ background: msg.ok ? '#f0fdf4' : '#fef2f2', border: `1px solid ${msg.ok ? '#86efac' : '#fca5a5'}`, borderRadius: 8, padding: '10px 16px', marginBottom: 16, fontSize: 13, color: msg.ok ? '#166534' : '#991b1b', fontWeight: 500 }}>
          {msg.text}
        </div>
      )}

      {/* ── VISTA ASIGNAR ──────────────────────────────────────────────────── */}
      {view === 'asignar' && (
        <div>
          {/* Metas de la semana */}
          <SectionTitle sub="Producción recomendada por el sistema para esta semana">Metas de la semana</SectionTitle>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 28 }}>
            {activeSKUs.map(s => (
              <div key={s} style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 10, padding: '12px 18px', minWidth: 130 }}>
                <div style={{ fontSize: 11, color: '#166534', fontWeight: 600, marginBottom: 4 }}>{s}</div>
                <div style={{ fontSize: 22, fontWeight: 800, color: '#166534' }}>{(week.metas[s] || 0).toLocaleString('es-PE')}</div>
                <div style={{ fontSize: 11, color: '#94a3b8' }}>unidades</div>
              </div>
            ))}
          </div>

          {/* Tabla de distribución */}
          <SectionTitle sub="Distribuye las metas entre tus operarios">Distribución por operario</SectionTitle>
          {operarios.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8', fontSize: 13 }}>
              Agrega operarios para distribuir las metas.
            </div>
          ) : (
            <div style={{ overflowX: 'auto', marginBottom: 16 }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f8fafc' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'left', color: '#475569', fontWeight: 600, borderBottom: '2px solid #e2e8f0', minWidth: 160 }}>Operario</th>
                    {activeSKUs.map(s => (
                      <th key={s} style={{ padding: '10px 12px', textAlign: 'right', color: '#166534', fontWeight: 600, borderBottom: '2px solid #e2e8f0', minWidth: 100 }}>{s}</th>
                    ))}
                    <th style={{ padding: '10px 12px', textAlign: 'right', color: '#475569', fontWeight: 600, borderBottom: '2px solid #e2e8f0' }}>Total</th>
                    <th style={{ width: 36, borderBottom: '2px solid #e2e8f0' }} />
                  </tr>
                </thead>
                <tbody>
                  {operarios.map((op, i) => {
                    const total = activeSKUs.reduce((s, k) => s + (op.asignaciones[k] || 0), 0)
                    return (
                      <tr key={op.id} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
                        <td style={{ padding: '8px 12px' }}>
                          <input value={op.nombre} placeholder="Nombre del operario"
                            onChange={e => updateOp(op.id, 'nombre', e.target.value)}
                            style={{ width: '100%', padding: '4px 8px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 13, fontWeight: 600, color: '#1a237e', boxSizing: 'border-box' }} />
                          <input value={op.email} placeholder="email@empresa.com"
                            onChange={e => updateOp(op.id, 'email', e.target.value)}
                            style={{ width: '100%', padding: '3px 8px', border: '1px solid #e2e8f0', borderRadius: 6, fontSize: 11, color: '#64748b', marginTop: 4, boxSizing: 'border-box' }} />
                        </td>
                        {activeSKUs.map(s => {
                          const meta = week.metas[s] || 0
                          const total_asig = operarios.reduce((sum, o) => sum + (o.asignaciones[s] || 0), 0)
                          const over = total_asig > meta
                          return (
                            <td key={s} style={{ padding: '8px 12px', textAlign: 'right' }}>
                              <input type="number" min={0} value={op.asignaciones[s] || 0}
                                onChange={e => updateOpSKU(op.id, s, e.target.value)}
                                style={{ width: 90, padding: '4px 8px', border: `1px solid ${over ? '#fca5a5' : '#e2e8f0'}`, borderRadius: 6, fontSize: 13, textAlign: 'right', background: over ? '#fef2f2' : '#fff' }} />
                            </td>
                          )
                        })}
                        <td style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700, color: '#1a237e' }}>{total.toLocaleString('es-PE')}</td>
                        <td style={{ padding: '8px 6px', textAlign: 'center' }}>
                          <button onClick={() => removeOp(op.id)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444', fontSize: 16, lineHeight: 1 }}>×</button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
                <tfoot>
                  <tr style={{ background: '#f0fdf4', fontWeight: 700 }}>
                    <td style={{ padding: '10px 12px', color: '#166534', borderTop: '2px solid #86efac' }}>Total asignado</td>
                    {activeSKUs.map(s => {
                      const total = operarios.reduce((sum, o) => sum + (o.asignaciones[s] || 0), 0)
                      const meta  = week.metas[s] || 0
                      const diff  = total - meta
                      return (
                        <td key={s} style={{ padding: '10px 12px', textAlign: 'right', borderTop: '2px solid #86efac' }}>
                          <div style={{ color: diff === 0 ? '#166534' : diff > 0 ? '#991b1b' : '#92400e' }}>{total.toLocaleString('es-PE')}</div>
                          <div style={{ fontSize: 10, fontWeight: 400, color: '#94a3b8' }}>meta: {meta.toLocaleString('es-PE')}</div>
                          {diff !== 0 && <div style={{ fontSize: 10, color: diff > 0 ? '#991b1b' : '#92400e' }}>{diff > 0 ? `+${diff}` : diff}</div>}
                        </td>
                      )
                    })}
                    <td style={{ borderTop: '2px solid #86efac' }} /><td style={{ borderTop: '2px solid #86efac' }} />
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <button onClick={addOperario} style={{ background: '#f0fdf4', color: '#166534', border: '1px solid #86efac', borderRadius: 8, padding: '8px 18px', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
              + Agregar operario
            </button>
            <button onClick={saveAsignacion} disabled={saving || operarios.length === 0}
              style={{ background: operarios.length === 0 ? '#e2e8f0' : '#166534', color: operarios.length === 0 ? '#94a3b8' : '#fff', border: 'none', borderRadius: 8, padding: '8px 24px', cursor: operarios.length === 0 ? 'not-allowed' : 'pointer', fontWeight: 700, fontSize: 13 }}>
              {saving ? 'Guardando...' : 'Guardar asignación'}
            </button>
          </div>
        </div>
      )}

      {/* ── VISTA SEGUIMIENTO ─────────────────────────────────────────────────── */}
      {view === 'seguimiento' && (
        <div>
          <SectionTitle sub="Registra el avance de cada operario — actualiza manualmente al consultar con el equipo">
            Seguimiento de avance
          </SectionTitle>
          {operarios.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8', fontSize: 13 }}>
              Primero guarda una asignación en la vista ① Asignar.
            </div>
          ) : (
            operarios.map(op => {
              const p = progreso[op.id] || { avances: {}, notas: '' }
              const totalMeta = activeSKUs.reduce((s, k) => s + (op.asignaciones[k] || 0), 0)
              const totalAv   = activeSKUs.reduce((s, k) => s + (p.avances?.[k] || 0), 0)
              const totalPct  = totalMeta > 0 ? Math.round(totalAv / totalMeta * 100) : 0
              return (
                <div key={op.id} style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '18px 20px', marginBottom: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <div style={{ fontWeight: 700, color: '#1a237e', fontSize: 15 }}>{op.nombre || '—'}</div>
                      {op.email && <div style={{ fontSize: 12, color: '#64748b' }}>{op.email}</div>}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <div style={{ fontSize: 11, background: STATUS_BG(totalPct), color: STATUS_COLOR(totalPct), padding: '3px 10px', borderRadius: 10, fontWeight: 700 }}>
                        {STATUS_LABEL(totalPct)} · {totalPct}%
                      </div>
                      <button onClick={() => saveProgreso(op.id)}
                        style={{ background: '#166534', color: '#fff', border: 'none', borderRadius: 7, padding: '6px 14px', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>
                        Guardar
                      </button>
                    </div>
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginBottom: 10 }}>
                    <thead>
                      <tr style={{ background: '#f8fafc' }}>
                        {['SKU', 'Meta', 'Avance actual', '%', 'Estado'].map(h => (
                          <th key={h} style={{ padding: '7px 10px', textAlign: h === 'SKU' ? 'left' : 'right', color: '#475569', fontWeight: 600, borderBottom: '1px solid #e2e8f0', fontSize: 12 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {activeSKUs.map(s => {
                        const meta  = op.asignaciones[s] || 0
                        const av    = p.avances?.[s] || 0
                        const pct   = meta > 0 ? Math.min(100, Math.round(av / meta * 100)) : 0
                        return (
                          <tr key={s}>
                            <td style={{ padding: '7px 10px', fontWeight: 600, color: '#0e7490' }}>{s}</td>
                            <td style={{ padding: '7px 10px', textAlign: 'right' }}>{meta.toLocaleString('es-PE')}</td>
                            <td style={{ padding: '7px 10px', textAlign: 'right' }}>
                              <input type="number" min={0} max={meta} value={av}
                                onChange={e => updateAvance(op.id, s, e.target.value)}
                                style={{ width: 90, padding: '3px 7px', border: '1px solid #e2e8f0', borderRadius: 6, textAlign: 'right', fontSize: 13 }} />
                            </td>
                            <td style={{ padding: '7px 10px', textAlign: 'right', fontWeight: 700, color: STATUS_COLOR(pct) }}>{pct}%</td>
                            <td style={{ padding: '7px 10px', textAlign: 'right' }}>
                              <span style={{ background: STATUS_BG(pct), color: STATUS_COLOR(pct), padding: '2px 8px', borderRadius: 8, fontSize: 11, fontWeight: 600 }}>
                                {STATUS_LABEL(pct)}
                              </span>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                  <textarea value={p.notas || ''} onChange={e => updateNotas(op.id, e.target.value)}
                    placeholder="Notas o incidencias del operario..."
                    style={{ width: '100%', borderRadius: 7, border: '1px solid #e2e8f0', padding: '8px 10px', fontSize: 12, color: '#475569', resize: 'vertical', minHeight: 54, boxSizing: 'border-box' }} />
                </div>
              )
            })
          )}
        </div>
      )}

      {/* ── VISTA RESUMEN ─────────────────────────────────────────────────────── */}
      {view === 'resumen' && (
        <div>
          {/* Print styles */}
          <style>{`@media print { .no-print { display: none !important; } body { font-size: 12px; } }`}</style>

          <div style={{ display: 'flex', gap: 12, marginBottom: 24 }} className="no-print">
            <button onClick={() => window.print()} style={{ background: '#1a237e', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 18px', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
              🖨️ Imprimir / PDF
            </button>
            {operarios.some(o => o.email) && (
              <button onClick={mailtoAll} style={{ background: '#0e7490', color: '#fff', border: 'none', borderRadius: 8, padding: '8px 18px', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>
                📧 Enviar a todos
              </button>
            )}
          </div>

          {/* Print header */}
          <div style={{ marginBottom: 24 }}>
            <h2 style={{ color: '#1a237e', margin: 0, fontSize: 18 }}>Plan de Producción — Semana del {week?.fecha}</h2>
            <div style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
              {operarios.length} operario(s) · {activeSKUs.length} SKU(s) con producción programada
            </div>
          </div>

          {operarios.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 0', color: '#94a3b8', fontSize: 13 }}>
              Sin asignaciones guardadas para esta semana.
            </div>
          ) : (
            operarios.map(op => {
              const p = progreso[op.id] || { avances: {}, notas: '' }
              const totalMeta = activeSKUs.reduce((s, k) => s + (op.asignaciones[k] || 0), 0)
              const totalAv   = activeSKUs.reduce((s, k) => s + (p.avances?.[k] || 0), 0)
              const totalPct  = totalMeta > 0 ? Math.round(totalAv / totalMeta * 100) : 0
              return (
                <div key={op.id} style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '16px 20px', marginBottom: 14 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                    <div>
                      <div style={{ fontWeight: 700, color: '#1a237e', fontSize: 16 }}>{op.nombre || '—'}</div>
                      {op.email && <div style={{ fontSize: 12, color: '#64748b' }}>{op.email}</div>}
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }} className="no-print">
                      <span style={{ background: STATUS_BG(totalPct), color: STATUS_COLOR(totalPct), padding: '3px 10px', borderRadius: 10, fontWeight: 700, fontSize: 12 }}>
                        {STATUS_LABEL(totalPct)} · {totalPct}%
                      </span>
                      <button onClick={() => copyLink(op.token)}
                        style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0', borderRadius: 7, padding: '5px 12px', cursor: 'pointer', fontSize: 12, fontWeight: 500 }}>
                        🔗 Copiar link
                      </button>
                      {op.email && (
                        <button onClick={() => mailtoOp(op)}
                          style={{ background: '#f0fdfe', color: '#0e7490', border: '1px solid #a5f3fc', borderRadius: 7, padding: '5px 12px', cursor: 'pointer', fontSize: 12, fontWeight: 500 }}>
                          📧 Enviar
                        </button>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    {activeSKUs.map(s => {
                      const meta = op.asignaciones[s] || 0
                      const av   = p.avances?.[s] || 0
                      const pct  = meta > 0 ? Math.min(100, Math.round(av / meta * 100)) : 0
                      return (
                        <div key={s} style={{ background: '#f8fafc', borderRadius: 8, padding: '10px 14px', minWidth: 110, borderLeft: `3px solid ${STATUS_COLOR(pct)}` }}>
                          <div style={{ fontWeight: 700, color: '#0e7490', fontSize: 12, marginBottom: 3 }}>{s}</div>
                          <div style={{ fontWeight: 800, fontSize: 17, color: '#1a237e' }}>{meta.toLocaleString('es-PE')}</div>
                          <div style={{ fontSize: 11, color: STATUS_COLOR(pct) }}>Avance: {av.toLocaleString('es-PE')} ({pct}%)</div>
                          <div style={{ height: 4, background: '#e2e8f0', borderRadius: 2, marginTop: 5, overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${pct}%`, background: STATUS_COLOR(pct), borderRadius: 2 }} />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                  {p.notas && (
                    <div style={{ marginTop: 10, fontSize: 12, color: '#92400e', background: '#fffbeb', padding: '6px 10px', borderRadius: 6 }}>
                      Nota: {p.notas}
                    </div>
                  )}
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 8 }} className="no-print">
                    Link operario: {baseUrl}/asignacion/{op.token}
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}

// ─── Tab: Ingesta de Datos y Reentrenamiento ─────────────────────────────────

function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  const chunk = 8192
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk))
  }
  return btoa(binary)
}

function parseMovimientosPreview(buffer, maxRows = 25) {
  const text = new TextDecoder('windows-1252').decode(buffer)
  const lines = text.trim().split(/\r?\n/)
  if (lines.length < 2) return { rows: [], totalRows: 0, error: 'Archivo vacío o sin datos.' }
  const sep = lines[0].includes(';') ? ';' : ','
  const header = lines[0].split(sep).map(h => h.trim())
  const normalize = s => s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z]/g, '')
  const idxOf = name => header.findIndex(h => normalize(h).includes(name))
  const iCodigo  = idxOf('codigo')
  const iFecha   = idxOf('fecha')
  const iDoc     = idxOf('documento')
  const iEntrada = idxOf('entrada')
  const iSalida  = idxOf('salida')
  const totalRows = lines.length - 1
  const preview = lines.slice(1, maxRows + 1).filter(l => l.trim()).map(line => {
    const p = line.split(sep)
    return {
      codigo:  (p[iCodigo]  || '').trim(),
      fecha:   (p[iFecha]   || '').trim(),
      doc:     (p[iDoc]     || '').trim().substring(0, 30),
      entrada: (p[iEntrada] || '').trim(),
      salida:  (p[iSalida]  || '').trim(),
    }
  })
  const hasRequired = iCodigo >= 0 && iFecha >= 0 && iEntrada >= 0 && iSalida >= 0
  return { rows: preview, totalRows, hasRequired }
}

function downloadMovimientosTemplate() {
  const year = new Date().getFullYear()
  const lines = [
    'Código;Descripción;Fecha;Documento;Número;Bodega;Entrada;Salida;Saldo;Valor Unitario;Entrada.1;Salida.1;Saldo.1;Costo Unitario;Empresa_Cliente;Canal_Venta;Punto_Venta',
    `CER001;CANALETA RANURADA FG 0.75 (60x40mm);${year}-04-07;Venta - Boleta;001-000123;;0.0;1200.0;3800.0;0.92;;;3484.0;0.92;CLIENTE A;MOSTRADOR;LOCAL 1`,
    `CER005;CANALETA RANURADA FG 0.75 (100x40mm);${year}-04-07;Venta - Boleta;001-000124;;0.0;750.0;2100.0;0.92;;;1932.0;0.92;CLIENTE B;MOSTRADOR;LOCAL 1`,
    `CEO001;CANALETA OMEGA FG 0.75 (60mm);${year}-04-14;Venta - Boleta;001-000125;;0.0;980.0;4100.0;1.17;;;3802.0;1.17;CLIENTE C;MAYORISTA;LOCAL 2`,
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `Movimientos_MayorAuxiliar_${year}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function TabIngestaReentrenamiento({ pipeline, setPipeline }) {
  const [fileInfo, setFileInfo]       = useState(null)   // { name, base64, preview, totalRows, hasRequired, year }
  const [uploadError, setUploadError] = useState('')
  const [uploading, setUploading]     = useState(false)
  const [uploadOk, setUploadOk]       = useState(null)
  const [history, setHistory]         = useState([])
  const [dragging, setDragging]       = useState(false)
  const [retraining, setRetraining]   = useState(false)

  useEffect(() => {
    fetch('/api/ingest-data').then(r => r.json()).then(d => setHistory(Array.isArray(d) ? d : [])).catch(() => {})
  }, [uploadOk])

  const handleFile = (file) => {
    if (!file) return
    setUploadError(''); setUploadOk(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      const buffer = e.target.result
      const base64 = arrayBufferToBase64(buffer)
      const { rows, totalRows, hasRequired, error } = parseMovimientosPreview(buffer)
      if (error) { setUploadError(error); setFileInfo(null); return }
      const yearMatch = file.name.match(/(\d{4})/)
      const year = yearMatch ? yearMatch[1] : null
      setFileInfo({ name: file.name, base64, preview: rows, totalRows, hasRequired, year })
    }
    reader.readAsArrayBuffer(file)
  }

  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleUpload = async () => {
    if (!fileInfo) return
    setUploading(true); setUploadError(''); setUploadOk(null)
    try {
      const r = await fetch('/api/ingest-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: fileInfo.name, content_base64: fileInfo.base64 }),
      })
      const data = await r.json()
      if (!r.ok) {
        setUploadError(data.error || 'Error desconocido')
      } else {
        setUploadOk(data.entry)
        setFileInfo(null)
      }
    } catch (err) {
      setUploadError(String(err))
    } finally {
      setUploading(false)
    }
  }

  const handleRetrain = async () => {
    setRetraining(true)
    try {
      const r = await fetch('/api/pipeline', { method: 'POST' })
      const data = await r.json()
      setPipeline({ status: data.status || 'running' })
    } catch (_) {}
    finally { setRetraining(false) }
  }

  const existsInHistory = fileInfo?.name && history.some(h => h.filename === fileInfo.name)

  return (
    <div>
      {/* ── Sección 1: Carga de datos ── */}
      <SectionTitle sub="Sube el archivo de Movimientos exportado desde el ERP para incorporar nuevos datos al sistema">
        Cargar nuevo archivo de movimientos
      </SectionTitle>

      {/* Info del formato */}
      <div style={{ background: '#f0fdfe', border: '1px solid #a5f3fc', borderRadius: 10, padding: '14px 20px', marginBottom: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: TEAL_DARK, marginBottom: 6 }}>Formato del archivo ERP (sin cambios)</div>
          <code style={{ fontSize: 11, color: '#0e7490', background: '#cffafe', padding: '3px 8px', borderRadius: 4 }}>
            Movimientos_MayorAuxiliar_YYYY.csv
          </code>
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 4 }}>
            Columnas requeridas: Código · Fecha · Entrada · Salida · Documento — separador&nbsp;<code>;</code>
          </div>
        </div>
        <button onClick={downloadMovimientosTemplate} style={{
          background: TEAL_DARK, color: '#fff', border: 'none', borderRadius: 8,
          padding: '8px 16px', cursor: 'pointer', fontSize: 13, fontWeight: 600,
        }}>
          ⬇ Descargar plantilla
        </button>
      </div>

      {/* Zona drag & drop */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => document.getElementById('file-input-mov').click()}
        style={{
          border: `2px dashed ${dragging ? TEAL_DARK : '#cbd5e1'}`,
          borderRadius: 12, padding: '36px 24px', textAlign: 'center',
          background: dragging ? '#f0fdfe' : '#f8fafc',
          cursor: 'pointer', marginBottom: 20, transition: 'all 0.15s',
        }}
      >
        <div style={{ fontSize: 28, marginBottom: 8 }}>📂</div>
        <div style={{ fontWeight: 600, color: dragging ? TEAL_DARK : '#64748b' }}>
          {dragging ? 'Suelta el archivo aquí' : 'Arrastra Movimientos_MayorAuxiliar_YYYY.csv o haz clic'}
        </div>
        <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 4 }}>El archivo se sube tal como lo exporta el ERP</div>
        <input id="file-input-mov" type="file" accept=".csv"
          style={{ display: 'none' }}
          onChange={e => handleFile(e.target.files[0])}
        />
      </div>

      {uploadError && (
        <div style={{ background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: 8, padding: '10px 16px', color: RED, marginBottom: 16, fontSize: 13 }}>
          {uploadError}
        </div>
      )}

      {/* Info del archivo detectado */}
      {fileInfo && (
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 12, flexWrap: 'wrap' }}>
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 16px', display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              <div>
                <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Archivo</div>
                <div style={{ fontWeight: 600, color: BLUE, fontSize: 13 }}>{fileInfo.name}</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Total filas</div>
                <div style={{ fontWeight: 600, color: BLUE, fontSize: 13 }}>{fileInfo.totalRows.toLocaleString('es-PE')}</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Año detectado</div>
                <div style={{ fontWeight: 600, color: fileInfo.year ? TEAL_DARK : ORANGE, fontSize: 13 }}>{fileInfo.year || 'No detectado'}</div>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Columnas</div>
                <div style={{ fontWeight: 600, color: fileInfo.hasRequired ? GREEN : RED, fontSize: 13 }}>
                  {fileInfo.hasRequired ? '✓ OK' : '✗ Faltan columnas'}
                </div>
              </div>
            </div>
            {existsInHistory && (
              <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 8, padding: '8px 14px', fontSize: 12, color: '#92400e' }}>
                Este archivo ya fue cargado antes — <strong>reemplazará</strong> la versión existente en el servidor.
              </div>
            )}
            <button onClick={() => { setFileInfo(null); setUploadError(''); setUploadOk(null) }}
              style={{ background: 'none', border: '1px solid #e2e8f0', borderRadius: 6, padding: '6px 12px', cursor: 'pointer', fontSize: 12, color: '#64748b', marginLeft: 'auto' }}>
              Limpiar
            </button>
          </div>

          {/* Preview primeras filas */}
          <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>
            Vista previa — primeras {fileInfo.preview.length} filas de {fileInfo.totalRows.toLocaleString('es-PE')}
          </div>
          <div style={{ overflowX: 'auto', maxHeight: 240, overflowY: 'auto', borderRadius: 8, border: '1px solid #e2e8f0' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead style={{ position: 'sticky', top: 0, background: '#f8fafc', zIndex: 1 }}>
                <tr>
                  {['Código', 'Fecha', 'Documento', 'Entrada', 'Salida'].map(h => (
                    <th key={h} style={{ padding: '7px 12px', textAlign: 'left', color: '#475569', fontWeight: 600, borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {fileInfo.preview.map((r, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
                    <td style={{ padding: '5px 12px', fontWeight: 500, color: TEAL_DARK }}>{r.codigo || '—'}</td>
                    <td style={{ padding: '5px 12px' }}>{r.fecha || '—'}</td>
                    <td style={{ padding: '5px 12px', color: '#64748b' }}>{r.doc || '—'}</td>
                    <td style={{ padding: '5px 12px', color: GREEN }}>{r.entrada || '—'}</td>
                    <td style={{ padding: '5px 12px', color: RED }}>{r.salida || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Resultado de carga exitosa */}
      {uploadOk && (
        <div style={{ background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: '12px 16px', marginBottom: 16, fontSize: 13 }}>
          <div style={{ fontWeight: 600, color: GREEN, marginBottom: 4 }}>Archivo guardado correctamente en el servidor</div>
          <div style={{ color: '#166534' }}>
            <strong>{uploadOk.filename}</strong> — {uploadOk.rows.toLocaleString('es-PE')} registros
            {uploadOk.replaced ? ' (reemplazó versión anterior)' : ' (nuevo archivo)'}
          </div>
          <div style={{ marginTop: 8, fontSize: 12, color: '#166534' }}>
            Ya puedes ejecutar el reentrenamiento para generar nuevas predicciones.
          </div>
        </div>
      )}

      {/* Botón de carga */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 36 }}>
        <button
          onClick={handleUpload}
          disabled={!fileInfo || !fileInfo.hasRequired || uploading}
          style={{
            background: !fileInfo || !fileInfo.hasRequired || uploading ? '#e2e8f0' : TEAL_DARK,
            color: !fileInfo || !fileInfo.hasRequired || uploading ? '#94a3b8' : '#fff',
            border: 'none', borderRadius: 8,
            padding: '10px 24px', cursor: !fileInfo || !fileInfo.hasRequired || uploading ? 'not-allowed' : 'pointer',
            fontWeight: 700, fontSize: 14, transition: 'all 0.15s',
          }}
        >
          {uploading ? 'Subiendo archivo...' : fileInfo ? `Subir ${fileInfo.name}` : 'Selecciona un archivo primero'}
        </button>
      </div>

      {/* ── Sección 2: Reentrenamiento ── */}
      <div style={{ borderTop: '2px solid #e2e8f0', paddingTop: 28, marginBottom: 28 }}>
        <SectionTitle sub="Ejecuta el pipeline completo con todos los datos disponibles incluyendo el archivo recién cargado">
          Reentrenamiento del modelo
        </SectionTitle>
        <div style={{ background: '#f8fafc', borderRadius: 10, border: '1px solid #e2e8f0', padding: '20px 24px', display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 260 }}>
            <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.8, marginBottom: 12 }}>
              <strong>Pasos del pipeline:</strong><br />
              1. Limpieza y filtrado de datos<br />
              2. Agregación semanal + feature engineering<br />
              3. Optimización de hiperparámetros (XGBoost)<br />
              4. Predicciones 52 semanas por SKU<br />
              <strong>Duración estimada: 5–15 minutos.</strong>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 10, height: 10, borderRadius: '50%',
                background: pipeline?.status === 'running' ? ORANGE : pipeline?.status === 'success' ? GREEN : '#94a3b8',
                boxShadow: pipeline?.status === 'running' ? `0 0 0 4px ${ORANGE}30` : 'none',
                transition: 'all 0.3s',
              }} />
              <span style={{ fontSize: 13, color: '#475569' }}>
                {pipeline?.status === 'running' ? 'Pipeline en ejecución...' :
                 pipeline?.status === 'success' ? 'Última ejecución completada exitosamente' :
                 pipeline?.status === 'error' ? 'Error en la última ejecución' :
                 'Esperando orden de ejecución'}
              </span>
            </div>
          </div>
          <button
            onClick={handleRetrain}
            disabled={retraining || pipeline?.status === 'running'}
            style={{
              background: retraining || pipeline?.status === 'running' ? '#e2e8f0' : '#166534',
              color: retraining || pipeline?.status === 'running' ? '#94a3b8' : '#fff',
              border: 'none', borderRadius: 8,
              padding: '12px 24px', cursor: retraining || pipeline?.status === 'running' ? 'not-allowed' : 'pointer',
              fontWeight: 700, fontSize: 14, whiteSpace: 'nowrap',
            }}
          >
            {retraining ? 'Iniciando...' : pipeline?.status === 'running' ? 'En proceso...' : '▶ Ejecutar pipeline'}
          </button>
        </div>
        {pipeline?.status === 'running' && (
          <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 8, padding: '10px 16px', marginTop: 12, fontSize: 12, color: '#92400e' }}>
            El pipeline está corriendo en segundo plano. Las nuevas predicciones estarán disponibles al terminar — no cierres la sesión.
          </div>
        )}
      </div>

      {/* ── Sección 3: Historial ── */}
      <div style={{ borderTop: '2px solid #e2e8f0', paddingTop: 28 }}>
        <SectionTitle sub="Archivos cargados al servidor">Historial de cargas</SectionTitle>
        {history.length === 0 ? (
          <div style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center', padding: '24px 0' }}>
            Sin cargas registradas todavía.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#f8fafc' }}>
                  {['Fecha de carga', 'Archivo', 'Registros', 'Acción'].map(h => (
                    <th key={h} style={{ padding: '9px 14px', textAlign: 'left', color: '#475569', fontWeight: 600, borderBottom: '2px solid #e2e8f0' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map((h, i) => (
                  <tr key={h.id} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
                    <td style={{ padding: '8px 14px', color: '#64748b' }}>
                      {new Date(h.fecha).toLocaleString('es-PE', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td style={{ padding: '8px 14px', fontWeight: 600, color: TEAL_DARK }}>{h.filename}</td>
                    <td style={{ padding: '8px 14px' }}>{h.rows?.toLocaleString('es-PE') || '—'}</td>
                    <td style={{ padding: '8px 14px', fontSize: 12 }}>
                      <span style={{ background: h.replaced ? '#fef9c3' : '#f0fdf4', color: h.replaced ? '#854d0e' : '#166534', padding: '2px 8px', borderRadius: 4, fontWeight: 600 }}>
                        {h.replaced ? 'Reemplazado' : 'Nuevo'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Tab: Simulación con Predicast ───────────────────────────────────────────

function TabSimulacionPredicast({ backtest, safetyWeeks, setSafetyWeeks, precios, skuPlancha }) {
  const skus = backtest?.skus || {}
  const timeline = backtest?.timeline || []

  const metrics = useMemo(() => {
    return Object.entries(skus).map(([sku, d]) => {
      const cfg = skuPlancha[sku]
      if (!cfg) return null
      const unitCost = (precios[cfg.tipo] || 0) / cfg.prod_por_plancha
      const { produccion_total, ventas_total, n_semanas, avg_semanal } = d.totales
      const sobreProdReal = Math.max(0, produccion_total - ventas_total)
      const sobreProdSistema = Math.round(avg_semanal * safetyWeeks)
      const costoReal = Math.round(sobreProdReal * unitCost)
      const costoSistema = Math.round(sobreProdSistema * unitCost)
      const ahorro = Math.max(0, costoReal - costoSistema)
      return { sku, sobreProdReal, sobreProdSistema, costoReal, costoSistema, ahorro, n_semanas }
    }).filter(Boolean)
  }, [skus, safetyWeeks, precios, skuPlancha])

  const totalReal    = metrics.reduce((s, m) => s + m.costoReal, 0)
  const totalSistema = metrics.reduce((s, m) => s + Math.min(m.costoSistema, m.costoReal), 0)
  const totalAhorro  = metrics.reduce((s, m) => s + m.ahorro, 0)
  const reduccion    = totalReal > 0 ? (totalAhorro / totalReal * 100).toFixed(1) : 0

  const barData = metrics.map(m => ({
    sku: m.sku,
    sistema: Math.min(m.costoSistema, m.costoReal),
    ahorro: m.ahorro,
  }))

  const monthly = useMemo(() => {
    const map = {}
    for (const r of timeline) {
      const mes = r.semana.substring(0, 7)
      if (!map[mes]) map[mes] = { mes, ventas: 0, produccion: 0 }
      map[mes].ventas    += r.ventas
      map[mes].produccion += r.produccion
    }
    return Object.values(map).sort((a, b) => a.mes.localeCompare(b.mes))
  }, [timeline])

  const n_semanas = metrics[0]?.n_semanas || 0
  const periodo   = timeline.length
    ? `${timeline[0].semana.substring(0, 7)} → ${timeline[timeline.length - 1].semana.substring(0, 7)}`
    : ''

  if (!backtest) return (
    <div style={{ textAlign: 'center', padding: 60, color: '#94a3b8' }}>
      Cargando datos históricos...
    </div>
  )

  return (
    <div>
      {/* Info / controls banner */}
      <div style={{
        background: '#f0fdfe', border: '1px solid #a5f3fc', borderRadius: 10,
        padding: '14px 20px', marginBottom: 24,
        display: 'flex', gap: 32, flexWrap: 'wrap', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: 11, color: '#0891b2', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>Período analizado</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: TEAL_DARK }}>{periodo}</div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: '#0891b2', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>Semanas de datos</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: TEAL_DARK }}>{n_semanas} sem.</div>
        </div>
        <div>
          <div style={{ fontSize: 11, color: '#0891b2', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>SKUs analizados</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: TEAL_DARK }}>7 productos</div>
        </div>
        <div style={{ marginLeft: 'auto' }}>
          <div style={{ fontSize: 11, color: '#0891b2', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5, marginBottom: 4 }}>
            Buffer de seguridad: <span style={{ color: TEAL_DARK }}>{safetyWeeks} sem.</span>
          </div>
          <input type="range" min={0} max={8} value={safetyWeeks}
            onChange={e => setSafetyWeeks(Number(e.target.value))}
            style={{ width: 140, accentColor: TEAL_DARK }}
          />
        </div>
      </div>

      {/* KPI strip */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 28, flexWrap: 'wrap' }}>
        <StatCard label="Sobrecosto real (mat. prima)" value={`S/ ${fmt(totalReal)}`}
          sub="Sobreproducción histórica acumulada" color={RED} bg="#fef2f2" />
        <StatCard label="Sobrecosto con Predicast" value={`S/ ${fmt(totalSistema)}`}
          sub={`Buffer intencional de ${safetyWeeks} sem.`} color={TEAL_DARK} bg="#f0fdfe" />
        <StatCard label="Ahorro potencial total" value={`S/ ${fmt(totalAhorro)}`}
          sub="Si se hubiera usado el sistema" color={GREEN} bg="#f0fdf4" />
        <StatCard label="Reducción de sobrecosto" value={`${reduccion}%`}
          sub="Eficiencia ganada con Predicast" color={PURPLE} bg="#f5f3ff" />
      </div>

      {/* Chart 1: stacked bar por SKU */}
      <SectionTitle sub="Costo de sobreproducción de materia prima por SKU — Real (apilado) vs si se hubiera usado Predicast">
        Comparativa de sobrecosto por SKU
      </SectionTitle>
      <div style={{ background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0', padding: '20px 8px 8px', marginBottom: 28 }}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData} margin={{ top: 8, right: 24, left: 10, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="sku" tick={{ fontSize: 12 }} />
            <YAxis tickFormatter={v => `S/${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v, n) => [`S/ ${fmt(v)}`, n === 'sistema' ? 'Con Predicast (buffer mín.)' : 'Ahorro potencial']} />
            <Legend formatter={v => v === 'sistema' ? 'Con Predicast (buffer mínimo)' : 'Ahorro potencial'} />
            <Bar dataKey="sistema" name="sistema" stackId="a" fill={TEAL_LIGHT} />
            <Bar dataKey="ahorro"  name="ahorro"  stackId="a" fill={GREEN} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p style={{ textAlign: 'center', fontSize: 11, color: '#94a3b8', margin: '4px 0 0' }}>
          Barra completa = costo real de sobreproducción. Sección verde = ahorro potencial con Predicast.
        </p>
      </div>

      {/* Chart 2: timeline producción vs ventas mensual */}
      <SectionTitle sub="Producción real vs ventas reales (todos los SKUs, agregado mensual) — la brecha visible es la sobreproducción">
        Evolución histórica: Producción vs Ventas (mensual)
      </SectionTitle>
      <div style={{ background: '#fff', borderRadius: 10, border: '1px solid #e2e8f0', padding: '20px 8px 8px', marginBottom: 28 }}>
        <ResponsiveContainer width="100%" height={260}>
          <ComposedChart data={monthly} margin={{ top: 8, right: 24, left: 10, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="mes" tick={{ fontSize: 10 }} interval={5} />
            <YAxis tickFormatter={v => `${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v, n) => [`${fmt(v)} uds.`, n === 'produccion' ? 'Producción real' : 'Ventas reales']} />
            <Legend formatter={v => v === 'produccion' ? 'Producción real' : 'Ventas reales'} />
            <Area type="monotone" dataKey="produccion" name="produccion"
              fill="#bfdbfe" stroke={BLUE_LIGHT} strokeWidth={1.5} fillOpacity={0.7} />
            <Line type="monotone" dataKey="ventas" name="ventas"
              stroke={GREEN} strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
        <p style={{ textAlign: 'center', fontSize: 11, color: '#94a3b8', margin: '4px 0 0' }}>
          Área azul sobre la línea verde = sobreproducción histórica. Con Predicast, la producción habría seguido de cerca la línea de ventas.
        </p>
      </div>

      {/* Tabla detalle */}
      <SectionTitle sub="Desglose numérico por SKU">Detalle por SKU</SectionTitle>
      <div style={{ overflowX: 'auto', marginBottom: 16 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f8fafc' }}>
              {['SKU', 'Sobreprod. real (uds)', 'Sobreprod. Predicast (uds)', 'Costo real (S/)', 'Costo c/ Predicast (S/)', 'Ahorro (S/)'].map((h, i) => (
                <th key={h} style={{
                  padding: '10px 14px', textAlign: i === 0 ? 'left' : 'right',
                  color: i === 3 ? RED : i === 4 ? TEAL_DARK : i === 5 ? GREEN : '#475569',
                  fontWeight: 600, borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap',
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.map((m, i) => (
              <tr key={m.sku} style={{ background: i % 2 === 0 ? '#fff' : '#f8fafc' }}>
                <td style={{ padding: '9px 14px', fontWeight: 600, color: TEAL_DARK }}>{m.sku}</td>
                <td style={{ padding: '9px 14px', textAlign: 'right' }}>{fmt(m.sobreProdReal)}</td>
                <td style={{ padding: '9px 14px', textAlign: 'right', color: '#64748b' }}>{fmt(m.sobreProdSistema)}</td>
                <td style={{ padding: '9px 14px', textAlign: 'right', color: RED }}>{fmt(m.costoReal)}</td>
                <td style={{ padding: '9px 14px', textAlign: 'right', color: TEAL_DARK }}>{fmt(Math.min(m.costoSistema, m.costoReal))}</td>
                <td style={{ padding: '9px 14px', textAlign: 'right', color: GREEN, fontWeight: 600 }}>
                  {m.ahorro > 0 ? fmt(m.ahorro) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr style={{ background: '#f0fdf4', fontWeight: 700 }}>
              <td style={{ padding: '10px 14px', borderTop: '2px solid #86efac', color: BLUE }}>TOTAL</td>
              <td style={{ padding: '10px 14px', textAlign: 'right', borderTop: '2px solid #86efac' }}>
                {fmt(metrics.reduce((s, m) => s + m.sobreProdReal, 0))}
              </td>
              <td style={{ padding: '10px 14px', textAlign: 'right', borderTop: '2px solid #86efac', color: '#64748b' }}>
                {fmt(metrics.reduce((s, m) => s + m.sobreProdSistema, 0))}
              </td>
              <td style={{ padding: '10px 14px', textAlign: 'right', borderTop: '2px solid #86efac', color: RED }}>
                S/ {fmt(totalReal)}
              </td>
              <td style={{ padding: '10px 14px', textAlign: 'right', borderTop: '2px solid #86efac', color: TEAL_DARK }}>
                S/ {fmt(totalSistema)}
              </td>
              <td style={{ padding: '10px 14px', textAlign: 'right', borderTop: '2px solid #86efac', color: GREEN }}>
                S/ {fmt(totalAhorro)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Nota metodológica */}
      <div style={{ background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 8, padding: '10px 16px', fontSize: 12, color: '#92400e' }}>
        <strong>Metodología:</strong> La sobreproducción real proviene de los datos históricos semana a semana (2021–2025).
        El escenario &quot;Con Predicast&quot; simula la producción ajustada a la demanda histórica real más un buffer
        intencional de <strong>{safetyWeeks} semana(s)</strong> de demanda promedio por SKU — representa el ahorro máximo alcanzable con forecast perfecto.
        El modelo ML actual (R² CV ≈ 0.65) captura una fracción de este potencial, que mejora con mayor horizonte histórico.
        El ahorro es la diferencia entre ambos escenarios de costo de materia prima (planchas).
      </div>
    </div>
  )
}

// ─── Tab nav ──────────────────────────────────────────────────────────────────

function TabNav({ active, onChange, tabs, color = BLUE }) {
  return (
    <div style={{ display: 'flex', borderBottom: `2px solid #e2e8f0`, marginBottom: 24, overflowX: 'auto' }}>
      {tabs.map(t => (
        <button key={t.id} onClick={() => onChange(t.id)} style={{
          padding: '10px 20px', background: 'none', border: 'none', cursor: 'pointer',
          fontWeight: 600, fontSize: 14, whiteSpace: 'nowrap',
          color: active === t.id ? color : '#64748b',
          borderBottom: active === t.id ? `3px solid ${color}` : '3px solid transparent',
          marginBottom: -2, transition: 'all 0.15s',
        }}>
          {t.label}
        </button>
      ))}
    </div>
  )
}

// ─── Guía Contextual ──────────────────────────────────────────────────────────

const GUIA_CONTENT = {
  resumen: {
    titulo: 'Resumen Ejecutivo',
    desc: 'Vista general del negocio con los indicadores más importantes de ventas y stock.',
    puntos: [
      'Revisa el total vendido y producido por período',
      'Identifica los SKUs con mayor volumen de movimiento',
      'Usa los filtros de fecha para acotar el análisis',
    ],
    tip: 'Comienza aquí para tener una foto rápida del estado general antes de ir al detalle.',
  },
  producto: {
    titulo: 'Análisis por Producto',
    desc: 'Comportamiento histórico de ventas y stock para cada SKU individualmente.',
    puntos: [
      'Selecciona un SKU del menú para ver su evolución',
      'Compara ventas vs. stock de cierre semana a semana',
      'Detecta temporadas altas y bajas por producto',
    ],
    tip: 'Útil para entender el patrón estacional de cada SKU antes de planificar.',
  },
  exploracion: {
    titulo: 'Exploración de Datos',
    desc: 'Vista interactiva para explorar relaciones y distribuciones del historial completo.',
    puntos: [
      'Filtra por rango de fechas y SKU',
      'Revisa distribuciones y correlaciones entre variables',
      'Detecta outliers o semanas atípicas',
    ],
    tip: 'Ideal para analistas que quieren profundizar antes de tomar decisiones.',
  },
  planificacion: {
    titulo: 'Planificación / GAP',
    desc: 'Compara lo planificado vs. lo ejecutado para identificar brechas de producción.',
    puntos: [
      'GAP positivo = sobreproducción, GAP negativo = subproducción',
      'Identifica semanas con mayor desviación histórica',
      'Usa esta vista para ajustar tu criterio de safety stock',
    ],
    tip: 'Un GAP negativo recurrente en un SKU indica que la meta de producción está subestimada.',
  },
  costo_planchas: {
    titulo: 'Inversión de Planchas',
    desc: 'Calcula el costo de materia prima (planchas metálicas) para el plan de producción.',
    puntos: [
      'Ingresa el precio actual de plancha por m²',
      'Ve el costo proyectado por SKU y semana',
      'Identifica las semanas de mayor inversión en material',
    ],
    tip: 'Actualiza el precio cuando cambie en el mercado para mantener proyecciones precisas.',
  },
  analisis_financiero: {
    titulo: 'Análisis Financiero Histórico',
    desc: 'Evalúa el impacto económico de las decisiones de producción en el tiempo.',
    puntos: [
      'Revisa la inversión acumulada por período',
      'Compara costos de sobreproducción vs. demanda insatisfecha',
      'Identifica los SKUs de mayor peso en el presupuesto',
    ],
    tip: 'Cruza esta vista con Planificación/GAP para cuantificar cuánto costaron las desviaciones.',
  },
  backtest_predicast: {
    titulo: 'Simulación con Predicast',
    desc: 'Retrospectiva: ¿cuánto se habría ahorrado si Predicast hubiera guiado la producción histórica?',
    puntos: [
      'Ajusta las semanas de safety stock con el slider',
      'Compara producción real vs. producción guiada por el modelo',
      'Ve el ahorro en unidades y costos por SKU',
    ],
    tip: 'Esta vista es ideal para presentar el valor del sistema ante la gerencia general.',
  },
  produccion: {
    titulo: 'Plan de Producción',
    desc: 'Calendario semanal de recomendaciones generado por el modelo de ML.',
    puntos: [
      'Las semanas urgentes indican stock por debajo del mínimo',
      'El safety stock dinámico se ajusta por SKU automáticamente',
      'Exporta o imprime el calendario para compartirlo',
    ],
    tip: 'Revisa primero las semanas marcadas como urgentes antes de planificar el calendario.',
  },
  asignacion: {
    titulo: 'Asignación de Operarios',
    desc: 'Distribuye las metas de producción entre tu equipo y haz seguimiento del avance.',
    puntos: [
      '① Asignar: define cuánto produce cada operario por SKU',
      '② Seguimiento: registra el avance real manualmente',
      '③ Resumen: genera un reporte imprimible o por email',
    ],
    tip: 'Usa "Copiar link" para enviar a cada operario su vista personalizada — sin necesidad de login.',
  },
  ingesta: {
    titulo: 'Actualización de Datos',
    desc: 'Sube el archivo del ERP para actualizar la base de datos y reentrenar los modelos.',
    puntos: [
      'El archivo debe llamarse Movimientos_MayorAuxiliar_YYYY.csv',
      'El sistema valida el formato antes de guardar',
      'Tras subir, pulsa "Ejecutar pipeline" para reentrenar',
    ],
    tip: 'Sube el archivo mensualmente o al cierre de cada período para mantener las predicciones vigentes.',
  },
  admin: {
    titulo: 'Administración de Usuarios',
    desc: 'Gestiona quién tiene acceso al sistema y qué módulos puede ver.',
    puntos: [
      'Asigna roles: admin, gerente_financiero, gerente_produccion',
      'Crea o desactiva usuarios desde el panel',
      'Los roles determinan qué módulos aparecen en el dashboard',
    ],
    tip: 'Solo usuarios con rol admin pueden acceder a esta sección.',
  },
}

function GuiaWidget({ tab }) {
  const [open, setOpen] = useState(false)
  const g = GUIA_CONTENT[tab]

  useEffect(() => { setOpen(false) }, [tab])

  if (!g) return null

  return (
    <>
      <style>{`
        @keyframes guiaSlideUp {
          from { opacity: 0; transform: translateY(12px) scale(0.97); }
          to   { opacity: 1; transform: translateY(0)    scale(1);    }
        }
        @keyframes guiaPulse {
          0%,100% { box-shadow: 0 4px 16px rgba(26,35,126,0.35); }
          50%      { box-shadow: 0 4px 24px rgba(26,35,126,0.55); }
        }
      `}</style>

      <div style={{ position: 'fixed', bottom: 28, right: 28, zIndex: 9999, display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 10 }}>
        {/* Panel */}
        {open && (
          <div style={{
            width: 300, background: '#fff', borderRadius: 18,
            boxShadow: '0 8px 40px rgba(0,0,0,0.16)',
            border: '1px solid #e2e8f0',
            padding: '18px 18px 14px',
            animation: 'guiaSlideUp 0.22s ease',
            position: 'relative',
          }}>
            {/* Triangle pointer */}
            <div style={{ position: 'absolute', bottom: -9, right: 17, width: 0, height: 0, borderLeft: '9px solid transparent', borderRight: '9px solid transparent', borderTop: '9px solid #e2e8f0' }} />
            <div style={{ position: 'absolute', bottom: -7, right: 18, width: 0, height: 0, borderLeft: '8px solid transparent', borderRight: '8px solid transparent', borderTop: '8px solid #fff' }} />

            {/* Header */}
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', marginBottom: 12 }}>
              <span style={{ fontSize: 26, lineHeight: 1 }}>🤖</span>
              <div>
                <div style={{ fontWeight: 700, color: '#1a237e', fontSize: 13, lineHeight: 1.2 }}>{g.titulo}</div>
                <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 3, lineHeight: 1.4 }}>{g.desc}</div>
              </div>
            </div>

            {/* Divider */}
            <div style={{ height: 1, background: '#f1f5f9', marginBottom: 10 }} />

            {/* Bullets */}
            <ul style={{ margin: '0 0 12px', padding: 0, listStyle: 'none' }}>
              {g.puntos.map((p, i) => (
                <li key={i} style={{ display: 'flex', gap: 7, alignItems: 'flex-start', marginBottom: 6, fontSize: 12, color: '#374151', lineHeight: 1.4 }}>
                  <span style={{ color: '#166534', fontWeight: 700, flexShrink: 0, marginTop: 1 }}>✓</span>
                  {p}
                </li>
              ))}
            </ul>

            {/* Tip */}
            <div style={{ background: '#fefce8', border: '1px solid #fde68a', borderRadius: 8, padding: '8px 11px', fontSize: 11, color: '#713f12', lineHeight: 1.45 }}>
              <span style={{ fontWeight: 700 }}>💡 Tip: </span>{g.tip}
            </div>
          </div>
        )}

        {/* Floating button */}
        <button
          onClick={() => setOpen(o => !o)}
          title={open ? 'Cerrar guía' : `Guía: ${g.titulo}`}
          style={{
            width: 50, height: 50, borderRadius: '50%',
            background: open ? '#1a237e' : 'linear-gradient(135deg, #1a237e 0%, #0e7490 100%)',
            border: '2px solid rgba(255,255,255,0.25)',
            cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22, transition: 'transform 0.18s, background 0.18s',
            transform: open ? 'scale(1.08) rotate(10deg)' : 'scale(1)',
            animation: open ? 'none' : 'guiaPulse 2.8s ease-in-out infinite',
          }}
        >
          {open ? '✕' : '🤖'}
        </button>
      </div>
    </>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Home() {
  const { data: session } = useSession()
  const roles = session?.roles ?? []
  const modules = visibleModules(roles)

  const [currentModule, setCurrentModule] = useState(null)
  const [tab, setTab] = useState(null)
  const [sku, setSku] = useState(null)


  const [predictions, setPredictions] = useState(null)
  const [metadata, setMetadata] = useState({})
  const [pareto, setPareto] = useState([])
  const [canal, setCanal] = useState([])
  const [bodega, setBodega] = useState([])
  const [semanal, setSemanal] = useState([])
  const [eficiencia, setEficiencia] = useState([])

  const [historical, setHistorical] = useState([])
  const [gap, setGap] = useState([])
  const [resumenProductos, setResumenProductos] = useState([])
  const [canalClientes, setCanalClientes] = useState({ canal_por_producto: [], top_clientes: [] })
  const [modeloComparativa, setModeloComparativa] = useState([])

  const [loading, setLoading] = useState(true)
  const [hasData, setHasData] = useState(null)
  const [error, setError] = useState(null)
  const [pipeline, setPipeline] = useState({ status: 'idle' })

  const [produccion, setProduccion] = useState(null)
  const [safetyWeeks, setSafetyWeeks] = useState(2)
  const [planchaConfig, setPlanchaConfig] = useState(PLANCHA_CONFIG_DEFAULT)
  const [backtest, setBacktest] = useState(null)

  const updatePrecios = async (newPrecios) => {
    const newConfig = { ...planchaConfig, precios: newPrecios }
    setPlanchaConfig(newConfig)
    fetch('/api/plancha-config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newConfig),
    }).catch(() => {})
  }

  const selectModule = (mod) => {
    setCurrentModule(mod)
    setTab(mod.tabs[0].id)
  }

  const loadAllData = async () => {
    try {
      const predRes = await fetch('/api/predictions')
      const pred = predRes.ok ? await predRes.json() : {}
      if (!pred || Object.keys(pred).length === 0) {
        setHasData(false)
        setLoading(false)
        return
      }
      setHasData(true)
      const [meta, par, can, bod, sem, efic, bt, rp, cc, mc] = await Promise.all([
        fetch('/api/metadata').then(r => r.json()),
        fetch('/api/pareto').then(r => r.json()),
        fetch('/api/canal').then(r => r.json()),
        fetch('/api/bodega').then(r => r.json()),
        fetch('/api/semanal').then(r => r.json()),
        fetch('/api/eficiencia').then(r => r.json()),
        fetch('/api/backtest').then(r => r.json()),
        fetch('/api/analisis/resumen-productos').then(r => r.json()).catch(() => []),
        fetch('/api/analisis/canal-clientes').then(r => r.json()).catch(() => ({})),
        fetch('/api/analisis/modelo-comparativa').then(r => r.json()).catch(() => []),
      ])
      setPredictions(pred)
      setMetadata(meta || {})
      setPareto(Array.isArray(par) ? par : [])
      setCanal(Array.isArray(can) ? can : [])
      setBodega(Array.isArray(bod) ? bod : [])
      setSemanal(Array.isArray(sem) ? sem : [])
      setEficiencia(Array.isArray(efic) ? efic : [])
      setBacktest(bt?.skus ? bt : null)
      setResumenProductos(Array.isArray(rp) ? rp : [])
      setCanalClientes(cc?.canal_por_producto ? cc : { canal_por_producto: [], top_clientes: [] })
      setModeloComparativa(Array.isArray(mc) ? mc : [])
      const skus = Object.keys(pred)
      if (skus.length) setSku(s => s || skus[0])
      setLoading(false)
    } catch (err) {
      setError(String(err))
      setLoading(false)
    }
  }

  useEffect(() => { loadAllData() }, [])

  useEffect(() => {
    const t = setTimeout(() => {
      fetch(`/api/produccion?safety_weeks=${safetyWeeks}`)
        .then(r => r.json())
        .then(d => setProduccion(d))
        .catch(() => {})
    }, 400)
    return () => clearTimeout(t)
  }, [safetyWeeks])

  useEffect(() => {
    if (pipeline.status !== 'running') return
    const id = setInterval(() => {
      fetch('/api/pipeline').then(r => r.json()).then(d => {
        setPipeline(d)
        if (d.status === 'done' || d.status === 'error') {
          clearInterval(id)
          if (d.status === 'done') {
            loadAllData()
            fetch(`/api/produccion?safety_weeks=${safetyWeeks}`)
              .then(r => r.json())
              .then(setProduccion)
              .catch(() => {})
          }
        }
      })
    }, 5000)
    return () => clearInterval(id)
  }, [pipeline.status])

  useEffect(() => {
    if (!sku) return
    Promise.all([
      fetch(`/api/historical/${sku}`).then(r => r.json()),
      fetch(`/api/gap/${sku}`).then(r => r.json()),
    ]).then(([hist, gapData]) => {
      setHistorical(Array.isArray(hist) ? hist : [])
      setGap(Array.isArray(gapData) ? gapData : [])
    }).catch(() => {})
  }, [sku])

  useEffect(() => {
    if (modules.length === 1 && !currentModule) selectModule(modules[0])
  }, [modules.length]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    fetch('/api/plancha-config')
      .then(r => r.json())
      .then(cfg => setPlanchaConfig(cfg))
      .catch(() => {})
  }, [])

  if (loading) return (
    <main style={{ fontFamily: 'Segoe UI, Arial, sans-serif', padding: 60, textAlign: 'center', color: '#555' }}>
      <div style={{ fontSize: 32, marginBottom: 12 }}>📊</div>
      <div style={{ fontSize: 18, fontWeight: 600, color: BLUE }}>Cargando datos del sistema...</div>
    </main>
  )

  if (error) return (
    <main style={{ fontFamily: 'Segoe UI, Arial, sans-serif', padding: 40, color: RED }}>
      <strong>Error al cargar datos:</strong> {error}
    </main>
  )

  if (hasData === false) {
    const produccionMod = MODULES.find(m => m.id === 'produccion')
    const goToIngesta = () => {
      if (produccionMod) { selectModule(produccionMod); setTab('ingesta') }
      setHasData(null); setLoading(true); loadAllData()
    }
    return (
      <main style={{ fontFamily: 'Segoe UI, Arial, sans-serif', padding: '24px 32px' }}>
        <header style={{ borderBottom: `3px solid ${BLUE}`, paddingBottom: 16, marginBottom: 40 }}>
          <h1 style={{ color: BLUE, margin: 0, fontSize: 28, fontWeight: 800, letterSpacing: 1 }}>PREDICAST</h1>
        </header>
        <div style={{ textAlign: 'center', padding: '60px 20px' }}>
          <div style={{ fontSize: 56, marginBottom: 20 }}>📂</div>
          <h2 style={{ color: BLUE, fontSize: 22, fontWeight: 700, marginBottom: 12 }}>Sin datos cargados</h2>
          <p style={{ color: '#475569', fontSize: 15, maxWidth: 480, margin: '0 auto 32px', lineHeight: 1.7 }}>
            El sistema no encontró datos de predicciones. Para comenzar, sube tu archivo
            de movimientos y ejecuta el pipeline desde la pestaña <strong>Actualización de Datos</strong>.
          </p>
          <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: '20px 28px', maxWidth: 420, margin: '0 auto 32px', textAlign: 'left', fontSize: 14, color: '#334155' }}>
            <div style={{ fontWeight: 700, marginBottom: 10, color: BLUE }}>Pasos para comenzar:</div>
            <ol style={{ margin: 0, paddingLeft: 20, lineHeight: 2 }}>
              <li>Sube tu archivo <code style={{ background: '#e2e8f0', padding: '1px 6px', borderRadius: 4 }}>Movimientos_MayorAuxiliar_YYYY.csv</code></li>
              <li>Haz clic en <strong>Ejecutar pipeline</strong></li>
              <li>Espera ~10 min a que termine</li>
              <li>El dashboard se cargará automáticamente</li>
            </ol>
          </div>
          <button
            onClick={goToIngesta}
            style={{ background: BLUE, color: '#fff', border: 'none', borderRadius: 8, padding: '12px 32px', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}
          >
            Ir a Actualización de Datos
          </button>
        </div>
      </main>
    )
  }

  const skus = Object.keys(predictions || {})
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Buenos días' : hour < 18 ? 'Buenas tardes' : 'Buenas noches'
  const firstName = (session?.user?.name || '').split(' ')[0] || 'Usuario'

  return (
    <main style={{ fontFamily: 'Segoe UI, Arial, sans-serif', padding: '24px 32px' }}>
      <header style={{ borderBottom: `3px solid ${BLUE}`, paddingBottom: 16, marginBottom: 8 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
            <h1 style={{ color: BLUE, margin: 0, fontSize: 28, fontWeight: 800, letterSpacing: 1 }}>PREDICAST</h1>
            <span style={{ color: '#64748b', fontSize: 13 }}>Sistema de Planificación Inteligente de Demanda</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {pipeline.status === 'running' && (
              <span style={{ fontSize: 12, color: ORANGE, fontWeight: 600 }}>⏳ Ejecutando pipeline...</span>
            )}
            {pipeline.status === 'done' && (
              <span style={{ fontSize: 12, color: GREEN, fontWeight: 600 }}>✓ Pipeline completado</span>
            )}
            {pipeline.status === 'error' && (
              <span style={{ fontSize: 12, color: RED, fontWeight: 600 }}>✗ Error en pipeline</span>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, borderLeft: '1px solid #e2e8f0', paddingLeft: 12 }}>
              {session?.user?.image && (
                <img
                  src={session.user.image}
                  alt=""
                  style={{ width: 28, height: 28, borderRadius: '50%', objectFit: 'cover' }}
                />
              )}
              <span style={{ fontSize: 13, color: '#374151', fontWeight: 500 }}>
                {session?.user?.name || session?.user?.email || 'Usuario'}
              </span>
              <button
                onClick={async () => {
                  await signOut({ redirect: false })
                  window.location.href = '/api/logout'
                }}
                style={{
                  padding: '5px 12px', borderRadius: 6, border: '1px solid #e2e8f0',
                  background: 'white', color: '#64748b',
                  cursor: 'pointer', fontSize: 12, fontWeight: 500,
                }}
              >
                Cerrar sesión
              </button>
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginTop: 10, flexWrap: 'wrap' }}>
          {[
            { icon: '📦', label: `${skus.length} SKUs activos` },
            { icon: '📅', label: '52 sem. de horizonte' },
            { icon: '✅', label: `${(skus.length * 52).toLocaleString('es-PE')} predicciones` },
          ].map(b => (
            <span key={b.label} style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              background: '#f1f5f9', border: '1px solid #e2e8f0',
              borderRadius: 20, padding: '3px 12px',
              fontSize: 12, color: '#475569', fontWeight: 500,
            }}>
              {b.icon} {b.label}
            </span>
          ))}
        </div>
      </header>

      {modules.length > 1 && currentModule && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 16, marginBottom: 4, fontSize: 13 }}>
          <button
            onClick={() => { setCurrentModule(null); setTab(null) }}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b', padding: '4px 0', fontWeight: 500 }}
          >
            ← Módulos
          </button>
          <span style={{ color: '#cbd5e1' }}>/</span>
          <span style={{ color: currentModule.color, fontWeight: 600 }}>
            {currentModule.icon} {currentModule.label}
          </span>
        </div>
      )}

      {!currentModule ? (
        <>
          <div style={{ marginTop: 28, marginBottom: 4 }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 700, color: '#1e293b' }}>
              {greeting}, {firstName}
            </h2>

          </div>

          <ModuleSelector modules={modules} onSelect={selectModule} />
        </>
      ) : (
        <>
          <div style={{ marginTop: 20 }}>
            <TabNav active={tab} onChange={setTab} tabs={currentModule.tabs} color={currentModule.accent} />
          </div>

          {tab === 'resumen' && (
            <TabResumen pareto={pareto} semanal={semanal} canal={canal} />
          )}
          {tab === 'producto' && (
            <TabProducto
              sku={sku} setSku={setSku}
              historical={historical} pareto={pareto}
              gap={gap} eficiencia={eficiencia} predictions={predictions}
            />
          )}
          {tab === 'analisis_productos' && (
            <TabAnalisisProductos resumenProductos={resumenProductos} pareto={pareto} />
          )}
          {tab === 'canal_mercado' && (
            <TabCanalMercado canalClientes={canalClientes} bodega={bodega} pareto={pareto} />
          )}
          {tab === 'modelo_comparativa' && (
            <TabModeloComparativa modeloComparativa={modeloComparativa} />
          )}
          {tab === 'costo_planchas' && (
            <TabCostoPlanchas
              produccion={produccion}
              safetyWeeks={safetyWeeks}
              setSafetyWeeks={setSafetyWeeks}
              precios={planchaConfig.precios}
              setPrecios={updatePrecios}
              skuPlancha={planchaConfig.skus}
            />
          )}
          {tab === 'analisis_financiero' && (
            <TabAnalisisFinanciero
              eficiencia={eficiencia}
              precios={planchaConfig.precios}
              skuPlancha={planchaConfig.skus}
            />
          )}
          {tab === 'backtest_predicast' && (
            <TabSimulacionPredicast
              backtest={backtest}
              safetyWeeks={safetyWeeks}
              setSafetyWeeks={setSafetyWeeks}
              precios={planchaConfig.precios}
              skuPlancha={planchaConfig.skus}
            />
          )}
          {tab === 'produccion' && (
            <TabProduccion
              produccion={produccion}
              safetyWeeks={safetyWeeks}
              setSafetyWeeks={setSafetyWeeks}
            />
          )}
          {tab === 'asignacion' && (
            <TabAsignacionSeguimiento produccion={produccion} />
          )}
          {tab === 'ingesta' && (
            <TabIngestaReentrenamiento pipeline={pipeline} setPipeline={setPipeline} />
          )}
          {tab === 'admin' && <TabAdmin />}
        </>
      )}
      {tab && <GuiaWidget tab={tab} />}
    </main>
  )
}

export async function getServerSideProps(context) {
  const session = await getServerSession(context.req, context.res, authOptions)
  if (!session) {
    return { redirect: { destination: '/auth/login', permanent: false } }
  }
  return { props: { session } }
}
