import { getServerSession } from 'next-auth/next'
import { authOptions } from '../../auth/[...nextauth]'
import { deleteUser, setUserRole, updateUser } from '../../../../lib/auth0-mgmt'

export default async function handler(req, res) {
  const session = await getServerSession(req, res, authOptions)
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
    const { roleId, name } = req.body
    try {
      if (name !== undefined) {
        if (!name.trim()) return res.status(400).json({ error: 'El nombre no puede estar vacío' })
        await updateUser(id, { name: name.trim() })
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
