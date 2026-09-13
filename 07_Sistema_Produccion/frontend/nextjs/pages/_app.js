import { SessionProvider, signOut, useSession } from 'next-auth/react'
import { useState, useEffect, useRef, useCallback } from 'react'

// aviso 2 min antes, pero no más del 50% del timeout total
const warnBeforeMs = (timeoutMs) => Math.min(2 * 60 * 1000, Math.floor(timeoutMs * 0.5))
const DEFAULT_TIMEOUT_MS = 30 * 60 * 1000

function IdleWatcher() {
  const { data: session } = useSession()
  const [timeoutMs, setTimeoutMs] = useState(DEFAULT_TIMEOUT_MS)
  const [showWarning, setShowWarning] = useState(false)
  const [secondsLeft, setSecondsLeft] = useState(120)
  const timerRef = useRef(null)
  const warnRef = useRef(null)
  const countRef = useRef(null)
  const warningActiveRef = useRef(false)

  // Carga el timeout configurado desde el servidor
  useEffect(() => {
    fetch('/api/admin/config')
      .then(r => r.json())
      .then(d => {
        if (d.idle_timeout_minutes) {
          setTimeoutMs(d.idle_timeout_minutes * 60 * 1000)
        }
      })
      .catch(() => {})
  }, [])

  const logout = useCallback(() => {
    signOut({ callbackUrl: '/auth/login' })
  }, [])

  const reset = useCallback(() => {
    warningActiveRef.current = false
    setShowWarning(false)
    clearTimeout(timerRef.current)
    clearTimeout(warnRef.current)
    clearInterval(countRef.current)

    const warnMs = warnBeforeMs(timeoutMs)
    const warnAt = timeoutMs - warnMs
    warnRef.current = setTimeout(() => {
      warningActiveRef.current = true
      setSecondsLeft(Math.round(warnMs / 1000))
      setShowWarning(true)
      countRef.current = setInterval(() => {
        setSecondsLeft(s => {
          if (s <= 1) { clearInterval(countRef.current); return 0 }
          return s - 1
        })
      }, 1000)
    }, warnAt > 0 ? warnAt : timeoutMs)

    timerRef.current = setTimeout(logout, timeoutMs)
  }, [timeoutMs, logout])

  // Re-armar timer cuando cambia el timeoutMs
  useEffect(() => {
    if (!session) return
    const events = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll']
    const handler = () => { if (!warningActiveRef.current) reset() }
    events.forEach(e => window.addEventListener(e, handler, { passive: true }))
    reset()
    return () => {
      events.forEach(e => window.removeEventListener(e, handler))
      clearTimeout(timerRef.current)
      clearTimeout(warnRef.current)
      clearInterval(countRef.current)
    }
  }, [session, reset])

  if (!showWarning) return null

  const mins = Math.floor(secondsLeft / 60)
  const secs = secondsLeft % 60
  const display = mins > 0
    ? `${mins}:${String(secs).padStart(2, '0')} min`
    : `${secs} seg`

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: 'rgba(15,23,42,0.65)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(3px)',
    }}>
      <div style={{
        background: 'white', borderRadius: 12, padding: '36px 40px', maxWidth: 420, width: '90%',
        boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
        textAlign: 'center', fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ fontSize: 40, marginBottom: 12 }}>⏱️</div>
        <h2 style={{ margin: '0 0 10px', fontSize: 18, color: '#1e293b', fontWeight: 700 }}>
          Sesión por expirar
        </h2>
        <p style={{ margin: '0 0 6px', fontSize: 14, color: '#64748b', lineHeight: 1.5 }}>
          Por inactividad, tu sesión se cerrará en:
        </p>
        <div style={{
          fontSize: 36, fontWeight: 800, color: secondsLeft <= 30 ? '#ef4444' : '#f59e0b',
          margin: '12px 0', fontVariantNumeric: 'tabular-nums', letterSpacing: -1,
          transition: 'color 0.3s',
        }}>
          {display}
        </div>
        <p style={{ margin: '0 0 24px', fontSize: 13, color: '#94a3b8' }}>
          Haz clic en continuar para mantener la sesión activa.
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
          <button
            onClick={reset}
            style={{
              padding: '10px 28px', background: '#1a237e', color: 'white',
              border: 'none', borderRadius: 7, cursor: 'pointer',
              fontWeight: 700, fontSize: 14,
            }}
          >
            Continuar sesión
          </button>
          <button
            onClick={logout}
            style={{
              padding: '10px 20px', background: 'white', color: '#64748b',
              border: '1px solid #e2e8f0', borderRadius: 7, cursor: 'pointer',
              fontWeight: 600, fontSize: 14,
            }}
          >
            Cerrar sesión
          </button>
        </div>
      </div>
    </div>
  )
}

export default function App({ Component, pageProps: { session, ...pageProps } }) {
  return (
    <SessionProvider session={session}>
      <IdleWatcher />
      <Component {...pageProps} />
    </SessionProvider>
  )
}
