import fs from 'fs'
import path from 'path'

// Reads all 08_SERIE_SEMANAL_{SKU}.csv files and returns per-product aggregated analysis:
// total ventas, total produccion, efficiency, by-year breakdown, avg demand by month
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const exploDir = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS')

    const files = fs.readdirSync(exploDir).filter(
      f => f.startsWith('08_SERIE_SEMANAL_') && f.endsWith('.csv')
    )

    const result = []

    for (const file of files) {
      const sku = file.replace('08_SERIE_SEMANAL_', '').replace('.csv', '')
      const content = fs.readFileSync(path.join(exploDir, file)).toString('latin1')
      const lines = content.trim().split(/\r?\n/)
      const sep = lines[0].includes(';') ? ';' : ','

      let totalVentas = 0
      let totalProduccion = 0
      let stockSum = 0
      let stockCount = 0
      const byYear = {}
      const byMonth = {}

      for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue
        const p = lines[i].split(sep)
        const fecha = (p[0] || '').trim()
        const ventas = parseFloat(p[1]) || 0
        const produccion = parseFloat(p[2]) || 0
        const stock = parseFloat(p[3]) || 0

        totalVentas += ventas
        totalProduccion += produccion

        if (stock > 0) {
          stockSum += stock
          stockCount++
        }

        const year = fecha.slice(0, 4)
        const month = parseInt(fecha.slice(5, 7))

        if (year && !isNaN(parseInt(year))) {
          if (!byYear[year]) byYear[year] = { anio: year, ventas: 0, produccion: 0 }
          byYear[year].ventas += ventas
          byYear[year].produccion += produccion
        }

        if (month >= 1 && month <= 12) {
          if (!byMonth[month]) byMonth[month] = { ventas: 0, n: 0 }
          byMonth[month].ventas += ventas
          byMonth[month].n++
        }
      }

      const avgStock = stockCount > 0 ? stockSum / stockCount : 0
      const rotacion = avgStock > 0 ? Math.round((totalVentas / avgStock) * 10) / 10 : 0

      const porMes = Array.from({ length: 12 }, (_, i) => {
        const m = i + 1
        const d = byMonth[m] || { ventas: 0, n: 1 }
        return { mes: m, ventas: Math.round(d.ventas / Math.max(d.n, 1)) }
      })

      result.push({
        codigo: sku,
        total_ventas: Math.round(totalVentas),
        total_produccion: Math.round(totalProduccion),
        eficiencia: totalProduccion > 0 ? Math.round((totalVentas / totalProduccion) * 1000) / 10 : 0,
        gap_unidades: Math.round(totalProduccion - totalVentas),
        rotacion,
        por_anio: Object.values(byYear)
          .sort((a, b) => a.anio.localeCompare(b.anio))
          .map(r => ({ anio: r.anio, ventas: Math.round(r.ventas), produccion: Math.round(r.produccion) })),
        por_mes: porMes,
      })
    }

    result.sort((a, b) => b.total_ventas - a.total_ventas)
    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
