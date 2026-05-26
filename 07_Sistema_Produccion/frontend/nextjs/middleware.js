export { default } from 'next-auth/middleware'

// Protect all routes except public ones
export const config = {
  matcher: [
    '/((?!api/auth|auth/login|auth/error|_next/static|_next/image|favicon.ico).*)',
  ],
}
