import { useState } from 'react'
import {
  ComposedChart, Area, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const PRODUCTOS = ['CEO001', 'CEO006', 'CER001', 'CER004', 'CER005', 'CER008', 'CERE002']

const th = { padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid #ddd' }
const td = { padding: '6px 12px', borderBottom: '1px solid #eee' }

function StatCard({ label, value }) {
  return (
    <div style={{ background: '#f0f4ff', padding: '10px 18px', borderRadius: 6, minWidth: 140 }}>
      <div style={{ fontSize: 11, color: '#666', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: '#1a237e' }}>{value}</div>
    </div>
  )
}

export default function Home() {
  const [productId, setProductId] = useState('CER001')
  const [periods, setPeriods] = useState(52)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function fetchForecast() {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await fetch('/api/v1/forecast/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, periods }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
      setResult(await res.json())
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const chartData = result?.forecasts?.map(p => ({
    semana: `S${p.period}`,
    forecast: Math.round(p.forecast * 100) / 100,
    lower: p.confidence_interval ? Math.round(p.confidence_interval.lower * 100) / 100 : undefined,
    upper: p.confidence_interval ? Math.round(p.confidence_interval.upper * 100) / 100 : undefined,
  })) ?? []

  return (
    <main style={{ padding: 24, fontFamily: 'Arial, sans-serif', maxWidth: 1100, margin: '0 auto' }}>
      <h1 style={{ color: '#1a237e', marginBottom: 4 }}>Predicast</h1>
      <p style={{ color: '#555', marginBottom: 20 }}>
        Sistema de predicción de demanda — horizonte 52 semanas
      </p>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 16, marginBottom: 24, alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 600, fontSize: 13 }}>
            Producto (SKU)
          </label>
          <select
            value={productId}
            onChange={e => setProductId(e.target.value)}
            style={{ padding: '7px 12px', fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }}
          >
            {PRODUCTOS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: 4, fontWeight: 600, fontSize: 13 }}>
            Semanas a predecir
          </label>
          <input
            type="number" value={periods} min={1} max={52}
            onChange={e => setPeriods(Number(e.target.value))}
            style={{ padding: '7px 10px', width: 80, fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }}
          />
        </div>

        <button
          onClick={fetchForecast}
          disabled={loading}
          style={{
            padding: '8px 22px', background: loading ? '#9fa8da' : '#1a237e',
            color: 'white', border: 'none', borderRadius: 4,
            cursor: loading ? 'not-allowed' : 'pointer', fontSize: 14, fontWeight: 600,
          }}
        >
          {loading ? 'Calculando...' : 'Generar predicción'}
        </button>
      </div>

      {error && (
        <div style={{ background: '#ffebee', border: '1px solid #ef9a9a', borderRadius: 4, padding: 12, marginBottom: 16, color: '#c62828' }}>
          {error}
        </div>
      )}

      {result && (
        <>
          {/* Metadata cards */}
          <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
            <StatCard label="Producto" value={result.product_id} />
            <StatCard label="Precisión del modelo" value={`${(result.model_accuracy * 100).toFixed(1)}%`} />
            <StatCard label="Versión del modelo" value={result.model_version} />
            <StatCard label="Semanas predichas" value={result.forecasts.length} />
            <StatCard label="Desde caché" value={result.cache_hit ? 'Sí' : 'No'} />
          </div>

          {/* Chart */}
          <h2 style={{ color: '#1a237e', marginBottom: 8 }}>
            Predicción de demanda — {result.product_id} ({periods} semanas)
          </h2>
          <div style={{ background: 'white', border: '1px solid #e0e0e0', borderRadius: 8, padding: '16px 8px 8px' }}>
            <ResponsiveContainer width="100%" height={320}>
              <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="semana"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v, i) => i % 4 === 0 ? v : ''}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip
                  formatter={(value, name) => [value, name === 'forecast' ? 'Predicción' : name]}
                />
                <Legend
                  formatter={v => v === 'forecast' ? 'Predicción' : v === 'upper' ? 'Banda confianza' : ''}
                />
                {/* Confidence band */}
                <Area
                  dataKey="upper" name="upper" stroke="none"
                  fill="#90caf9" fillOpacity={0.35} dot={false} legendType="square"
                />
                <Area
                  dataKey="lower" name="lower" stroke="none"
                  fill="white" fillOpacity={1} dot={false} legendType="none"
                />
                {/* Forecast line */}
                <Line
                  dataKey="forecast" name="forecast" stroke="#1a237e"
                  strokeWidth={2} dot={false} activeDot={{ r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Table */}
          <h2 style={{ color: '#1a237e', marginTop: 28, marginBottom: 8 }}>Detalle semanal</h2>
          <div style={{ overflowX: 'auto', border: '1px solid #e0e0e0', borderRadius: 8 }}>
            <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 13 }}>
              <thead>
                <tr style={{ background: '#1a237e', color: 'white' }}>
                  <th style={th}>Semana</th>
                  <th style={th}>Predicción</th>
                  <th style={th}>Límite inferior (95%)</th>
                  <th style={th}>Límite superior (95%)</th>
                </tr>
              </thead>
              <tbody>
                {chartData.map((row, i) => (
                  <tr key={i} style={{ background: i % 2 === 0 ? '#fafafa' : 'white' }}>
                    <td style={td}>{row.semana}</td>
                    <td style={{ ...td, fontWeight: 600 }}>{row.forecast}</td>
                    <td style={td}>{row.lower ?? '—'}</td>
                    <td style={td}>{row.upper ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  )
}
