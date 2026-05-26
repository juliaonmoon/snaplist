import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const STEPS = ['Welcome', 'Profile', 'eBay', 'Etsy', 'Defaults', 'Done']

export default function Onboarding() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [saving, setSaving] = useState(false)
  const [ebayConnected, setEbayConnected] = useState(false)
  const [ebayConnecting, setEbayConnecting] = useState(false)

  const [showLogin, setShowLogin] = useState(false)
  const [loginEmail, setLoginEmail] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  const [form, setForm] = useState({
    name: '',
    email: '',
    location: '',
    pickup_location: '',
    default_priority: 'balanced',
    default_shipping_preference: 'both',
    default_markdown_percent: 10,
    default_markdown_days: 14,
    default_floor_price: 0,
    notification_email: '',
  })

  function set(field, val) { setForm(f => ({ ...f, [field]: val })) }

  function canAdvanceProfile() {
    return form.name.trim() && form.email.trim() && form.location.trim() && form.pickup_location.trim()
  }

  function missingProfileFields() {
    const missing = []
    if (!form.name.trim()) missing.push('Full name')
    if (!form.email.trim()) missing.push('Email')
    if (!form.location.trim()) missing.push('City & province')
    if (!form.pickup_location.trim()) missing.push('Pickup location')
    return missing
  }

  async function finish() {
    setSaving(true)
    try {
      await api.profile.create({ ...form, notification_email: form.notification_email || form.email })
    } catch { /* profile may already exist — continue anyway */ }
    localStorage.setItem('snaplist_onboarded', '1')
    localStorage.setItem('snaplist_user_email', form.email)
    setSaving(false)
    navigate('/')
  }

  async function handleLogin() {
    const email = loginEmail.trim().toLowerCase()
    if (!email) return
    setLoginLoading(true)
    setLoginError('')
    try {
      const stored = localStorage.getItem('snaplist_user_email')
      if (stored && stored.toLowerCase() === email) {
        localStorage.setItem('snaplist_onboarded', '1')
        navigate('/')
        return
      }
      const profile = await api.profile.get(1)
      if (profile?.email?.toLowerCase() === email) {
        localStorage.setItem('snaplist_onboarded', '1')
        localStorage.setItem('snaplist_user_email', profile.email)
        navigate('/')
        return
      }
      setLoginError('No account found with that email.')
    } catch {
      setLoginError('Could not reach the server. Check your connection.')
    } finally {
      setLoginLoading(false)
    }
  }

  function simulateEbayOAuth() {
    setEbayConnecting(true)
    // In production this opens the real eBay OAuth URL.
    // For now, simulate the redirect + callback.
    setTimeout(() => { setEbayConnecting(false); setEbayConnected(true) }, 2000)
  }

  const progress = (step / (STEPS.length - 1)) * 100

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column', background: '#f8fafc', maxWidth: 430, margin: '0 auto' }}>

      {/* Progress bar */}
      {step > 0 && step < STEPS.length - 1 && (
        <div style={{ height: 4, background: '#e2e8f0', position: 'fixed', top: 0, left: '50%', transform: 'translateX(-50%)', width: '100%', maxWidth: 430, zIndex: 200 }}>
          <div style={{ height: '100%', background: '#22c55e', width: `${progress}%`, transition: 'width .4s ease' }} />
        </div>
      )}

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '60px 24px 40px' }}>

        {/* ── Step 0: Welcome ── */}
        {step === 0 && !showLogin && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 72, marginBottom: 16 }}>📸</div>
            <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 10 }}>Welcome to SnapList</h1>
            <p style={{ fontSize: 16, color: '#64748b', lineHeight: 1.6, marginBottom: 40 }}>
              Snap a photo of anything you want to sell. AI writes the listing. You approve. Auto-post to eBay & Etsy — one-click fill for Facebook & Kijiji.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                ['📸', 'One photo → complete listing'],
                ['🤖', 'AI sets the title, price & description'],
                ['🛍️', 'Auto-posts to eBay & Etsy (when connected)'],
                ['🧩', 'One-click fill for Facebook & Kijiji via Chrome extension'],
                ['📬', 'Daily digest keeps everything on track'],
              ].map(([icon, text]) => (
                <div key={text} style={{ display: 'flex', alignItems: 'center', gap: 14, background: 'white', borderRadius: 12, padding: '12px 16px', border: '1px solid #e2e8f0', textAlign: 'left' }}>
                  <span style={{ fontSize: 22 }}>{icon}</span>
                  <span style={{ fontSize: 14, fontWeight: 500 }}>{text}</span>
                </div>
              ))}
            </div>
            <button className="btn btn-primary" style={{ marginTop: 32 }} onClick={() => setStep(1)}>
              Get started →
            </button>
            <button className="btn btn-outline" style={{ marginTop: 12 }} onClick={() => setShowLogin(true)}>
              Log in
            </button>
          </div>
        )}

        {/* ── Login view (shown from step 0) ── */}
        {step === 0 && showLogin && (
          <div>
            <button onClick={() => { setShowLogin(false); setLoginError('') }}
              style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', marginBottom: 16 }}>←</button>
            <div style={{ fontSize: 40, marginBottom: 12 }}>👋</div>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>Welcome back</h2>
            <p style={{ fontSize: 14, color: '#64748b', marginBottom: 28, lineHeight: 1.5 }}>
              Enter the email you used when you set up SnapList.
            </p>
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 6 }}>Email</div>
              <input
                className="input"
                type="email"
                placeholder="you@email.com"
                value={loginEmail}
                onChange={e => setLoginEmail(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleLogin()}
                autoFocus
              />
            </div>
            {loginError && (
              <div style={{ fontSize: 13, color: '#dc2626', marginBottom: 12 }}>{loginError}</div>
            )}
            <button className="btn btn-primary" onClick={handleLogin} disabled={loginLoading || !loginEmail.trim()}>
              {loginLoading ? 'Checking…' : 'Log in →'}
            </button>
            <div style={{ marginTop: 20, fontSize: 13, color: '#94a3b8', textAlign: 'center' }}>
              New here?{' '}
              <button style={{ background: 'none', border: 'none', color: '#22c55e', fontWeight: 600, cursor: 'pointer', fontSize: 13 }}
                onClick={() => { setShowLogin(false); setLoginError('') }}>
                Get started instead
              </button>
            </div>
          </div>
        )}

        {/* ── Step 1: Profile ── */}
        {step === 1 && (
          <div>
            <div style={{ fontSize: 40, marginBottom: 12 }}>👤</div>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>Your profile</h2>
            <p style={{ fontSize: 14, color: '#64748b', marginBottom: 28, lineHeight: 1.5 }}>
              Set this once. Used to target the right local marketplaces and keep your home address private.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                { label: 'Full name', field: 'name', type: 'text', placeholder: 'Julia Cheng' },
                { label: 'Email', field: 'email', type: 'email', placeholder: 'you@email.com' },
                { label: 'City & province', field: 'location', type: 'text', placeholder: 'Surrey, BC, Canada' },
              ].map(({ label, field, type, placeholder }) => (
                <div key={field}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 6 }}>{label}</div>
                  <input className="input" type={type} placeholder={placeholder}
                    value={form[field]} onChange={e => set(field, e.target.value)} />
                </div>
              ))}

              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 4 }}>Preferred pickup location</div>
                <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 6 }}>🔒 Never your home address unless you choose it</div>
                <input className="input" type="text" placeholder='e.g. "Tim Hortons on 152nd St, Surrey"'
                  value={form.pickup_location} onChange={e => set('pickup_location', e.target.value)} />
              </div>
            </div>

            {!canAdvanceProfile() && (
              <div style={{ marginTop: 20, fontSize: 12, color: '#dc2626' }}>
                Please fill in: {missingProfileFields().join(', ')}
              </div>
            )}
            <button className="btn btn-primary"
              style={{
                marginTop: 12,
                opacity: canAdvanceProfile() ? 1 : 0.5,
                cursor: canAdvanceProfile() ? 'pointer' : 'not-allowed',
              }}
              onClick={() => canAdvanceProfile() && setStep(2)}
              disabled={!canAdvanceProfile()}>
              Continue →
            </button>
          </div>
        )}

        {/* ── Step 2: eBay ── */}
        {step === 2 && (
          <div>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🛍️</div>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>Connect eBay</h2>
            <p style={{ fontSize: 14, color: '#64748b', marginBottom: 8, lineHeight: 1.5 }}>
              eBay is the only marketplace that lets SnapList post <strong>fully automatically</strong> — no tapping required.
            </p>

            <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 12, padding: '14px 16px', marginBottom: 16, fontSize: 13, color: '#92400e', lineHeight: 1.6 }}>
              ⏳ <strong>eBay developer approval pending.</strong> Real auto-posting unlocks once eBay grants API access. Skip this step for now — you can connect later from Profile.
            </div>

            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12, padding: '14px 16px', marginBottom: 24, fontSize: 13, color: '#64748b', lineHeight: 1.6 }}>
              When connected, SnapList will:<br/>
              • Post listings directly to eBay CA<br/>
              • Detect when items sell automatically<br/>
              • Update prices when you approve markdowns
            </div>

            <button className="btn btn-primary" onClick={() => setStep(3)}>
              Skip — connect later in Profile →
            </button>
          </div>
        )}

        {/* ── Step 3: Etsy ── */}
        {step === 3 && (
          <div>
            <div style={{ fontSize: 40, marginBottom: 12 }}>🎨</div>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>Etsy — coming in v0.2</h2>
            <p style={{ fontSize: 14, color: '#64748b', marginBottom: 8, lineHeight: 1.5 }}>
              Etsy auto-posting (handmade, vintage, craft supplies) ships in the next release. You'll be able to connect it later from your Profile.
            </p>

            <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: 12, padding: '12px 16px', marginBottom: 24, fontSize: 13, color: '#92400e' }}>
              ℹ️ When live: Etsy charges $0.20 per listing + 6.5% transaction fee.
            </div>

            <button className="btn btn-primary" onClick={() => setStep(4)}>
              Continue →
            </button>
          </div>
        )}

        {/* ── Step 4: Defaults ── */}
        {step === 4 && (
          <div>
            <div style={{ fontSize: 40, marginBottom: 12 }}>⚙️</div>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>Your selling style</h2>
            <p style={{ fontSize: 14, color: '#64748b', marginBottom: 28, lineHeight: 1.5 }}>
              These are your defaults — you can override them for any individual item.
            </p>

            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>What matters most to you?</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  ['speed',    '⚡ Sell fast',     'Price a bit lower, sell in days not weeks'],
                  ['balanced', '⚖️ Balanced',       'Good price, reasonable timeline'],
                  ['price',    '💰 Maximum profit', 'Price higher, wait for the right buyer'],
                ].map(([val, label, desc]) => (
                  <button key={val} onClick={() => set('default_priority', val)}
                    style={{
                      padding: '14px 16px', borderRadius: 12, textAlign: 'left', cursor: 'pointer',
                      border: `2px solid ${form.default_priority === val ? '#22c55e' : '#e2e8f0'}`,
                      background: form.default_priority === val ? '#f0fdf4' : 'white',
                    }}>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{label}</div>
                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: 24 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>How do you prefer to sell?</div>
              <div style={{ display: 'flex', gap: 8 }}>
                {[['pickup_only','📍 Pickup only'],['both','↔️ Both'],['shipping_only','📦 Ship only']].map(([val, label]) => (
                  <button key={val} className={`priority-btn ${form.default_shipping_preference === val ? 'active' : ''}`}
                    onClick={() => set('default_shipping_preference', val)}>{label}</button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: 28 }}>
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>Auto-price drop rule</div>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 10 }}>If an item doesn't sell, drop the price automatically</div>
              <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: 12, padding: 16 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', fontSize: 14 }}>
                  <span>Drop by</span>
                  <input className="input" type="number" value={form.default_markdown_percent}
                    onChange={e => set('default_markdown_percent', e.target.value)} style={{ width: 60 }} />
                  <span>% every</span>
                  <input className="input" type="number" value={form.default_markdown_days}
                    onChange={e => set('default_markdown_days', e.target.value)} style={{ width: 60 }} />
                  <span>days</span>
                </div>
              </div>
            </div>

            <button className="btn btn-primary" onClick={() => { finish(); setStep(5) }} disabled={saving}>
              {saving ? 'Setting up…' : 'Finish setup →'}
            </button>
          </div>
        )}

        {/* ── Step 5: Done ── */}
        {step === 5 && (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 72, marginBottom: 16 }}>🎉</div>
            <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 10 }}>You're all set!</h2>
            <p style={{ fontSize: 15, color: '#64748b', lineHeight: 1.6, marginBottom: 32 }}>
              Tap the <strong>+</strong> button on the dashboard, snap a photo, and SnapList takes it from there.
            </p>
            <button className="btn btn-primary" onClick={() => navigate('/')}>
              Go to Dashboard →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
