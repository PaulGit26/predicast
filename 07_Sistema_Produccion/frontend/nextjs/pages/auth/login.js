import { signIn, useSession } from 'next-auth/react'
import { useEffect } from 'react'
import { useRouter } from 'next/router'

export default function LoginPage() {
  const { status } = useSession()
  const router = useRouter()
  const { error } = router.query

  useEffect(() => {
    if (status === 'authenticated') {
      router.replace('/')
    }
  }, [status, router])

  if (status === 'loading') {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <Logo />
          <p style={styles.subtitle}>Cargando...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <Logo />
        <h1 style={styles.title}>Predicast</h1>
        <p style={styles.subtitle}>Sistema de Pronóstico de Demanda</p>

        {error && (
          <div style={styles.errorBox}>
            {error === 'OAuthCallback'
              ? 'Error al autenticar con Auth0. Intenta de nuevo.'
              : 'Ocurrió un error. Intenta de nuevo.'}
          </div>
        )}

        <button
          style={styles.button}
          onClick={() => signIn('auth0', { callbackUrl: '/' }, { prompt: 'login' })}
        >
          Iniciar sesión con Auth0
        </button>

        <p style={styles.footer}>
          Acceso restringido — solo usuarios autorizados
        </p>
      </div>
    </div>
  )
}

function Logo() {
  return (
    <div style={styles.logoWrapper}>
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <rect width="48" height="48" rx="12" fill="#1a237e" />
        <path d="M10 34 L18 20 L24 28 L30 16 L38 34" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <circle cx="38" cy="16" r="3" fill="#3b82f6" />
      </svg>
    </div>
  )
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  card: {
    background: 'white',
    borderRadius: '16px',
    padding: '48px 40px',
    width: '100%',
    maxWidth: '400px',
    textAlign: 'center',
    boxShadow: '0 25px 50px rgba(0,0,0,0.4)',
  },
  logoWrapper: {
    marginBottom: '20px',
    display: 'flex',
    justifyContent: 'center',
  },
  title: {
    fontSize: '28px',
    fontWeight: '700',
    color: '#1a237e',
    margin: '0 0 8px 0',
  },
  subtitle: {
    fontSize: '14px',
    color: '#64748b',
    margin: '0 0 32px 0',
  },
  errorBox: {
    background: '#fee2e2',
    border: '1px solid #fca5a5',
    borderRadius: '8px',
    padding: '12px',
    marginBottom: '20px',
    fontSize: '13px',
    color: '#dc2626',
  },
  button: {
    width: '100%',
    padding: '14px',
    background: '#1a237e',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '15px',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background 0.2s',
  },
  footer: {
    marginTop: '24px',
    fontSize: '12px',
    color: '#94a3b8',
  },
}
