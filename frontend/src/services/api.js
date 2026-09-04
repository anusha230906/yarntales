import { resolveAsset } from './assets'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000').replace(/\/$/, '')
const USE_BACKEND = import.meta.env.VITE_USE_BACKEND !== 'false'

const getToken = () => localStorage.getItem('yarntales-token') || ''

const getUserId = (user) => user?.userId || user?.id || ''

const normalizeUser = (user) => ({
  ...user,
  id: user?.userId || user?.id,
})

export const normalizeProduct = (product) => ({
  ...product,
  id: String(product?._id || product?.productId || product?.id),
  price: Number(product?.basePrice ?? product?.price ?? 0),
  colors: product?.availableColors || product?.colors || [],
  category: product?.category || product?.categoryName || 'Handmade',
  image: resolveAsset(product?.images?.[0] || product?.image),
  gallery: (product?.images?.length ? product.images : [product?.image]).filter(Boolean).map(resolveAsset),
  rating: Number(product?.rating ?? 4.9),
  reviews: Number(product?.reviews ?? 12),
})

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
  })

  let data
  try {
    data = await response.json()
  } catch {
    data = {}
  }

  if (!response.ok) {
    throw new Error(data.message || `Request failed (${response.status})`)
  }

  return data
}

export async function signUp(payload) {
  if (!USE_BACKEND) throw new Error('Backend integration is disabled.')
  const data = await request('/api/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  if (data.token) localStorage.setItem('yarntales-token', data.token)
  return { ...data, user: normalizeUser(data.user) }
}

export async function signIn(payload) {
  if (!USE_BACKEND) throw new Error('Backend integration is disabled.')
  const data = await request('/api/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
  if (data.token) localStorage.setItem('yarntales-token', data.token)
  return { ...data, user: normalizeUser(data.user) }
}

export async function getProfile() {
  const data = await request('/api/profile')
  return normalizeUser(data.user)
}

export async function getProducts() {
  const data = await request('/api/products')
  return (data.products || []).map(normalizeProduct)
}

export async function getCart(userId) {
  const data = await request(`/api/cart/${encodeURIComponent(userId)}`)
  return data.cart || []
}

export async function addCartItem({ userId, productId, quantity = 1, customizationId = null }) {
  return request('/api/cart', {
    method: 'POST',
    body: JSON.stringify({ userId, productId, quantity, customizationId }),
  })
}

export async function updateCartItem(userId, productId, quantity) {
  return request(`/api/cart/${encodeURIComponent(userId)}/${encodeURIComponent(productId)}`, {
    method: 'PUT',
    body: JSON.stringify({ quantity }),
  })
}

export async function removeCartItem(userId, productId) {
  return request(`/api/cart/${encodeURIComponent(userId)}/${encodeURIComponent(productId)}`, {
    method: 'DELETE',
  })
}

export async function clearCart(userId) {
  return request(`/api/cart/${encodeURIComponent(userId)}`, { method: 'DELETE' })
}

export async function getWishlist(userId) {
  const data = await request(`/api/wishlist/${encodeURIComponent(userId)}`)
  return data.wishlist || []
}

export async function addWishlistItem(userId, productId) {
  return request('/api/wishlist', {
    method: 'POST',
    body: JSON.stringify({ userId, productId }),
  })
}

export async function removeWishlistItem(userId, productId) {
  return request(`/api/wishlist/${encodeURIComponent(userId)}/${encodeURIComponent(productId)}`, {
    method: 'DELETE',
  })
}

export async function createCustomization(payload) {
  return request('/api/customizations', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getCustomizationTemplate() {
  const data = await request('/api/customizations/template')
  return normalizeProduct(data.product)
}

export async function getCustomizations(userId) {
  const data = await request(`/api/customizations/user/${encodeURIComponent(userId)}`)
  return data.customizations || []
}

export async function createGiftRequest(payload) {
  return request('/api/gift-mode', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getGiftRequests(userId) {
  const data = await request(`/api/gift-mode/user/${encodeURIComponent(userId)}`)
  return data.giftRequests || []
}

export async function createOrder(payload) {
  return request('/api/orders', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getOrders(userId) {
  const data = await request(`/api/orders/user/${encodeURIComponent(userId)}`)
  return data.orders || []
}

export async function getOrderTracking(orderId) {
  return request(`/api/orders/${encodeURIComponent(orderId)}/tracking`)
}

export async function getFeed() {
  const data = await request('/api/feed')
  return data.feed || []
}

export function clearSession() {
  localStorage.removeItem('yarntales-token')
}

export { getUserId }
