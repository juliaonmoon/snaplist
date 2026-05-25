import { useState, useEffect } from 'react'
import { api } from '../api'

const USER_ID = 1

export default function Profile() {
  const [profile, setProfile] = useState(null)
  const [saving, setSaving]   = useState(false)
  const [saved, setSaved]     = useState(false)
  const [form, setForm]       = useState({
    name: 'Julia Cheng',
    email: 'juliaonmoon@gmail.com',
    location: 'Surrey, BC, Canada',
    pickup_location: 'Tim Hortons on 152nd St, Surrey',
    default_priority: 'balanced',
    default_shipping_preference: 'both',
    default_markdown_percent: 10,
    default_markdown_days: 14,
    default_floor_price: 0,
    notification_email: 'juliaonmoon@gmail.com',
  })

  useEffect(() => {
    api.profile.get(USER_ID)
      .then(data => { setProfile(data); setForm(f => ({ ...f, ...data })) })
      .catch(() => {}) // use defaults if backend not running
  }, [])

  function set(field, val) { setForm(f => ({ ...f, [field]: val })) }

  async function save() {
    setSaving(true)
    try {
      if (profile) {
        await api.profile.update(USER_ID, form)
      } else {
        await api.profile.create(form)
      }
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } catch { }
    setSaving(false)
  }

  return (
    <div className="page">
      <div className="page-header">
        <div><h1>Profile</h1><p>Your selling preferences</p></div>
      </div>

      <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div className="avatar">{form.name?.[0] ?? 'J'}</div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 18 }}>{form.name}</div>
          <div style={{ fontSize: 13, color: '#64748b' }}>{form.location}</div>
          <div style={{ fontSize: 13, color: '#22c55e', marginTop: 2 }}>{form.email}</div>
        </div>
      </div>

      <div className="section-label">Pickup Location</div>
      <div style={{ padding: '0 16px 16px' }}>
        <input className="input" value={form.pickup_location} onChange={e => set('pickup_location', e.target.value)} />
        <div style={{ fontSize: 12, color: '#64748b', marginTop: 6 }}>🔒 Your home address is never shared</div>
      </div>

      <div className="section-label">Default Selling Priority</div>
      <div className="priority-row">
        {[['speed','⚡ Fast'],['balanced','⚖️ Balanced'],['price','💰 Max Price']].map(([val, label]) => (
          <button key={val} className={`priority-btn ${form.default_priority === val ? 'active' : ''}`}
            onClick={() => set('default_priority', val)}>{label}</button>
        ))}
      </div>

      <div className="section-label">Default Shipping</div>
      <div className="priority-row">
        {[['pickup_only','📍 Pickup'],['both','↔️ Both'],['shipping_only','📦 Ship']].map(([val, label]) => (
          <button key={val} className={`priority-btn ${form.default_shipping_preference === val ? 'active' : ''}`}
            onClick={() => set('default_shipping_preference', val)}>{label}</button>
        ))}
      </div>

      <div className="section-label">Auto-Markdown Rule</div>
      <div className="card">
        <div style={{ fontSize: 13, color: '#64748b', marginBottom: 10 }}>Drop price automatically if unsold</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 10, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 13 }}>Drop by</span>
          <input className="input" type="number" value={form.default_markdown_percent}
            onChange={e => set('default_markdown_percent', e.target.value)} style={{ width: 66 }} />
          <span style={{ fontSize: 13 }}>% every</span>
          <input className="input" type="number" value={form.default_markdown_days}
            onChange={e => set('default_markdown_days', e.target.value)} style={{ width: 66 }} />
          <span style={{ fontSize: 13 }}>days</span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 13, whiteSpace: 'nowrap' }}>Never below C$</span>
          <input className="input" type="number" value={form.default_floor_price}
            onChange={e => set('default_floor_price', e.target.value)} style={{ width: 80 }} />
        </div>
      </div>

      <div className="section-label">Connected Platforms</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '0 16px 16px' }}>
        {[
          { name: 'eBay CA',              status: 'pending',     icon: '🛍️', note: 'API approval pending' },
          { name: 'Facebook Marketplace', status: 'browser',     icon: '📘', note: 'Browser pre-fill' },
          { name: 'Kijiji',              status: 'browser',     icon: '🍁', note: 'Browser pre-fill' },
          { name: 'Craigslist',          status: 'browser',     icon: '📋', note: 'Browser pre-fill' },
          { name: 'Etsy', status: 'soon', icon: '🎨', note: 'OAuth ships in v0.2' },
        ].map(p => (
          <div key={p.name} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: 0, padding: '12px 14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 22 }}>{p.icon}</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{p.name}</div>
                <div style={{ fontSize: 12, color: p.status === 'browser' ? '#22c55e' : '#94a3b8' }}>
                  {p.status === 'browser' ? '✅ ' : p.status === 'pending' ? '⏳ ' : p.status === 'soon' ? '🚧 ' : '— '}{p.note}
                </div>
              </div>
            </div>
            {p.status === 'soon' && (
              <button className="btn btn-sm" disabled style={{ width: 'auto', background: '#e2e8f0', color: '#94a3b8', cursor: 'not-allowed', border: 'none' }}>Coming soon</button>
            )}
          </div>
        ))}
      </div>

      <div className="section-label">Notification Email</div>
      <div style={{ padding: '0 16px 16px' }}>
        <input className="input" type="email" value={form.notification_email}
          onChange={e => set('notification_email', e.target.value)} />
      </div>

      <div style={{ padding: '0 16px 8px' }}>
        <button className="btn btn-primary" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : saved ? '✅ Saved!' : 'Save Profile'}
        </button>
      </div>

      <div style={{ padding: '16px' }}>
        <button
          className="btn"
          onClick={() => {
            if (!confirm('Log out of SnapList?')) return
            localStorage.removeItem('snaplist_onboarded')
            window.location.href = '/onboarding'
          }}
          style={{ width: '100%', background: '#fff', color: '#ef4444', border: '1px solid #fecaca' }}
        >
          Log out
        </button>
      </div>
    </div>
  )
}
