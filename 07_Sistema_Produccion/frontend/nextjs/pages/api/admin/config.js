import fs from 'fs'
import path from 'path'
import { getServerSession } from 'next-auth/next'
import { authOptions } from '../auth/[...nextauth]'

function configPath() {
  const root = process.env.DATA_ROOT || path.resolve(process.cwd(), '../../..')
  return path.resolve(root, 'config.json')
}

function readConfig() {
  try {
    if (fs.existsSync(configPath())) return JSON.parse(fs.readFileSync(configPath(), 'utf-8'))
  } catch (_) {}
  return { idle_timeout_minutes: 30 }
}

function writeConfig(d) {
  const p = configPath()
  const dir = path.dirname(p)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(p, JSON.stringify(d, null, 2), 'utf-8')
}

export default async function handler(req, res) {
  const session = await getServerSession(req, res, authOptions)

  if (req.method === 'GET') {
    return res.status(200).json(readConfig())
  }

  if (req.method === 'PUT') {
    if (!session?.roles?.includes('admin')) {
      return res.status(403).json({ error: 'Forbidden' })
    }
    const config = readConfig()
    const { idle_timeout_minutes } = req.body
    if (idle_timeout_minutes !== undefined) {
      const mins = parseInt(idle_timeout_minutes, 10)
      if (isNaN(mins) || mins < 2 || mins > 480) {
        return res.status(400).json({ error: 'El tiempo debe estar entre 2 y 480 minutos' })
      }
      config.idle_timeout_minutes = mins
    }
    try { writeConfig(config) } catch (e) {
      return res.status(500).json({ error: `Error guardando: ${e.message}` })
    }
    return res.status(200).json(config)
  }

  res.status(405).json({ error: 'Method not allowed' })
}
