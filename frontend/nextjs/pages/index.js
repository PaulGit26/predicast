import { useState, useEffect } from 'react'
import {
  ComposedChart, Area, Line, Bar, BarChart,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const PRODUCTOS = ['CEO001', 'CEO006', 'CER001', 'CER004', 'CER005', 'CER008', 'CERE002']
const BRAND = '#1a237e'
const BRAND_LIGHT = '#e8eaf6'
const ACCENT = '#1565c0'

function Sidebar() {
  return (
    <aside style={{
      width: 210, minHeight: '100vh', background: BRAND, color: 'white',
      padding: '20px 14px', boxSizing: 'border-box', flexShrink: 0,
    }}>
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: 1 }}>PREDICAST</div>
        <div style={{ fontSize: 11, opacity: 0.7, marginTop: 2 }}>Sistema de Predicción</div>
      </div>

      <div style={{ background: 'rgba(255,255,255,0.12)', borderRadius: 8, padding: '10px 12px', marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 700 }}>Paulcesar</div>
        <div style={{ fontSize: 11, opacity: 0.65 }}>Admin</div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 10, opacity: 0.55, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
          Configuración
        </div>
        {[
          ['Productos', '7'],
          ['Semanas', '52'],
          ['Historial', '222 sem'],
          ['Algoritmo', 'XGBoost'],
        ].map(([label, value]) => (
          <div key={label} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: 12 }}>
            <span style={{ opacity: 0.75 }}>{label}</span>
            <span style={{ fontWeight: 700 }}>{value}</span>
          </div>
        ))}
      </div>

      <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 8, padding: '10px 12px', marginBottom: 20 }}>
        <div style={{ fontSize: 10, opacity: 0.55, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
          Rendimiento del Modelo
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
          <span style={{ opacity: 0.75 }}>R²</span>
          <span style={{ fontWeight: 700, color: '#69f0ae' }}>0.9939</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 6 }}>
          <span style={{ opacity: 0.75 }}>MAE</span>
          <span style={{ fontWeight: 700 }}>17.34 u</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
          <span style={{ opacity: 0.75 }}>Versión</span>
          <span style={{ fontWeight: 700 }}>v4.0</span>
        </div>
      </div>

      <div>
        <div style={{ fontSize: 10, opacity: 0.55, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
          Estado del Sistema
        </div>
        {[
          ['Modelo ML', true],
          ['Datos CSV', true],
          ['API Backend', false],
        ].map(([label, ok]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, fontSize: 12 }}>
            <span style={{
              width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
              background: ok ? '#69f0ae' : '#ff5252',
              boxShadow: ok ? '0 0 4px #69f0ae88' : '0 0 4px #ff525288',
            }} />
            <span style={{ opacity: 0.8 }}>{label}</span>
          </div>
        ))}
      </div>
    </aside>
  )
}

