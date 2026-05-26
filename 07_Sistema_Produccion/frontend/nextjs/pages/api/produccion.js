import fs from 'fs'
import path from 'path'

export default function handler(req, res) {
  const safetyWeeks = Math.max(0.5, Math.min(12, parseFloat(req.query.safety_weeks) || 2))
  const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')

  try {
    // ── 1. Load demand forecasts ─────────────────────────────────────────────
    const predPath = path.resolve(dataRoot, '01_Datos/predicciones_52semanas_largo_V4.csv')
    const predLines = fs.readFileSync(predPath, 'utf-8').trim().split(/\r?\n/)
    const predictions = {}
    for (let i = 1; i < predLines.length; i++) {
      if (!predLines[i].trim()) continue
      const parts = predLines[i].split(',')
      const codigo = parts[0].replace(/\s+/g, '')
      const semana = parts[1]
      const forecast = parseFloat(parts[2]) || 0
      if (!predictions[codigo]) predictions[codigo] = []
      predictions[codigo].push({ semana, forecast })
    }

    // ── 2. Load current stock from 08_SERIE_SEMANAL files ───────────────────
    const exploDir = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS')
    const files = fs.readdirSync(exploDir).filter(
      f => f.startsWith('08_SERIE_SEMANAL_') && f.endsWith('.csv')
    )

    const result = {}

    for (const file of files) {
      const sku = file.replace('08_SERIE_SEMANAL_', '').replace('.csv', '')
      if (!predictions[sku]) continue

      const content = fs.readFileSync(path.join(exploDir, file)).toString('latin1')
      const rows = content.trim().split(/\r?\n/)
      const sep = rows[0].includes(';') ? ';' : ','
      const lastRow = rows[rows.length - 1].split(sep)
      const currentStock = parseFloat(lastRow[3]) || 0
      const lastDateStr = (lastRow[0] || '').trim()

      // Cap outlier forecasts at 5× historical median (robust to one-off demand spikes)
      const histSales = rows.slice(1).map(r => parseFloat(r.split(sep)[1]) || 0).sort((a, b) => a - b)
      const histMedian = histSales[Math.floor(histSales.length / 2)]
      const forecastCap = Math.max(histMedian * 5, 100)

      const weeks = predictions[sku].map(w => ({
        ...w,
        forecast: Math.min(w.forecast, forecastCap),
      }))
      const avgDemand = weeks.reduce((s, w) => s + w.forecast, 0) / weeks.length
      const safetyStock = safetyWeeks * avgDemand

      // ── 3. MRP calculation ──────────────────────────────────────────────
      let stock = currentStock
      const calendar = []
      const lastDate = new Date(lastDateStr)

      for (let i = 0; i < weeks.length; i++) {
        const { semana, forecast } = weeks[i]
        const weekDate = new Date(lastDate)
        weekDate.setDate(weekDate.getDate() + (i + 1) * 7)
        const fecha = weekDate.toISOString().slice(0, 10)

        const projected = stock - forecast
        let production = 0
        if (projected < safetyStock) {
          production = Math.max(0, forecast + safetyStock - stock)
        }
        const stockFin = stock + production - forecast

        calendar.push({
          semana,
          fecha,
          demanda: Math.round(forecast),
          produccion: Math.round(production),
          stock_inicio: Math.round(stock),
          stock_fin: Math.round(stockFin),
          urgente: projected < 0,
        })
        stock = stockFin
      }

      result[sku] = {
        stock_actual: Math.round(currentStock),
        stock_seguridad: Math.round(safetyStock),
        avg_demand: Math.round(avgDemand),
        semanas_produccion: calendar.filter(w => w.produccion > 0).length,
        calendar,
      }
    }

    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
