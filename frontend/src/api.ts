import type { ChatReply, Product, ProductDetail, ShopOrder, Shopper } from './types.ts'

export async function fetchProducts(size = ''): Promise<Product[]> {
  const query = size ? `?size=${encodeURIComponent(size)}` : ''
  const response = await fetch(`/api/products${query}`)
  if (!response.ok) {
    throw new Error('Could not load the catalogue')
  }
  return response.json()
}

export async function fetchProduct(productId: string): Promise<ProductDetail> {
  const response = await fetch(`/api/products/${encodeURIComponent(productId)}`)
  if (response.status === 404) {
    throw new Error('This product is not in the catalogue')
  }
  if (!response.ok) {
    throw new Error('Could not load this product')
  }
  return response.json()
}

export type AccountInput = {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

async function errorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (
      typeof body === 'object' &&
      body !== null &&
      'detail' in body &&
      typeof body.detail === 'string'
    ) {
      return body.detail
    }
  } catch {
    // The response was not JSON.
  }
  return fallback
}

export async function createAccount(input: AccountInput): Promise<Shopper> {
  const response = await fetch('/api/account', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'Could not create the account'))
  }
  return response.json()
}

export async function login(email: string, password: string, size = ''): Promise<Shopper> {
  const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, size }),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'Could not log in'))
  }
  return response.json()
}

export type ChatHistoryTurn = {
  role: 'user' | 'assistant'
  content: string
}

export type ChatShopperRef = {
  id: number
  email: string
}

export type ChatPageRef = {
  path: string
  product_id: string
}

export type StoredChatMessage = {
  role: 'user' | 'assistant'
  content: string
  products: ChatReply['products']
}

export async function fetchChatHistory(shopper: ChatShopperRef): Promise<StoredChatMessage[]> {
  const response = await fetch('/api/chat/history', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(shopper),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'Could not load your chat.'))
  }
  const body: { messages: StoredChatMessage[] } = await response.json()
  return body.messages
}

export type ResetNote = {
  message: string
  reset_path: string
  email_subject: string
  email_body: string
}

export async function requestPasswordReset(email: string): Promise<ResetNote> {
  const response = await fetch('/api/password/forgot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'Could not prepare a reset link'))
  }
  return response.json()
}

export async function resetPassword(
  token: string,
  password: string,
  confirmPassword: string,
): Promise<void> {
  const response = await fetch('/api/password/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token,
      password,
      confirm_password: confirmPassword,
    }),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'Could not update the password'))
  }
}

export async function placeOrder(
  shopper: ChatShopperRef,
  productId: string,
  size: string,
  color: string,
): Promise<ShopOrder> {
  const response = await fetch('/api/orders', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: shopper.id,
      email: shopper.email,
      product_id: productId,
      size,
      color,
    }),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'Could not buy this item'))
  }
  return response.json()
}

export type ShippedNote = {
  id: number
  status: string
  email_subject: string
  email_body: string
}

export async function shipOrder(shopper: ChatShopperRef, orderId: number): Promise<ShippedNote> {
  const response = await fetch(`/api/orders/${orderId}/ship`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: shopper.id, email: shopper.email }),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'Could not mark this order shipped'))
  }
  return response.json()
}

export async function sendChat(
  message: string,
  history: ChatHistoryTurn[],
  shopper: ChatShopperRef | null,
  page: ChatPageRef,
): Promise<ChatReply> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, shopper, page }),
  })
  if (!response.ok) {
    throw new Error(await errorMessage(response, 'The shop assistant could not answer just now.'))
  }
  return response.json()
}
