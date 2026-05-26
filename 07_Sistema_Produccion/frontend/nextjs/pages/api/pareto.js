import fs from 'fs'
import path from 'path'

// cols: Código,Num_Transacciones,Salida_Total,...,Descripción,Acumulado_pct
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS/01_VENTAS_POR_PRODUCTO.csv')
    const text = fs.readFileSync(filePath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','
    const result = lines.slice(1).filter(l => l.trim()).map(line => {
      const p = line.split(sep)
      return {
        codigo: (p[0] || '').trim().replace(/\s+/g, '').replace(/'/g, ''),
        descripcion: (p[7] || '').trim(),
        ventas: parseFloat(p[2]) || 0,
        pct: parseFloat(p[8]) || 0,
      }
    }).filter(r => r.codigo)
    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
