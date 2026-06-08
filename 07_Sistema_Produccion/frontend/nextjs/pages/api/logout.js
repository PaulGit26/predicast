export default function handler(req, res) {
  const domain = process.env.AUTH0_DOMAIN
  const clientId = process.env.AUTH0_CLIENT_ID
  const base = process.env.NEXTAUTH_URL || `http://${req.headers.host}`
  const returnTo = encodeURIComponent(`${base}/auth/login`)
  res.redirect(`https://${domain}/v2/logout?client_id=${clientId}&returnTo=${returnTo}`)
}
