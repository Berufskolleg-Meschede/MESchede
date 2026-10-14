'use client'

import { useCallback } from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import { useOrderSnapshot } from '@/hooks/use-order-snapshot'
import { StatCard } from '@/components/stat-card'
import { OrderDispatchNotice } from '@/components/order-dispatch-notice'
import { OrderSourceStatus } from '@/components/order-source-status'
import { RunSummary } from '@/components/run-summary'
import { OrderPageFeedback } from '@/components/order-page-feedback'
import { WaitingOrders } from '@/components/waiting-orders'
import { Empty, EmptyDescription } from '@/components/ui/empty'

export default function DashboardPage() {
  const load = useCallback((signal: AbortSignal) => api.overview(signal), [])
  const { data, error, loading, reload, checkedAt } = useOrderSnapshot('overview', load)

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 p-5 md:p-8 lg:p-10">
      <header className="border-b border-border pb-5"><p className="mb-2 text-xs text-muted-foreground">Fertigungssteuerung / Übersicht</p>
        <h1 className="text-2xl font-semibold tracking-tight">Betriebsübersicht</h1><p className="mt-1.5 text-sm text-muted-foreground">Produktion und Lieferung gemeinsam im Überblick.</p></header>
      <OrderPageFeedback error={error} loading={loading} hasData={data !== null} reload={reload} />
      {data && <>
        <div className="flex flex-col gap-2"><OrderSourceStatus label="Produktion" source={data.sources.production} staleAfter={data.stale_after_s} checkedAt={checkedAt} />
          <OrderSourceStatus label="Lieferung" source={data.sources.delivery} staleAfter={data.stale_after_s} checkedAt={checkedAt} /></div>
        <OrderDispatchNotice dispatch={data.dispatch} reviews={data.reviews} />
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border md:grid-cols-4">
          <StatCard label="Wartende Aufträge" value={data.combined.pending} /><StatCard label="In Bearbeitung" value={data.combined.in_progress} />
          <StatCard label="Prüfung erforderlich" value={data.combined.review_required} /><StatCard label="Abgeschlossen" value={data.combined.completed} />
        </div>
        <div className="grid gap-6 md:grid-cols-2">{(['production', 'delivery'] as const).map(kind => {
          const summary = data[kind]
          return <section key={kind} className="rounded-sm border border-border bg-card p-5">
            <div className="flex items-center justify-between gap-3"><h2 className="font-semibold">{kind === 'production' ? 'Fertigungsaufträge' : 'Lieferaufträge'}</h2>
              <Link href={kind === 'production' ? '/production-orders' : '/delivery-orders'} className="inline-flex items-center gap-2 text-sm underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-ring">Zur Seite <ArrowRight size={14} aria-hidden /></Link></div>
            <dl className="mt-5 grid grid-cols-3 gap-4 text-sm">{[['Gesamt', summary.total], ['Wartend', summary.pending], ['Fehler', summary.error]].map(([label, value]) =>
              <div key={label}><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 tabular-nums">{value}</dd></div>)}</dl>
          </section>
        })}</div>
        <section aria-labelledby="active-title" className="flex flex-col gap-3"><h2 id="active-title" className="text-base font-semibold">Aktueller Lauf und Produktqueue</h2>
          {data.active.length === 0 ? <Empty className="py-6"><EmptyDescription>Kein Lauf aktiv.</EmptyDescription></Empty> : data.active.map(order => <RunSummary key={order.run_id} order={order} />)}</section>
        <WaitingOrders orders={data.waiting} showType />
      </>}
      {!loading && !data && <p className="text-sm text-muted-foreground">Keine Betriebsdaten verfügbar.</p>}
    </div>
  )
}
