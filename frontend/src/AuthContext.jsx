import { createContext, useContext, useEffect, useState } from 'react'
import { onAuthStateChanged } from 'firebase/auth'
import { auth, configured } from './firebase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  // undefined = loading, null = not logged in, object = logged in
  const [user, setUser] = useState(undefined)

  useEffect(() => {
    if (!configured) {
      // No Firebase: treat existing snaplist_onboarded flag as a local "user"
      const onboarded = localStorage.getItem('snaplist_onboarded')
      setUser(onboarded ? { uid: 'local', displayName: null, email: null, photoURL: null } : null)
      return
    }
    return onAuthStateChanged(auth, firebaseUser => setUser(firebaseUser ?? null))
  }, [])

  function isOnboarded(u) {
    if (!u) return false
    if (u.uid === 'local') return Boolean(localStorage.getItem('snaplist_onboarded'))
    // Accept either the scoped key or the legacy key (migration path)
    return Boolean(
      localStorage.getItem(`snaplist_onboarded_${u.uid}`) ||
      localStorage.getItem('snaplist_onboarded')
    )
  }

  function setOnboarded(u) {
    if (!u) return
    if (u.uid === 'local') {
      localStorage.setItem('snaplist_onboarded', '1')
    } else {
      localStorage.setItem(`snaplist_onboarded_${u.uid}`, '1')
      localStorage.removeItem('snaplist_onboarded') // clean up legacy key
    }
  }

  function clearOnboarded(u) {
    if (!u) return
    localStorage.removeItem('snaplist_onboarded')
    if (u.uid !== 'local') localStorage.removeItem(`snaplist_onboarded_${u.uid}`)
  }

  return (
    <AuthContext.Provider value={{ user, isOnboarded, setOnboarded, clearOnboarded }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
