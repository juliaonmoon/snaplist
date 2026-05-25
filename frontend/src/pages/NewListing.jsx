import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const STEPS = ['Photo', 'Details', 'Platforms', 'Price', 'Post']

const DEFAULT_PLATFORMS = ['Facebook', 'Kijiji']

export default function NewListing() {
  const navigate = useNavigate()
  const [step, setStep]         = useState(0)
  const [photoFile, setPhotoFile] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisError, setAnalysisError] = useState(null)
  const [analysisMeta, setAnalysisMeta] = useState(null)

  // Listing fields — pre-filled by AI or manually entered
  const [title, setTitle]             = useState('')
  const [category, setCategory]       = useState('')
  const [condition, setCondition]     = useState('good')
  const [condDesc, setCondDesc]       = useState('')
  const [description, setDescription] = useState('')
  const [quantity, setQuantity]       = useState(1)

  // Platform & pricing
  const [availPlatforms, setAvailPlatforms] = useState([])
  const [platforms, setPlatforms]   = useState(['facebook', 'kijiji'])
  const [priority, setPriority]     = useState('balanced')
  const [shipping, setShipping]     = useState('both')
  const [price, setPrice]           = useState('')
  const [fees, setFees]             = useState([])
  const [currency, setCurrency]     = useState('CAD')
  const [postResults, setPostResults] = useState([])
  const [createdListingId, setCreatedListingId] = useState(null)
  const [posting, setPosting]       = useState(false)

  useEffect(() => {
    api.platforms.available()
      .then(data => {
        setAvailPlatforms(data.platforms || [])
        setCurrency(data.region?.currency || 'CAD')
      })
      .catch(() => {
        setAvailPlatforms([
          { id: 'facebook', name: 'Facebook Marketplace' },
          { id: 'kijiji',   name: 'Kijiji' },
          { id: 'ebay',     name: 'eBay CA' },
          { id: 'craigslist', name: 'Craigslist' },
          { id: 'etsy',     name: 'Etsy' },
        ])
      })
  }, [])

  function togglePlatform(id) {
    setPlatforms(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  async function handlePhoto(e) {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoFile(file)
    setPhotoPreview(URL.createObjectURL(file))
    setAnalyzing(true)
    setAnalysisError(null)
    try {
      const result = await api.analyze.photo(file, priority, platforms[0] || 'facebook')
      setAnalysisMeta({
        brand: result.brand,
        model: result.model,
        identified_product: result.identified_product,
        identification_confidence: result.identification_confidence,
        official_specs: result.official_specs,
        original_product_url: result.original_product_url,
        msrp_original: result.msrp_original,
        product_summary: result.product_summary,
      })
      setTitle(result.title || '')
      setCategory(result.category || '')
      setCondition(result.condition || 'good')
      setCondDesc(result.condition_description || '')
      // Backend builds a clean seller-voice description; fall back to notes if missing.
      setDescription(result.seller_description || result.notes || '')
      setStep(1)
    } catch (err) {
      setAnalysisError('AI analysis failed — enter details manually below.')
      setStep(1)
    } finally {
      setAnalyzing(false)
    }
  }

  async function fetchFees() {
    if (!price || platforms.length === 0) return
    try {
      const data = await api.platforms.feeEstimate(platforms, parseFloat(price), shipping === 'shipping_only' ? 15 : 0)
      setFees(data)
    } catch {
      // show no fees if backend is down
    }
  }

  async function handlePost() {
    setPosting(true)
    try {
      // 1. Create the listing
      const listing = await api.listings.create({
        user_id: 1,
        title, category, condition,
        condition_description: condDesc,
        description,
        quantity: Number(quantity),
        priority,
        shipping_preference: shipping,
      })
      // 2. Publish it
      await api.listings.publish(listing.id)
      setCreatedListingId(listing.id)

      // 3. Post to each platform
      const results = await api.platforms.post(listing.id, platforms)
      setPostResults(results)
    } catch (err) {
      setPostResults([{ platform: 'error', success: false, message: err.message }])
    } finally {
      setPosting(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button onClick={() => step > 0 ? setStep(s => s - 1) : navigate('/')}
            style={{ background: 'none', border: 'none', fontSize: 22, cursor: 'pointer', marginBottom: 4 }}>←</button>
          <h1>New Listing</h1>
        </div>
      </div>

      {/* Step indicator */}
      <div style={{ display: 'flex', gap: 4, padding: '0 16px 20px' }}>
        {STEPS.map((s, i) => (
          <div key={s} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <div style={{ width: '100%', height: 4, borderRadius: 99, background: i <= step ? '#22c55e' : '#e2e8f0' }}/>
            <span style={{ fontSize: 10, color: i === step ? '#22c55e' : '#94a3b8', fontWeight: i === step ? 700 : 400 }}>{s}</span>
          </div>
        ))}
      </div>

      {/* ── Step 0: Photo ── */}
      {step === 0 && (
        <>
          <label className="upload-zone" htmlFor="photo-input">
            {photoPreview
              ? <img src={photoPreview} style={{ width: '100%', maxHeight: 220, objectFit: 'contain', borderRadius: 12 }} />
              : (<><div className="icon">📸</div><p style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>Tap to take a photo</p><p>Or choose from your library</p></>)
            }
          </label>
          <input id="photo-input" type="file" accept="image/*" capture="environment" style={{ display: 'none' }} onChange={handlePhoto} />

          {analyzing && (
            <div className="card" style={{ textAlign: 'center', background: '#f0fdf4', borderColor: '#bbf7d0' }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>🤖</div>
              <div style={{ fontWeight: 600 }}>AI is analyzing your photo…</div>
              <div style={{ fontSize: 13, color: '#15803d', marginTop: 4 }}>Identifying item, condition &amp; keywords</div>
            </div>
          )}

          <div style={{ padding: '0 16px' }}>
            <button className="btn btn-outline" onClick={() => setStep(1)}>Skip — enter details manually</button>
          </div>
        </>
      )}

      {/* ── Step 1: Details ── */}
      {step === 1 && (
        <>
          {title && !analysisError && (
            <div className="card" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#15803d', marginBottom: 4 }}>✨ AI filled this in from your photo</div>
              <div style={{ fontSize: 13, color: '#15803d' }}>Review and edit anything below</div>
            </div>
          )}
          {analysisMeta?.identified_product && (
            <div className="card" style={{ background: '#eff6ff', borderColor: '#bfdbfe' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1e40af', marginBottom: 4 }}>
                🔎 Identified: {analysisMeta.identified_product}
                {analysisMeta.identification_confidence && (
                  <span style={{ marginLeft: 8, fontSize: 11, fontWeight: 500, color: '#64748b' }}>
                    confidence: {analysisMeta.identification_confidence}
                  </span>
                )}
              </div>
              {analysisMeta.product_summary && (
                <div style={{ fontSize: 12, color: '#334155', marginBottom: 4 }}>{analysisMeta.product_summary}</div>
              )}
              {analysisMeta.msrp_original && (
                <div style={{ fontSize: 12, color: '#334155' }}>Original retail: ${analysisMeta.msrp_original}</div>
              )}
              {analysisMeta.original_product_url && (
                <div style={{ fontSize: 12, marginTop: 4 }}>
                  <a href={analysisMeta.original_product_url} target="_blank" rel="noreferrer" style={{ color: '#1d4ed8' }}>
                    View original product page →
                  </a>
                </div>
              )}
            </div>
          )}
          {analysisError && (
            <div className="card" style={{ background: '#fef3c7', borderColor: '#fde68a' }}>
              <div style={{ fontSize: 13, color: '#92400e' }}>⚠ {analysisError}</div>
            </div>
          )}

          <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { label: 'Title', val: title, set: setTitle, multi: false },
              { label: 'Category', val: category, set: setCategory, multi: false },
              { label: 'Condition', val: condition, set: setCondition, multi: false },
              { label: 'Condition notes', val: condDesc, set: setCondDesc, multi: true },
              { label: 'Description', val: description, set: setDescription, multi: true },
            ].map(f => (
              <div key={f.label}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 5 }}>{f.label}</div>
                {f.multi
                  ? <textarea className="input" value={f.val} onChange={e => f.set(e.target.value)} rows={3} style={{ resize: 'none' }} />
                  : <input className="input" value={f.val} onChange={e => f.set(e.target.value)} />
                }
              </div>
            ))}
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 5 }}>Quantity</div>
              <input className="input" type="number" value={quantity} onChange={e => setQuantity(e.target.value)} min={1} style={{ width: 100 }} />
            </div>
          </div>

          <div style={{ padding: '16px 16px 0' }}>
            <button className="btn btn-primary" onClick={() => setStep(2)} disabled={!title}>Continue →</button>
          </div>
        </>
      )}

      {/* ── Step 2: Platforms ── */}
      {step === 2 && (
        <>
          <div className="section-label">Where do you want to list?</div>
          <div className="platform-chips">
            {availPlatforms.map(p => (
              <button key={p.id} className={`platform-chip ${platforms.includes(p.id) ? 'selected' : ''}`} onClick={() => togglePlatform(p.id)}>
                {p.name}
              </button>
            ))}
          </div>

          <div className="section-label">Shipping preference</div>
          <div className="priority-row">
            {[['pickup_only','📍 Pickup'],['both','↔️ Both'],['shipping_only','📦 Ship']].map(([val, label]) => (
              <button key={val} className={`priority-btn ${shipping === val ? 'active' : ''}`} onClick={() => setShipping(val)}>{label}</button>
            ))}
          </div>

          <div className="section-label">Selling priority</div>
          <div className="priority-row">
            {[['speed','⚡ Fast sale'],['balanced','⚖️ Balanced'],['price','💰 Max profit']].map(([val, label]) => (
              <button key={val} className={`priority-btn ${priority === val ? 'active' : ''}`} onClick={() => setPriority(val)}>{label}</button>
            ))}
          </div>

          <div style={{ padding: '8px 16px 0' }}>
            <button className="btn btn-primary" onClick={() => { setStep(3); fetchFees() }} disabled={platforms.length === 0}>
              Research Prices →
            </button>
          </div>
        </>
      )}

      {/* ── Step 3: Price ── */}
      {step === 3 && (
        <>
          <div className="card" style={{ background: '#f0fdf4', borderColor: '#bbf7d0' }}>
            <div style={{ fontWeight: 600, marginBottom: 6 }}>🤖 AI Recommendation</div>
            <div style={{ fontSize: 13, color: '#15803d', lineHeight: 1.5 }}>
              Set your price below. Similar items sell for <strong>{currency} $60–$130</strong> in your area.
              {priority === 'speed' && ' Priced lower = faster sale.'}
              {priority === 'price' && ' Priced higher = more profit.'}
            </div>
          </div>

          <div style={{ padding: '0 16px 16px' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 8 }}>Your asking price ({currency})</div>
            <input
              className="input"
              type="number"
              value={price}
              onChange={e => setPrice(e.target.value)}
              onBlur={fetchFees}
              placeholder="e.g. 95"
              style={{ fontSize: 22, fontWeight: 700, marginBottom: 16 }}
            />

            {fees.length > 0 && (
              <table className="fee-table">
                <thead><tr><th>Platform</th><th>Fee</th><th>Shipping</th><th>You get</th></tr></thead>
                <tbody>
                  {fees.map(f => (
                    <tr key={f.platform}>
                      <td>{f.display_name}</td>
                      <td>{currency} {f.platform_fee.toFixed(2)}</td>
                      <td>{currency} {f.shipping_cost.toFixed(2)}</td>
                      <td className="profit">{currency} {f.net_profit.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div style={{ padding: '0 16px' }}>
            <button className="btn btn-primary" onClick={() => setStep(4)} disabled={!price}>Post it →</button>
          </div>
        </>
      )}

      {/* ── Step 4: Post ── */}
      {step === 4 && (
        <>
          {postResults.length === 0 ? (
            <div style={{ padding: '20px 16px', textAlign: 'center' }}>
              <div style={{ fontSize: 56, marginBottom: 12 }}>🎉</div>
              <h2 style={{ fontSize: 20, marginBottom: 8 }}>Ready to post!</h2>
              <p style={{ color: '#64748b', fontSize: 14, lineHeight: 1.5, marginBottom: 24 }}>
                eBay posts automatically. For other platforms, we'll open a pre-filled listing for you.
              </p>
              <button className="btn btn-primary" onClick={handlePost} disabled={posting}>
                {posting ? 'Posting…' : 'Confirm & Post'}
              </button>
            </div>
          ) : (
            <>
              <div style={{ padding: '20px 16px 8px', textAlign: 'center' }}>
                <div style={{ fontSize: 48, marginBottom: 8 }}>✅</div>
                <h2 style={{ fontSize: 20 }}>Listing created!</h2>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '8px 16px' }}>
                {postResults.map(r => (
                  <div key={r.platform} className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: 0 }}>
                    <div>
                      <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{r.platform}</div>
                      <div style={{ fontSize: 12, color: r.success ? '#22c55e' : '#64748b' }}>{r.message}</div>
                    </div>
                    {r.url && (
                      <a href={r.url} target="_blank" rel="noreferrer">
                        <button className="btn btn-primary btn-sm" style={{ width: 'auto' }}>Open →</button>
                      </a>
                    )}
                    {!r.url && r.success && <span className="badge badge-green">Done</span>}
                    {!r.success && r.platform !== 'error' && <span className="badge badge-gray">Pending</span>}
                  </div>
                ))}
              </div>
              <div style={{ padding: '16px' }}>
                <button className="btn btn-outline" onClick={() => navigate('/')}>← Back to Dashboard</button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
