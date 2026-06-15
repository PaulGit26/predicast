import fs from 'fs'
import path from 'path'

export default function handler(_req, res) {
  try {
    const dataRoot = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
    const reportPath = path.resolve(dataRoot, 'EDA_Outputs/REPORTE_OPTIMIZACION_HIPERPARAMETROS.json')

    if (!fs.existsSync(reportPath)) return res.status(200).json([])

    const report = JSON.parse(fs.readFileSync(reportPath, 'utf-8'))
    const grupo1 = report.grupo_1 || {}

    const result = Object.entries(grupo1).map(([sku, data]) => {
      const comp = data.comparativa || {}
      const getR2 = (algo) => comp[algo]?.R2_CV ?? comp[algo]?.R2 ?? null
      const getMAE = (algo) => comp[algo]?.MAE ?? null

      return {
        sku,
        ganador: data.algoritmo_ganador || '—',
        hiperparametros: data.hiperparametros_ganador || {},
        metricas: {
          r2:   data.metricas_test?.R2   ?? null,
          mae:  data.metricas_test?.MAE  ?? null,
          rmse: data.metricas_test?.RMSE ?? null,
        },
        comparativa: {
          Ridge:        { r2: getR2('Ridge'),        mae: getMAE('Ridge')        },
          XGBoost:      { r2: getR2('XGBoost'),      mae: getMAE('XGBoost')      },
          RandomForest: { r2: getR2('RandomForest'), mae: getMAE('RandomForest') },
        },
      }
    })

    res.status(200).json(result)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
}
