"use client"

import * as React from "react"
import { productionOrderAPI, deliveryOrderAPI, storageAPI } from "@/lib/api-client"
import {
  ProductionOrder,
  DeliveryOrder,
  StorageItem,
  OrderStats,
  RecentOrder,
  InventoryAlert,
} from "@/lib/types"

// Mock data for development when backend is not ready
const MOCK_PRODUCTION_ORDERS: ProductionOrder[] = [
  { id: 1, quantity: 100, status: "PENDING", article_id: 1, created_at: "2026-05-11T10:00:00" },
  { id: 2, quantity: 50, status: "IN_PROGRESS", article_id: 2, created_at: "2026-05-11T09:30:00" },
  { id: 3, quantity: 200, status: "COMPLETED", article_id: 1, created_at: "2026-05-10T15:00:00" },
  { id: 4, quantity: 75, status: "ERROR", article_id: 3, created_at: "2026-05-10T12:00:00" },
]

const MOCK_DELIVERY_ORDERS: DeliveryOrder[] = [
  { id: 101, quantity: 100, status: "COMPLETED", article_id: 1, created_at: "2026-05-11T08:00:00" },
  { id: 102, quantity: 50, status: "IN_PROGRESS", article_id: 2, created_at: "2026-05-11T09:00:00" },
  { id: 103, quantity: 200, status: "PENDING", article_id: 3, created_at: "2026-05-11T11:00:00" },
]

const MOCK_STORAGE: StorageItem[] = [
  { id: 1, quantity: 450, article_id: 1 },
  { id: 2, quantity: 120, article_id: 2 },
  { id: 3, quantity: 5, article_id: 3 }, // Low stock
]

/**
 * Hook for fetching production orders with auto-refetch
 */
export function useProductionOrders(refetchInterval: number = 10000) {
  const [data, setData] = React.useState<ProductionOrder[]>(MOCK_PRODUCTION_ORDERS)
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  const fetch = React.useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Uncomment when backend is ready:
      // const result = await productionOrderAPI.list()
      // setData(result)
      
      // For now, use mock data
      setData(MOCK_PRODUCTION_ORDERS)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch"))
    } finally {
      setIsLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetch()
    const interval = setInterval(fetch, refetchInterval)
    return () => clearInterval(interval)
  }, [fetch, refetchInterval])

  return { data, isLoading, error, refetch: fetch }
}

/**
 * Hook for fetching delivery orders with auto-refetch
 */
export function useDeliveryOrders(refetchInterval: number = 10000) {
  const [data, setData] = React.useState<DeliveryOrder[]>(MOCK_DELIVERY_ORDERS)
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  const fetch = React.useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Uncomment when backend is ready:
      // const result = await deliveryOrderAPI.list()
      // setData(result)
      
      // For now, use mock data
      setData(MOCK_DELIVERY_ORDERS)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch"))
    } finally {
      setIsLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetch()
    const interval = setInterval(fetch, refetchInterval)
    return () => clearInterval(interval)
  }, [fetch, refetchInterval])

  return { data, isLoading, error, refetch: fetch }
}

/**
 * Hook for fetching storage/inventory with auto-refetch
 */
export function useStorage(refetchInterval: number = 15000) {
  const [data, setData] = React.useState<StorageItem[]>(MOCK_STORAGE)
  const [isLoading, setIsLoading] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  const fetch = React.useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Uncomment when backend is ready:
      // const result = await storageAPI.list()
      // setData(result)
      
      // For now, use mock data
      setData(MOCK_STORAGE)
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Failed to fetch"))
    } finally {
      setIsLoading(false)
    }
  }, [])

  React.useEffect(() => {
    fetch()
    const interval = setInterval(fetch, refetchInterval)
    return () => clearInterval(interval)
  }, [fetch, refetchInterval])

  return { data, isLoading, error, refetch: fetch }
}

/**
 * Hook for calculating order statistics
 */
export function useOrderStats() {
  const { data: prodOrders } = useProductionOrders()
  const { data: delivOrders } = useDeliveryOrders()

  const stats = React.useMemo((): OrderStats => {
    const calculateStats = (orders: any[]) => ({
      total: orders.length,
      pending: orders.filter((o) => o.status === "PENDING").length,
      inProgress: orders.filter((o) => o.status === "IN_PROGRESS").length,
      completed: orders.filter((o) => o.status === "COMPLETED").length,
    })

    return {
      production: calculateStats(prodOrders),
      delivery: calculateStats(delivOrders),
    }
  }, [prodOrders, delivOrders])

  return stats
}

/**
 * Hook for getting low-stock inventory alerts
 */
export function useInventoryAlerts(threshold: number = 50) {
  const { data: storage } = useStorage()

  const alerts = React.useMemo((): InventoryAlert[] => {
    return storage
      .filter((item) => item.quantity < threshold)
      .map((item) => ({
        article: {
          id: item.article_id,
          name: `Article ${item.article_id}`,
          description: "",
          price: 0,
        },
        currentQty: item.quantity,
        threshold,
      }))
  }, [storage, threshold])

  return alerts
}

/**
 * Hook for getting recent orders (combined timeline)
 */
export function useRecentOrders(limit: number = 5) {
  const { data: prodOrders } = useProductionOrders()
  const { data: delivOrders } = useDeliveryOrders()

  const recentOrders = React.useMemo((): RecentOrder[] => {
    const combined: RecentOrder[] = [
      ...prodOrders.map((o) => ({
        id: o.id,
        type: "production" as const,
        article: `Article ${o.article_id}`,
        quantity: o.quantity,
        status: o.status,
        createdAt: o.created_at || new Date().toISOString(),
      })),
      ...delivOrders.map((o) => ({
        id: o.id + 1000, // Offset to avoid ID collision
        type: "delivery" as const,
        article: `Article ${o.article_id}`,
        quantity: o.quantity,
        status: o.status,
        createdAt: o.created_at || new Date().toISOString(),
      })),
    ]

    return combined.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()).slice(0, limit)
  }, [prodOrders, delivOrders, limit])

  return recentOrders
}
