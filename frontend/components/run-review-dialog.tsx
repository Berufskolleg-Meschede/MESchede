'use client'

import { useRef, useState } from 'react'
import { api, OrderApiError } from '@/lib/api'
import type { OrderRunView, RunReview } from '@/lib/types'
import { orderLabel, quantity, reviewRequestId } from '@/lib/order-format'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'

function parseQuantity(value: string): number | null {
  if (value.trim() === '') { return null }
  if (!/^\d+$/.test(value) || !Number.isSafeInteger(Number(value))) {
    throw new Error('Bitte ganze, nicht negative Mengen eingeben oder das Feld für „unbekannt“ leer lassen.')
  }
  return Number(value)
}

/** Bewahrt die bearbeitete Version und wiederholt unsicher beantwortete Requests idempotent. */
export function RunReviewDialog({ order, onClose, onSaved }: {
  order: OrderRunView; onClose: () => void; onSaved: () => void
}) {
  const [baseline, setBaseline] = useState(order)
  const [outcome, setOutcome] = useState<RunReview['outcome']>('unknown')
  const [good, setGood] = useState(order.good_quantity?.toString() ?? '')
  const [failed, setFailed] = useState(order.error_quantity?.toString() ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [conflict, setConflict] = useState(false)
  const [invalidQuantities, setInvalidQuantities] = useState(false)
  const request = useRef<{ fingerprint: string; id: string } | null>(null)
  const submitting = useRef(false)

  async function refreshRun() {
    setSaving(true)
    try {
      const current = await api.detail(order.order_type, order.order_id)
      setBaseline(current)
      setConflict(false)
      setError(current.review_required ? null : 'Dieser Lauf wurde inzwischen bewertet. Bitte den Dialog schließen.')
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Der Lauf konnte nicht aktualisiert werden.')
    } finally {
      setSaving(false)
    }
  }

  async function save() {
    if (submitting.current) { return }
    setError(null)
    setInvalidQuantities(false)
    let body: Omit<RunReview, 'request_id'>
    try {
      body = { expected_version: baseline.version, outcome, good_quantity: parseQuantity(good), error_quantity: parseQuantity(failed) }
      if ((body.good_quantity ?? 0) + (body.error_quantity ?? 0) > baseline.planned_quantity) {
        throw new Error('Die Summe aus erfolgreichen und fehlgeschlagenen Einheiten überschreitet die Sollmenge.')
      }
    } catch (failure) {
      setInvalidQuantities(true)
      setError(failure instanceof Error ? failure.message : 'Die Mengen sind ungültig.')
      return
    }
    const fingerprint = JSON.stringify(body)
    if (request.current?.fingerprint !== fingerprint) {
      request.current = { fingerprint, id: reviewRequestId() }
    }
    submitting.current = true
    setSaving(true)
    try {
      await api.review(order.run_id, { ...body, request_id: request.current.id })
      onSaved()
    } catch (failure) {
      setConflict(failure instanceof OrderApiError && failure.status === 409)
      setInvalidQuantities(failure instanceof OrderApiError && failure.status === 422)
      setError(failure instanceof Error ? failure.message : 'Die Prüfung konnte nicht gespeichert werden.')
    } finally {
      submitting.current = false
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={open => { if (!open && !saving) { onClose() } }}>
      <DialogContent showCloseButton={!saving} className="max-h-[90dvh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Lauf {orderLabel(order.order_id)} prüfen</DialogTitle>
          <DialogDescription>Den Ausgang und bekannte Stückzahlen festhalten. Unbekannte Mengen bleiben leer. Eine Erklärung ist nicht erforderlich.</DialogDescription>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">Sollmenge: {quantity(baseline.planned_quantity)} · Bestätigt erfolgreich: {quantity(baseline.good_quantity)} · Fehlgeschlagen: {quantity(baseline.error_quantity)}</p>
        <p className="text-sm">{baseline.review_reason}</p>
        <form id="run-review" onSubmit={event => { event.preventDefault(); void save() }}>
          <FieldGroup>
            <Field data-disabled={saving}>
              <FieldLabel id="review-outcome-label">Laufausgang</FieldLabel>
              <ToggleGroup type="single" variant="outline" value={outcome} disabled={saving}
                aria-labelledby="review-outcome-label" className="flex-wrap"
                onValueChange={value => { if (value) { setOutcome(value as RunReview['outcome']) } }}>
                <ToggleGroupItem value="completed">Abgeschlossen</ToggleGroupItem>
                <ToggleGroupItem value="interrupted">Unterbrochen</ToggleGroupItem>
                <ToggleGroupItem value="unknown">Unklar</ToggleGroupItem>
              </ToggleGroup>
              <FieldDescription>Bei „Unklar“ bleibt die Startsperre bestehen. Nach einer Bewertung muss die Anlage ihre Bereitschaft bestätigen.</FieldDescription>
            </Field>
            <FieldGroup className="grid gap-4 sm:grid-cols-2">
              <Field data-invalid={invalidQuantities} data-disabled={saving}><FieldLabel htmlFor="review-good">Erfolgreiche Einheiten</FieldLabel>
                <Input id="review-good" type="number" min="0" max={baseline.planned_quantity} step="1" value={good} disabled={saving}
                  aria-invalid={invalidQuantities}
                  aria-describedby="review-quantity-help" onChange={event => setGood(event.target.value)} placeholder="Unbekannt" /></Field>
              <Field data-invalid={invalidQuantities} data-disabled={saving}><FieldLabel htmlFor="review-failed">Fehlgeschlagene Einheiten</FieldLabel>
                <Input id="review-failed" type="number" min="0" max={baseline.planned_quantity} step="1" value={failed} disabled={saving}
                  aria-invalid={invalidQuantities}
                  aria-describedby="review-quantity-help" onChange={event => setFailed(event.target.value)} placeholder="Unbekannt" /></Field>
            </FieldGroup>
            <FieldDescription id="review-quantity-help">„Abgeschlossen“ setzt die Gutmenge nicht automatisch auf die Sollmenge. Die Bewertung verändert keine PLC-Signale.</FieldDescription>
            {error && <FieldError>{error}</FieldError>}
            {conflict && <Button type="button" variant="outline" disabled={saving} onClick={() => void refreshRun()}>Aktuelle Laufdaten übernehmen</Button>}
          </FieldGroup>
        </form>
        <DialogFooter>
          <Button variant="ghost" disabled={saving} onClick={onClose}>Abbrechen</Button>
          <Button type="submit" form="run-review" disabled={saving || conflict || !baseline.review_required}>{saving ? 'Speichert…' : 'Bewertung speichern'}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
