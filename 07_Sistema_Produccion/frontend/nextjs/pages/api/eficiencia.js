import fs from 'fs'
import path from 'path'

// cols: Código,Producción_Total,Ventas_Total,Planchas_Producción,Planchas_Ventas,
//       Planchas_Gap,Costo_Producción_S/,Costo_Ventas_S/,Ahorro_Potencial_S/,Eficiencia_%
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS/14_COSTO_PLANCHA_ACUMULADO_POR_PRODUCTO.csv')
    const text = fs.readFileSync(filePath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','
    const result = lines.slice(1).filter(l => l.trim()).map(line => {
      const p = line.split(sep)
      return {
        codigo: (p[0] || '').trim().replace(/\s+/g, ''),
        produccion_total: parseFloat(p[1]) || 0,
        ventas_total: parseFloat(p[2]) || 0,
        planchas_gap: parseFloat(p[5]) || 0,
        costo_produccion: parseFloat(p[6]) || 0,
        costo_ventas: parseFloat(p[7]) || 0,
        ahorro: parseFloat(p[8]) || 0,
        eficiencia: parseFloat(p[9]) || 0,
      }
    }).filter(r => r.codigo)
    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