function KpiCard({ label, value, sub }) {
  return (
    <div style={{
      background: 'white', border: '1px solid #e0e0e0', borderRadius: 10,
      padding: '16px 20px', flex: 1, minWidth: 130,
      borderTop: `3px solid ${BRAND}`,
    }}>
      <div style={{ fontSize: 11, color: '#888', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 800, color: BRAND }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: '#aaa', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div style={{ background: BRAND_LIGHT, borderRadius: 8, padding: '10px 16px', minWidth: 110 }}>
      <div style={{ fontSize: 11, color: '#666', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: color || BRAND }}>{value}</div>
    </div>
  )
}

const fmt = v => (v == null || isNaN(v) ? '—' : Math.round(v).toLocaleString('es-PE'))
const th = { padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid #ddd', fontSize: 12, fontWeight: 600 }
const td = { padding: '6px 12px', borderBottom: '1px solid #eee', fontSize: 12 }

export default function Home() {
  const [tab, setTab] = useState('individual')
  const [product, setProduct] = useState('CER001')
  const [predictions, setPredictions] = useState(null)
  const [historical, setHistorical] = useState(null)
  const [loadingPred, setLoadingPred] = useState(true)
  const [loadingHist, setLoadingHist] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/api/predictions')
      .then(r => r.json())
      .then(d => { setPredictions(d); setLoadingPred(false) })
      .catch(e => { setError(String(e)); setLoadingPred(false) })
  }, [])

  useEffect(() => {
    setLoadingHist(true)
    setHistorical(null)
    fetch(`/api/historical/${product}`)
      .then(r => r.json())
      .then(d => { setHistorical(Array.isArray(d) ? d : []); setLoadingHist(false) })
      .catch(e => { setError(String(e)); setLoadingHist(false) })
  }, [product])

  const productForecasts = predictions?.[product] ?? []

  const chartData = (() => {
    const hist = historical ?? []
    const last26 = hist.slice(-26)
    const combined = []

    last26.forEach(h => {
      combined.push({
        label: h.semana.slice(0, 7),
        ventas: h.ventas,
        forecast: null, lower: null, upper: null,
      })
    })

    productForecasts.forEach(f => {
      combined.push({
        label: f.semana,
        ventas: null,
        forecast: Math.round(f.forecast * 100) / 100,
        lower: Math.round(f.lower * 100) / 100,
        upper: Math.round(f.upper * 100) / 100,
      })
    })

    return combined
  })()

  const forecastValues = productForecasts.map(f => f.forecast)
  const total = forecastValues.reduce((a, b) => a + b, 0)
  const media = forecastValues.length ? total / forecastValues.length : 0
  const maxVal = forecastValues.length ? Math.max(...forecastValues) : 0
  const minVal = forecastValues.length ? Math.min(...forecastValues) : 0
  const stddev = forecastValues.length
    ? Math.sqrt(forecastValues.reduce((a, b) => a + (b - media) ** 2, 0) / forecastValues.length)
    : 0

  const comparativeData = predictions
    ? PRODUCTOS.map(p => {
        const vals = (predictions[p] ?? []).map(f => f.forecast)
        const t = vals.reduce((a, b) => a + b, 0)
        return {
          producto: p,
          total: Math.round(t),
          media: Math.round(t / 52),
          max: Math.round(vals.length ? Math.max(...vals) : 0),
          min: Math.round(vals.length ? Math.min(...vals) : 0),
        }
      })
    : []

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: "'Segoe UI', Arial, sans-serif", background: '#f5f6fa' }}>
      <Sidebar />

      <main style={{ flex: 1, padding: '24px 28px', overflowX: 'hidden', minWidth: 0 }}>
        <div style={{ marginBottom: 20 }}>
          <h1 style={{ color: BRAND, margin: 0, fontSize: 24, fontWeight: 800 }}>Dashboard de Predicción de Demanda</h1>
          <p style={{ color: '#777', margin: '4px 0 0', fontSize: 13 }}>
            Empresa Metalúrgica · Horizonte: 52 semanas · Modelo XGBoost v4.0
          </p>
        </div>

        {error && (
          <div style={{ background: '#ffebee', border: '1px solid #ef9a9a', borderRadius: 6, padding: '10px 14px', marginBottom: 16, color: '#c62828', fontSize: 13 }}>
            {error}
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
          <KpiCard label="Productos activos" value="7" sub="SKUs monitoreados" />
          <KpiCard label="Horizonte de predicción" value="52" sub="semanas futuras" />
          <KpiCard label="Precisión del modelo" value="99.39%" sub="R² — XGBoost" />
          <KpiCard label="Predicciones totales" value="364" sub="7 productos × 52 semanas" />
        </div>

        <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '2px solid #e0e0e0' }}>
          {[
            ['individual', 'Análisis Individual'],
            ['comparativo', 'Comparativo de Productos'],
          ].map(([key, label]) => (
            <button key={key} onClick={() => setTab(key)} style={{
              padding: '10px 20px', background: 'none', border: 'none', cursor: 'pointer',
              borderBottom: tab === key ? `3px solid ${BRAND}` : '3px solid transparent',
              color: tab === key ? BRAND : '#666',
              fontWeight: tab === key ? 700 : 400,
              fontSize: 14, marginBottom: -2,
            }}>
              {label}
            </button>
          ))}
        </div>

        {tab === 'individual' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
              <label style={{ fontWeight: 600, fontSize: 13, color: '#444' }}>Producto (SKU):</label>
              <select
                value={product}
                onChange={e => setProduct(e.target.value)}
                style={{ padding: '7px 14px', fontSize: 14, borderRadius: 6, border: '1px solid #ccc', background: 'white', cursor: 'pointer' }}
              >
                {PRODUCTOS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
              {(loadingPred || loadingHist) && (
                <span style={{ fontSize: 12, color: '#888', fontStyle: 'italic' }}>Cargando datos...</span>
              )}
            </div>

            <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap' }}>
              <StatCard label="Media Semanal" value={fmt(media)} />
              <StatCard label="Máximo" value={fmt(maxVal)} color="#1b5e20" />
              <StatCard label="Mínimo" value={fmt(minVal)} color="#b71c1c" />
              <StatCard label="Total Anual" value={fmt(total)} color={ACCENT} />
              <StatCard label="Desv. Estándar" value={fmt(stddev)} />
            </div>

            <div style={{ background: 'white', border: '1px solid #e0e0e0', borderRadius: 10, padding: '14px 8px 8px', marginBottom: 20 }}>
              <div style={{ padding: '0 12px 10px', fontSize: 13, fontWeight: 600, color: '#444' }}>
                Ventas Históricas + Predicción — {product} (26 semanas históricas + 52 predichas)
              </div>
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 10 }}
                    tickFormatter={(v, i) => i % 8 === 0 ? v : ''}
                  />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip
                    formatter={(value, name) => [
                      value != null ? Math.round(value).toLocaleString('es-PE') : '—',
                      name === 'ventas' ? 'Ventas Reales'
                        : name === 'forecast' ? 'Predicción'
                        : name === 'upper' ? 'Límite Sup. 95%'
                        : '',
                    ]}
                  />
                  <Legend
                    formatter={v =>
                      v === 'ventas' ? 'Ventas Reales'
                        : v === 'forecast' ? 'Predicción'
                        : v === 'upper' ? 'Banda Confianza 95%'
                        : ''
                    }
                  />
                  <Area
                    dataKey="upper" name="upper" stroke="none"
                    fill="#90caf9" fillOpacity={0.3} dot={false} legendType="square"
                    connectNulls={false}
                  />
                  <Area
                    dataKey="lower" name="lower" stroke="none"
                    fill="white" fillOpacity={1} dot={false} legendType="none"
                    connectNulls={false}
                  />
                  <Area
                    dataKey="ventas" name="ventas" stroke="#26a69a"
                    fill="#b2dfdb" fillOpacity={0.4} strokeWidth={1.5} dot={false}
                    connectNulls={false}
                  />
                  <Line
                    dataKey="forecast" name="forecast" stroke={BRAND}
                    strokeWidth={2} dot={false} activeDot={{ r: 4 }}
                    connectNulls={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div style={{ background: 'white', border: '1px solid #e0e0e0', borderRadius: 10, overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #eee', fontSize: 13, fontWeight: 600, color: '#444' }}>
                Detalle semanal — {product}
              </div>
              <div style={{ maxHeight: 320, overflowY: 'auto' }}>
                <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                  <thead>
                    <tr style={{ background: BRAND, color: 'white', position: 'sticky', top: 0 }}>
                      <th style={th}>Semana</th>
                      <th style={th}>Predicción</th>
                      <th style={th}>Límite Inf. (95%)</th>
                      <th style={th}>Límite Sup. (95%)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {productForecasts.map((row, i) => (
                      <tr key={i} style={{ background: i % 2 === 0 ? '#fafafa' : 'white' }}>
                        <td style={td}>{row.semana}</td>
                        <td style={{ ...td, fontWeight: 600 }}>{fmt(row.forecast)}</td>
                        <td style={td}>{fmt(row.lower)}</td>
                        <td style={td}>{fmt(row.upper)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {tab === 'comparativo' && (
          <div>
            <div style={{ background: 'white', border: '1px solid #e0e0e0', borderRadius: 10, padding: '14px 8px 8px', marginBottom: 20 }}>
              <div style={{ padding: '0 12px 10px', fontSize: 13, fontWeight: 600, color: '#444' }}>
                Demanda Total Anual por Producto (52 semanas)
              </div>
              {loadingPred ? (
                <div style={{ height: 280, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: 13 }}>
                  Cargando datos...
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={comparativeData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="producto" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip formatter={v => [Math.round(v).toLocaleString('es-PE'), 'Total anual']} />
                    <Bar dataKey="total" name="Total Anual" fill={BRAND} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div style={{ background: 'white', border: '1px solid #e0e0e0', borderRadius: 10, overflow: 'hidden' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #eee', fontSize: 13, fontWeight: 600, color: '#444' }}>
                Resumen de Predicciones — Todos los Productos
              </div>
              <table style={{ borderCollapse: 'collapse', width: '100%' }}>
                <thead>
                  <tr style={{ background: BRAND, color: 'white' }}>
                    <th style={th}>Producto</th>
                    <th style={th}>Media Semanal</th>
                    <th style={th}>Máximo</th>
                    <th style={th}>Mínimo</th>
                    <th style={th}>Total Anual</th>
                  </tr>
                </thead>
                <tbody>
                  {comparativeData.map((row, i) => (
                    <tr key={row.producto} style={{ background: i % 2 === 0 ? '#fafafa' : 'white' }}>
                      <td style={{ ...td, fontWeight: 700, color: BRAND }}>{row.producto}</td>
                      <td style={td}>{fmt(row.media)}</td>
                      <td style={td}>{fmt(row.max)}</td>
                      <td style={td}>{fmt(row.min)}</td>
                      <td style={{ ...td, fontWeight: 700 }}>{fmt(row.total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
