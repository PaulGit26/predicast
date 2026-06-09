import fs from 'fs'
import path from 'path'

const SKUS = ['CER001', 'CER005', 'CEO001', 'CEO006', 'CER008', 'CER004', 'CERE002']

export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const skuData = {}
    const timelineMap = {}

    for (const sku of SKUS) {
      const filePath = path.resolve(dataRoot, `03_ANALISIS_EXPLORATORIO_DATOS/08_SERIE_SEMANAL_${sku}.csv`)
      if (!fs.existsSync(filePath)) continue

      const text = fs.readFileSync(filePath).toString('latin1')
      const lines = text.trim().split(/\r?\n/)
      const sep = lines[0].includes(';') ? ';' : ','

      const series = lines.slice(1).filter(l => l.trim()).map(line => {
        const p = line.split(sep)
        return {
          semana: (p[0] || '').trim(),
          ventas: parseFloat(p[1]) || 0,
          produccion: parseFloat(p[2]) || 0,
        }
      }).filter(r => r.semana)

      const produccion_total = series.reduce((s, r) => s + r.produccion, 0)
      const ventas_total = series.reduce((s, r) => s + r.ventas, 0)
      const n_semanas = series.length

      skuData[sku] = {
        totales: {
          produccion_total: Math.round(produccion_total),
          ventas_total: Math.round(ventas_total),
          n_semanas,
          avg_semanal: Math.round(ventas_total / n_semanas),
        },
        series,
      }

      for (const row of series) {
        if (!timelineMap[row.semana]) {
          timelineMap[row.semana] = { semana: row.semana, ventas: 0, produccion: 0 }
        }
        timelineMap[row.semana].ventas += row.ventas
        timelineMap[row.semana].produccion += row.produccion
      }
    }

    const timeline = Object.values(timelineMap)
      .sort((a, b) => a.semana.localeCompare(b.semana))
      .map(r => ({ semana: r.semana, ventas: Math.round(r.ventas), produccion: Math.round(r.produccion) }))

    res.status(200).json({ skus: skuData, timeline })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
