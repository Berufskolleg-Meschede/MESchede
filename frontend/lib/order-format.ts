import type { OrderRunView, RunPhase } from './types'

export const STATUS_LABELS = {
  pending: 'Ausstehend', in_progress: 'In Bearbeitung', error: 'Fehler',
  completed: 'Abgeschlossen', review_required: 'Prüfung erforderlich',
}

export const PHASE_LABELS: Record<RunPhase, string> = {
  queued: 'Wartend', preparing: 'Übergabe vorbereitet', start_pending: 'Warte auf Startbestätigung',
  running: 'Lauf bestätigt', completion_observed: 'Laufende bestätigt', awaiting_reset: 'Warte auf Bereitschaft',
  completed: 'Lauf abgeschlossen', interrupted: 'Lauf unterbrochen', review_required: 'Ausgang prüfen',
}

/** Erhält fachliche String-IDs und formatiert nur rein numerische IDs. */
export function orderLabel(id: string) {
  return /^\d+$/.test(id) ? `#${id.padStart(4, '0')}` : id
}

export function quantity(value: number | null) {
  return value === null ? 'Unbekannt' : `${value.toLocaleString('de-DE')} Stk.`
}

export function timestamp(value: string | null) {
  return value === null ? 'Noch keine Rückmeldung' : new Date(value).toLocaleString('de-DE')
}

export function productLabel(order: OrderRunView) {
  const names = [...new Set(order.units.map(unit => unit.product_text || `Produkt #${unit.product_id}`))]
  return names.join(', ') || 'Produktinformationen unbekannt'
}

/** Erzeugt auch auf einem unverschlüsselten NAS-Origin eine kryptografische Review-ID. */
export function reviewRequestId() {
  if (typeof crypto.randomUUID === 'function') { return crypto.randomUUID() }
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map(byte => byte.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}
