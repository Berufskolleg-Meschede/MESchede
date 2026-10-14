import type { DispatchStatus, OrderOverview, OrderPageData, OrderRunView, OrderSummary, OrderType, ReviewResult, RunReview, SourceStatus } from '../../lib/types'

export class PreviewError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** Besitzt ausschließlich simulierte Aufträge und Bewertungen im Prozessspeicher. */
export class PreviewOrderStore {
  private orders: OrderRunView[] = []
  private requests = new Map<string, { runId: string; payload: string; result: ReviewResult }>()
  private activeRunId = ''
  private readonly clock: () => Date

  constructor(clock: () => Date = () => new Date()) {
    this.clock = clock
    this.reset()
  }

  reset(): void {
    this.requests.clear()
    const completed = this.createOrder('production', 1001, 1, ['good', 'good', 'good', 'failed'])
    Object.assign(completed, { status: 'completed', run_phase: 'completed', started_at: completed.accepted_at, ended_at: completed.accepted_at })
    const interrupted = this.createOrder('delivery', 2001, 2, ['good', null, null])
    Object.assign(interrupted, { status: 'error', run_phase: 'interrupted', has_manual_review: true, quantity_source: 'manual', good_quantity: 1, error_quantity: 0, processed_quantity: 1 })
    const review = this.createOrder('production', 1002, 3, ['good', 'failed', null, null])
    Object.assign(review, { status: 'review_required', run_phase: 'review_required', review_required: true,
      review_reason: 'Simulierter Wiederanlauf: Bitte Ausgang und bekannte Mengen dieses Testlaufs prüfen.', started_at: review.accepted_at })
    this.orders = [completed, interrupted, review,
      this.createOrder('delivery', 2002, 4, Array(3).fill(null)),
      this.createOrder('production', 1003, 5, Array(5).fill(null)),
      this.createOrder('delivery', 2003, 6, Array(2).fill(null)),
    ]
    this.activeRunId = review.run_id
  }

  overview(): OrderOverview {
    const orders = this.views()
    return structuredClone({
      production: this.summary(orders.filter(item => item.order_type === 'production')),
      delivery: this.summary(orders.filter(item => item.order_type === 'delivery')),
      combined: this.summary(orders), dispatch: this.dispatch(orders),
      sources: { production: this.source(), delivery: this.source() },
      reviews: orders.filter(item => item.review_required), active: orders.filter(item => item.run_id === this.activeRunId),
      waiting: orders.filter(item => item.run_phase === 'queued'), refresh_interval_s: 2, stale_after_s: 10,
    })
  }

  page(kind: OrderType, parameters: URLSearchParams): OrderPageData {
    const overview = this.overview()
    const orders = this.views().filter(item => item.order_type === kind)
    const query = (parameters.get('search') ?? '').trim().toLocaleLowerCase('de-DE')
    const status = parameters.get('status')
    const filtered = orders.filter(item => (!status || item.status === status) && [
      item.order_id, String(item.plc_order_number), ...item.units.flatMap(unit => [unit.product_text, String(unit.product_id)]),
    ].join(' ').toLocaleLowerCase('de-DE').includes(query))
    const offset = Math.max(0, Number(parameters.get('offset') ?? 0) || 0)
    const limit = Math.max(1, Math.min(200, Number(parameters.get('limit') ?? 50) || 50))
    return structuredClone({ orders: filtered.slice(offset, offset + limit), total: orders.length, filtered_total: filtered.length, offset, limit,
      summary: overview[kind], source: overview.sources[kind], dispatch: overview.dispatch, reviews: overview.reviews,
      active: overview.active.filter(item => item.order_type === kind), waiting: overview.waiting.filter(item => item.order_type === kind),
      refresh_interval_s: overview.refresh_interval_s, stale_after_s: overview.stale_after_s })
  }

  detail(kind: OrderType, id: string): OrderRunView {
    const order = this.views().find(item => item.order_type === kind && item.order_id === id)
    if (!order) { throw new PreviewError(404, 'Der Testauftrag ist nicht vorhanden.') }
    return structuredClone(order)
  }

