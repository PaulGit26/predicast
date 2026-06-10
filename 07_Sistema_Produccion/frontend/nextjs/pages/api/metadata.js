import fs from 'fs'
import path from 'path'

export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const filePath = path.resolve(dataRoot, '01_Datos/predicciones_52semanas_METADATA_V4.json')
    const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'))
    const result = {}
    for (const [sku, info] of Object.entries(data.modelos || {})) {
      result[sku.replace(/\s+/g, '')] = {
        algoritmo: info.algoritmo,
        r2:   info.r2,
        mae:  info.mae,
        rmse: info.rmse,
        mape: info.mape ?? null,
      }
    }
    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
