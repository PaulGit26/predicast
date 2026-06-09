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

export default NextAuth(authOptions)
