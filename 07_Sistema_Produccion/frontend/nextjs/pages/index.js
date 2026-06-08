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

const TABS = [
  { id: 'resumen',       label: 'Resumen Ejecutivo' },
  { id: 'producto',      label: 'Por Producto' },
  { id: 'planificacion', label: 'Planificación / GAP' },
  { id: 'exploracion',   label: 'Exploración de Datos' },
  { id: 'produccion',    label: 'Plan de Producción' },
]

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

function Badge({ label, value, color = BLUE }) {
  return (
    <div style={{ background: '#fff', border: `1px solid ${color}`, borderRadius: 8, padding: '10px 16px', textAlign: 'center', minWidth: 120 }}>
      <div style={{ fontSize: 10, color: '#888', marginBottom: 3, textTransform: 'uppercase', letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color }}>{value}</div>
    </div>
  )
}

function SectionTitle({ children, sub }) {
  return (
    <div style={{ marginBottom: 12, marginTop: 24 }}>
      <h2 style={{ color: BLUE, margin: 0, fontSize: 17, fontWeight: 700 }}>{children}</h2>
      {sub && <p style={{ color: '#666', margin: '4px 0 0', fontSize: 13 }}>{sub}</p>}
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

function TabResumen({ predictions, metadata, pareto, semanal, canal }) {
  const skus = Object.keys(predictions || {})
  const totalForecast = skus.reduce((s, k) => s + (predictions[k] || []).reduce((a, r) => a + r.forecast, 0), 0)
  const avgR2 = metadata && skus.length
    ? skus.reduce((s, k) => s + (metadata[k]?.r2 || 0), 0) / skus.length
    : 0

  const skuTotals = skus.map((k, i) => ({
    sku: k,
    total: Math.round((predictions[k] || []).reduce((a, r) => a + r.forecast, 0)),
    fill: SKU_COLORS[i % SKU_COLORS.length],
  })).sort((a, b) => b.total - a.total)

  const semanalSlice = semanal.slice(-104)

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <StatCard label="SKUs monitoreados" value={skus.length} sub="Productos activos" color={BLUE} />
        <StatCard label="Demanda total 52s" value={fmt(totalForecast)} sub="Todas las referencias" color={GREEN} />
        <StatCard label="R² promedio modelos" value={`${fmtDec(avgR2 * 100)}%`} sub="Precisión del sistema" color={PURPLE} />
        <StatCard label="Predicciones generadas" value={fmt(skus.length * 52)} sub="Puntos de forecast" color={ORANGE} />
      </div>

      <SectionTitle sub="Últimas 2 años — ventas y producción global consolidadas">
        Serie histórica global
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={semanalSlice} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="semana" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % 12 === 0 ? v : ''} />
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
          <SectionTitle sub="Demanda proyectada total 52 semanas por referencia">
            Forecast por SKU
          </SectionTitle>
          <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart layout="vertical" data={skuTotals} margin={{ left: 10, right: 30 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={fmt} />
                <YAxis type="category" dataKey="sku" width={70} tick={{ fontSize: 12, fontWeight: 600 }} />
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <Tooltip formatter={v => [fmt(v), 'Demanda proyectada']} />
                <Bar dataKey="total" name="Demanda 52s" radius={[0, 4, 4, 0]}>
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

      <SectionTitle sub="Análisis de Pareto — volumen de ventas históricas por referencia">
        Ventas históricas por producto
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={pareto.slice(0, 7)} margin={{ left: 10, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="codigo" tick={{ fontSize: 12, fontWeight: 600 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), n === 'ventas' ? 'Ventas históricas' : n]} labelFormatter={label => {
              const p = pareto.find(r => r.codigo === label)
              return p ? `${label} — ${p.descripcion.slice(0, 40)}` : label
            }} />
            <Bar dataKey="ventas" name="ventas" radius={[4, 4, 0, 0]}>
              {pareto.slice(0, 7).map((_, i) => <Cell key={i} fill={SKU_COLORS[i % SKU_COLORS.length]} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

// ─── Tab: Por Producto ────────────────────────────────────────────────────────

function TabProducto({ sku, setSku, predictions, metadata, historical, pareto, periods, setPeriods }) {
  const skus = Object.keys(predictions || {})
  const forecastData = (predictions?.[sku] || []).slice(0, periods)
  const histSlice = historical.slice(-52)
  const model = metadata?.[sku]

  const chartData = [
    ...histSlice.map(h => ({ label: h.semana, ventas: h.ventas, type: 'hist' })),
    ...forecastData.map(f => ({ label: f.semana, forecast: f.forecast, lower: f.lower || 0, upper: f.upper, type: 'fc' })),
  ]

  const stockData = histSlice.map(h => ({ label: h.semana, stock: h.stock, produccion: h.produccion }))

  const totalFc = forecastData.reduce((s, r) => s + r.forecast, 0)
  const avgFc = forecastData.length ? totalFc / forecastData.length : 0
  const maxFc = forecastData.length ? Math.max(...forecastData.map(r => r.forecast)) : 0
  const avgHist = histSlice.length ? histSlice.reduce((s, h) => s + h.ventas, 0) / histSlice.length : 0
  const trendUp = avgFc > avgHist * 1.1
  const trendDown = avgFc < avgHist * 0.9

  const lastStock = histSlice.length ? histSlice[histSlice.length - 1].stock : 0
  const stockLow = lastStock < avgFc * 2

  const descMap = useMemo(() => {
    const m = {}
    pareto.forEach(r => { m[r.codigo] = r.descripcion })
    return m
  }, [pareto])

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 20 }}>
        <div>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 4 }}>PRODUCTO (SKU)</label>
          <SkuSelect skus={skus} value={sku} onChange={setSku} pareto={pareto} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 4 }}>
            SEMANAS A MOSTRAR: <strong>{periods}</strong>
          </label>
          <input type="range" value={periods} min={4} max={52} step={4} onChange={e => setPeriods(+e.target.value)}
            style={{ width: 140, cursor: 'pointer' }} />
        </div>
      </div>

      {descMap[sku] && (
        <p style={{ color: '#555', fontSize: 13, marginBottom: 12, fontStyle: 'italic' }}>{descMap[sku]}</p>
      )}

      {model && (
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 20 }}>
          <Badge label="Algoritmo" value={model.algoritmo} color={BLUE} />
          <Badge label="R² Score" value={fmtDec(model.r2, 4)} color={model.r2 > 0.95 ? GREEN : ORANGE} />
          <Badge label="MAE" value={`${fmt(model.mae)} u`} color={BLUE_LIGHT} />
          <Badge label="RMSE" value={`${fmt(model.rmse)} u`} color={PURPLE} />
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <StatCard label="Demanda total proyectada" value={fmt(totalFc)} color={BLUE} />
        <StatCard label="Promedio semanal (fc)" value={fmt(avgFc)} color={BLUE_LIGHT} />
        <StatCard label="Pico de demanda" value={fmt(maxFc)} color={ORANGE} />
        <StatCard label="Stock actual" value={fmt(lastStock)} color={stockLow ? RED : GREEN} sub={stockLow ? 'Nivel bajo' : 'Nivel OK'} />
      </div>

      {trendUp && <Alert type="warning">La demanda proyectada supera el promedio histórico en más del 10% — considerar incrementar producción.</Alert>}
      {trendDown && <Alert type="info">La demanda proyectada está por debajo del histórico — oportunidad de optimizar inventario.</Alert>}
      {stockLow && <Alert type="danger">Stock actual ({fmt(lastStock)} u) es menor a 2 semanas de demanda promedio proyectada — revisar plan de producción urgente.</Alert>}
      {model?.r2 >= 0.95 && <Alert type="success">Modelo {model.algoritmo} con R²={fmtDec(model.r2, 4)} — alta confianza en las predicciones.</Alert>}

      <SectionTitle sub="Últimas 52 semanas históricas + forecast con banda de confianza al 95%">
        Demanda histórica + predicción — {sku}
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 16 }}>
        <ResponsiveContainer width="100%" height={320}>
          <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % 8 === 0 ? v : ''} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), { forecast: 'Predicción', ventas: 'Ventas reales', upper: 'Límite sup. 95%', lower: 'Límite inf. 95%' }[n] ?? n]} />
            <Legend formatter={v => ({ forecast: 'Predicción', ventas: 'Ventas reales', upper: 'Banda confianza', lower: '' }[v] ?? v)} />
            <Area dataKey="upper" name="upper" stroke="none" fill={BLUE_LIGHT} fillOpacity={0.25} dot={false} legendType="square" />
            <Area dataKey="lower" name="lower" stroke="none" fill="white" fillOpacity={1} dot={false} legendType="none" />
            <Line dataKey="ventas" name="ventas" stroke={GREEN} strokeWidth={1.5} dot={false} connectNulls={false} />
            <Line dataKey="forecast" name="forecast" stroke={BLUE} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <SectionTitle sub="Evolución del stock e ingresos por producción en el periodo histórico">
        Stock e ingresos por producción — {sku}
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={200}>
          <ComposedChart data={stockData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % 8 === 0 ? v : ''} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), n === 'stock' ? 'Stock cierre' : 'Producción ingresada']} />
            <Legend formatter={v => ({ stock: 'Stock cierre', produccion: 'Producción ingresada' }[v] ?? v)} />
            <Area dataKey="stock" name="stock" stroke={TEAL} fill={TEAL} fillOpacity={0.2} dot={false} />
            <Line dataKey="produccion" name="produccion" stroke={ORANGE} strokeWidth={1.5} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <SectionTitle>Detalle semanal de predicción — {sku}</SectionTitle>
      <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 8 }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
          <thead>
            <tr style={{ background: BLUE }}>
              {['Semana', 'Predicción (u)', 'Límite inferior 95%', 'Límite superior 95%'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: 'white', fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {forecastData.map((row, i) => (
              <tr key={i} style={{ background: i % 2 === 0 ? '#fafafa' : 'white' }}>
                <td style={{ padding: '6px 12px', borderBottom: '1px solid #eee' }}>{row.semana}</td>
                <td style={{ padding: '6px 12px', borderBottom: '1px solid #eee', fontWeight: 600 }}>{fmt(row.forecast)}</td>
                <td style={{ padding: '6px 12px', borderBottom: '1px solid #eee', color: '#666' }}>{row.lower > 0 ? fmt(row.lower) : '—'}</td>
                <td style={{ padding: '6px 12px', borderBottom: '1px solid #eee', color: '#666' }}>{fmt(row.upper)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Tab: Planificación / GAP ─────────────────────────────────────────────────

function TabPlanificacion({ sku, setSku, gap, eficiencia, predictions, pareto }) {
  const skus = Object.keys(predictions || {})
  const skuEfic = eficiencia.find(r => r.codigo === sku) || null
  const gapSlice = gap.slice(-78)
  const forecastData = predictions?.[sku] || []

  const avgDemanda = forecastData.length ? forecastData.reduce((s, r) => s + r.forecast, 0) / forecastData.length : 0
  const avgProd = gapSlice.length ? gapSlice.reduce((s, r) => s + r.produccion, 0) / gapSlice.length : 0
  const gapRatio = avgProd > 0 ? (avgDemanda / avgProd) * 100 : 0

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#555', marginBottom: 4 }}>PRODUCTO (SKU)</label>
        <SkuSelect skus={skus} value={sku} onChange={setSku} pareto={pareto} />
      </div>

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

      <SectionTitle sub="Comparación semanal ventas vs producción real (últimas 78 semanas)">
        Ventas vs Producción — {sku}
      </SectionTitle>
      <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 20 }}>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={gapSlice} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="semana" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % 8 === 0 ? v : ''} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
            <Tooltip formatter={(v, n) => [fmt(v), { ventas: 'Ventas', produccion: 'Producción' }[n] ?? n]} />
            <Legend formatter={v => ({ ventas: 'Ventas reales', produccion: 'Producción ingresada' }[v] ?? v)} />
            <Area dataKey="produccion" name="produccion" stroke={ORANGE} fill={ORANGE} fillOpacity={0.15} dot={false} />
            <Line dataKey="ventas" name="ventas" stroke={GREEN} strokeWidth={2} dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 20 }}>
        <StatCard label="Demanda media proyectada/semana" value={fmt(avgDemanda)} color={BLUE} />
        <StatCard label="Producción media histórica/semana" value={fmt(avgProd)} color={ORANGE} />
        <StatCard label="Cobertura de demanda" value={`${fmtDec(gapRatio)}%`} color={gapRatio >= 100 ? GREEN : RED} sub={gapRatio >= 100 ? 'Producción suficiente' : 'Producción insuficiente'} />
      </div>

      <SectionTitle sub="Comparativa de eficiencia y costos para todos los SKUs monitoreados">
        Eficiencia global por producto
      </SectionTitle>
      <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 8 }}>
        <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
          <thead>
            <tr style={{ background: BLUE }}>
              {['SKU', 'Producción total', 'Ventas total', 'GAP planchas', 'Eficiencia', 'Ahorro S/'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', color: 'white', fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {eficiencia.map((r, i) => (
              <tr key={i} style={{ background: r.codigo === sku ? '#eff6ff' : i % 2 === 0 ? '#fafafa' : 'white' }}>
                <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee', fontWeight: r.codigo === sku ? 700 : 400 }}>{r.codigo}</td>
                <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee' }}>{fmt(r.produccion_total)}</td>
                <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee' }}>{fmt(r.ventas_total)}</td>
                <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee' }}>{fmtDec(r.planchas_gap)}</td>
                <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee', color: r.eficiencia >= 98 ? GREEN : ORANGE, fontWeight: 600 }}>
                  {fmtDec(r.eficiencia)}%
                </td>
                <td style={{ padding: '7px 12px', borderBottom: '1px solid #eee' }}>S/ {fmt(r.ahorro)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ─── Tab: Exploración de Datos ────────────────────────────────────────────────

function TabExploracion({ tendencia, bodega, canal }) {
  const anios = [...new Set(tendencia.map(r => r.anio))].sort()
  const [anioSel, setAnioSel] = useState(null)
  const anioFinal = anioSel || anios[anios.length - 1]
  const tendFiltrada = anio => tendencia.filter(r => r.anio === anio)
  const tendGlobal = tendencia.slice(-60)

  return (
    <div>
      <SectionTitle sub="Evolución mensual de ventas totales de la empresa — últimos 5 años">
        Tendencia mensual de ventas
      </SectionTitle>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
        {anios.map(a => (
          <button key={a} onClick={() => setAnioSel(a === anioFinal && anioSel ? null : a)}
            style={{
              padding: '5px 14px', borderRadius: 20, border: `1px solid ${BLUE}`,
              background: anioFinal === a ? BLUE : 'white',
              color: anioFinal === a ? 'white' : BLUE,
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
            }}>
            {a}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <div style={{ flex: 2, minWidth: 300 }}>
          <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#555', marginBottom: 8, paddingLeft: 8 }}>
              Ventas mensuales — {anioFinal}
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={tendFiltrada(anioFinal)} margin={{ left: 10, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="mes" tickFormatter={m => ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][m] || m} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
                <Tooltip formatter={(v, n) => [fmt(v), n === 'ventas' ? 'Salida total' : 'Transacciones']} labelFormatter={m => ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'][m] || m} />
                <Bar dataKey="ventas" name="ventas" fill={BLUE} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#555', marginBottom: 8, paddingLeft: 8 }}>
              Tendencia histórica completa
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <ComposedChart data={tendGlobal} margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} tickFormatter={(v, i) => i % 6 === 0 ? v : ''} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={fmt} />
                <Tooltip formatter={(v, n) => [fmt(v), n === 'ventas' ? 'Salida total' : 'Transacciones']} />
                <Area dataKey="ventas" name="ventas" stroke={BLUE} fill={BLUE} fillOpacity={0.15} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 220 }}>
          <SectionTitle sub="Distribución de ventas por canal">Canal de ventas</SectionTitle>
          <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px', marginBottom: 16 }}>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={canal} dataKey="ventas" nameKey="canal" cx="50%" cy="50%" outerRadius={75}
                  label={({ canal: c, percent }) => `${c}: ${(percent * 100).toFixed(0)}%`}>
                  {canal.map((_, i) => <Cell key={i} fill={[BLUE, GREEN][i % 2]} />)}
                </Pie>
                <Tooltip formatter={v => [fmt(v), 'Ventas']} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <SectionTitle sub="Ventas por almacén / punto de venta">Ventas por bodega</SectionTitle>
          <div style={{ background: '#fff', border: '1px solid #e0e0e0', borderRadius: 8, padding: '12px 8px' }}>
            <ResponsiveContainer width="100%" height={160}>
              <BarChart layout="vertical" data={bodega} margin={{ left: 10, right: 20 }}>
                <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={fmt} />
                <YAxis type="category" dataKey="bodega" width={130} tick={{ fontSize: 10 }} tickFormatter={v => v.length > 18 ? v.slice(0, 18) + '…' : v} />
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <Tooltip formatter={v => [fmt(v), 'Ventas']} labelFormatter={v => v} />
                <Bar dataKey="ventas" name="Ventas" radius={[0, 4, 4, 0]}>
                  {bodega.map((_, i) => <Cell key={i} fill={SKU_COLORS[i % SKU_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Tab: Plan de Producción ──────────────────────────────────────────────────

function TabProduccion({ produccion, safetyWeeks, setSafetyWeeks }) {
  const [horizon, setHorizon] = useState(12)
  const [detailSku, setDetailSku] = useState(null)

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

  const activeSku = detailSku && produccion[detailSku] ? detailSku : skus[0]
  const allWeeks = produccion[skus[0]]?.calendar.slice(0, horizon).map(w => w.semana) || []

  const totalProduccion = skus.reduce((s, k) => {
    return s + produccion[k].calendar.slice(0, horizon).reduce((a, w) => a + w.produccion, 0)
  }, 0)
  const urgentSkus = skus.filter(k =>
    produccion[k].calendar.slice(0, horizon).some(w => w.urgente)
  ).length
  const skusConPlan = skus.filter(k =>
    produccion[k].calendar.slice(0, horizon).some(w => w.produccion > 0)
  ).length

  const cellColor = (w) => {
    if (w.urgente) return '#fecaca'
    if (w.produccion > 0) return '#bbf7d0'
    return '#f1f5f9'
  }

  const detailData = produccion[activeSku]?.calendar.slice(0, horizon).map(w => ({
    name: w.semana,
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
        <h3 style={{ margin: '0 0 16px', color: BLUE, fontSize: 15, fontWeight: 700 }}>
          Calendario de Producción — próximas {horizon} semanas
        </h3>
        <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 10, display: 'flex', gap: 16 }}>
          <span><span style={{ background: '#bbf7d0', padding: '1px 6px', borderRadius: 3 }}>■</span> Producir</span>
          <span><span style={{ background: '#fecaca', padding: '1px 6px', borderRadius: 3 }}>■</span> Urgente (stock bajo 0)</span>
          <span><span style={{ background: '#f1f5f9', padding: '1px 6px', borderRadius: 3 }}>■</span> Sin producción</span>
        </div>
        <table style={{ borderCollapse: 'collapse', fontSize: 11, minWidth: '100%' }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 10px', textAlign: 'left', background: '#f8fafc', borderBottom: '2px solid #e2e8f0', fontWeight: 700, color: '#374151', minWidth: 90 }}>SKU</th>
              {allWeeks.map(w => (
                <th key={w} style={{ padding: '4px 6px', textAlign: 'center', background: '#f8fafc', borderBottom: '2px solid #e2e8f0', fontWeight: 600, color: '#64748b', minWidth: 52, fontSize: 10 }}>
                  {w.replace('semana_', 'S')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {skus.map(sku => {
              const weeks = produccion[sku].calendar.slice(0, horizon)
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
          Semanas a producir: <strong>{produccion[activeSku]?.calendar.slice(0, horizon).filter(w => w.produccion > 0).length}</strong>
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <ComposedChart data={detailData} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 10 }} tickFormatter={v => v.replace('semana_', 'S')} />
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
              {['Semana', 'Fecha', 'Demanda', 'Producción', 'Stock inicio', 'Stock fin', 'Estado'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'right', fontWeight: 700, color: '#374151', borderBottom: '2px solid #e2e8f0', whiteSpace: 'nowrap' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {produccion[activeSku]?.calendar.slice(0, horizon).map((w, i) => (
              <tr key={i} style={{ background: w.urgente ? '#fff5f5' : w.produccion > 0 ? '#f0fdf4' : 'white' }}>
                <td style={{ padding: '6px 12px', textAlign: 'right', color: '#64748b', borderBottom: '1px solid #f1f5f9' }}>{w.semana}</td>
                <td style={{ padding: '6px 12px', textAlign: 'right', color: '#64748b', borderBottom: '1px solid #f1f5f9' }}>{w.fecha}</td>
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

// ─── Tab nav ──────────────────────────────────────────────────────────────────

function TabNav({ active, onChange }) {
  return (
    <div style={{ display: 'flex', borderBottom: `2px solid #e2e8f0`, marginBottom: 24, overflowX: 'auto' }}>
      {TABS.map(t => (
        <button key={t.id} onClick={() => onChange(t.id)} style={{
          padding: '10px 20px', background: 'none', border: 'none', cursor: 'pointer',
          fontWeight: 600, fontSize: 14, whiteSpace: 'nowrap',
          color: active === t.id ? BLUE : '#64748b',
          borderBottom: active === t.id ? `3px solid ${BLUE}` : '3px solid transparent',
          marginBottom: -2, transition: 'all 0.15s',
        }}>
          {t.label}
        </button>
      ))}
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

export default function Home() {
  const [tab, setTab] = useState('resumen')
  const [sku, setSku] = useState(null)
  const [periods, setPeriods] = useState(52)

  const [predictions, setPredictions] = useState(null)
  const [metadata, setMetadata] = useState({})
  const [pareto, setPareto] = useState([])
  const [tendencia, setTendencia] = useState([])
  const [canal, setCanal] = useState([])
  const [bodega, setBodega] = useState([])
  const [semanal, setSemanal] = useState([])
  const [eficiencia, setEficiencia] = useState([])

  const [historical, setHistorical] = useState([])
  const [gap, setGap] = useState([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pipeline, setPipeline] = useState({ status: 'idle' })

  const [produccion, setProduccion] = useState(null)
  const [safetyWeeks, setSafetyWeeks] = useState(2)

  const loadAllData = async () => {
    return Promise.all([
      fetch('/api/predictions').then(r => r.json()),
      fetch('/api/metadata').then(r => r.json()),
      fetch('/api/pareto').then(r => r.json()),
      fetch('/api/tendencia').then(r => r.json()),
      fetch('/api/canal').then(r => r.json()),
      fetch('/api/bodega').then(r => r.json()),
      fetch('/api/semanal').then(r => r.json()),
      fetch('/api/eficiencia').then(r => r.json()),
    ]).then(([pred, meta, par, tend, can, bod, sem, efic]) => {
      setPredictions(pred)
      setMetadata(meta || {})
      setPareto(Array.isArray(par) ? par : [])
      setTendencia(Array.isArray(tend) ? tend : [])
      setCanal(Array.isArray(can) ? can : [])
      setBodega(Array.isArray(bod) ? bod : [])
      setSemanal(Array.isArray(sem) ? sem : [])
      setEficiencia(Array.isArray(efic) ? efic : [])
      const skus = Object.keys(pred || {})
      if (skus.length) setSku(s => s || skus[0])
      setLoading(false)
    }).catch(err => { setError(String(err)); setLoading(false) })
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

  const skus = Object.keys(predictions || {})

  return (
    <main style={{ fontFamily: 'Segoe UI, Arial, sans-serif', maxWidth: 1200, margin: '0 auto', padding: '24px 20px' }}>
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
            <button
              disabled={pipeline.status === 'running'}
              onClick={() => fetch('/api/pipeline', { method: 'POST' }).then(r => r.json()).then(d => setPipeline(d.status === 'started' ? { status: 'running' } : pipeline))}
              style={{
                padding: '6px 14px', borderRadius: 6, border: `1px solid ${BLUE}`,
                background: pipeline.status === 'running' ? '#e2e8f0' : BLUE,
                color: pipeline.status === 'running' ? '#94a3b8' : 'white',
                cursor: pipeline.status === 'running' ? 'not-allowed' : 'pointer',
                fontSize: 13, fontWeight: 600,
              }}
            >
              Regenerar datos
            </button>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
          <span style={{ fontSize: 12, color: '#888' }}>📦 {skus.length} SKUs</span>
          <span style={{ fontSize: 12, color: '#888' }}>📅 52 semanas de horizonte</span>
          <span style={{ fontSize: 12, color: '#888' }}>✅ {skus.length * 52} predicciones generadas</span>
        </div>
      </header>

      <TabNav active={tab} onChange={setTab} />

      {tab === 'resumen' && (
        <TabResumen predictions={predictions} metadata={metadata} pareto={pareto} semanal={semanal} canal={canal} />
      )}
      {tab === 'producto' && (
        <TabProducto
          sku={sku} setSku={setSku}
          predictions={predictions} metadata={metadata}
          historical={historical} pareto={pareto}
          periods={periods} setPeriods={setPeriods}
        />
      )}
      {tab === 'planificacion' && (
        <TabPlanificacion
          sku={sku} setSku={setSku}
          gap={gap} eficiencia={eficiencia}
          predictions={predictions} pareto={pareto}
        />
      )}
      {tab === 'exploracion' && (
        <TabExploracion tendencia={tendencia} bodega={bodega} canal={canal} />
      )}
      {tab === 'produccion' && (
        <TabProduccion
          produccion={produccion}
          safetyWeeks={safetyWeeks}
          setSafetyWeeks={setSafetyWeeks}
        />
      )}
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
