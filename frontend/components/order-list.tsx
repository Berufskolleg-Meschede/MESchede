import type { OrderPageData, OrderRunView, OrderStatus } from '@/lib/types'
import { orderLabel, productLabel, quantity, STATUS_LABELS } from '@/lib/order-format'
import { StatusBadge } from '@/components/status-badge'
import { Button } from '@/components/ui/button'
import { Empty, EmptyDescription } from '@/components/ui/empty'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

function OrderFilters({ search, status, onSearch, onStatus }: {
  search: string; status: OrderStatus | 'all'; onSearch: (value: string) => void; onStatus: (value: OrderStatus | 'all') => void
}) {
  return <FieldGroup className="flex-row flex-wrap items-end gap-3">
    <Field className="w-full gap-2 sm:max-w-sm"><FieldLabel htmlFor="order-search">Aufträge suchen</FieldLabel>
      <Input id="order-search" value={search} maxLength={200} onChange={event => onSearch(event.target.value)} placeholder="Produkt oder Auftragsnummer" /></Field>
    <Field className="w-auto gap-2"><FieldLabel htmlFor="status-filter">Status</FieldLabel>
      <select id="status-filter" value={status} onChange={event => onStatus(event.target.value as OrderStatus | 'all')}
        className="h-9 rounded-sm border border-input bg-card px-3 text-sm focus-visible:outline-2 focus-visible:outline-ring">
        <option value="all">Alle Status</option>{Object.entries(STATUS_LABELS).map(([value,label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
  </FieldGroup>
}

function OrderRows({ orders, onDetail, onReview }: {
  orders: OrderRunView[]; onDetail: (order: OrderRunView) => void; onReview: (order: OrderRunView) => void
}) {
  return <Table><TableHeader><TableRow className="bg-secondary/35"><TableHead className="px-5">Auftrag</TableHead><TableHead>Produkte</TableHead>
    <TableHead className="text-right">Sollmenge</TableHead><TableHead>Status</TableHead><TableHead><span className="sr-only">Aktionen</span></TableHead></TableRow></TableHeader>
    <TableBody>{orders.map(order => <TableRow key={order.run_id}>
      <TableCell className="px-5 font-mono text-xs">{orderLabel(order.order_id)}</TableCell><TableCell>{productLabel(order)}</TableCell>
      <TableCell className="text-right tabular-nums">{quantity(order.planned_quantity)}</TableCell><TableCell><StatusBadge status={order.status} /></TableCell>
      <TableCell className="text-right"><Button size="sm" variant="ghost" aria-label={`Details zu Auftrag ${order.order_id}`} onClick={() => onDetail(order)}>Details</Button>
        {order.review_required && <Button size="sm" variant="outline" aria-label={`Lauf ${order.order_id} prüfen`} onClick={() => onReview(order)}>Prüfen</Button>}</TableCell>
    </TableRow>)}</TableBody></Table>
}

export function OrderList({ data, loading, error, search, status, offset, onSearch, onStatus, onOffset, onDetail, onReview }: {
  data: OrderPageData | null; loading: boolean; error: string | null; search: string; status: OrderStatus | 'all'; offset: number
  onSearch: (value: string) => void; onStatus: (value: OrderStatus | 'all') => void; onOffset: (value: number) => void
  onDetail: (order: OrderRunView) => void; onReview: (order: OrderRunView) => void
}) {
  const empty = loading ? 'Lade Aufträge…' : error ? 'Keine aktuellen Daten verfügbar.' : data?.total === 0 ? 'Keine Aufträge vorhanden.' : 'Keine Aufträge für diese Suche gefunden.'
  return <section aria-labelledby="orders-title" className="flex flex-col gap-4">
    <h2 id="orders-title" className="text-base font-semibold">Alle Aufträge</h2>
    <OrderFilters search={search} status={status} onSearch={onSearch} onStatus={onStatus} />
    <p aria-live="polite" className="text-xs text-muted-foreground">{data ? `${data.filtered_total} von ${data.total} Aufträgen` : loading ? 'Lade Aufträge…' : 'Keine Daten verfügbar'}</p>
    <div className="overflow-hidden rounded-sm border border-border bg-card">{data && data.orders.length > 0 ?
      <OrderRows orders={data.orders} onDetail={onDetail} onReview={onReview} /> : <Empty><EmptyDescription>{empty}</EmptyDescription></Empty>}</div>
    {data && <nav aria-label="Auftragsseiten" className="flex items-center justify-between gap-3 text-xs text-muted-foreground">
      <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => onOffset(Math.max(0,offset-data.limit))}>Zurück</Button>
      <span>{data.filtered_total === 0 ? '0' : `${offset+1}–${Math.min(offset+data.limit,data.filtered_total)}`} von {data.filtered_total}</span>
      <Button variant="outline" size="sm" disabled={offset+data.limit >= data.filtered_total} onClick={() => onOffset(offset+data.limit)}>Weiter</Button></nav>}
  </section>
}
