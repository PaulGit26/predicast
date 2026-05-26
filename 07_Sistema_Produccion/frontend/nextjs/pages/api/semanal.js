import fs from 'fs'
import path from 'path'

// cols: Semana_Inicio,Ventas_Semanales,Produccion_Semanal,Stock_Cierre_Semanal
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS/07_SERIE_SEMANAL_VENTAS_PRODUCCION_STOCK.csv')
    const text = fs.readFileSync(filePath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','
    const result = lines.slice(1).filter(l => l.trim()).map(line => {
      const p = line.split(sep)
      return {
        semana: (p[0] || '').trim(),
        ventas: parseFloat(p[1]) || 0,
        produccion: parseFloat(p[2]) || 0,
        stock: parseFloat(p[3]) || 0,
      }
    }).filter(r => r.semana)
    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
