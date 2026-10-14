import {
  ApiValidationError,
  type Article,
  type ProductionOrder,
  type DeliveryOrder,
  type Machine,
  type OrderFormData,
  type Settings,
  type FieldErrorDetail,
  type StorageItem,
  type StorageStatus,
  type LagerSnapshot,
  type AnalyticsRun,
  type OrderOverview,
  type OrderPageData,
  type OrderRunView,
  type OrderType as RunOrderType,
  type OrderStatus as RunOrderStatus,
  type RunReview,
  type ReviewResult,
} from './types'
import { OrderApiClient, OrderApiError } from './order-api'

export { OrderApiClient, OrderApiError }

const orderApi = new OrderApiClient()

const USE_MOCK = true
const BASE_URL = '/api'

// ── Mock data ─────────────────────────────────────────────────────────────────

const MOCK_ARTICLES: Article[] = [
  { id: 1, name: 'Stahlträger A400', description: 'Standardstahlträger 400mm', price: 299.99 },
  { id: 2, name: 'Aluminiumplatte B200', description: 'Aluminiumblech 200×200 mm', price: 89.50 },
  { id: 3, name: 'Verbundrohr C100', description: 'Verbundrohr DN100', price: 45.00 },
  { id: 4, name: 'Kupferleitung D50', description: 'Kupferrohr 50mm', price: 32.75 },
]

let MOCK_PRODUCTION_ORDERS: ProductionOrder[] = [
  { id: 1, quantity: 50, status: 'completed', article_id: 1, article: MOCK_ARTICLES[0] },
  { id: 2, quantity: 25, status: 'in_progress', article_id: 2, article: MOCK_ARTICLES[1] },
  { id: 3, quantity: 100, status: 'pending', article_id: 1, article: MOCK_ARTICLES[0] },
  { id: 4, quantity: 10, status: 'error', article_id: 3, article: MOCK_ARTICLES[2] },
  { id: 5, quantity: 75, status: 'pending', article_id: 2, article: MOCK_ARTICLES[1] },
]

let MOCK_DELIVERY_ORDERS: DeliveryOrder[] = [
  { id: 1, quantity: 30, status: 'completed', article_id: 2, article: MOCK_ARTICLES[1] },
  { id: 2, quantity: 15, status: 'pending', article_id: 1, article: MOCK_ARTICLES[0] },
  { id: 3, quantity: 8, status: 'in_progress', article_id: 3, article: MOCK_ARTICLES[2] },
]

const MOCK_MACHINES: Machine[] = [
  { id: 1, name: 'Fräsmaschine 1', type: 'CNC Fräse', status: 'online' },
  { id: 2, name: 'Schweißroboter A', type: 'Schweißanlage', status: 'online' },
  { id: 3, name: 'Drehmaschine 2', type: 'CNC Drehmaschine', status: 'offline' },
  { id: 4, name: 'Bohrwerk B', type: 'Bohranlage', status: 'online' },
]

let mockIdCounter = 100

// ── Helpers ───────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw await buildApiError(res, path)
  return res.json()
}

async function buildApiError(res: Response, path: string): Promise<ApiValidationError> {
  let message = `API error ${res.status}: ${path}`
  const fieldErrors: Record<string, string> = {}
  try {
    const body = await res.json()
    const detail = body?.detail
    if (Array.isArray(detail)) {
      for (const item of detail as FieldErrorDetail[]) {
        const field = item.loc?.[item.loc.length - 1]
        if (typeof field === 'string') fieldErrors[field] = item.msg
      }
      message = (detail as FieldErrorDetail[]).map(d => d.msg).join(' ') || message
    } else if (typeof detail === 'string') {
      message = detail
    }
  } catch {
    // Response body wasn't JSON; keep the generic message.
  }
  return new ApiValidationError(message, fieldErrors)
}

function resolveArticle(article_id: number): Article | undefined {
  return MOCK_ARTICLES.find(a => a.id === article_id)
}

// ── API object ────────────────────────────────────────────────────────────────

