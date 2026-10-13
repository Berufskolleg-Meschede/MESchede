'use client'

import { useCallback, useEffect, useState } from 'react'
import { Package } from 'lucide-react'
import { api } from '@/lib/api'
import type { StorageItem, StorageStatus } from '@/lib/types'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

function formatUpdatedAt(value: string | null): string {
  if (!value) return 'Noch kein Bestand empfangen'
  return new Intl.DateTimeFormat('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function InventoryPage() {
  const [items, setItems] = useState<StorageItem[]>([])
  const [status, setStatus] = useState<StorageStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const refreshInventory = useCallback(async () => {
    try {
      const [storageItems, consumerStatus] = await Promise.all([
        api.storage.list(),
        api.storage.status(),
      ])
      setItems(storageItems)
      setStatus(consumerStatus)
      setError(false)
    } catch {
      setError(true)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refreshInventory()
    const refreshTimer = window.setInterval(() => {
      void refreshInventory()
    }, 5000)
    return () => window.clearInterval(refreshTimer)
  }, [refreshInventory])

  const knownItems = items.filter(item => item.quantity !== null)
  const totalQuantity = knownItems.reduce((sum, item) => sum + (item.quantity ?? 0), 0)
  const unknownCount = items.length - knownItems.length
  const isBrokerUnavailable = status !== null && !status.connected
  const isItemStale = (item: StorageItem): boolean => {
    if (isBrokerUnavailable || !item.updated_at || !status) return true
    const age = Date.now() - new Date(item.updated_at).getTime()
    return age > status.stale_after_seconds * 1000
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-5 md:p-8 lg:p-10">
      <header className="border-b border-border pb-5">
        <h1 className="text-2xl font-semibold tracking-tight">Lagerbestände</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          {loading ? 'Lade Bestände.' : `${items.length} Artikel im Lager`}
        </p>
      </header>

      {error && (
        <p role="alert" className="rounded-sm border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          Lagerdaten oder Verbindungsstatus konnten nicht geladen werden.
        </p>
      )}

      {!error && status && !status.configured && (
        <p role="status" className="rounded-sm border border-border bg-secondary/35 p-3 text-sm">
          RabbitMQ ist noch nicht konfiguriert. Angezeigte Bestände stammen aus der letzten Speicherung.
        </p>
      )}

      {!error && status?.configured && !status.connected && (
        <p role="status" className="rounded-sm border border-amber-600/40 bg-amber-500/5 p-3 text-sm">
          RabbitMQ ist nicht erreichbar. Letzte gespeicherte Bestände bleiben erhalten und sind als veraltet markiert.
        </p>
      )}

      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-sm border border-border bg-border md:grid-cols-3">
        <div className="min-w-0 bg-card px-5 py-4">
          <p className="text-sm text-muted-foreground">Artikel</p>
          <p className="mt-2 text-2xl font-semibold tabular-nums leading-none">{loading || error ? '–' : items.length}</p>
        </div>
        <div className="min-w-0 bg-card px-5 py-4">
          <p className="text-sm text-muted-foreground">Bekannter Gesamtbestand</p>
          <p className="mt-2 text-2xl font-semibold tabular-nums leading-none">
            {loading || error ? '–' : `${totalQuantity} Stk.`}
          </p>
        </div>
        <div className="min-w-0 bg-card px-5 py-4">
          <p className="text-sm text-muted-foreground">Bestand unbekannt</p>
          <p className="mt-2 text-2xl font-semibold tabular-nums leading-none">
            {loading || error ? '–' : unknownCount}
          </p>
        </div>
      </div>

      <section className="overflow-hidden rounded-sm border border-border bg-card" aria-labelledby="inventory-title">
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <Package size={16} strokeWidth={1.5} className="text-muted-foreground" aria-hidden="true" />
          <h2 id="inventory-title" className="text-base font-semibold">Bestandsübersicht</h2>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-secondary/35 hover:bg-secondary/35">
              <TableHead className="w-24 px-5 text-xs font-medium text-muted-foreground">ID</TableHead>
              <TableHead className="text-xs font-medium text-muted-foreground">Artikel</TableHead>
              <TableHead className="w-32 text-right text-xs font-medium text-muted-foreground">Verfügbar</TableHead>
              <TableHead className="w-64 text-xs font-medium text-muted-foreground">Letzte Aktualisierung</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="px-5 py-12 text-center text-sm text-muted-foreground">
                  Lade Lagerbestände.
                </TableCell>
              </TableRow>
            ) : error ? (
              <TableRow>
                <TableCell colSpan={4} className="px-5 py-12 text-center text-sm text-muted-foreground">
                  Keine Daten verfügbar.
                </TableCell>
              </TableRow>
            ) : items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="px-5 py-12 text-center text-sm text-muted-foreground">
                  Noch keine Bestandsdaten empfangen.
                </TableCell>
              </TableRow>
            ) : (
              items.map(item => {
                const stale = isItemStale(item)
                return (
                  <TableRow key={item.id ?? item.article_id} className="border-border hover:bg-secondary/40">
                    <TableCell className="px-5 py-3.5">
                      <span className="font-mono text-xs text-muted-foreground">#{item.article_id}</span>
                    </TableCell>
                    <TableCell className="text-sm text-foreground">
                      {item.article?.name ?? `Artikel #${item.article_id}`}
                    </TableCell>
                    <TableCell className="text-right text-sm tabular-nums text-foreground">
                      {item.quantity === null ? 'Unbekannt' : item.quantity}
                      {item.quantity !== null && <span className="ml-1 text-xs text-muted-foreground">Stk.</span>}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      <span>{formatUpdatedAt(item.updated_at)}</span>
                      {stale && <span className="ml-2 text-amber-700">Veraltet</span>}
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </section>
    </div>
  )
}
