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

export interface OrderFormData {
  quantity: number
  status: OrderStatus
  article_id: number
}
