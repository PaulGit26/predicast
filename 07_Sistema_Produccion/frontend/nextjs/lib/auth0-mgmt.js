const DOMAIN = process.env.AUTH0_DOMAIN
const API_BASE = `https://${DOMAIN}/api/v2`

async function getToken() {
  const res = await fetch(`https://${DOMAIN}/oauth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_id: process.env.AUTH0_MGMT_CLIENT_ID,
      client_secret: process.env.AUTH0_MGMT_CLIENT_SECRET,
      audience: `https://${DOMAIN}/api/v2/`,
      grant_type: 'client_credentials',
    }),
  })
  const data = await res.json()
  if (!data.access_token) throw new Error('Failed to get Management API token')
  return data.access_token
}

async function mgmt(path, options = {}) {
  const token = await getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  })
  if (res.status === 204) return null
  return res.json()
}

export async function listRoles() {
  return mgmt('/roles?per_page=50')
}

export async function listUsers() {
  const [users, roles] = await Promise.all([
    mgmt('/users?per_page=50&include_totals=false&fields=user_id,email,name,picture,last_login,created_at,blocked'),
    listRoles(),
  ])

  const usersWithRoles = await Promise.all(
    users.map(async (user) => {
      const userRoles = await mgmt(`/users/${encodeURIComponent(user.user_id)}/roles`)
      return { ...user, roles: Array.isArray(userRoles) ? userRoles : [] }
    })
  )

  return { users: usersWithRoles, allRoles: Array.isArray(roles) ? roles : [] }
}

export async function createUser(email, password, name) {
  return mgmt('/users', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      name: name || email.split('@')[0],
      connection: 'Username-Password-Authentication',
      email_verified: false,
    }),
  })
}

export async function deleteUser(userId) {
  return mgmt(`/users/${encodeURIComponent(userId)}`, { method: 'DELETE' })
}

export async function setUserRole(userId, roleId) {
  const current = await mgmt(`/users/${encodeURIComponent(userId)}/roles`)
  if (Array.isArray(current) && current.length > 0) {
    await mgmt(`/users/${encodeURIComponent(userId)}/roles`, {
      method: 'DELETE',
      body: JSON.stringify({ roles: current.map((r) => r.id) }),
    })
  }
  if (roleId) {
    await mgmt(`/users/${encodeURIComponent(userId)}/roles`, {
      method: 'POST',
      body: JSON.stringify({ roles: [roleId] }),
    })
  }
}
