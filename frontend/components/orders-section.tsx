'use client'

import { useCallback, useState } from 'react'
import { api } from '@/lib/api'
import type { OrderAdmission, OrderRunView, OrderStatus, OrderType } from '@/lib/types'
import { useOrderSnapshot } from '@/hooks/use-order-snapshot'
import { StatCard } from '@/components/stat-card'
import { OrderDispatchNotice } from '@/components/order-dispatch-notice'
import { OrderSourceStatus } from '@/components/order-source-status'
import { RunSummary } from '@/components/run-summary'
import { RunReviewDialog } from '@/components/run-review-dialog'
import { OrderDetailDialog } from '@/components/order-detail-dialog'
import { ManualOrderEntry } from '@/components/manual-order-entry'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { OrderPageFeedback } from '@/components/order-page-feedback'
import { OrderList } from '@/components/order-list'
import { WaitingOrders } from '@/components/waiting-orders'

export function OrdersSection({ type, title }: { type: OrderType; title: string }) {
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<OrderStatus | 'all'>('all')
  const [offset, setOffset] = useState(0)
  const [review, setReview] = useState<OrderRunView | null>(null)
  const [detail, setDetail] = useState<Pick<OrderRunView, 'order_type' | 'order_id'> | null>(null)
  const [accepted, setAccepted] = useState<OrderAdmission | null>(null)
  const load = useCallback((signal: AbortSignal) => api.list(type, { search, status, offset }, signal), [type, search, status, offset])
  const { data, error, loading, reload, checkedAt } = useOrderSnapshot(`${type}:${search}:${status}:${offset}`, load)
  const onAccepted = useCallback((order: OrderAdmission) => {
    setAccepted(order)
    setSearch(order.order_id)
    setStatus('all')
    setOffset(0)
    reload()
  }, [reload])
  const runs = data ? [...new Map([...data.active, ...data.reviews.filter(order => order.order_type === type)].map(order => [order.run_id, order])).values()] : []

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-5 md:p-8 lg:p-10">
      <header className="flex flex-wrap items-start justify-between gap-4 border-b border-border pb-5"><div><h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">{data ? `${data.total} dauerhaft gespeicherte Aufträge` : 'Aufträge und Laufzustände'}</p></div>
        <ManualOrderEntry type={type} blockedReason={data?.dispatch.reason} onAccepted={onAccepted}
          onInspect={id => setDetail({ order_type: type, order_id: id })} /></header>
      {accepted && <Alert><AlertTitle>Auftrag angenommen</AlertTitle><AlertDescription>
        <p>{type === 'production' ? 'Fertigungsauftrag' : 'Lieferauftrag'} {accepted.order_id} ist dauerhaft gespeichert. Die Annahme bestätigt noch keinen PLC-Start.</p>
        <Button className="mt-3" variant="outline" onClick={() => setDetail({ order_type: type, order_id: accepted.order_id })}>Auftragsdetails anzeigen</Button>
      </AlertDescription></Alert>}
      <OrderPageFeedback error={error} loading={loading} hasData={data !== null} reload={reload} />
      {data && <>
        <OrderSourceStatus source={data.source} staleAfter={data.stale_after_s} checkedAt={checkedAt} />
        <OrderDispatchNotice dispatch={data.dispatch} reviews={data.reviews} />
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border md:grid-cols-5 [&>div:last-child]:col-span-2 md:[&>div:last-child]:col-span-1">
          <StatCard label="Wartend" value={data.summary.pending} /><StatCard label="In Bearbeitung" value={data.summary.in_progress} />
          <StatCard label="Prüfung erforderlich" value={data.summary.review_required} /><StatCard label="Fehler" value={data.summary.error} />
          <StatCard label="Abgeschlossen" value={data.summary.completed} />
        </div>
        <section aria-labelledby="active-runs-title" className="flex flex-col gap-3"><h2 id="active-runs-title" className="text-base font-semibold">Lauf und Produktqueue</h2>
          {runs.length === 0 ? <p className="text-sm text-muted-foreground">Kein Lauf in diesem Bereich aktiv.</p> : runs.map(order => <RunSummary key={order.run_id} order={order} onReview={setReview} />)}</section>
        <WaitingOrders orders={data.waiting} onDetail={setDetail} />
      </>}
      <OrderList data={data} loading={loading} error={error} search={search} status={status} offset={offset}
        onSearch={value => { setSearch(value); setOffset(0) }} onStatus={value => { setStatus(value); setOffset(0) }}
        onOffset={setOffset} onDetail={setDetail} onReview={setReview} />
      {review && <RunReviewDialog key={review.run_id} order={review} onClose={() => setReview(null)} onSaved={() => { setReview(null); reload() }} />}
      {detail && <OrderDetailDialog key={`${detail.order_type}:${detail.order_id}`} order={detail} onClose={() => setDetail(null)}
        onReview={order => { setDetail(null); setReview(order) }} />}
    </div>
  )
}
