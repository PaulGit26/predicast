export { default } from 'next-auth/middleware'

// Protect all routes except login, error, and public API paths
export const config = {
  matcher: ['/((?!auth|api/auth|_next/static|_next/image|favicon.ico).*)'],
}
