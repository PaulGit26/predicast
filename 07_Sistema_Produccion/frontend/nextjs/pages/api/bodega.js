import fs from 'fs'
import path from 'path'

// cols (sep=;): Bodega,Num_Transacciones,Salida_Total,Productos_Unicos
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS/04_VENTAS_POR_BODEGA.csv')
    const text = fs.readFileSync(filePath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','
    const result = lines.slice(1).filter(l => l.trim()).map(line => {
      const p = line.split(sep)
      return {
        bodega: (p[0] || '').trim(),
        ventas: parseFloat(p[2]) || 0,
        transacciones: parseInt(p[1]) || 0,
      }
    }).filter(r => r.bodega)
    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
