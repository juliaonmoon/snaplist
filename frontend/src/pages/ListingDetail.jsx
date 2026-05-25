import { useNavigate, useParams } from 'react-router-dom'

const DETAIL = {
  1: { emoji: '🛋️', title: 'Blue Sectional Couch', price: '$280', days: 3, platforms: ['Facebook', 'Kijiji'], condition: 'Good', category: 'Furniture', qty: 1, status: 'Active' },
  2: { emoji: '🌿', title: 'Lawn Mower (Honda)', price: '$120', days: 14, platforms: ['Facebook', 'eBay'], condition: 'Good', category: 'Yard & Garden', qty: 1, status: 'Price Alert' },
}

export default function ListingDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const item = DETAIL[id] || DETAIL[1]

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button onClick={() => navigate('/')} style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', marginBottom: 4 }}>←</button>
          <h1 style={{ fontSize: 20 }}>{item.title}</h1>
        </div>
        <span className={`badge ${item.status === 'Active' ? 'badge-green' : 'badge-amber'}`}>{item.status}</span>
      </div>

      <div style={{ fontSize: 80, textAlign: 'center', padding: '8px 0 16px', background: '#f1f5f9', margin: '0 16px', borderRadius: 16 }}>
        {item.emoji}
      </div>

      <div className="stats-row" style={{ marginTop: 12 }}>
        <div className="stat-box"><div className="val">{item.price}</div><div className="lbl">Your Price</div></div>
        <div className="stat-box"><div className="val">{item.days}d</div><div className="lbl">Listed</div></div>
        <div className="stat-box"><div className="val">{item.qty}</div><div className="lbl">In Stock</div></div>
      </div>

      <div className="section-label">Listed On</div>
      <div className="platform-chips">
        {item.platforms.map(p => <span key={p} className="platform-chip selected">{p}</span>)}
      </div>

      <div className="section-label">Details</div>
      <div className="card">
        {[['Condition', item.condition], ['Category', item.category], ['Qty available', item.qty]].map(([k, v]) => (
          <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
            <span style={{ color: '#64748b', fontSize: 14 }}>{k}</span>
            <span style={{ fontWeight: 600, fontSize: 14 }}>{v}</span>
          </div>
        ))}
      </div>

      <div className="section-label">Actions</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '0 16px' }}>
        <button className="btn btn-primary">Mark as Sold</button>
        <button className="btn btn-outline">Edit Listing</button>
        <button className="btn btn-outline" style={{ color: '#ef4444', borderColor: '#fecaca' }}>Archive</button>
      </div>
    </div>
  )
}
