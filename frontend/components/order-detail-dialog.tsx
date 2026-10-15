'use client'

import { useCallback } from 'react'
import { api } from '@/lib/api'
import type { OrderRunView } from '@/lib/types'
import { useOrderSnapshot } from '@/hooks/use-order-snapshot'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { OrderSourceStatus } from '@/components/order-source-status'
import { RunSummary } from '@/components/run-summary'
import { Button } from '@/components/ui/button'

/** Aktualisiert ein geöffnetes Detail unabhängig von Listenfiltern und Pagination. */
export function OrderDetailDialog({ order, onClose, onReview }: {
  order: Pick<OrderRunView, 'order_type' | 'order_id'>; onClose: () => void; onReview: (order: OrderRunView) => void
}) {
  const load = useCallback((signal: AbortSignal) => api.detail(order.order_type, order.order_id, signal), [order.order_type, order.order_id])
  const snapshot = useOrderSnapshot(`detail:${order.order_type}:${order.order_id}`, load)
  return <Dialog open onOpenChange={open => { if (!open) { onClose() } }}>
    <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-3xl">
      <DialogHeader><DialogTitle>Auftragsdetails</DialogTitle><DialogDescription>Gespeicherter Lauf mit Mengen und Produkteinheiten.</DialogDescription></DialogHeader>
      {snapshot.loading && <p role="status" className="text-sm">Lade Auftragsdetails…</p>}
      {snapshot.error && <div role="alert" className="flex flex-col gap-2 text-sm"><p>{snapshot.error}</p>
        <Button variant="outline" onClick={snapshot.reload}>Details erneut laden</Button></div>}
      {snapshot.data && <>
        <OrderSourceStatus source={snapshot.data.source} staleAfter={snapshot.data.stale_after_s} checkedAt={snapshot.checkedAt} />
        <RunSummary order={snapshot.data} onReview={onReview} />
      </>}
    </DialogContent>
  </Dialog>
}
