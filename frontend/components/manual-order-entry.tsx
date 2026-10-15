'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { api, OrderApiError } from '@/lib/api'
import type { OrderAdmission, OrderPayload, OrderType } from '@/lib/types'
import { completeOrderInput, inputFieldErrors, orderDraft, orderPayload, sameOrder, type InputErrors, type OrderDraft } from '@/lib/order-input'
import { useOrderSnapshot } from '@/hooks/use-order-snapshot'
import { OrderEntryFields } from '@/components/order-entry-fields'
import { OrderEntrySummary } from '@/components/order-entry-summary'
import { Button } from '@/components/ui/button'
import { FieldError } from '@/components/ui/field'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'

interface OrderAttempt { payload: OrderPayload; draft: OrderDraft }
type EntryPhase = 'edit' | 'review' | 'checking' | 'uncertain' | 'missing' | 'conflict'
const storageKey = (type: OrderType) => `meschede.order-attempt.v1.${type}`

function readAttempt(type: OrderType): OrderAttempt | null {
  const saved = sessionStorage.getItem(storageKey(type))
  if (!saved) { return null }
  const attempt: OrderAttempt = JSON.parse(saved)
  if (!attempt.payload?.order_id || !attempt.payload.mes_auftrag?.kopf || !Array.isArray(attempt.draft?.rows)) {
    throw new Error('Der gespeicherte Sendeversuch ist nicht lesbar. Bitte den Annahmestand in der Auftragsübersicht prüfen.')
  }
  return attempt
}

/** Stellt unaufgeklärte Versuche nach Reload wieder her, bevor eine neue Erfassung möglich ist. */
export function ManualOrderEntry({ type, blockedReason, onAccepted, onInspect }: {
  type: OrderType; blockedReason?: string | null; onAccepted: (order: OrderAdmission) => void; onInspect: (id: string) => void
}) {
  const [ready, setReady] = useState(false)
  const [open, setOpen] = useState(false)
  const [initial, setInitial] = useState<OrderAttempt | null>(null)
  const [error, setError] = useState<string | null>(null)
  const trigger = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    let active = true
    void Promise.resolve().then(() => {
      if (!active) { return }
      try {
        const attempt = readAttempt(type)
        setInitial(attempt)
        setOpen(!!attempt)
        setReady(true)
      } catch (failure) { setError(failure instanceof Error ? failure.message : 'Der Sendeversuch konnte nicht gelesen werden.') }
    })
    return () => { active = false }
  }, [type])
  function start() {
    try { setInitial(readAttempt(type)); setOpen(true); setError(null) }
    catch (failure) { setError(failure instanceof Error ? failure.message : 'Die Erfassung konnte nicht geöffnet werden.') }
  }
  const accepted = useCallback((order: OrderAdmission) => {
    setOpen(false)
    setInitial(null)
    onAccepted(order)
    requestAnimationFrame(() => trigger.current?.focus())
  }, [onAccepted])
  return <div className="flex flex-col items-start gap-2">
    <Button ref={trigger} onClick={start} disabled={!ready}>Neuer Auftrag</Button>
    {error && <FieldError>{error}</FieldError>}
    {open && <OrderEntryDialog type={type} initial={initial} blockedReason={blockedReason} onClose={() => {
      setOpen(false); requestAnimationFrame(() => trigger.current?.focus())
    }} onAccepted={accepted} onInspect={id => { setOpen(false); onInspect(id) }} />}
  </div>
}

