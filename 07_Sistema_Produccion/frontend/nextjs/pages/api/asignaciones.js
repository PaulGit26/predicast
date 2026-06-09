import fs from 'fs'
import path from 'path'
import crypto from 'crypto'

function dataPath() {
  const root = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
  return path.resolve(root, 'asignaciones.json')
}

function readData() {
  try {
    if (fs.existsSync(dataPath())) return JSON.parse(fs.readFileSync(dataPath(), 'utf-8'))
  } catch (_) {}
  return { semanas: {} }
}

function writeData(d) {
  const p = dataPath()
  const dir = path.dirname(p)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(p, JSON.stringify(d, null, 2), 'utf-8')
}

export default function handler(req, res) {
  let data
  try { data = readData() } catch (e) {
    return res.status(500).json({ error: `Error leyendo datos: ${e.message}` })
  }

  // GET: list, by semana key, or by operator token
  if (req.method === 'GET') {
    const { semana, token } = req.query

    if (token) {
      for (const sem of Object.values(data.semanas)) {
        const op = (sem.operarios || []).find(o => o.token === token)
        if (op) return res.status(200).json({ operario: op, semana: sem })
      }
      return res.status(404).json({ error: 'Token no encontrado' })
    }

    if (semana) return res.status(200).json(data.semanas[semana] || null)

    return res.status(200).json(
      Object.values(data.semanas)
        .sort((a, b) => (b.fecha_inicio || '').localeCompare(a.fecha_inicio || ''))
        .map(s => ({
          semana: s.semana,
          fecha_inicio: s.fecha_inicio,
          n_operarios: s.operarios?.length || 0,
          updated_at: s.updated_at,
        }))
    )
  }

  // POST: create / update full assignment for a week
  if (req.method === 'POST') {
    const { semana, fecha_inicio, metas_sku, operarios } = req.body
    if (!semana) return res.status(400).json({ error: 'semana requerida' })

    const existing = data.semanas[semana] || {}
    const ops = (operarios || []).map(op => ({
      ...op,
      id:    op.id    || crypto.randomBytes(4).toString('hex'),
      token: op.token || crypto.randomBytes(8).toString('hex'),
    }))

    data.semanas[semana] = {
      ...existing,
      semana,
      fecha_inicio,
      metas_sku: metas_sku || {},
      operarios: ops,
      progreso:  existing.progreso || {},
      created_at: existing.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    try { writeData(data) } catch (e) {
      return res.status(500).json({ error: `Error guardando datos: ${e.message}`, path: dataPath() })
    }
    return res.status(200).json({ ok: true, semana: data.semanas[semana] })
  }

  // PUT: update progress for one operator
  if (req.method === 'PUT') {
    const { semana, operario_id, avances, notas } = req.body
    if (!semana || !operario_id) return res.status(400).json({ error: 'semana y operario_id requeridos' })
    if (!data.semanas[semana]) return res.status(404).json({ error: 'Semana no encontrada' })

    if (!data.semanas[semana].progreso) data.semanas[semana].progreso = {}
    data.semanas[semana].progreso[operario_id] = {
      avances: avances || {},
      notas:   notas   || '',
      updated: new Date().toISOString(),
    }
    data.semanas[semana].updated_at = new Date().toISOString()
    try { writeData(data) } catch (e) {
      return res.status(500).json({ error: `Error guardando progreso: ${e.message}` })
    }
    return res.status(200).json({ ok: true })
  }

  res.status(405).json({ error: 'Method not allowed' })
}
