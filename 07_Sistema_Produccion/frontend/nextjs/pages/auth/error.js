import { useRouter } from 'next/router'

const ERROR_MESSAGES = {
  Configuration: 'Error de configuración del servidor.',
  AccessDenied: 'No tienes permiso para acceder a esta aplicación.',
  Verification: 'El enlace de verificación ha expirado o ya fue usado.',
  OAuthCallback: 'Error al procesar la respuesta de Auth0.',
  OAuthSignin: 'Error al iniciar sesión con Auth0.',
  Default: 'Ocurrió un error inesperado.',
}

export default function AuthErrorPage() {
  const router = useRouter()
  const { error } = router.query
  const message = ERROR_MESSAGES[error] || ERROR_MESSAGES.Default

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.iconWrapper}>
          <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
            <circle cx="24" cy="24" r="24" fill="#fee2e2" />
            <path d="M24 14v12M24 32v2" stroke="#dc2626" strokeWidth="3" strokeLinecap="round" />
          </svg>
        </div>

        <h1 style={styles.title}>Error de autenticación</h1>
        <p style={styles.message}>{message}</p>

        {error && (
          <p style={styles.code}>Código: {error}</p>
        )}

        <button
          style={styles.button}
          onClick={() => router.push('/auth/login')}
        >
          Volver al inicio de sesión
        </button>
      </div>
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
  iconWrapper: {
    marginBottom: '20px',
    display: 'flex',
    justifyContent: 'center',
  },
  title: {
    fontSize: '22px',
    fontWeight: '700',
    color: '#1a237e',
    margin: '0 0 12px 0',
  },
  message: {
    fontSize: '15px',
    color: '#475569',
    margin: '0 0 8px 0',
    lineHeight: '1.5',
  },
  code: {
    fontSize: '12px',
    color: '#94a3b8',
    margin: '0 0 28px 0',
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
  },
}
