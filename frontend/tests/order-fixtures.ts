import type { OrderOverview, OrderPageData, OrderRunView, OrderType, SourceStatus } from '../lib/types'

export const source: SourceStatus = { connection_status: 'connected', freshness: 'fresh', last_success_at: new Date().toISOString(), error: null }

/** Simulierte Browserdaten sind auf den Testordner begrenzt. */
export function order(kind: OrderType, id: string, review = false): OrderRunView {
  return {
    order_id: id, order_type: kind, order_ref: `${kind}-${id}`, run_id: `${kind}-${id}`,
    plc_order_number: Number(id), accepted_sequence: Number(id), accepted_at: source.last_success_at!,
    status: review ? 'review_required' : 'pending', run_phase: review ? 'review_required' : 'queued',
    planned_quantity: 2, processed_quantity: null, good_quantity: null, error_quantity: null,
    result_complete: false, quantity_source: 'unknown', review_required: review,
    review_reason: review ? 'Der Lauf ist nach Neustart nicht bestätigt.' : null,
    has_manual_review: false, queue_position: review ? null : 1, version: 2,
    started_at: null, ended_at: null, source,
    units: [{ index: 0, product_id: 1, product_text: 'Prüfprodukt', serial_number: 10, sequence_number: 1, result: null, raw_status: null, error_code: null },
      { index: 1, product_id: 1, product_text: 'Prüfprodukt', serial_number: 11, sequence_number: 2, result: null, raw_status: null, error_code: null }],
  }
}

export function pageData(kind: OrderType): OrderPageData {
  const active = order(kind, '1', true)
  const waiting = order(kind, '2')
  return {
    orders: [active, waiting], total: 2, filtered_total: 2, offset: 0, limit: 50, active: [active], waiting: [waiting], reviews: [active],
    summary: { total: 2, pending: 1, in_progress: 0, completed: 0, error: 0, review_required: 1 },
    dispatch: { blocked: true, reason: 'Ein Lauf muss geprüft werden.', active_run_id: active.run_id, worker_running: true },
    source, refresh_interval_s: 0.3, stale_after_s: 10,
  }
}

export function overview(): OrderOverview {
  const production = pageData('production')
  const delivery = pageData('delivery')
  return { production: production.summary, delivery: delivery.summary,
    combined: { total: 4, pending: 2, in_progress: 0, completed: 0, error: 0, review_required: 2 },
    dispatch: production.dispatch, sources: { production: source, delivery: source },
    reviews: [...production.reviews, ...delivery.reviews], active: production.active,
    waiting: [...production.waiting, ...delivery.waiting.map(item => ({ ...item, queue_position: 2 }))],
    refresh_interval_s: 0.3, stale_after_s: 10,
  }
}
