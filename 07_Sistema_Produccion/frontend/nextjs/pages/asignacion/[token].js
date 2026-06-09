import { useState, useEffect } from 'react'

const TEAL = '#0e7490'
const GREEN = '#166534'
const ORANGE = '#92400e'
const RED = '#991b1b'

function statusColor(pct) { return pct >= 80 ? GREEN : pct >= 40 ? ORANGE : RED }
function statusBg(pct)    { return pct >= 80 ? '#f0fdf4' : pct >= 40 ? '#fffbeb' : '#fef2f2' }
function statusLabel(pct) { return pct >= 80 ? 'En meta' : pct >= 40 ? 'En progreso' : pct > 0 ? 'Rezagado' : 'Sin iniciar' }

export default function OperarioView({ token }) {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState('')

  useEffect(() => {
    if (!token) return
    fetch(`/api/asignaciones?token=${token}`)
      .then(r => r.json())
      .then(d => { if (d.error) setError(d.error); else setData(d); setLoading(false) })
      .catch(() => { setError('Error de conexión'); setLoading(false) })
  }, [token])

  if (loading) return (
    <div style={{ padding: 60, textAlign: 'center', fontFamily: 'system-ui', color: '#64748b' }}>
      Cargando tu asignación...
    </div>
  )
  if (error) return (
    <div style={{ padding: 60, textAlign: 'center', fontFamily: 'system-ui' }}>
      <div style={{ fontSize: 36, marginBottom: 12 }}>⚠️</div>
      <div style={{ color: RED, fontWeight: 600 }}>{error}</div>
      <div style={{ color: '#94a3b8', marginTop: 8, fontSize: 13 }}>Verifica el enlace con tu supervisor.</div>
    </div>
  )

  const { operario, semana } = data
  const skus = Object.keys(operario.asignaciones || {}).filter(s => (operario.asignaciones[s] || 0) > 0)
  const progreso = semana.progreso?.[operario.id] || {}
  const totalMeta = skus.reduce((s, k) => s + (operario.asignaciones[k] || 0), 0)
  const totalAvance = skus.reduce((s, k) => s + (progreso.avances?.[k] || 0), 0)
  const totalPct = totalMeta > 0 ? Math.round(totalAvance / totalMeta * 100) : 0

  return (
    <div style={{ maxWidth: 520, margin: '0 auto', padding: '32px 20px 60px', fontFamily: 'system-ui, sans-serif', minHeight: '100vh', background: '#f8fafc' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <div style={{ fontSize: 11, color: TEAL, fontWeight: 700, letterSpacing: 1.5, marginBottom: 6 }}>
          PREDICAST · PLAN DE PRODUCCIÓN
        </div>
        <h1 style={{ margin: 0, fontSize: 24, color: '#1a237e', fontWeight: 700 }}>{operario.nombre}</h1>
        <div style={{ color: '#64748b', marginTop: 6, fontSize: 14 }}>
          Semana del {semana.fecha_inicio}
        </div>
      </div>

      {/* Overall progress */}
      <div style={{ background: '#fff', borderRadius: 14, padding: '20px 24px', marginBottom: 20, border: '1px solid #e2e8f0', boxShadow: '0 1px 4px #0001' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <span style={{ fontWeight: 600, color: '#1a237e', fontSize: 15 }}>Progreso global</span>
          <span style={{ fontWeight: 800, fontSize: 22, color: statusColor(totalPct) }}>{totalPct}%</span>
        </div>
        <div style={{ height: 12, background: '#e2e8f0', borderRadius: 6, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${totalPct}%`, background: statusColor(totalPct), borderRadius: 6, transition: 'width 0.6s ease' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6, fontSize: 12, color: '#64748b' }}>
          <span>Avance: {totalAvance.toLocaleString('es-PE')} uds.</span>
          <span>Meta: {totalMeta.toLocaleString('es-PE')} uds.</span>
        </div>
      </div>

      {/* Per-SKU cards */}
      {skus.map(sku => {
        const meta   = operario.asignaciones[sku] || 0
        const avance = progreso.avances?.[sku] || 0
        const pct    = meta > 0 ? Math.min(100, Math.round(avance / meta * 100)) : 0
        return (
          <div key={sku} style={{ background: '#fff', borderRadius: 14, padding: '16px 20px', marginBottom: 12, border: '1px solid #e2e8f0', borderLeft: `5px solid ${statusColor(pct)}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 700, color: TEAL, fontSize: 16 }}>{sku}</div>
                <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 2 }}>Meta semana</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 800, fontSize: 20, color: statusColor(pct) }}>{pct}%</div>
                <div style={{ fontSize: 11, background: statusBg(pct), color: statusColor(pct), padding: '1px 8px', borderRadius: 10, fontWeight: 600, marginTop: 2 }}>
                  {statusLabel(pct)}
                </div>
              </div>
            </div>
            <div style={{ display: 'flex', gap: 24, marginBottom: 10 }}>
              <div>
                <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Tu meta</div>
                <div style={{ fontWeight: 700, fontSize: 20, color: '#1a237e' }}>{meta.toLocaleString('es-PE')}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Avance actual</div>
                <div style={{ fontWeight: 700, fontSize: 20, color: statusColor(pct) }}>{avance.toLocaleString('es-PE')}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5 }}>Restante</div>
                <div style={{ fontWeight: 700, fontSize: 20, color: '#64748b' }}>{Math.max(0, meta - avance).toLocaleString('es-PE')}</div>
              </div>
            </div>
            <div style={{ height: 8, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`, background: statusColor(pct), borderRadius: 4 }} />
            </div>
          </div>
        )
      })}

      {progreso.notas && (
        <div style={{ background: '#fffbeb', borderRadius: 10, padding: '12px 16px', marginTop: 8, fontSize: 13, color: '#92400e', border: '1px solid #fcd34d' }}>
          <strong>Nota del supervisor:</strong> {progreso.notas}
        </div>
      )}

      <div style={{ textAlign: 'center', marginTop: 32, fontSize: 11, color: '#cbd5e1' }}>
        Vista actualizada por el gerente de producción · Solo lectura
      </div>
    </div>
  )
}

export async function getServerSideProps({ params }) {
  return { props: { token: params?.token || '' } }
}
