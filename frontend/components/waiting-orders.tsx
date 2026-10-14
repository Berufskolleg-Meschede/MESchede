import Link from 'next/link'
import type { OrderRunView } from '@/lib/types'
import { orderLabel, productLabel, quantity } from '@/lib/order-format'
import { Button } from '@/components/ui/button'
import { Empty, EmptyDescription } from '@/components/ui/empty'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

/** Zeigt MES-Aufträge in globaler Reihenfolge, getrennt von der Produktqueue. */
export function WaitingOrders({ orders, showType = false, onDetail }: {
  orders: OrderRunView[]; showType?: boolean; onDetail?: (order: OrderRunView) => void
}) {
  return <section aria-labelledby="waiting-title" className="overflow-hidden rounded-sm border border-border bg-card">
    <div className="border-b border-border px-5 py-4"><h2 id="waiting-title" className="text-base font-semibold">Wartende MES-Aufträge</h2>
      <p className="mt-1 text-xs text-muted-foreground">Globale Annahmereihenfolge für Produktion und Lieferung. Die Position zählt beide Bereiche.</p></div>
    {orders.length === 0 ? <Empty className="py-6"><EmptyDescription>Keine wartenden Aufträge.</EmptyDescription></Empty> :
      <Table><TableHeader><TableRow className="bg-secondary/35"><TableHead className="px-5">Position</TableHead><TableHead>Auftrag</TableHead>
        {showType && <TableHead>Bereich</TableHead>}<TableHead>Produkte</TableHead><TableHead className="text-right">Sollmenge</TableHead></TableRow></TableHeader>
        <TableBody>{orders.map(order => <TableRow key={order.run_id}>
          <TableCell className="px-5 tabular-nums">{order.queue_position}</TableCell>
          <TableCell>{onDetail ? <Button variant="link" className="h-auto p-0 font-mono" onClick={() => onDetail(order)}>{orderLabel(order.order_id)}</Button> :
            <Link href={order.order_type === 'production' ? '/production-orders' : '/delivery-orders'} className="font-mono text-xs underline underline-offset-4">{orderLabel(order.order_id)}</Link>}</TableCell>
          {showType && <TableCell>{order.order_type === 'production' ? 'Produktion' : 'Lieferung'}</TableCell>}
          <TableCell>{productLabel(order)}</TableCell><TableCell className="text-right tabular-nums">{quantity(order.planned_quantity)}</TableCell>
        </TableRow>)}</TableBody>
      </Table>}
  </section>
}
