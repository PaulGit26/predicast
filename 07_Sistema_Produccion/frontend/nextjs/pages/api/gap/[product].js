import fs from 'fs'
import path from 'path'

// cols: Semana_Inicio,Ventas_Semanales,Produccion_Semanal,Planchas_Ventas,Planchas_Produccion,Planchas_Gap
export default function handler(req, res) {
  const { product } = req.query

  if (!/^[A-Z0-9]+$/.test(product)) {
    return res.status(400).json({ error: 'Invalid product code' })
  }

  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, `03_ANALISIS_EXPLORATORIO_DATOS/13_PLANCHA_GAP_${product}.csv`)
    const text = fs.readFileSync(filePath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','
    const result = lines.slice(1).filter(l => l.trim()).map(line => {
      const p = line.split(sep)
      return {
        semana: (p[0] || '').trim(),
        ventas: parseFloat(p[1]) || 0,
        produccion: parseFloat(p[2]) || 0,
        planchas_gap: parseFloat(p[5]) || 0,
      }
    }).filter(r => r.semana)
    res.status(200).json(result)
  } catch (err) {
    if (err.code === 'ENOENT') return res.status(404).json({ error: `No gap data for ${product}` })
    res.status(500).json({ error: err.message })
  }
}
