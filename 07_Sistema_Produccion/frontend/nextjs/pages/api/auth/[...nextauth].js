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
          audience: process.env.AUTH0_API_AUDIENCE,
          scope: 'openid profile email',
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      // Persist the Auth0 access_token so it can be sent to the backend API
      if (account) {
        token.accessToken = account.access_token
      }
      return token
    },
    async session({ session, token }) {
      // Expose access token on the client session
      session.accessToken = token.accessToken
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
}

export default NextAuth(authOptions)
