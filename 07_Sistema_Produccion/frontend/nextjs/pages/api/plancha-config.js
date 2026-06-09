import fs from 'fs'
import path from 'path'

const DEFAULT_CONFIG = {
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

function configPath() {
  const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
  return path.resolve(dataRoot, 'plancha_config.json')
}

export default function handler(req, res) {
  const p = configPath()

  if (req.method === 'GET') {
    try {
      if (fs.existsSync(p)) {
        return res.status(200).json(JSON.parse(fs.readFileSync(p, 'utf-8')))
      }
      return res.status(200).json(DEFAULT_CONFIG)
    } catch (err) {
      return res.status(500).json({ error: err.message })
    }
  }

  if (req.method === 'PUT') {
    try {
      const body = req.body
      if (!body?.precios || !body?.skus) {
        return res.status(400).json({ error: 'Invalid config: must include precios and skus' })
      }
      fs.writeFileSync(p, JSON.stringify(body, null, 2), 'utf-8')
      return res.status(200).json({ ok: true })
    } catch (err) {
      return res.status(500).json({ error: err.message })
    }
  }

  res.status(405).json({ error: 'Method not allowed' })
}
