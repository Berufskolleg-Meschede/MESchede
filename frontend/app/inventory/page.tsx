'use client'

import { useCallback, useEffect, useState } from 'react'
import { Boxes } from 'lucide-react'
import { api } from '@/lib/api'
import type { LagerSnapshot } from '@/lib/types'
import { StatCard } from '@/components/stat-card'

const EMPTY_SNAPSHOT: LagerSnapshot = {
  gehaeuse: { gesamt: 0, rot: 0, silber: 0, schwarz: 0 },
  deckel_blau: 0,
  deckel_gruen: 0,
  produkte: {
    gesamt: 0, salz_rot: 0, salz_silber: 0, salz_schwarz: 0,
    pfeffer_rot: 0, pfeffer_silber: 0, pfeffer_schwarz: 0,
  },
  observed_at: '',
}

function formatObservedAt(value: string | null): string {
  if (!value) return 'Noch keine Daten empfangen'
  return new Intl.DateTimeFormat('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export default function InventoryPage() {
  const [snapshot, setSnapshot] = useState<LagerSnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const refreshInventory = useCallback(async () => {
    try {
      const data = await api.plcStorage.get()
      setSnapshot(data)
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

  const showDash = loading || error
  const data = snapshot ?? EMPTY_SNAPSHOT
  const value = (n: number): string | number => (showDash ? '–' : n)

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-5 md:p-8 lg:p-10">
      <header className="border-b border-border pb-5">
        <h1 className="text-2xl font-semibold tracking-tight">Lagerbestände</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          {loading ? 'Lade Bestände aus der SPS.' : `Stand: ${formatObservedAt(snapshot?.observed_at ?? null)}`}
        </p>
      </header>

      {error && (
        <p role="alert" className="rounded-sm border border-destructive/40 bg-destructive/5 p-3 text-sm text-destructive">
          Die Lagerbestände konnten nicht von der SPS gelesen werden.
        </p>
      )}

      <section className="overflow-hidden rounded-sm border border-border bg-card" aria-labelledby="deckel-title">
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <Boxes size={16} strokeWidth={1.5} className="text-muted-foreground" aria-hidden="true" />
          <h2 id="deckel-title" className="text-base font-semibold">Deckel</h2>
        </div>
        <div className="grid grid-cols-2 gap-px overflow-hidden bg-border">
          <StatCard label="Blau (Deckelmagazin 1)" value={value(data.deckel_blau)} />
          <StatCard label="Grün (Deckelmagazin 2)" value={value(data.deckel_gruen)} />
        </div>
      </section>

      <section className="overflow-hidden rounded-sm border border-border bg-card" aria-labelledby="gehaeuse-title">
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <Boxes size={16} strokeWidth={1.5} className="text-muted-foreground" aria-hidden="true" />
          <h2 id="gehaeuse-title" className="text-base font-semibold">Gehäuse</h2>
        </div>
        <div className="grid grid-cols-2 gap-px overflow-hidden bg-border md:grid-cols-4">
          <StatCard label="Gesamt" value={value(data.gehaeuse.gesamt)} />
          <StatCard label="Rot" value={value(data.gehaeuse.rot)} />
          <StatCard label="Silber" value={value(data.gehaeuse.silber)} />
          <StatCard label="Schwarz" value={value(data.gehaeuse.schwarz)} />
        </div>
      </section>

      <section className="overflow-hidden rounded-sm border border-border bg-card" aria-labelledby="produkte-title">
        <div className="flex items-center gap-3 border-b border-border px-5 py-4">
          <Boxes size={16} strokeWidth={1.5} className="text-muted-foreground" aria-hidden="true" />
          <h2 id="produkte-title" className="text-base font-semibold">Hochregallager</h2>
        </div>
        <div className="grid grid-cols-2 gap-px overflow-hidden bg-border md:grid-cols-4">
          <StatCard label="Gesamt" value={value(data.produkte.gesamt)} />
          <StatCard label="Salz, Rot" value={value(data.produkte.salz_rot)} />
          <StatCard label="Salz, Silber" value={value(data.produkte.salz_silber)} />
          <StatCard label="Salz, Schwarz" value={value(data.produkte.salz_schwarz)} />
          <StatCard label="Pfeffer, Rot" value={value(data.produkte.pfeffer_rot)} />
          <StatCard label="Pfeffer, Silber" value={value(data.produkte.pfeffer_silber)} />
          <StatCard label="Pfeffer, Schwarz" value={value(data.produkte.pfeffer_schwarz)} />
        </div>
      </section>
    </div>
  )
}
