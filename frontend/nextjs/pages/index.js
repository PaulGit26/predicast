import { useState } from 'react'

export default function Home() {
  const [productId, setProductId] = useState('P1')
  const [periods, setPeriods] = useState(12)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  async function fetchForecast() {
    setLoading(true)
    setResult(null)
    try {
      const res = await fetch('/api/v1/forecast/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, periods })
      })
      const data = await res.json()
      setResult(data)
    } catch (err) {
      setResult({ error: String(err) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: 'Arial, sans-serif' }}>
      <h1>Predicast - Frontend (Next.js skeleton)</h1>
      <div style={{ marginBottom: 12 }}>
        <label>Product ID: </label>
        <input value={productId} onChange={e => setProductId(e.target.value)} />
      </div>
      <div style={{ marginBottom: 12 }}>
        <label>Periods: </label>
        <input type="number" value={periods} onChange={e => setPeriods(Number(e.target.value))} />
      </div>
      <button onClick={fetchForecast} disabled={loading}>{loading ? 'Loading...' : 'Get Forecast'}</button>

      <section style={{ marginTop: 20 }}>
        <h2>Result</h2>
        <pre style={{ background: '#f6f6f6', padding: 12 }}>{JSON.stringify(result, null, 2)}</pre>
      </section>

      <footer style={{ marginTop: 24, color: '#666' }}>
        <small>Note: this is a skeleton. The app calls ` /api/v1/forecast/predict` on the same origin.</small>
      </footer>
    </main>
  )
}
