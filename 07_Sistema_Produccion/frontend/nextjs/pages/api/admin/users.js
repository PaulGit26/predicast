import { getServerSession } from 'next-auth/next'
import { authOptions } from '../auth/[...nextauth]'
import { listUsers, createUser } from '../../../lib/auth0-mgmt'

export default async function handler(req, res) {
  let session
  try { session = await getServerSession(req, res, authOptions) } catch (e) {
    return res.status(500).json({ error: `Error de autenticación: ${e.message}` })
  }
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
      if (user?.statusCode >= 400) {
        const statusCode = user.statusCode
        let mensaje = user.message || 'Error al crear usuario'
        if (statusCode === 409 || /already exists/i.test(mensaje)) {
          mensaje = `El correo ${email} ya está registrado. Usa otro correo o recupera la contraseña del usuario existente.`
        } else if (statusCode === 400 && /password/i.test(mensaje)) {
          mensaje = 'La contraseña no cumple los requisitos de seguridad de Auth0.'
        }
        return res.status(statusCode).json({ error: mensaje })
      }
      return res.status(201).json(user)
    } catch (e) {
      return res.status(500).json({ error: e.message })
    }
  }

  res.status(405).end()
}