  review(runId: string, request: RunReview): ReviewResult {
    this.validateRequest(request)
    const payload = JSON.stringify({ request_id: request.request_id, expected_version: request.expected_version,
      outcome: request.outcome, good_quantity: request.good_quantity, error_quantity: request.error_quantity })
    const previous = this.requests.get(request.request_id)
    if (previous) {
      if (previous.runId !== runId || previous.payload !== payload) {
        throw new PreviewError(409, 'Die Testanfrage wurde bereits mit anderem Inhalt gespeichert.')
      }
      return structuredClone(previous.result)
    }
    const order = this.orders.find(item => item.run_id === runId)
    if (!order) { throw new PreviewError(404, 'Der Testlauf ist nicht vorhanden.') }
    if (order.version !== request.expected_version || !order.review_required) {
      throw new PreviewError(409, 'Der Testlauf wurde inzwischen geändert. Bitte die Ansicht aktualisieren.')
    }
    this.validateQuantities(order, request)
    order.has_manual_review = true
    order.good_quantity = request.good_quantity ?? this.observed(order, 'good')
    order.error_quantity = request.error_quantity ?? this.observed(order, 'failed')
    order.processed_quantity = order.good_quantity === null || order.error_quantity === null ? null : order.good_quantity + order.error_quantity
    order.quantity_source = request.good_quantity !== null || request.error_quantity !== null ? 'mixed' : 'plc'
    order.review_required = request.outcome === 'unknown'
    order.run_phase = request.outcome === 'unknown' ? 'review_required' : request.outcome
    order.status = order.review_required ? 'review_required' : request.outcome === 'completed' ? 'completed' : 'error'
    order.review_reason = order.review_required ? 'Der simulierte Lauf bleibt unklar.' : null
    order.version += 1
    const result: ReviewResult = { request_id: request.request_id, outcome: request.outcome, good_quantity: request.good_quantity,
      error_quantity: request.error_quantity, run_id: runId, reviewed_at: this.clock().toISOString() }
    this.requests.set(request.request_id, { runId, payload, result })
    return structuredClone(result)
  }

  private validateRequest(request: RunReview): void {
    if (!request || typeof request.request_id !== 'string' || !Number.isInteger(request.expected_version) ||
      !['completed', 'interrupted', 'unknown'].includes(request.outcome)) {
      throw new PreviewError(422, 'Die Testbewertung besitzt keinen gültigen Versionsbezug oder Ausgang.')
    }
    for (const amount of [request.good_quantity, request.error_quantity]) {
      if (amount !== null && (!Number.isSafeInteger(amount) || amount < 0)) {
        throw new PreviewError(422, 'Testmengen müssen nicht negative Ganzzahlen oder unbekannt sein.')
      }
    }
  }

  private validateQuantities(order: OrderRunView, request: RunReview): void {
    const good = this.observed(order, 'good') ?? 0
    const failed = this.observed(order, 'failed') ?? 0
    if ((request.good_quantity !== null && request.good_quantity < good) ||
      (request.error_quantity !== null && request.error_quantity < failed) ||
      (request.good_quantity ?? good) + (request.error_quantity ?? failed) > order.planned_quantity) {
      throw new PreviewError(422, 'Die Testmengen widersprechen den simulierten Ergebnissen oder der Sollmenge.')
    }
  }

  private observed(order: OrderRunView, result: 'good' | 'failed'): number | null {
    return order.units.some(unit => unit.result !== null) ? order.units.filter(unit => unit.result === result).length : null
  }

  private createOrder(kind: OrderType, number: number, sequence: number, results: Array<'good' | 'failed' | null>): OrderRunView {
    const instant = new Date(this.clock().getTime() - (10 - sequence) * 60000).toISOString()
    const units = results.map((result, index) => ({ index, product_id: index % 2 ? 202 : 201,
      product_text: index % 2 ? 'Testplatte B' : 'Teststück A', serial_number: number * 10 + index,
      sequence_number: index + 1, result, raw_status: null, error_code: result === 'failed' ? 7 : result === 'good' ? 0 : null }))
    const observed = results.some(result => result !== null)
    const good = observed ? results.filter(result => result === 'good').length : null
    const failed = observed ? results.filter(result => result === 'failed').length : null
    return { order_id: `DEMO-${kind === 'production' ? 'P' : 'L'}-${number}`, order_type: kind, order_ref: crypto.randomUUID(), run_id: crypto.randomUUID(),
      plc_order_number: number, accepted_sequence: sequence, accepted_at: instant, status: 'pending', run_phase: 'queued',
      planned_quantity: results.length, processed_quantity: good === null || failed === null ? null : good + failed,
      good_quantity: good, error_quantity: failed, result_complete: results.every(result => result !== null), quantity_source: observed ? 'plc' : 'unknown',
      review_required: false, review_reason: null, has_manual_review: false, queue_position: null, version: 1,
      started_at: null, ended_at: null, source: this.source(), units }
  }

  private source(): SourceStatus {
    return { connection_status: 'connected', freshness: 'fresh', last_success_at: this.clock().toISOString(), error: null }
  }

  private views(): OrderRunView[] {
    let position = 0
    return this.orders.map(order => ({ ...order, source: this.source(), queue_position: order.run_phase === 'queued' ? ++position : null }))
  }

  private summary(orders: OrderRunView[]): OrderSummary {
    return { total: orders.length, pending: orders.filter(item => item.status === 'pending').length,
      in_progress: orders.filter(item => item.status === 'in_progress').length, completed: orders.filter(item => item.status === 'completed').length,
      error: orders.filter(item => item.status === 'error').length, review_required: orders.filter(item => item.review_required).length }
  }

  private dispatch(orders: OrderRunView[]): DispatchStatus {
    return { blocked: true, reason: orders.some(item => item.review_required) ? 'Ein Testlauf muss geprüft werden.' : 'Testdaten-Vorschau: Anlagenbereitschaft wird nicht simuliert; neue Starts gesperrt.',
      active_run_id: this.activeRunId, worker_running: true }
  }
}
