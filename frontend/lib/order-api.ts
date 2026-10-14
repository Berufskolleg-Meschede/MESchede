import type { OrderPageData, OrderOverview, OrderType, RunReview, ReviewResult, OrderStatus, OrderRunView } from './types'

export class OrderApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
    this.name = 'OrderApiError'
  }
}

/** Transportiert ausschließlich echte Auftragsdaten; ein Quellenfehler aktiviert keine Demodaten. */
export class OrderApiClient {
  constructor(
    private readonly baseUrl = '/api/mes',
    private readonly transport: typeof fetch = (...args) => fetch(...args),
  ) {}

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await this.transport(`${this.baseUrl}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
      cache: 'no-store',
    })
    if (!response.ok) {
      const body = await response.json().catch(() => null)
      const detail = typeof body?.detail === 'string' ? body.detail :
        response.status === 422 ? 'Die Laufangaben sind ungültig. Bitte die Mengen prüfen.' :
        'Die Auftragsdaten konnten nicht geladen werden. Bitte erneut versuchen.'
      throw new OrderApiError(detail, response.status)
    }
    return response.json()
  }

  list(
    type: OrderType,
    options: { offset?: number; search?: string; status?: OrderStatus | 'all' } = {},
    signal?: AbortSignal,
  ): Promise<OrderPageData> {
    const parameters = new URLSearchParams({
      offset: String(options.offset ?? 0), limit: '50', search: options.search ?? '',
    })
    if (options.status && options.status !== 'all') { parameters.set('status', options.status) }
    return this.request(`/${type === 'production' ? 'productionorder' : 'deliveryorder'}/?${parameters}`, { signal })
  }

  overview(signal?: AbortSignal): Promise<OrderOverview> {
    return this.request('/orders/overview', { signal })
  }

  detail(type: OrderType, orderId: string): Promise<OrderRunView> {
    return this.request(`/${type === 'production' ? 'productionorder' : 'deliveryorder'}/${encodeURIComponent(orderId)}`)
  }

  review(runId: string, data: RunReview): Promise<ReviewResult> {
    return this.request(`/orders/runs/${encodeURIComponent(runId)}/reviews`, {
      method: 'POST', body: JSON.stringify(data),
    })
  }
}

export const api = new OrderApiClient()
