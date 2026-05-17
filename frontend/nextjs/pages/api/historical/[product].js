import fs from 'fs'
import path from 'path'

export default function handler(req, res) {
  const { product } = req.query

  if (!/^[A-Z0-9]+$/.test(product)) {
    return res.status(400).json({ error: 'Invalid product code' })
  }

  try {
    const csvPath = path.resolve(
      process.cwd(),
      `../../../03_ANALISIS_EXPLORATORIO_DATOS/08_SERIE_SEMANAL_${product}.csv`
    )
    const text = fs.readFileSync(csvPath, 'utf-8')
    const lines = text.trim().split(/\r?\n/)
    const data = []

    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue
      const parts = lines[i].split(';')
      data.push({
        semana: parts[0],
        ventas: parseFloat(parts[1]),
        produccion: parseFloat(parts[2]),
        stock: parseFloat(parts[3]),
      })
    }

    res.status(200).json(data)
  } catch (err) {
    if (err.code === 'ENOENT') {
      return res.status(404).json({ error: `No data for product ${product}` })
    }
    res.status(500).json({ error: err.message })
  }
}
