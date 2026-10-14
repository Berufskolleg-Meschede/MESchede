import type { ProductUnit } from '@/lib/types'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatusBadge } from '@/components/status-badge'

export function ProductQueue({ units }: { units: ProductUnit[] }) {
  return (
    <Table>
      <TableHeader><TableRow>
        <TableHead>Einheit</TableHead><TableHead>Produkt</TableHead>
        <TableHead>Seriennummer</TableHead><TableHead>Sequenz</TableHead>
        <TableHead>Ergebnis</TableHead><TableHead>Fehlercode</TableHead>
      </TableRow></TableHeader>
      <TableBody>{units.map(unit => <TableRow key={unit.index}>
        <TableCell className="tabular-nums">{unit.index + 1}</TableCell>
        <TableCell>{unit.product_text || `Produkt #${unit.product_id}`}<span className="ml-2 text-xs text-muted-foreground">#{unit.product_id}</span></TableCell>
        <TableCell className="font-mono text-xs">{unit.serial_number ?? 'Unbekannt'}</TableCell>
        <TableCell className="tabular-nums">{unit.sequence_number ?? 'Unbekannt'}</TableCell>
        <TableCell><StatusBadge status={unit.result ?? 'unknown'} /></TableCell>
        <TableCell className="tabular-nums">{unit.error_code ?? 'Unbekannt'}</TableCell>
      </TableRow>)}</TableBody>
    </Table>
  )
}
