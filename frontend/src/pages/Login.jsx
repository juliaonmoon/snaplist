import { useState } from 'react'
import { signInWithPopup, GoogleAuthProvider, FacebookAuthProvider } from 'firebase/auth'
import { auth, configured } from '../firebase'

export default function Login() {
  const [loading, setLoading] = useState(null) // 'google' | 'facebook' | null
  const [error, setError] = useState(null)

  async function signIn(provider) {
    setLoading(provider)
    setError(null)
    try {
      const p = provider === 'google' ? new GoogleAuthProvider() : new FacebookAuthProvider()
      await signInWithPopup(auth, p)
      // AuthContext's onAuthStateChanged fires → App.jsx routes to / or /onboarding
    } catch (e) {
      if (e.code !== 'auth/popup-closed-by-user') setError(e.message)
      setLoading(null)
    }
  }

  if (!configured) {
    return (
      <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 32, background: '#f8fafc', maxWidth: 430, margin: '0 auto' }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>🔧</div>
        <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12, textAlign: 'center' }}>Firebase not configured</h2>
        <p style={{ fontSize: 14, color: '#64748b', textAlign: 'center', lineHeight: 1.6 }}>
          Add your Firebase project keys to <code style={{ background: '#f1f5f9', padding: '1px 5px', borderRadius: 4 }}>frontend/.env</code> to enable Google and Facebook login.
          See <code style={{ background: '#f1f5f9', padding: '1px 5px', borderRadius: 4 }}>frontend/.env.example</code> for the required <code style={{ background: '#f1f5f9', padding: '1px 5px', borderRadius: 4 }}>VITE_FIREBASE_*</code> variables.
        </p>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 24px 48px', background: '#f8fafc', maxWidth: 430, margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>📸</div>
        <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 8 }}>SnapList</h1>
        <p style={{ fontSize: 16, color: '#64748b' }}>Sign in to continue</p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <button
          onClick={() => signIn('google')}
          disabled={Boolean(loading)}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
            padding: '14px 20px', borderRadius: 12, border: '1.5px solid #e2e8f0',
            background: 'white', fontSize: 15, fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading && loading !== 'google' ? 0.5 : 1,
            transition: 'opacity .15s',
          }}
        >
          <GoogleIcon />
          {loading === 'google' ? 'Signing in…' : 'Continue with Google'}
        </button>

        <button
          onClick={() => signIn('facebook')}
          disabled={Boolean(loading)}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
            padding: '14px 20px', borderRadius: 12, border: 'none',
            background: '#1877F2', color: 'white', fontSize: 15, fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading && loading !== 'facebook' ? 0.5 : 1,
            transition: 'opacity .15s',
          }}
        >
          <FacebookIcon />
          {loading === 'facebook' ? 'Signing in…' : 'Continue with Facebook'}
        </button>
      </div>

      {error && (
        <div style={{ marginTop: 20, padding: '12px 14px', background: '#fee2e2', borderRadius: 10, fontSize: 13, color: '#991b1b', lineHeight: 1.5 }}>
          {error}
        </div>
      )}
    </div>
  )
}

function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 48 48">
      <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"/>
      <path fill="#FF3D00" d="m6.306 14.691l6.571 4.819C14.655 15.108 19.001 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C16.318 4 9.656 8.337 6.306 14.691z"/>
      <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"/>
      <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002l6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"/>
    </svg>
  )
}

function FacebookIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  )
}
