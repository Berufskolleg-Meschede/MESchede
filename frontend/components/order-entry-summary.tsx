import type { OrderPayload, OrderType } from '@/lib/types'
import type { OrderDraft } from '@/lib/order-input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

/** Zeigt exakt die wirksamen Werte des bestätigbaren beziehungsweise gesicherten Requests. */
export function OrderEntrySummary({ payload, draft, type }: { payload: OrderPayload; draft: OrderDraft; type: OrderType }) {
  const { kopf, inhalt } = payload.mes_auftrag
  const values = [
    ['Auftragsart', type === 'production' ? 'Fertigungsauftrag' : 'Lieferauftrag'],
    ['Auftrag-ID', payload.order_id], ['PLC-Auftragsnummer', String(kopf.Auftragsnummer)],
    ['Gesamtmenge', `${inhalt.Produktqueue.length} Stk.`],
    ['Seriennummern', `${inhalt.SeriennummerStart} bis ${inhalt.Produktqueue.at(-1)?.Seriennummer}`],
    ['Startdatum / Startzeit', `${kopf.Startdatum.split('-').reverse().join('.')} · ${kopf.Startzeit}`],
    ['Kundennummer', String(kopf.Kundennummer)], ['Priorität', String(kopf.Prioritaet)],
    ['Parameter 0 / Parameter 1', `${kopf.Parameter0} / ${kopf.Parameter1}`],
  ]
  return <div className="flex min-w-0 flex-col gap-4">
    <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">{values.map(([label, value]) => <div key={label} className="min-w-0">
      <dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 break-words text-sm tabular-nums">{value}</dd>
    </div>)}</dl>
    <Table><TableHeader><TableRow><TableHead>Produkt</TableHead><TableHead className="text-right">Menge</TableHead></TableRow></TableHeader>
      <TableBody>{draft.rows.map(row => <TableRow key={row.key}><TableCell>
        {inhalt.Produktqueue.find(unit => String(unit.ProduktID) === row.product)?.Produkttext} · ID {row.product}
      </TableCell><TableCell className="text-right tabular-nums">{row.quantity} Stk.</TableCell></TableRow>)}</TableBody>
    </Table>
    <p className="text-sm text-muted-foreground">Die Annahme speichert den Auftrag und reiht ihn in die gemeinsame Warteschlange ein. Der PLC-Start wird anschließend gesondert bestätigt.</p>
  </div>
}
