import fs from 'fs'
import path from 'path'

// cols (sep=;): Año,Mes,Num_Transacciones,Salida_Total,Año_Mes
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS/06_TENDENCIA_MENSUAL.csv')
    const text = fs.readFileSync(filePath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','
    const result = lines.slice(1).filter(l => l.trim()).map(line => {
      const p = line.split(sep)
      return {
        label: (p[4] || '').trim(),
        anio: parseInt(p[0]) || 0,
        mes: parseInt(p[1]) || 0,
        ventas: parseFloat(p[3]) || 0,
        transacciones: parseInt(p[2]) || 0,
      }
    }).filter(r => r.label)
    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
