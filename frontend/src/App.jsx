import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './AuthContext'
import Dashboard from './pages/Dashboard'
import NewListing from './pages/NewListing'
import ListingDetail from './pages/ListingDetail'
import Profile from './pages/Profile'
import Onboarding from './pages/Onboarding'
import Login from './pages/Login'
import './index.css'

function BottomNav() {
  const navigate = useNavigate()
  const location = useLocation()
  const path = location.pathname
  if (path === '/onboarding' || path === '/login') return null

  return (
    <nav className="bottom-nav">
      <button className={`nav-item ${path === '/' ? 'active' : ''}`} onClick={() => navigate('/')}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
          <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
        </svg>
        Dashboard
      </button>
      <button className={`nav-item ${path === '/new' ? 'active' : ''}`} onClick={() => navigate('/new')}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="9"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
        </svg>
        Sell
      </button>
      <button className={`nav-item ${path === '/profile' ? 'active' : ''}`} onClick={() => navigate('/profile')}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
        </svg>
        Profile
      </button>
    </nav>
  )
}

function AppRoutes() {
  const { user, isOnboarded } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    if (user === undefined) return // still loading auth state

    if (!user) {
      if (location.pathname !== '/login') navigate('/login', { replace: true })
      return
    }

    if (!isOnboarded(user)) {
      if (location.pathname !== '/onboarding') navigate('/onboarding', { replace: true })
      return
    }

    if (location.pathname === '/login' || location.pathname === '/onboarding') {
      navigate('/', { replace: true })
    }
  }, [user, location.pathname])

  if (user === undefined) return null

  return (
    <>
      <Routes>
        <Route path="/login"       element={<Login />} />
        <Route path="/onboarding"  element={<Onboarding />} />
        <Route path="/"            element={<Dashboard />} />
        <Route path="/new"         element={<NewListing />} />
        <Route path="/listing/:id" element={<ListingDetail />} />
        <Route path="/profile"     element={<Profile />} />
      </Routes>
      <BottomNav />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app">
          <AppRoutes />
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}
