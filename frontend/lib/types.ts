export type OrderStatus = 'pending' | 'in_progress' | 'error' | 'completed'
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

export interface AnalyticsRun {
  id: number
  order_type: 'production' | 'delivery'
  order_id: string
  plc_order_number: number | null
  planned_quantity: number | null
  processed_quantity: number | null
  good_quantity: number | null
  defective_quantity: number | null
  status: 'queued' | 'running' | 'completed' | 'unknown'
  started_at: string | null
  ended_at: string | null
  created_at: string
  last_observed_at: string | null
  last_error_type: string | null
}

export interface OrderFormData {
  quantity: number
  status: OrderStatus
  article_id: number
}
