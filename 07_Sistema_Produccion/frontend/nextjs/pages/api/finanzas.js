import fs from 'fs'
import path from 'path'

function dataPath() {
  const root = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
  return path.resolve(root, 'finanzas.json')
}

function readData() {
  try {
    if (fs.existsSync(dataPath())) return JSON.parse(fs.readFileSync(dataPath(), 'utf-8'))
  } catch (_) {}
  return {}
}

function writeData(d) {
  const p = dataPath()
  const dir = path.dirname(p)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(p, JSON.stringify(d, null, 2), 'utf-8')
}

export default function handler(req, res) {
  if (req.method === 'GET') {
    let data
    try { data = readData() } catch (e) {
      return res.status(500).json({ error: `Error leyendo datos: ${e.message}` })
    }
    return res.status(200).json(data)
  }

  if (req.method === 'PUT') {
    let data
    try { data = readData() } catch (_) { data = {} }
    const { precios_venta, overhead_pct, sueldos, cargas_sociales_pct } = req.body
    if (precios_venta        !== undefined) data.precios_venta        = { ...(data.precios_venta || {}), ...precios_venta }
    if (overhead_pct         !== undefined) data.overhead_pct         = overhead_pct
    if (sueldos              !== undefined) data.sueldos              = { ...(data.sueldos || {}), ...sueldos }
    if (cargas_sociales_pct  !== undefined) data.cargas_sociales_pct  = cargas_sociales_pct
    try { writeData(data) } catch (e) {
      return res.status(500).json({ error: `Error guardando: ${e.message}` })
    }
    return res.status(200).json(data)
  }

  res.status(405).json({ error: 'Method not allowed' })
}
