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

export interface OrderFormData {
  quantity: number
  status: OrderStatus
  article_id: number
}

export interface Settings {
  opcua_node_production_order: string
  opcua_node_delivery_order: string
  polling_interval_ms: number
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
