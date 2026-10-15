'use client'

import type { OrderInputContext } from '@/lib/types'
import type { OrderDraft, InputErrors } from '@/lib/order-input'
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

/** Präsentiert den Entwurf; Validierung und Nebenwirkungen liegen außerhalb dieser Felder. */
export function OrderEntryFields({ draft, context, errors, disabled, onChange }: {
  draft: OrderDraft; context: OrderInputContext; errors: InputErrors; disabled: boolean
  onChange: (draft: OrderDraft) => void
}) {
  function input(key: keyof Omit<OrderDraft, 'rows'>, label: string, type = 'text', min?: number | string, max?: number | string) {
    return <Field data-invalid={!!errors[key]} data-disabled={disabled}>
      <FieldLabel htmlFor={`entry-${key}`}>{label}</FieldLabel>
      <Input id={`entry-${key}`} type={type} value={draft[key]} disabled={disabled} min={min} max={max}
        step={type === 'time' ? 1 : type === 'number' ? 1 : undefined} maxLength={key === 'order_id' ? 200 : undefined}
        aria-invalid={!!errors[key]} aria-describedby={errors[key] ? `error-${key}` : undefined}
        onChange={event => onChange({ ...draft, [key]: event.target.value })} />
      {errors[key] && <FieldError id={`error-${key}`}>{errors[key]}</FieldError>}
    </Field>
  }
  function rowChange(index: number, field: 'product' | 'quantity', value: string) {
    onChange({ ...draft, rows: draft.rows.map((row, position) => position === index ? { ...row, [field]: value } : row) })
  }
  const total = draft.rows.reduce((sum, row) => sum + (Number(row.quantity) || 0), 0)
  return <FieldGroup>
    <FieldGroup className="grid gap-4 sm:grid-cols-2">
      {input('order_id', 'Auftrag-ID')}{input('plc_number', 'PLC-Auftragsnummer', 'number', 0, 65535)}
    </FieldGroup>
    <FieldDescription>Die Vorschläge sind noch nicht reserviert. Auftrag-ID und PLC-Auftragsnummer können unabhängig geändert werden.</FieldDescription>
    <fieldset className="flex min-w-0 flex-col gap-4" disabled={disabled}>
      <legend className="mb-3 text-base font-semibold">Produkte</legend>
      {draft.rows.map((row, index) => <FieldGroup key={row.key} className="grid gap-3 border-b border-border pb-4 sm:grid-cols-[minmax(0,1fr)_7rem_auto] sm:items-start">
        <Field data-invalid={!!errors[`product.${index}`]}>
          <FieldLabel htmlFor={`entry-product-${index}`}>Produkt {index + 1}</FieldLabel>
          <Select value={row.product} disabled={disabled} onValueChange={value => rowChange(index, 'product', value)}>
            <SelectTrigger id={`entry-product-${index}`} className="w-full min-w-0" aria-invalid={!!errors[`product.${index}`]}
              aria-describedby={errors[`product.${index}`] ? `error-product-${index}` : undefined}><SelectValue placeholder="Produkt auswählen" /></SelectTrigger>
            <SelectContent><SelectGroup>{context.products.map(product => <SelectItem key={product.product_id} value={String(product.product_id)}>
              {product.product_text} · ID {product.product_id}
            </SelectItem>)}</SelectGroup></SelectContent>
          </Select>
          {errors[`product.${index}`] && <FieldError id={`error-product-${index}`}>{errors[`product.${index}`]}</FieldError>}
        </Field>
        <Field data-invalid={!!errors[`quantity.${index}`]}>
          <FieldLabel htmlFor={`entry-quantity-${index}`}>Menge {index + 1} (Stk.)</FieldLabel>
          <Input id={`entry-quantity-${index}`} type="number" min={1} max={context.capacity ?? 255} step={1} value={row.quantity}
            disabled={disabled} aria-invalid={!!errors[`quantity.${index}`]}
            aria-describedby={errors[`quantity.${index}`] ? `error-quantity-${index}` : undefined}
            onChange={event => rowChange(index, 'quantity', event.target.value)} />
          {errors[`quantity.${index}`] && <FieldError id={`error-quantity-${index}`}>{errors[`quantity.${index}`]}</FieldError>}
        </Field>
        <Button type="button" variant="ghost" className="sm:mt-7" disabled={disabled || draft.rows.length === 1}
          aria-label={`Produktzeile ${index + 1} entfernen`} onClick={() => onChange({ ...draft, rows: draft.rows.filter((_, position) => position !== index) })}>Entfernen</Button>
      </FieldGroup>)}
      <Button type="button" variant="outline" className="self-start" disabled={disabled || draft.rows.length >= (context.capacity ?? 255)}
        onClick={() => onChange({ ...draft, rows: [...draft.rows, { key: Math.max(...draft.rows.map(row => row.key)) + 1, product: '', quantity: '1' }] })}>Produkt hinzufügen</Button>
      <p className="text-sm tabular-nums" aria-live="polite">Gesamtmenge: {total} Stk. · Maximal {context.capacity ?? 'unbekannt'} Stk.</p>
      {errors.products && <FieldError>{errors.products}</FieldError>}
    </fieldset>
    {input('serial_start', 'Seriennummer ab', 'number', 0, 65535)}
    <FieldDescription>Fortlaufend über alle Produktzeilen dieses Auftrags. Bereich: {draft.serial_start || '—'} bis {total > 0 ? Number(draft.serial_start) + total - 1 : '—'}.</FieldDescription>
    <FieldGroup className="grid gap-4 sm:grid-cols-2">
      {input('start_date', 'Startdatum', 'date', '1990-01-01', '2168-12-31')}{input('start_time', 'Startzeit', 'time')}
    </FieldGroup>
    <FieldDescription>Lokale Anlagenzeit ({context.plant_timezone}). Diese Angaben sind keine bestätigten Laufzeitpunkte.</FieldDescription>
    {input('customer', 'Kundennummer (optional)', 'number', 0, 65535)}
    <details className="rounded-sm border border-border p-4">
      <summary className="cursor-pointer text-sm font-medium">Weitere Angaben</summary>
      <FieldGroup className="mt-4 grid gap-4 sm:grid-cols-3">
        {input('priority', 'Priorität', 'number', 0, 2)}
        {input('parameter_zero', 'Parameter 0', 'number', 0, 255)}{input('parameter_one', 'Parameter 1', 'number', 0, 255)}
      </FieldGroup>
      <FieldDescription className="mt-3">Priorität verändert die gemeinsame MES-Reihenfolge nicht.</FieldDescription>
    </details>
  </FieldGroup>
}
