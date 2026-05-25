import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const EMOJI = { furniture: '🛋️', electronics: '📷', clothing: '👟', tools: '🔧', sports: '⛳', default: '📦' }
function itemEmoji(category) {
  if (!category) return EMOJI.default
  const c = category.toLowerCase()
  if (c.includes('furn')) return EMOJI.furniture
  if (c.includes('electr') || c.includes('camera') || c.includes('phone')) return EMOJI.electronics
  if (c.includes('cloth') || c.includes('shoe') || c.includes('foot')) return EMOJI.clothing
  if (c.includes('tool') || c.includes('yard') || c.includes('garden')) return EMOJI.tools
  if (c.includes('sport')) return EMOJI.sports
  return EMOJI.default
}

// Fallback mock data shown when backend isn't running yet
const MOCK = [
  { id: 1, title: 'Blue Sectional Couch',    category: 'furniture',    platform_listings: [{list_price:280}], status:'active', days_listed: 3  },
  { id: 2, title: 'Lawn Mower (Honda)',       category: 'tools',        platform_listings: [{list_price:120}], status:'active', days_listed: 14 },
  { id: 3, title: 'Dining Table + 4 Chairs', category: 'furniture',    platform_listings: [{list_price:200}], status:'active', days_listed: 7  },
  { id: 4, title: 'Canon DSLR Camera Kit',   category: 'electronics',  platform_listings: [{list_price:385}], status:'active', days_listed: 1  },
  { id: 5, title: 'Nike Air Max — Size 9',   category: 'clothing',     platform_listings: [{list_price:95}],  status:'active', days_listed: 5  },
]

function statusBadge(listing) {
  if (listing.status === 'sold')     return { label: '✅ Sold',         cls: 'badge-green' }
  if ((listing.days_listed || 0) >= 14) return { label: '⚠ Price Alert', cls: 'badge-amber' }
  return { label: 'Active', cls: 'badge-green' }
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [listings, setListings] = useState(MOCK)
  const [loading, setLoading]   = useState(true)
  const [earned, setEarned]     = useState(1140)
  const [unread, setUnread]     = useState(2)
  const [usingMock, setUsingMock] = useState(false)

  useEffect(() => {
    api.listings.list(1)
      .then(data => {
        if (data && data.length > 0) {
          const enriched = data.map(l => ({
            ...l,
            days_listed: l.listed_at
              ? Math.floor((Date.now() - new Date(l.listed_at)) / 86400000)
              : 0,
          }))
          setListings(enriched)
          const total = data.filter(l => l.status === 'sold')
            .flatMap(l => l.platform_listings || [])
            .reduce((s, pl) => s + (pl.net_profit || 0), 0)
          setEarned(Math.round(total) || 1140)
        } else {
          setUsingMock(true)
        }
      })
      .catch(() => setUsingMock(true))
      .finally(() => setLoading(false))

    api.notifications.list(true)
      .then(data => setUnread(data?.length ?? 2))
      .catch(() => {})
  }, [])

  const active = listings.filter(l => l.status === 'active').length
  const avgDays = listings.length
    ? (listings.reduce((s, l) => s + (l.days_listed || 0), 0) / listings.length).toFixed(1)
    : '—'

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>SnapList</h1>
          <p>Good morning, Julia 👋</p>
        </div>
        <div style={{ position: 'relative', cursor: 'pointer' }} onClick={() => {}}>
          <span style={{ fontSize: 26 }}>🔔</span>
          {unread > 0 && (
            <span style={{
              position: 'absolute', top: 0, right: 0,
              width: 10, height: 10, background: '#ef4444',
              borderRadius: '50%', border: '2px solid white'
            }}/>
          )}
        </div>
      </div>

      <div className="stats-row">
        <div className="stat-box"><div className="val">{active}</div><div className="lbl">Active</div></div>
        <div className="stat-box"><div className="val" style={{ color: '#22c55e' }}>C${earned.toLocaleString()}</div><div className="lbl">Earned</div></div>
        <div className="stat-box"><div className="val">{avgDays}d</div><div className="lbl">Avg. Sell</div></div>
      </div>

      {usingMock && (
        <div className="card" style={{ background: '#fef3c7', borderColor: '#fde68a', marginBottom: 0 }}>
          <div style={{ fontSize: 13, color: '#92400e' }}>
            ⚠ Backend not connected — showing sample data. Start the API server to see real listings.
          </div>
        </div>
      )}

      {!usingMock && unread > 0 && (
        <div className="card" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <span style={{ fontSize: 20 }}>📬</span>
            <div>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Daily Digest — {unread} action{unread > 1 ? 's' : ''} needed</div>
              <div style={{ fontSize: 13, color: '#15803d' }}>Review your price recommendations</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
            <button className="btn btn-primary btn-sm" style={{ flex: 1 }}>Review</button>
            <button className="btn btn-outline btn-sm" style={{ flex: 1 }}>Later</button>
          </div>
        </div>
      )}

      <div className="section-label">Active Listings</div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 40, color: '#94a3b8' }}>Loading…</div>
      ) : (
        <div style={{ background: 'white', borderRadius: 16, margin: '0 16px', overflow: 'hidden', border: '1px solid var(--border)' }}>
          {listings.map((l, i) => {
            const badge = statusBadge(l)
            const price = l.platform_listings?.[0]?.list_price ?? '—'
            return (
              <div
                key={l.id}
                className="listing-item"
                style={{ cursor: 'pointer', borderBottom: i < listings.length - 1 ? undefined : 'none' }}
                onClick={() => navigate(`/listing/${l.id}`)}
              >
                <div className="listing-thumb">{itemEmoji(l.category)}</div>
                <div className="listing-info">
                  <div className="listing-title">{l.title}</div>
                  <div className="listing-meta">{l.days_listed ?? 0}d listed</div>
                  <span className={`badge ${badge.cls}`} style={{ marginTop: 5 }}>{badge.label}</span>
                </div>
                <div className="listing-price">{typeof price === 'number' ? `C$${price}` : price}</div>
              </div>
            )
          })}
        </div>
      )}

      <button className="fab" onClick={() => navigate('/new')}>+</button>
    </div>
  )
}
