import NextAuth from 'next-auth'
import Auth0Provider from 'next-auth/providers/auth0'

export const authOptions = {
  providers: [
    Auth0Provider({
      clientId: process.env.AUTH0_CLIENT_ID,
      clientSecret: process.env.AUTH0_CLIENT_SECRET,
      issuer: `https://${process.env.AUTH0_DOMAIN}`,
      authorization: {
        params: {
          scope: 'openid profile email',
        },
      },
      httpOptions: { timeout: 10000 },
    }),
  ],
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account) {
        token.accessToken = account.access_token
      }
      if (profile) {
        token.roles = profile['https://predicast/roles'] ?? []
        token.auth0Id = profile.sub
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken
      session.roles = token.roles ?? []
      session.auth0Id = token.auth0Id
      return session
    },
  },
  pages: {
    signIn: '/auth/login',
    error:  '/auth/error',
  },
  session: {
    strategy: 'jwt',
    maxAge: 24 * 60 * 60, // 24 hours
  },
  trustHost: true,
}

const handler = NextAuth(authOptions)

export default async function auth(req, res) {
  // Auth0 manda error_description="user is blocked" cuando la cuenta está bloqueada.
  // NextAuth lo pierde al mapear todo a OAuthCallback — lo interceptamos aquí.
  const isCallback = req.query.nextauth?.[0] === 'callback'
  if (isCallback && req.query.error) {
    const desc = (req.query.error_description ?? '').toLowerCase()
    if (desc.includes('blocked')) {
      return res.redirect('/auth/login?error=AccountBlocked')
    }
  }
  return handler(req, res)
}
