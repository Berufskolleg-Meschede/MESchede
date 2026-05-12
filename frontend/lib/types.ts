/**
 * TypeScript interfaces matching the backend FastAPI models
 */

export type OrderStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "ERROR";
export type MachineStatus = "OFFLINE" | "ONLINE";

export interface Article {
  id: number;
  name: string;
  description: string;
  price: number;
}

export interface ProductionOrder {
  id: number;
  quantity: number;
  status: OrderStatus;
  article_id: number;
  created_at?: string;
  article?: Article;
}

export interface DeliveryOrder {
  id: number;
  quantity: number;
  status: OrderStatus;
  article_id: number;
  created_at?: string;
  article?: Article;
}

export interface StorageItem {
  id: number;
  quantity: number;
  article_id: number;
  article?: Article;
}

export interface Machine {
  id: number;
  name: string;
  type: string;
  status: MachineStatus;
}

export interface User {
  id: number;
  email: string;
}

/**
 * Dashboard statistics
 */
export interface OrderStats {
  production: {
    total: number;
    pending: number;
    inProgress: number;
    completed: number;
  };
  delivery: {
    total: number;
    pending: number;
    inProgress: number;
    completed: number;
  };
}

export interface InventoryAlert {
  article: Article;
  currentQty: number;
  threshold: number;
}

export interface RecentOrder {
  id: number;
  type: "production" | "delivery";
  article: string;
  quantity: number;
  status: OrderStatus;
  createdAt: string;
}
