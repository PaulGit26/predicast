import { getServerSession } from 'next-auth/next'
import { authOptions } from '../../auth/[...nextauth]'
import { deleteUser, setUserRole, updateUser, sendPasswordResetTicket } from '../../../../lib/auth0-mgmt'

export default async function handler(req, res) {
  let session
  try { session = await getServerSession(req, res, authOptions) } catch (e) {
    return res.status(500).json({ error: `Error de autenticación: ${e.message}` })
  }
  if (!session?.roles?.includes('admin')) {
    return res.status(403).json({ error: 'Forbidden' })
  }

  const { id } = req.query

  if (req.method === 'DELETE') {
    if (session.auth0Id === id) {
      return res.status(400).json({ error: 'No puedes eliminar tu propia cuenta' })
    }
    try {
      await deleteUser(id)
      return res.status(204).end()
    } catch (e) {
      return res.status(500).json({ error: e.message })
    }
  }

  if (req.method === 'PATCH') {
    const { roleId, name, email, blocked, password, sendResetEmail } = req.body
    try {
      if (name !== undefined) {
        if (!name.trim()) return res.status(400).json({ error: 'El nombre no puede estar vacío' })
        await updateUser(id, { name: name.trim() })
      }
      if (email !== undefined) {
        if (!email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
          return res.status(400).json({ error: 'Correo electrónico inválido' })
        }
        await updateUser(id, { email: email.trim(), email_verified: false })
      }
      if (blocked !== undefined) {
        await updateUser(id, { blocked: Boolean(blocked) })
      }
      if (password !== undefined) {
        if (password.length < 8) return res.status(400).json({ error: 'La contraseña debe tener al menos 8 caracteres' })
        await updateUser(id, { password, connection: 'Username-Password-Authentication' })
      }
      if (sendResetEmail) {
        const ticket = await sendPasswordResetTicket(id)
        if (ticket?.ticket) return res.status(200).json({ ok: true, resetUrl: ticket.ticket })
        throw new Error('No se pudo generar el enlace de recuperación')
      }
      if (roleId !== undefined) {
        await setUserRole(id, roleId)
      }
      return res.status(200).json({ ok: true })
    } catch (e) {
      return res.status(500).json({ error: e.message })
    }
  }

  res.status(405).end()
}
