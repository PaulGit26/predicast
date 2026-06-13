import fs from 'fs'
import path from 'path'

export const config = {
  api: { bodyParser: { sizeLimit: '50mb' } },
}

const REQUIRED_COLS = ['fecha', 'entrada', 'salida']
const FILENAME_RE = /^Movimientos_.*\.csv$/i

function dataRoot() {
  return process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
}

function ingestionDir() {
  return path.resolve(dataRoot(), '01_Datos_Nuevos')
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

function countRows(buffer) {
  const text = buffer.toString('latin1')
  const lines = text.trim().split(/\r?\n/)
  return Math.max(0, lines.length - 1)
}

function validateHeader(buffer) {
  const text = buffer.toString('latin1')
  const firstLine = text.split(/\r?\n/)[0] || ''
  const sep = firstLine.includes(';') ? ';' : ','
  const cols = firstLine.split(sep).map(c => c.replace(/[^a-zA-Z]/g, '').toLowerCase())
  const missing = REQUIRED_COLS.filter(r => !cols.some(c => c.includes(r)))
  return { valid: missing.length === 0, missing }
}

export default function handler(req, res) {
  if (req.method === 'GET') {
    return res.status(200).json(readLog())
  }

  if (req.method === 'POST') {
    try {
      const { filename, content_base64 } = req.body

      if (!filename || !content_base64) {
        return res.status(400).json({ error: 'filename y content_base64 son requeridos' })
      }

      if (!FILENAME_RE.test(filename)) {
        return res.status(400).json({ error: `El archivo debe llamarse "Movimientos_*.csv". Recibido: "${filename}"` })
      }

      const buffer = Buffer.from(content_base64, 'base64')

      const { valid, missing } = validateHeader(buffer)
      if (!valid) {
        return res.status(422).json({
          error: `El archivo no tiene las columnas requeridas. Faltan: ${missing.join(', ')}`,
        })
      }

      const destDir = ingestionDir()
      if (!fs.existsSync(destDir)) fs.mkdirSync(destDir, { recursive: true })

      const destPath = path.resolve(destDir, filename)
      const existed = fs.existsSync(destPath)
      fs.writeFileSync(destPath, buffer)

      const rows = countRows(buffer)

      const log = readLog()
      const entry = {
        id: Date.now(),
        fecha: new Date().toISOString(),
        filename,
        rows,
        replaced: existed,
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
