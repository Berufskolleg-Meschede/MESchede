export type OrderStatus = 'pending' | 'in_progress' | 'error' | 'completed' | 'review_required'
export type MachineStatus = 'offline' | 'online'

export interface Article {
  id: number
  name: string
  description: string
  price: number
}

export interface ProductionOrder {
  id: number
  quantity: number
  status: OrderStatus
  article_id: number
  article?: Article
}

export interface DeliveryOrder {
  id: number
  quantity: number
  status: OrderStatus
  article_id: number
  article?: Article
}

export interface Machine {
  id: number
  name: string
  type: string
  status: MachineStatus
}

export interface OrderFormData {
  quantity: number
  status: OrderStatus
  article_id: number
}

export interface StorageItem {
  id: number | null
  quantity: number | null
  article_id: number
  updated_at: string | null
  article?: Article
}

export interface StorageStatus {
  configured: boolean
  connected: boolean
  last_error: string | null
  last_message_at: string | null
  stale_after_seconds: number
}

export interface AnalyticsRun {
  id: number
  order_type: 'production' | 'delivery'
  order_id: string
  plc_order_number: number | null
  planned_quantity: number | null
  processed_quantity: number | null
  good_quantity: number | null
  defective_quantity: number | null
  status: 'queued' | 'running' | 'completed' | 'unknown' | 'review_required'
  started_at: string | null
  ended_at: string | null
  created_at: string
  last_observed_at: string | null
  last_error_type: string | null
}

export interface Settings {
  opcua_node_production_order: string
  opcua_node_delivery_order: string
  polling_interval_ms: number
  opcua_node_kopf: string
  opcua_node_inhalt: string
  opcua_node_feedback: string
  opcua_node_auftragssteuerung: string
  opcua_node_status: string
  opcua_node_produktqueue_pattern: string
  opcua_node_lager_gehaeuse: string
  opcua_node_magazin_deckel_1: string
  opcua_node_magazin_deckel_2: string
  opcua_node_lager_produkte: string
}

export interface LagerGehaeuseBestand {
  gesamt: number
  rot: number
  silber: number
  schwarz: number
}

export interface LagerProdukteBestand {
  gesamt: number
  salz_rot: number
  salz_silber: number
  salz_schwarz: number
  pfeffer_rot: number
  pfeffer_silber: number
  pfeffer_schwarz: number
}

export interface LagerSnapshot {
  gehaeuse: LagerGehaeuseBestand
  deckel_blau: number
  deckel_gruen: number
  produkte: LagerProdukteBestand
  observed_at: string
}

export interface FieldErrorDetail {
  loc: (string | number)[]
  msg: string
}

export class ApiValidationError extends Error {
  fieldErrors: Record<string, string>

  constructor(message: string, fieldErrors: Record<string, string> = {}) {
    super(message)
    this.name = 'ApiValidationError'
    this.fieldErrors = fieldErrors
  }
}

export type OrderType = 'production' | 'delivery'
export type RunPhase = 'queued' | 'preparing' | 'start_pending' | 'running' | 'completion_observed' |
  'awaiting_reset' | 'completed' | 'interrupted' | 'review_required'

export interface SourceStatus {
  connection_status: 'connected' | 'disconnected' | 'unknown'
  freshness: 'fresh' | 'stale' | 'unknown'
  last_success_at: string | null
  error: string | null
}

export interface ProductUnit {
  index: number
  product_id: number
  product_text: string
  serial_number: number | null
  sequence_number: number | null
  result: 'good' | 'failed' | null
  raw_status: number | null
  error_code: number | null
}

export interface OrderRunView {
  order_id: string
  order_type: OrderType
  order_ref: string
  run_id: string
  plc_order_number: number
  accepted_sequence: number
  accepted_at: string
  status: OrderStatus
  run_phase: RunPhase
  planned_quantity: number
  processed_quantity: number | null
  good_quantity: number | null
  error_quantity: number | null
  result_complete: boolean
  quantity_source: 'plc' | 'completion' | 'manual' | 'mixed' | 'unknown'
  review_required: boolean
  review_reason: string | null
  has_manual_review: boolean
  queue_position: number | null
  version: number
  started_at: string | null
  ended_at: string | null
  source: SourceStatus
  units: ProductUnit[]
}

export interface DispatchStatus {
  blocked: boolean
  reason: string | null
  active_run_id: string | null
  worker_running: boolean
}

export interface OrderSummary {
  total: number
  pending: number
  in_progress: number
  completed: number
  error: number
  review_required: number
}

export interface OrderPageData {
  orders: OrderRunView[]
  total: number
  filtered_total: number
  offset: number
  limit: number
  active: OrderRunView[]
  waiting: OrderRunView[]
  reviews: OrderRunView[]
  summary: OrderSummary
  dispatch: DispatchStatus
  source: SourceStatus
  refresh_interval_s: number
  stale_after_s: number
}

export interface OrderOverview {
  production: OrderSummary
  delivery: OrderSummary
  combined: OrderSummary
  dispatch: DispatchStatus
  sources: Record<OrderType, SourceStatus>
  reviews: OrderRunView[]
  active: OrderRunView[]
  waiting: OrderRunView[]
  refresh_interval_s: number
  stale_after_s: number
}

export interface RunReview {
  request_id: string
  expected_version: number
  outcome: 'completed' | 'interrupted' | 'unknown'
  good_quantity: number | null
  error_quantity: number | null
}

export interface ReviewResult {
  request_id: string
  run_id: string
  outcome: RunReview['outcome']
  good_quantity: number | null
  error_quantity: number | null
  reviewed_at: string
}