function OrderEntryDialog({ type, initial, blockedReason, onClose, onAccepted, onInspect }: {
  type: OrderType; initial: OrderAttempt | null; blockedReason?: string | null
  onClose: () => void; onAccepted: (order: OrderAdmission) => void; onInspect: (id: string) => void
}) {
  const [draft, setDraft] = useState<OrderDraft | null>(initial?.draft ?? null)
  const [payload, setPayload] = useState<OrderPayload | null>(initial?.payload ?? null)
  const [phase, setPhase] = useState<EntryPhase>(initial ? 'checking' : 'edit')
  const [saving, setSaving] = useState(false)
  const [synchronizing, setSynchronizing] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [errors, setErrors] = useState<InputErrors>({})
  const [now, setNow] = useState(() => Date.now())
  const submitting = useRef(false)
  const form = useRef<HTMLFormElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const load = useCallback(async (signal: AbortSignal) => {
    const context = await api.inputContext(type, signal)
    if (!signal.aborted) { setDraft(previous => previous ?? orderDraft(context)) }
    return context
  }, [type])
  const preparation = useOrderSnapshot(`entry:${type}`, load)
  const locked = saving || synchronizing || phase === 'checking'
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 500)
    return () => clearInterval(timer)
  }, [])

  const finish = useCallback((order: OrderAdmission) => {
    try { sessionStorage.removeItem(storageKey(type)) } catch { /* Ein verbliebener Versuch wird beim Reload erneut nur lesend abgeglichen. */ }
    onAccepted(order)
  }, [type, onAccepted])

  const check = useCallback(async (attempt: OrderPayload) => {
    if (submitting.current) { return }
    submitting.current = true
    setPhase('checking')
    setMessage('Die Annahme wird geprüft…')
    try {
      const detail = await api.detail(type, attempt.order_id)
      if (!completeOrderInput(detail.mes_auftrag) || detail.order_type !== type || typeof detail.order_ref !== 'string' || typeof detail.run_id !== 'string') {
        throw new Error('Der gespeicherte Auftrag konnte nicht vollständig geprüft werden.')
      }
      if (!sameOrder(attempt, detail)) {
        setPhase('conflict')
        setMessage('Unter dieser Auftrag-ID sind andere Daten gespeichert. Bitte den bestehenden Auftrag in der Übersicht prüfen.')
        return
      }
      finish({ order_id: detail.order_id, order_ref: detail.order_ref, run_id: detail.run_id,
        accepted_sequence: detail.accepted_sequence, queue_size: 0, queued: detail.run_phase === 'queued' })
    } catch (failure) {
      const missing = failure instanceof OrderApiError && failure.status === 404
      setPhase(missing ? 'missing' : 'uncertain')
      setMessage(missing ? 'Der Auftrag wurde noch nicht gespeichert gefunden. Du kannst denselben Auftrag erneut senden.' :
        'Die Annahme ist noch unklar. Bitte erneut prüfen, bevor der Auftrag wieder gesendet wird.')
    } finally { submitting.current = false }
  }, [type, finish])

  useEffect(() => { if (initial) { void check(initial.payload) } }, [initial, check])

  function review() {
    if (!draft || !preparation.data) { return }
    const result = orderPayload(draft, preparation.data)
    setErrors(result.errors)
    setMessage(null)
    if (!result.payload) {
      requestAnimationFrame(() => form.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus())
      return
    }
    setPayload(result.payload)
    setPhase('review')
    requestAnimationFrame(() => heading.current?.focus())
  }

  async function send() {
    if (submitting.current || !payload || !draft || (phase !== 'review' && phase !== 'missing')) { return }
    try { sessionStorage.setItem(storageKey(type), JSON.stringify({ payload, draft })) }
    catch { setMessage('Der Sendeversuch konnte nicht gesichert werden. Bitte den Browserspeicher prüfen. Es wurde nichts gesendet.'); return }
    submitting.current = true
    setSaving(true)
    setMessage(null)
    try {
      const result = await api.createOrder(type, payload)
      if (result.order_id !== payload.order_id || typeof result.run_id !== 'string' || !result.run_id || typeof result.order_ref !== 'string' || !result.order_ref) {
        throw new Error('Die Annahmeantwort ist unvollständig.')
      }
      finish(result)
    } catch (failure) {
      if (failure instanceof OrderApiError && [409, 422].includes(failure.status)) {
        try { sessionStorage.removeItem(storageKey(type)) } catch { /* Der Request ist belegt abgelehnt; ein verbliebener Versuch wird später lesend geprüft. */ }
        setErrors(inputFieldErrors(failure.fieldErrors, draft))
        setMessage(failure.message)
        setPhase('edit')
        requestAnimationFrame(() => form.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus())
      } else {
        submitting.current = false
        await check(payload)
      }
    } finally { submitting.current = false; setSaving(false) }
  }

  async function synchronizeCatalog() {
    if (synchronizing) { return }
    setSynchronizing(true)
    setMessage(null)
    try {
      await api.synchronizeCatalog(type)
      preparation.reload()
    } catch (failure) {
      setMessage(failure instanceof Error ? failure.message : 'Der Produktkatalog konnte nicht abgeglichen werden.')
      preparation.reload()
    } finally { setSynchronizing(false) }
  }

  const fresh = preparation.data?.observed_at && now - Date.parse(preparation.data.observed_at) < preparation.data.stale_after_s * 1000
  const canSubmit = preparation.data?.available && !preparation.error && fresh
  return <Dialog open onOpenChange={value => { if (!value && !locked) { onClose() } }}>
    <DialogContent showCloseButton={!locked} className="max-h-[90dvh] overflow-y-auto sm:max-w-2xl">
      <DialogHeader><DialogTitle ref={heading} tabIndex={-1}>{phase === 'edit' ? 'Neuer Auftrag' : phase === 'review' ? 'Auftrag prüfen' : 'Auftragannahme prüfen'}</DialogTitle>
        <DialogDescription>{type === 'production' ? 'Fertigungsauftrag' : 'Lieferauftrag'} erfassen und nach Prüfung in die gemeinsame MES-Warteschlange stellen.</DialogDescription></DialogHeader>
      {blockedReason && <Alert><AlertDescription>Der tatsächliche Start wartet: {blockedReason}</AlertDescription></Alert>}
      {(preparation.error || preparation.data?.error) && <Alert variant="destructive"><AlertDescription>{preparation.error ?? preparation.data?.error}</AlertDescription></Alert>}
      {preparation.data?.available && !fresh && <Alert variant="destructive"><AlertDescription>Die Produktdaten sind veraltet. Bitte erneut laden.</AlertDescription></Alert>}
      {message && <p role={phase === 'checking' ? 'status' : 'alert'} className="text-sm">{message}</p>}
      {phase === 'edit' ? draft && preparation.data ? <form ref={form} id="manual-order-entry" noValidate onSubmit={event => { event.preventDefault(); review() }}>
        <OrderEntryFields draft={draft} context={preparation.data} errors={errors} disabled={locked || !canSubmit}
          onChange={value => { setDraft(value); setErrors({}); setMessage(null) }} />
      </form> : <p className="text-sm text-muted-foreground">Lade Erfassungsvoraussetzungen…</p> :
        payload && draft && <OrderEntrySummary payload={payload} draft={draft} type={type} />}
      <DialogFooter className="flex-wrap">
        <Button variant="ghost" disabled={locked} onClick={onClose}>{phase === 'edit' || phase === 'review' ? 'Abbrechen' : 'Schließen'}</Button>
        {phase === 'edit' && <>
          <Button variant="outline" disabled={locked} onClick={() => void synchronizeCatalog()}>{synchronizing ? 'Gleicht ab…' : 'Produktdaten abgleichen'}</Button>
          {draft && preparation.data && <Button variant="outline" disabled={locked || !canSubmit} onClick={() => {
            setDraft({ ...draft, order_id: preparation.data!.suggested_order_id ?? '', plc_number: preparation.data!.suggested_plc_order_number?.toString() ?? '' })
            setErrors({}); setMessage(null)
          }}>ID-Vorschläge übernehmen</Button>}
          <Button type="submit" form="manual-order-entry" disabled={locked || !canSubmit || !draft}>Zusammenfassung anzeigen</Button>
        </>}
        {phase === 'review' && <>
          <Button variant="outline" disabled={locked} onClick={() => setPhase('edit')}>Zurück</Button>
          <Button disabled={locked || !canSubmit} onClick={() => void send()}>{saving ? 'Sendet…' : 'Auftrag annehmen'}</Button>
        </>}
        {phase === 'missing' && <Button disabled={locked} onClick={() => void send()}>{saving ? 'Sendet…' : 'Denselben Auftrag erneut senden'}</Button>}
        {phase === 'conflict' && payload && <Button variant="outline" onClick={() => onInspect(payload.order_id)}>Bestehenden Auftrag anzeigen</Button>}
        {phase === 'conflict' && <Button variant="outline" onClick={() => {
          try { sessionStorage.removeItem(storageKey(type)) } catch { /* Der abweichende gespeicherte Inhalt ist bereits lesend belegt. */ }
          setPhase('edit'); setPayload(null); setErrors({})
          setMessage('Bitte den Entwurf korrigieren und die geänderten Angaben erneut prüfen.')
        }}>Entwurf korrigieren</Button>}
        {(phase === 'uncertain' || phase === 'missing' || phase === 'conflict') && <Button variant="outline" disabled={locked} onClick={() => payload && void check(payload)}>Annahme prüfen</Button>}
      </DialogFooter>
    </DialogContent>
  </Dialog>
}
