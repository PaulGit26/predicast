import fs from 'fs'
import path from 'path'

const VALID_SKUS = ['CER001', 'CER005', 'CEO001', 'CEO006', 'CER008', 'CER004', 'CERE002']
const SERIES_HEADER = 'Semana_Inicio;Ventas_Semanales;Produccion_Semanal;Stock_Cierre_Semanal'

function dataRoot() {
  return process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
}

function seriesPath(sku) {
  return path.resolve(dataRoot(), `03_ANALISIS_EXPLORATORIO_DATOS/08_SERIE_SEMANAL_${sku}.csv`)
}

function logPath() {
  return path.resolve(dataRoot(), 'ingest_log.json')
}

function readLog() {
  try {
    const p = logPath()
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf-8'))
  } catch (_) {}
  return []
}

function writeLog(entries) {
  fs.writeFileSync(logPath(), JSON.stringify(entries, null, 2), 'utf-8')
}

function validateRows(rows) {
  const errors = []
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i]
    const row = i + 1
    if (!VALID_SKUS.includes(r.sku)) errors.push(`Fila ${row}: SKU "${r.sku}" no reconocido`)
    if (!/^\d{4}-\d{2}-\d{2}$/.test(r.semana)) errors.push(`Fila ${row}: fecha "${r.semana}" inválida (usar YYYY-MM-DD)`)
    if (isNaN(r.ventas) || r.ventas < 0) errors.push(`Fila ${row}: ventas inválidas`)
    if (isNaN(r.produccion) || r.produccion < 0) errors.push(`Fila ${row}: producción inválida`)
    if (isNaN(r.stock) || r.stock < 0) errors.push(`Fila ${row}: stock inválido`)
  }
  return errors
}

function appendToSeries(sku, rows) {
  const p = seriesPath(sku)
  const newLines = rows.map(r => `${r.semana};${r.ventas};${r.produccion};${r.stock}`).join('\n')

  if (!fs.existsSync(p)) {
    fs.writeFileSync(p, SERIES_HEADER + '\n' + newLines + '\n', 'latin1')
    return { created: true }
  }

  // Check for duplicate semanas already in the file
  const existing = fs.readFileSync(p).toString('latin1')
  const existingDates = new Set(
    existing.trim().split(/\r?\n/).slice(1).map(l => l.split(';')[0]?.trim())
  )
  const toAppend = rows.filter(r => !existingDates.has(r.semana))
  const skipped = rows.length - toAppend.length

  if (toAppend.length > 0) {
    const append = '\n' + toAppend.map(r => `${r.semana};${r.ventas};${r.produccion};${r.stock}`).join('\n')
    fs.appendFileSync(p, append, 'latin1')
  }
  return { appended: toAppend.length, skipped }
}

export default function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json(readLog())
  }

  if (req.method === 'POST') {
    try {
      const { rows } = req.body
      if (!Array.isArray(rows) || rows.length === 0) {
        return res.status(400).json({ error: 'rows debe ser un array no vacío' })
      }

      const errors = validateRows(rows)
      if (errors.length > 0) {
        return res.status(422).json({ errors })
      }

      // Group by SKU
      const bySku = {}
      for (const r of rows) {
        if (!bySku[r.sku]) bySku[r.sku] = []
        bySku[r.sku].push(r)
      }

      const results = {}
      for (const [sku, skuRows] of Object.entries(bySku)) {
        results[sku] = appendToSeries(sku, skuRows)
      }

      // Append to log
      const log = readLog()
      const entry = {
        id: Date.now(),
        fecha: new Date().toISOString(),
        skus: Object.keys(bySku),
        total_filas: rows.length,
        detalle: results,
      }
      log.unshift(entry)
      if (log.length > 50) log.length = 50
      writeLog(log)

      return res.status(200).json({ ok: true, entry })
    } catch (err) {
      return res.status(500).json({ error: err.message })
    }
  }

  res.status(405).json({ error: 'Method not allowed' })
}
