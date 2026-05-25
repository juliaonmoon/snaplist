const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

async function request(method, path, body, isFormData = false) {
  const headers = isFormData ? {} : { 'Content-Type': 'application/json' }
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'API error')
  }
  if (res.status === 204) return null
  return res.json()
}

const get  = (path)        => request('GET',    path)
const post = (path, body)  => request('POST',   path, body)
const patch= (path, body)  => request('PATCH',  path, body)
const del  = (path)        => request('DELETE', path)

// ── Profile ──────────────────────────────────────────────────────────────────
export const api = {
  profile: {
    get:    (id)       => get(`/profile/${id}`),
    create: (data)     => post('/profile/', data),
    update: (id, data) => patch(`/profile/${id}`, data),
  },

  // ── Listings ───────────────────────────────────────────────────────────────
  listings: {
    list:    (userId, status) => {
      const params = new URLSearchParams()
      if (userId) params.set('user_id', userId)
      if (status) params.set('status_filter', status)
      return get(`/listings/?${params}`)
    },
    get:     (id)      => get(`/listings/${id}`),
    create:  (data)    => post('/listings/', data),
    update:  (id, data)=> patch(`/listings/${id}`, data),
    publish: (id)      => post(`/listings/${id}/publish`),
    markSold:(id, platform) => post(`/listings/${id}/sold${platform ? `?platform=${platform}` : ''}`),
    archive: (id)      => del(`/listings/${id}`),
  },

  // ── AI Analysis ────────────────────────────────────────────────────────────
  analyze: {
    photo: (file, priority = 'balanced', platform = 'facebook') => {
      const form = new FormData()
      form.append('photo', file)
      form.append('priority', priority)
      form.append('platform', platform)
      return request('POST', '/analyze/photo', form, true)
    },
  },

  // ── Platforms ──────────────────────────────────────────────────────────────
  platforms: {
    available:   ()          => get('/platforms/available'),
    feeEstimate: (platforms, listPrice, shippingCost = 0) =>
      post('/platforms/fee-estimate', { platforms, list_price: listPrice, shipping_cost: shippingCost }),
    post: (listingId, platforms) =>
      post(`/platforms/post/${listingId}`, platforms),
  },

  // ── Inventory ──────────────────────────────────────────────────────────────
  inventory: {
    forListing:   (listingId) => get(`/inventory/listing/${listingId}`),
    priceHistory: (listingId) => get(`/inventory/price-history/${listingId}`),
  },

  // ── Notifications ──────────────────────────────────────────────────────────
  notifications: {
    list:    (unreadOnly = false) => get(`/notifications/?unread_only=${unreadOnly}`),
    markRead: (id)                => post(`/notifications/${id}/read`),
  },
}
