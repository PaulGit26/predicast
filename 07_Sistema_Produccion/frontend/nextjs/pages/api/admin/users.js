import { getServerSession } from 'next-auth/next'
import { authOptions } from '../auth/[...nextauth]'
import { listUsers, createUser } from '../../../lib/auth0-mgmt'

export default async function handler(req, res) {
  const session = await getServerSession(req, res, authOptions)
  if (!session?.roles?.includes('admin')) {
    return res.status(403).json({ error: 'Forbidden' })
  }

  if (req.method === 'GET') {
    try {
      const data = await listUsers()
      return res.status(200).json(data)
    } catch (e) {
      return res.status(500).json({ error: e.message })
    }
  }

  if (req.method === 'POST') {
    const { email, password, name } = req.body
    if (!email || !password) {
      return res.status(400).json({ error: 'Email y contraseña son requeridos' })
    }
    try {
      const user = await createUser(email, password, name)
      if (user.statusCode >= 400) {
        return res.status(user.statusCode).json({ error: user.message })
      }
      return res.status(201).json(user)
    } catch (e) {
      return res.status(500).json({ error: e.message })
    }
  }

  res.status(405).end()
}
