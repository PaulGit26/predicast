import fs from 'fs'
import path from 'path'
import crypto from 'crypto'

function dataPath() {
  const root = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
  return path.resolve(root, 'operarios.json')
}

function readData() {
  try {
    if (fs.existsSync(dataPath())) return JSON.parse(fs.readFileSync(dataPath(), 'utf-8'))
  } catch (_) {}
  return { operarios: [] }
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

  // GET: list active operators
  if (req.method === 'GET') {
    return res.status(200).json(
      (data.operarios || [])
        .filter(o => o.activo !== false)
        .sort((a, b) => a.nombre.localeCompare(b.nombre, 'es'))
    )
  }

  // POST: create operator
  if (req.method === 'POST') {
    const { nombre, email } = req.body
    if (!nombre?.trim()) return res.status(400).json({ error: 'El nombre es requerido.' })
    if (!email?.trim())  return res.status(400).json({ error: 'El correo electrónico es requerido.' })

    const emailNorm = email.trim().toLowerCase()
    const dupNombre = (data.operarios || []).find(
      o => o.activo !== false && o.nombre.toLowerCase() === nombre.trim().toLowerCase()
    )
    if (dupNombre) return res.status(400).json({ error: `Ya existe un operario con el nombre "${nombre.trim()}".` })

    const dupEmail = (data.operarios || []).find(
      o => o.activo !== false && o.email.toLowerCase() === emailNorm
    )
    if (dupEmail) return res.status(400).json({ error: `El correo "${email.trim()}" ya está registrado en otro operario.` })

    const op = {
      id: crypto.randomBytes(4).toString('hex'),
      nombre: nombre.trim(),
      email: email.trim(),
      activo: true,
      created_at: new Date().toISOString(),
    }
    if (!data.operarios) data.operarios = []
    data.operarios.push(op)
    try { writeData(data) } catch (e) {
      return res.status(500).json({ error: `Error guardando: ${e.message}` })
    }
    return res.status(201).json(op)
  }

  // PUT: update (name, email) or deactivate (activo: false)
  if (req.method === 'PUT') {
    const { id, nombre, email, activo } = req.body
    if (!id) return res.status(400).json({ error: 'id requerido' })
    const idx = (data.operarios || []).findIndex(o => o.id === id)
    if (idx === -1) return res.status(404).json({ error: 'Operario no encontrado.' })

    if (nombre !== undefined) data.operarios[idx].nombre = nombre.trim()
    if (email !== undefined)  data.operarios[idx].email  = email.trim()
    if (activo !== undefined) data.operarios[idx].activo = activo
    data.operarios[idx].updated_at = new Date().toISOString()

    try { writeData(data) } catch (e) {
      return res.status(500).json({ error: `Error guardando: ${e.message}` })
    }
    return res.status(200).json(data.operarios[idx])
  }

  res.status(405).json({ error: 'Method not allowed' })
}
