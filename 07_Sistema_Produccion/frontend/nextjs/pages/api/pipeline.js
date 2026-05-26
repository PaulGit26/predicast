const PIPELINE_URL = process.env.PIPELINE_URL || 'http://localhost:5001'

export default async function handler(req, res) {
  try {
    if (req.method === 'POST') {
      const r = await fetch(`${PIPELINE_URL}/run`, { method: 'POST' })
      const data = await r.json()
      return res.status(r.status).json(data)
    }
    const r = await fetch(`${PIPELINE_URL}/status`)
    const data = await r.json()
    return res.status(200).json(data)
  } catch (err) {
    return res.status(503).json({ error: 'Pipeline service unavailable', detail: err.message })
  }
}
