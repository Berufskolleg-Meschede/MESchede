'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import { Activity, ChartLine } from 'lucide-react'
import { api } from '@/lib/api'
import type { AnalyticsRun } from '@/lib/types'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

type OrderFilter = 'all' | 'production' | 'delivery'

function dateValue(daysAgo: number): string {
  const value = new Date()
  value.setDate(value.getDate() - daysAgo)
  return value.toISOString().slice(0, 10)
}

function formatDate(value: string | null): string {
  if (!value) return 'Unbekannt'
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

function formatDuration(seconds: number | null): string {
  if (seconds === null || !Number.isFinite(seconds) || seconds < 0) return 'Unbekannt'
  const wholeSeconds = Math.floor(seconds)
  const minutes = Math.floor(wholeSeconds / 60)
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  const remainingSeconds = wholeSeconds % 60
  if (hours) return `${hours} h ${remainingMinutes} min`
  if (minutes) return `${minutes} min ${remainingSeconds} s`
  return `${remainingSeconds} s`
}

function runDuration(run: AnalyticsRun, now: number): number | null {
  if (!run.started_at) return null
  const end = run.ended_at ? new Date(run.ended_at).getTime() : run.status === 'running' ? now : null
  if (end === null) return null
  return Math.max(0, (end - new Date(run.started_at).getTime()) / 1000)
}

function quantity(value: number | null): string {
  return value === null ? 'Unbekannt' : `${value} Stk.`
}

export default function AnalyticsPage() {
  const [from, setFrom] = useState(dateValue(30))
  const [to, setTo] = useState(dateValue(0))
  const [orderFilter, setOrderFilter] = useState<OrderFilter>('all')
  const [runs, setRuns] = useState<AnalyticsRun[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [now, setNow] = useState(Date.now())

  const refresh = useCallback(async () => {
    try {
      const data = await api.analytics.list({
        from,
        to,
        order_type: orderFilter === 'all' ? undefined : orderFilter,
      })
      setRuns(data)
      setError(false)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [from, to, orderFilter])

  useEffect(() => {
    setLoading(true)
    void refresh()
  }, [refresh])

  useEffect(() => {
    const refreshTimer = window.setInterval(() => void refresh(), 5000)
    return () => window.clearInterval(refreshTimer)
  }, [refresh])

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])

  const totals = useMemo(() => runs.reduce((result, run) => {
    if (run.order_type === 'production') result.production += run.good_quantity ?? 0
    else result.delivery += run.good_quantity ?? 0
    return result
  }, { production: 0, delivery: 0 }), [runs])
  const productionKnown = runs.some(run => run.order_type === 'production' && run.good_quantity !== null)
  const deliveryKnown = runs.some(run => run.order_type === 'delivery' && run.good_quantity !== null)

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-5 md:p-8 lg:p-10">
      <header className="border-b border-border pb-5">
        <p className="mb-2 text-xs text-muted-foreground">Fertigungssteuerung / Auswertung</p>
        <h1 className="text-2xl font-semibold tracking-tight">Analysen</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">Beobachtete Auftragsläufe, Mengen und Zeiten</p>
      </header>

      {error && <p role="alert" className="rounded-sm border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">Analysedaten konnten nicht geladen werden. Backend-Verbindung prüfen und erneut versuchen.</p>}

      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border md:grid-cols-4">
        <div className="bg-card px-5 py-4"><p className="text-sm text-muted-foreground">Auftragsläufe</p><p className="mt-2 text-2xl font-semibold tabular-nums">{loading || error ? '-' : runs.length}</p></div>
        <div className="bg-card px-5 py-4"><p className="text-sm text-muted-foreground">Gute Produktion</p><p className="mt-2 text-2xl font-semibold tabular-nums">{loading || error || !productionKnown ? 'Unbekannt' : `${totals.production} Stk.`}</p></div>
        <div className="bg-card px-5 py-4"><p className="text-sm text-muted-foreground">Gute Lieferungen</p><p className="mt-2 text-2xl font-semibold tabular-nums">{loading || error || !deliveryKnown ? 'Unbekannt' : `${totals.delivery} Stk.`}</p></div>
        <div className="bg-card px-5 py-4"><p className="text-sm text-muted-foreground">Ergebnisse unbekannt</p><p className="mt-2 text-2xl font-semibold tabular-nums">{loading || error ? '-' : runs.filter(run => run.good_quantity === null || run.defective_quantity === null).length}</p></div>
      </div>

      <section className="rounded-sm border border-border bg-card" aria-labelledby="analytics-filter-title">
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <ChartLine size={16} strokeWidth={1.5} className="text-muted-foreground" aria-hidden="true" />
          <h2 id="analytics-filter-title" className="text-base font-semibold">Zeitraum und Auftragsart</h2>
        </div>
        <div className="grid gap-4 p-5 sm:grid-cols-3">
          <label className="grid gap-1.5 text-sm">Von
            <input type="date" value={from} max={to} onChange={event => setFrom(event.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
          </label>
          <label className="grid gap-1.5 text-sm">Bis
            <input type="date" value={to} min={from} onChange={event => setTo(event.target.value)} className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" />
          </label>
          <label className="grid gap-1.5 text-sm">Auftragsart
            <select value={orderFilter} onChange={event => setOrderFilter(event.target.value as OrderFilter)} className="h-9 rounded-md border border-input bg-background px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <option value="all">Produktion und Lieferung</option>
              <option value="production">Produktion</option>
              <option value="delivery">Lieferung</option>
            </select>
          </label>
        </div>
      </section>

      <section className="overflow-hidden rounded-sm border border-border bg-card" aria-labelledby="runs-title">
        <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex items-center gap-3"><Activity size={16} strokeWidth={1.5} className="text-muted-foreground" aria-hidden="true" /><h2 id="runs-title" className="text-base font-semibold">Einzelne Läufe</h2></div>
          <span aria-live="polite" className="text-xs text-muted-foreground">{loading || error ? '-' : `${runs.length} Läufe`}</span>
        </div>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader><TableRow className="bg-secondary/35 hover:bg-secondary/35">
              <TableHead className="px-5 text-xs text-muted-foreground">Auftrag</TableHead>
              <TableHead className="text-xs text-muted-foreground">Art</TableHead>
              <TableHead className="text-xs text-muted-foreground">Status</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground">Soll</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground">Bearbeitet</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground">Gut</TableHead>
              <TableHead className="text-right text-xs text-muted-foreground">Fehler</TableHead>
              <TableHead className="text-xs text-muted-foreground">Start</TableHead>
              <TableHead className="text-xs text-muted-foreground">Ende</TableHead>
              <TableHead className="px-5 text-right text-xs text-muted-foreground">Dauer</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {loading || error || runs.length === 0 ? <TableRow><TableCell colSpan={10} className="px-5 py-10 text-sm text-muted-foreground">{loading ? 'Lade Analysedaten.' : error ? 'Keine Daten verfügbar.' : 'Für diesen Zeitraum liegen keine Auftragsläufe vor.'}</TableCell></TableRow> : runs.map(run => {
                const duration = runDuration(run, now)
                return <TableRow key={run.id}>
                  <TableCell className="px-5 py-3.5"><span className="font-mono text-xs">#{run.order_id}</span><span className="ml-2 text-xs text-muted-foreground">PLC #{run.plc_order_number ?? '–'}</span></TableCell>
                  <TableCell>{run.order_type === 'production' ? 'Produktion' : 'Lieferung'}</TableCell>
                  <TableCell className="text-sm">
                    {run.status === 'queued' ? 'Wartet' : run.status === 'running' ? 'Läuft' : run.status === 'completed' ? 'Abgeschlossen' : run.status === 'review_required' ? 'Prüfung nötig' : (
                      <span title={run.last_error_type ?? undefined}>
                        Laufstatus unbekannt
                        {run.last_error_type && <span className="block text-xs text-muted-foreground">{run.last_error_type === 'BackendRestart' ? 'nach Backend-Neustart' : 'Steuerungsrückmeldung ausgefallen'}</span>}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">{quantity(run.planned_quantity)}</TableCell>
                  <TableCell className="text-right tabular-nums">{quantity(run.processed_quantity)}</TableCell>
                  <TableCell className="text-right tabular-nums">{quantity(run.good_quantity)}</TableCell>
                  <TableCell className="text-right tabular-nums">{quantity(run.defective_quantity)}</TableCell>
                  <TableCell className="whitespace-nowrap text-sm text-muted-foreground">{formatDate(run.started_at)}</TableCell>
                  <TableCell className="whitespace-nowrap text-sm text-muted-foreground">{formatDate(run.ended_at)}</TableCell>
                  <TableCell className="whitespace-nowrap px-5 text-right text-sm tabular-nums">{duration === null ? 'Unbekannt' : `${run.status === 'running' ? 'Vorläufig · ' : ''}${formatDuration(duration)}`}</TableCell>
                </TableRow>
              })}
            </TableBody>
          </Table>
        </div>
      </section>
    </div>
  )
}
