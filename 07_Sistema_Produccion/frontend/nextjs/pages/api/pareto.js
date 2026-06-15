import fs from 'fs'
import path from 'path'

// cols: Código,Num_Transacciones,Salida_Total,...,Descripción,Acumulado_pct
// Returns only the Pareto-selected products from PARETO_RESULTADO.json
export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, '03_ANALISIS_EXPLORATORIO_DATOS/01_VENTAS_POR_PRODUCTO.csv')
    const text = fs.readFileSync(filePath).toString('latin1')
    const lines = text.trim().split(/\r?\n/)
    const sep = lines[0].includes(';') ? ';' : ','

    // Load selected SKUs from pipeline Pareto result (no spaces for comparison)
    let selectedSkus = null
    const paretoResPath = path.resolve(dataRoot, 'EDA_Outputs/PARETO_RESULTADO.json')
    if (fs.existsSync(paretoResPath)) {
      const pr = JSON.parse(fs.readFileSync(paretoResPath, 'utf-8'))
      selectedSkus = new Set((pr.productos_seleccionados || []).map(s => s.replace(/\s+/g, '')))
    }

    const result = lines.slice(1).filter(l => l.trim()).map(line => {
      const p = line.split(sep)
      return {
        codigo: (p[0] || '').trim().replace(/\s+/g, '').replace(/'/g, ''),
        descripcion: (p[7] || '').trim(),
        ventas: parseFloat(p[2]) || 0,
        pct: parseFloat(p[8]) || 0,
      }
    }).filter(r => r.codigo && (!selectedSkus || selectedSkus.has(r.codigo)))

    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
