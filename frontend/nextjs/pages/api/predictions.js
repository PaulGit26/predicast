import fs from 'fs'
import path from 'path'

export default function handler(req, res) {
  try {
    const csvPath = path.resolve(process.cwd(), '../../../01_Datos/predicciones_52semanas_largo_V4.csv')
    const text = fs.readFileSync(csvPath, 'utf-8')
    const lines = text.trim().split(/\r?\n/)
    const result = {}

    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue
      const parts = lines[i].split(',')
      const codigo = parts[0].replace(/\s+/g, '')
      const semana = parts[1]
      const forecast = parseFloat(parts[2])
      const lower = parseFloat(parts[3])
      const upper = parseFloat(parts[4])

      if (!result[codigo]) result[codigo] = []
      result[codigo].push({ semana, forecast, lower, upper })
    }

    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
