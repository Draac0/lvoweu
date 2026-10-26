import createClient, { type Middleware } from 'openapi-fetch'
import type { paths } from '@/api/schema'

const TOKEN_KEY = 'wind-forecast-token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

let onUnauthorized = () => {}

/** Register what to do when the server rejects our token (e.g. it expired). */
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler
}

const auth: Middleware = {
  onRequest({ request }) {
    const token = tokenStore.get()
    if (token) request.headers.set('Authorization', `Bearer ${token}`)
    return request
  },
  onResponse({ response }) {
    if (response.status === 401 && !response.url.endsWith('/auth/login')) {
      tokenStore.clear()
      onUnauthorized()
    }
    return response
  },
}

export const api = createClient<paths>()
api.use(auth)

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** Turn openapi-fetch's { data, error } result into data or a thrown ApiError. */
export async function unwrap<T>(
  call: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await call
  if (data !== undefined) return data
  const detail = (error as { detail?: unknown } | undefined)?.detail
  const message = typeof detail === 'string' ? detail : `Request failed (${response.status})`
  throw new ApiError(response.status, message)
}
