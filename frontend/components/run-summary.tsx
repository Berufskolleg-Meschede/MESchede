import type { OrderRunView } from '@/lib/types'
import { orderLabel, PHASE_LABELS, productLabel, quantity, timestamp } from '@/lib/order-format'
import { StatusBadge } from '@/components/status-badge'
import { ProductQueue } from '@/components/product-queue'
import { Button } from '@/components/ui/button'

export function RunSummary({ order, onReview }: { order: OrderRunView; onReview?: (order: OrderRunView) => void }) {
  const values = [
    ['Sollmenge', quantity(order.planned_quantity)], ['Bearbeitet', quantity(order.processed_quantity)],
    ['Erfolgreich', quantity(order.good_quantity)], ['Fehlgeschlagen', quantity(order.error_quantity)],
  ]
  return (
    <section id={`run-${order.run_id}`} className="overflow-hidden rounded-sm border border-border bg-card scroll-mt-6">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-5 py-4">
        <div className="flex flex-col gap-2">
          <h2 className="font-semibold">{order.order_type === 'production' ? 'Fertigungsauftrag' : 'Lieferauftrag'} <span className="font-mono">{orderLabel(order.order_id)}</span></h2>
          <p className="text-sm text-muted-foreground">{productLabel(order)}</p>
          <div className="flex flex-wrap items-center gap-3"><StatusBadge status={order.status} /><span className="text-xs text-muted-foreground">{PHASE_LABELS[order.run_phase]}</span></div>
        </div>
        {order.review_required && onReview && <Button variant="outline" onClick={() => onReview(order)}>Lauf prüfen</Button>}
      </div>
      <dl className="grid grid-cols-2 gap-4 border-b border-border p-5 md:grid-cols-4">
        {values.map(([label, value]) => <div key={label}><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 text-base tabular-nums">{value}</dd></div>)}
      </dl>
      <div className="flex flex-wrap gap-x-6 gap-y-2 px-5 py-3 text-xs text-muted-foreground">
        <span>Start beobachtet: {timestamp(order.started_at)}</span><span>Ende beobachtet: {timestamp(order.ended_at)}</span>
        <span>Steuerungsauftrag: {order.plc_order_number}</span>
        {order.has_manual_review && <span className="text-primary">Manuell bewertet</span>}
        <span>Mengenherkunft: {{ plc: 'PLC-Rückmeldung', manual: 'Manuelle Bewertung', mixed: 'PLC und manuelle Bewertung', unknown: 'Unbekannt' }[order.quantity_source]}</span>
      </div>
      {order.review_required && order.review_reason && <p className="px-5 pb-3 text-sm text-muted-foreground">Prüfgrund: {order.review_reason}</p>}
      <div className="border-t border-border px-5 py-3"><h3 className="text-sm font-medium">Produktqueue dieses Laufs</h3>
        {!order.result_complete && <p className="mt-1 text-xs text-muted-foreground">Die einzelnen Ergebnisse sind noch nicht vollständig bestätigt.</p>}
      </div>
      <ProductQueue units={order.units} />
    </section>
  )
}
