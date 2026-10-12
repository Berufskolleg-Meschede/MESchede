'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowRight } from 'lucide-react'
import { api } from '@/lib/api'
import type { ProductionOrder, DeliveryOrder, Machine, OrderStatus } from '@/lib/types'
import { StatCard } from '@/components/stat-card'
import { StatusBadge } from '@/components/status-badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const PRIORITY: Record<OrderStatus, number> = { error: 0, in_progress: 1, pending: 2, completed: 3 }

export default function DashboardPage() {
  const [productionOrders, setProductionOrders] = useState<ProductionOrder[]>([])
  const [deliveryOrders, setDeliveryOrders] = useState<DeliveryOrder[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([api.productionOrders.list(), api.deliveryOrders.list(), api.machines.list()])
      .then(([production, delivery, machineData]) => {
        if (cancelled) return
        setProductionOrders(production)
        setDeliveryOrders(delivery)
        setMachines(machineData)
      })
      .catch(() => { if (!cancelled) setError(true) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const orders = [
    ...productionOrders.map(order => ({ ...order, type: 'Produktion', href: '/production-orders' })),
    ...deliveryOrders.map(order => ({ ...order, type: 'Lieferung', href: '/delivery-orders' })),
  ]
  const openOrders = orders.filter(order => order.status !== 'completed')
    .sort((a, b) => PRIORITY[a.status] - PRIORITY[b.status] || a.id - b.id)
  const online = machines.filter(machine => machine.status === 'online').length
  const volume = productionOrders.reduce<Record<string, number>>((result, order) => {
    const article = order.article?.name ?? `Artikel #${order.article_id}`
    result[article] = (result[article] ?? 0) + order.quantity
    return result
  }, {})
  const articles = Object.entries(volume).sort((a, b) => b[1] - a[1])
  const maximum = Math.max(...articles.map(([, quantity]) => quantity), 1)

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-5 md:p-8 lg:p-10">
      <header className="border-b border-border pb-5">
        <p className="mb-2 text-xs text-muted-foreground">Fertigungssteuerung / Übersicht</p>
        <h1 className="text-2xl font-semibold tracking-tight">Betriebsübersicht</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">Offene Aufträge und Maschinen im Überblick.</p>
      </header>
      {error && <p role="alert" className="rounded-sm border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">Die Übersicht konnte nicht geladen werden. Bitte lade die Seite erneut.</p>}
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border md:grid-cols-4">
        <StatCard label="Offene Aufträge" value={loading || error ? '—' : openOrders.length} />
        <StatCard label="In Bearbeitung" value={loading || error ? '—' : orders.filter(order => order.status === 'in_progress').length} />
        <StatCard label="Aufträge mit Fehler" value={loading || error ? '—' : orders.filter(order => order.status === 'error').length} />
        <StatCard label="Maschinen online" value={loading || error ? '—' : `${online} / ${machines.length}`} />
      </div>
      <section className="overflow-hidden rounded-sm border border-border bg-card" aria-labelledby="open-orders-title">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div>
            <h2 id="open-orders-title" className="text-base font-semibold">Offene Aufträge</h2>
            <p className="mt-1 text-xs text-muted-foreground">Fehler und laufende Aufträge zuerst.</p>
          </div>
          <Link href="/production-orders" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring">Zur Produktion <ArrowRight size={14} aria-hidden="true" /></Link>
        </div>
        <Table>
          <TableHeader><TableRow className="bg-secondary/35 hover:bg-secondary/35">
            <TableHead className="px-5 text-xs text-muted-foreground">Auftrag</TableHead>
            <TableHead className="text-xs text-muted-foreground">Bereich</TableHead>
            <TableHead className="text-xs text-muted-foreground">Artikel</TableHead>
            <TableHead className="text-right text-xs text-muted-foreground">Menge</TableHead>
            <TableHead className="px-5 text-xs text-muted-foreground">Status</TableHead>
          </TableRow></TableHeader>
          <TableBody>
            {loading || error || openOrders.length === 0 ? <TableRow><TableCell colSpan={5} className="px-5 py-10 text-sm text-muted-foreground">{loading ? 'Lade Aufträge…' : error ? 'Keine Daten verfügbar.' : 'Keine offenen Aufträge.'}</TableCell></TableRow>
              : openOrders.map(order => <TableRow key={`${order.type}-${order.id}`}>
                <TableCell className="px-5 py-3"><Link href={order.href} className="font-mono text-xs underline decoration-border underline-offset-4 hover:decoration-foreground">#{String(order.id).padStart(4, '0')}</Link></TableCell>
                <TableCell className="text-muted-foreground">{order.type}</TableCell>
                <TableCell>{order.article?.name ?? `Artikel #${order.article_id}`}</TableCell>
                <TableCell className="text-right tabular-nums">{order.quantity} <span className="text-xs text-muted-foreground">Stk.</span></TableCell>
                <TableCell className="px-5"><StatusBadge status={order.status} /></TableCell>
              </TableRow>)}
          </TableBody>
        </Table>
      </section>
      <div className="grid gap-6 xl:grid-cols-[3fr_2fr]">
        <section className="rounded-sm border border-border bg-card" aria-labelledby="machines-title">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <h2 id="machines-title" className="text-base font-semibold">Maschinen</h2>
            <span className="text-xs text-muted-foreground">{loading || error ? '—' : `${online} von ${machines.length} online`}</span>
          </div>
          <div className="divide-y divide-border px-5">
            {loading || error ? <p className="py-6 text-sm text-muted-foreground">{loading ? 'Lade Maschinen…' : 'Keine Daten verfügbar.'}</p> : machines.length === 0 ? <p className="py-6 text-sm text-muted-foreground">Keine Maschinen vorhanden.</p> : machines.map(machine => (
              <div key={machine.id} className="flex items-center justify-between gap-4 py-3.5">
                <div><p className="text-sm">{machine.name}</p><p className="mt-1 text-xs text-muted-foreground"><span className="font-mono">M-{String(machine.id).padStart(2, '0')}</span> · {machine.type}</p></div>
                <StatusBadge status={machine.status} />
              </div>
            ))}
          </div>
        </section>
        <section className="rounded-sm border border-border bg-card" aria-labelledby="volume-title">
          <div className="border-b border-border px-5 py-4"><h2 id="volume-title" className="text-base font-semibold">Geplante Stückzahlen</h2><p className="mt-1 text-xs text-muted-foreground">Summe aller Fertigungsaufträge je Artikel</p></div>
          <div className="space-y-5 p-5">
            {loading || error ? <p className="text-sm text-muted-foreground">{loading ? 'Lade Stückzahlen…' : 'Keine Daten verfügbar.'}</p> : articles.length === 0 ? <p className="text-sm text-muted-foreground">Keine Fertigungsaufträge vorhanden.</p> : articles.map(([article, quantity]) => (
              <div key={article}><div className="mb-2 flex items-start justify-between gap-4 text-sm"><span>{article}</span><span className="shrink-0 tabular-nums text-muted-foreground">{quantity} Stk.</span></div><div aria-hidden="true" className="h-1 bg-secondary"><div className="h-1 bg-[#98aaa0]" style={{ width: `${quantity / maximum * 100}%` }} /></div></div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