export const api = {
  list: (type: RunOrderType, options?: { offset?: number; search?: string; status?: RunOrderStatus | 'all' }, signal?: AbortSignal): Promise<OrderPageData> =>
    orderApi.list(type, options, signal),
  overview: (signal?: AbortSignal): Promise<OrderOverview> => orderApi.overview(signal),
  detail: (type: RunOrderType, orderId: string): Promise<OrderRunView> => orderApi.detail(type, orderId),
  review: (runId: string, data: RunReview): Promise<ReviewResult> => orderApi.review(runId, data),

  analytics: {
    list: async (filters: { from?: string; to?: string; order_type?: 'production' | 'delivery' }): Promise<AnalyticsRun[]> => {
      const query = new URLSearchParams()
      if (filters.from) query.set('from', filters.from)
      if (filters.to) query.set('to', filters.to)
      if (filters.order_type) query.set('order_type', filters.order_type)
      const queryString = query.toString()
      const response = await fetch(`/api/analytics${queryString ? `?${queryString}` : ''}`, { cache: 'no-store' })
      if (!response.ok) throw new Error(`Analytics API error ${response.status}`)
      return response.json()
    },
  },

  articles: {
    list: async (): Promise<Article[]> => {
      if (USE_MOCK) return MOCK_ARTICLES
      return apiFetch('/article/')
    },
  },

  productionOrders: {
    list: async (): Promise<ProductionOrder[]> => {
      if (USE_MOCK) return [...MOCK_PRODUCTION_ORDERS]
      return apiFetch('/productionorder/')
    },
    create: async (data: OrderFormData): Promise<ProductionOrder> => {
      if (USE_MOCK) {
        const order: ProductionOrder = {
          id: ++mockIdCounter,
          ...data,
          article: resolveArticle(data.article_id),
        }
        MOCK_PRODUCTION_ORDERS = [...MOCK_PRODUCTION_ORDERS, order]
        return order
      }
      return apiFetch('/productionorder/', {
        method: 'POST',
        body: JSON.stringify(data),
      })
    },
    update: async (id: number, data: OrderFormData): Promise<ProductionOrder> => {
      if (USE_MOCK) {
        MOCK_PRODUCTION_ORDERS = MOCK_PRODUCTION_ORDERS.map(o =>
          o.id === id ? { ...o, ...data, article: resolveArticle(data.article_id) } : o
        )
        return MOCK_PRODUCTION_ORDERS.find(o => o.id === id)!
      }
      return apiFetch(`/productionorder/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
    },
    delete: async (id: number): Promise<void> => {
      if (USE_MOCK) {
        MOCK_PRODUCTION_ORDERS = MOCK_PRODUCTION_ORDERS.filter(o => o.id !== id)
        return
      }
      await apiFetch(`/productionorder/${id}`, { method: 'DELETE' })
    },
  },

  deliveryOrders: {
    list: async (): Promise<DeliveryOrder[]> => {
      if (USE_MOCK) return [...MOCK_DELIVERY_ORDERS]
      return apiFetch('/deliveryorder/')
    },
    create: async (data: OrderFormData): Promise<DeliveryOrder> => {
      if (USE_MOCK) {
        const order: DeliveryOrder = {
          id: ++mockIdCounter,
          ...data,
          article: resolveArticle(data.article_id),
        }
        MOCK_DELIVERY_ORDERS = [...MOCK_DELIVERY_ORDERS, order]
        return order
      }
      return apiFetch('/deliveryorder/', {
        method: 'POST',
        body: JSON.stringify(data),
      })
    },
    update: async (id: number, data: OrderFormData): Promise<DeliveryOrder> => {
      if (USE_MOCK) {
        MOCK_DELIVERY_ORDERS = MOCK_DELIVERY_ORDERS.map(o =>
          o.id === id ? { ...o, ...data, article: resolveArticle(data.article_id) } : o
        )
        return MOCK_DELIVERY_ORDERS.find(o => o.id === id)!
      }
      return apiFetch(`/deliveryorder/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      })
    },
    delete: async (id: number): Promise<void> => {
      if (USE_MOCK) {
        MOCK_DELIVERY_ORDERS = MOCK_DELIVERY_ORDERS.filter(o => o.id !== id)
        return
      }
      await apiFetch(`/deliveryorder/${id}`, { method: 'DELETE' })
    },
  },

  machines: {
    list: async (): Promise<Machine[]> => {
      if (USE_MOCK) return MOCK_MACHINES
      return apiFetch('/machine/')
    },
  },

  settings: {
    get: async (): Promise<Settings> => apiFetch('/settings/'),
    update: async (data: Settings): Promise<Settings> =>
      apiFetch('/settings/', {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
  },

  storage: {
    list: async (): Promise<StorageItem[]> => apiFetch('/storage/'),
    status: async (): Promise<StorageStatus> => {
      return apiFetch('/storage/status')
    },
  },

  plcStorage: {
    get: async (): Promise<LagerSnapshot> => apiFetch('/plc-storage/'),
  },
}
